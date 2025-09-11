import subprocess
import os
import tempfile
import re
from pathlib import Path
from typing import List


def run(cmd: List[str], cwd: Path | None = None, input_bytes: bytes | None = None) -> str:
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(cmd)}\n{result.stderr.decode(errors='ignore')}")
    return result.stdout.decode(errors='ignore').strip()


def ensure_repo(repo_dir: Path, repo_url: str) -> None:
    if not repo_dir.exists():
        run(["git", "clone", repo_url, str(repo_dir)])
    # Fetch all heads and tags
    # Make refspec configuration idempotent: clear existing, then add ours
    try:
        run(["git", "config", "--unset-all", "remote.origin.fetch"], cwd=repo_dir)
    except RuntimeError:
        # Ignore if remote.origin.fetch doesn't exist
        pass
    run(["git", "config", "--add", "remote.origin.fetch", "+refs/heads/*:refs/remotes/origin/*"], cwd=repo_dir)
    run(["git", "config", "--add", "remote.origin.fetch", "+refs/tags/*:refs/tags/*"], cwd=repo_dir)
    # Also fetch GitHub PR refs (head and merge) so --all traverses PRs
    try:
        run(["git", "config", "--add", "remote.origin.fetch", "+refs/pull/*/head:refs/remotes/origin/pr/*"], cwd=repo_dir)
        run(["git", "config", "--add", "remote.origin.fetch", "+refs/pull/*/merge:refs/remotes/origin/pr-merge/*"], cwd=repo_dir)
    except RuntimeError:
        # Not all remotes support PR refs; ignore
        pass
    run([
        "git", "fetch", "--force", "--prune", "--tags", "origin",
        "+refs/heads/*:refs/remotes/origin/*", "+refs/tags/*:refs/tags/*",
        "+refs/pull/*/head:refs/remotes/origin/pr/*", "+refs/pull/*/merge:refs/remotes/origin/pr-merge/*",
    ], cwd=repo_dir)


def compute_blob_hash_bytes(blob_bytes: bytes) -> str:
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        tf.write(blob_bytes)
        tf.flush()
        temp_path = tf.name
    try:
        return run(["git", "hash-object", temp_path])
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            # Ignore if temp file doesn't exist or can't be removed
            pass


def find_exact_blob_commits(repo_dir: Path, blob_hash: str) -> List[str]:
    out = run(["git", "log", "--all", f"--find-object={blob_hash}", "--pretty=format:%H"], cwd=repo_dir)
    commits = [line.strip() for line in out.splitlines() if line.strip()]
    return commits


def commits_touching_path(repo_dir: Path, repo_file_path: str) -> List[str]:
    out = run(["git", "log", "--all", "--follow", "--pretty=format:%H", "--", repo_file_path], cwd=repo_dir)
    commits = [line.strip() for line in out.splitlines() if line.strip()]
    return commits


def discover_paths_by_filename(repo_dir: Path, filename: str) -> List[str]:
    """Discover repository paths whose basename matches the given filename.

    We scan all reachable objects via `git rev-list --objects --all` and collect
    unique paths that end with the filename. This surfaces files across branches
    and PR refs, even if they were renamed.
    """
    try:
        out = run(["git", "rev-list", "--objects", "--all"], cwd=repo_dir)
    except RuntimeError:
        # Return empty list if git command fails
        return []
    matches: List[str] = []
    seen = set()
    for line in out.splitlines():
        parts = line.split(" ", 1)
        if len(parts) != 2:
            continue
        path = parts[1]
        if path.endswith("/" + filename) or path == filename:
            if path not in seen:
                seen.add(path)
                matches.append(path)
    return matches


def file_content_at(repo_dir: Path, commit: str, repo_file_path: str) -> bytes | None:
    try:
        out = run(["git", "show", f"{commit}:{repo_file_path}"], cwd=repo_dir)
        return out.encode()
    except RuntimeError:
        # Return None if file doesn't exist at this commit
        return None


def blob_id_at(repo_dir: Path, commit: str, repo_file_path: str) -> str | None:
    """Return the blob object id for commit:path without reading content.

    Uses `git rev-parse <commit>:<path>` which resolves to the blob id.
    Returns None if the path does not exist at that commit.
    """
    try:
        out = run(["git", "rev-parse", f"{commit}:{repo_file_path}"] , cwd=repo_dir)
        oid = out.strip()
        # Minimal validation: 40 hex chars
        if len(oid) == 40:
            return oid
        return None
    except RuntimeError:
        # Return None if blob ID cannot be determined
        return None


def branches_containing(repo_dir: Path, commit: str) -> List[str]:
    try:
        out = run(["git", "branch", "-r", "--contains", commit], cwd=repo_dir)
        branches = [line.strip() for line in out.splitlines() if line.strip()]
        return branches
    except RuntimeError:
        # Return empty list if git command fails
        return []


def commit_timestamp(repo_dir: Path, commit: str) -> int:
    out = run(["git", "show", "-s", "--format=%ct", commit], cwd=repo_dir)
    try:
        return int(out.strip())
    except Exception:
        # Return 0 if timestamp cannot be parsed
        return 0


def sanitize_remote_name(candidate: str) -> str:
    # Allow only alphanumerics, dash, underscore, dot
    name = re.sub(r"[^A-Za-z0-9_.-]", "_", candidate)
    # Avoid leading dot which Git dislikes for remote names
    if name.startswith("."):
        name = name.replace(".", "_", 1)
    return name[:200] if len(name) > 200 else name


def existing_remote_names(repo_dir: Path) -> List[str]:
    try:
        out = run(["git", "remote"], cwd=repo_dir)
        return [line.strip() for line in out.splitlines() if line.strip()]
    except RuntimeError:
        # Return empty list if git command fails
        return []


def ensure_remote_with_refspec(repo_dir: Path, name: str, url: str) -> None:
    remotes = set(existing_remote_names(repo_dir))
    if name in remotes:
        try:
            run(["git", "remote", "set-url", name, url], cwd=repo_dir)
        except RuntimeError:
            # Ignore if remote doesn't exist
            pass
        # Reset fetch refspecs
        try:
            run(["git", "config", "--unset-all", f"remote.{name}.fetch"], cwd=repo_dir)
        except RuntimeError:
            # Ignore if remote fetch config doesn't exist
            pass
    else:
        run(["git", "remote", "add", name, url], cwd=repo_dir)
    # Heads into refs/remotes/<name>/* and also tags
    run(["git", "config", "--add", f"remote.{name}.fetch", f"+refs/heads/*:refs/remotes/{name}/*"], cwd=repo_dir)
    run(["git", "config", "--add", f"remote.{name}.fetch", "+refs/tags/*:refs/tags/*"], cwd=repo_dir)


