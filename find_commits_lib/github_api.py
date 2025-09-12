import json
import re
import sys
from pathlib import Path
from typing import List, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from find_commits_lib.git_ops import (
    ensure_remote_with_refspec,
    existing_remote_names,
    run,
    sanitize_remote_name,
)


def parse_github_owner_repo(repo_url: str) -> Tuple[str, str] | None:
    """Parse GitHub owner/repo from common URL forms.

    Supports:
      - https://github.com/owner/repo(.git)
      - http(s)://github.com/owner/repo
      - git@github.com:owner/repo(.git)
      - ssh://git@github.com/owner/repo(.git)
    Returns (owner, repo) or None if not a GitHub URL.
    """
    cleaned = repo_url.strip()
    m = re.search(
        r"github\.com[:/]+([^/]+)/([^/]+?)(?:\.git)?(?:[#?].*)?$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if not m:
        return None
    owner = m.group(1)
    repo = m.group(2)
    return owner, repo


def github_api_get(url: str, token: str | None) -> Tuple[int, bytes]:
    # Security validation: only allow HTTPS URLs
    if not url.startswith("https://"):
        raise ValueError("Only HTTPS URLs are allowed for security")

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "find-commits-script",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(url, headers=headers)
    try:
        with urlopen(
            req, timeout=30
        ) as resp:  # nosec B310 - URL scheme is validated above
            status = getattr(resp, "status", 200)
            data = resp.read()
            return status, data
    except HTTPError as e:
        # Return HTTP error code and response body
        return e.code, e.read() if hasattr(e, "read") else b""
    except URLError:
        # Return 0 status and empty body for network errors
        return 0, b""


def list_github_forks(
    owner: str, repo: str, token: str | None, max_forks: int
) -> List[dict]:
    """List forks via GitHub API, up to max_forks. Returns list of JSON dicts."""
    forks: List[dict] = []
    per_page = 100
    page = 1
    while len(forks) < max_forks:
        url = f"https://api.github.com/repos/{owner}/{repo}/forks?per_page={per_page}&page={page}&sort=newest"
        status, data = github_api_get(url, token)
        if status != 200:
            break
        try:
            arr = json.loads(data.decode("utf-8", errors="ignore"))
        except Exception:
            # Break if JSON parsing fails
            break
        if not isinstance(arr, list) or not arr:
            break
        forks.extend(arr)
        if len(arr) < per_page:
            break
        page += 1
    return forks[:max_forks]


def github_repo_details(
    owner: str, repo: str, token: str | None
) -> tuple[int, dict | None]:
    url = f"https://api.github.com/repos/{owner}/{repo}"
    status, data = github_api_get(url, token)
    if status != 200:
        try:
            err = json.loads(data.decode("utf-8", errors="ignore"))
            msg = err.get("message", "")
        except Exception:
            # Use empty message if JSON parsing fails
            msg = ""
        if msg:
            print(
                f"GitHub API error ({status}) for repo details {owner}/{repo}: {msg}",
                file=sys.stderr,
            )
        else:
            print(
                f"GitHub API error ({status}) for repo details {owner}/{repo}.",
                file=sys.stderr,
            )
        return status, None
    try:
        info = json.loads(data.decode("utf-8", errors="ignore"))
    except Exception:
        # Print error and return None if JSON parsing fails
        print("Failed to parse repository details JSON.", file=sys.stderr)
        return 200, None
    return 200, info


def fetch_forks_into_repo(
    repo_dir: Path,
    repo_url: str,
    token: str | None,
    max_forks: int,
    forks_offset: int = 0,
) -> Tuple[int, int, int]:
    parsed = parse_github_owner_repo(repo_url)
    if not parsed:
        print(
            "--include-forks specified, but repository is not a GitHub URL; skipping forks.",
            file=sys.stderr,
        )
        return 0
    owner, repo = parsed

    # Always try to fetch repo details; if it's a fork, prefer parent for fork discovery
    _, info = github_repo_details(owner, repo, token)
    parent_owner = None
    parent_repo = None
    if info and bool(info.get("fork")) and isinstance(info.get("parent"), dict):
        parent = info.get("parent", {})
        # full_name is like "owner/name"
        full_name = parent.get("full_name") or ""
        if "/" in full_name:
            parent_owner, parent_repo = full_name.split("/", 1)
        else:
            # Fallback to owner/name fields
            parent_owner = (parent.get("owner") or {}).get("login")
            parent_repo = parent.get("name")
        # Ensure and fetch upstream remote for parent
        clone_url = (
            parent.get("clone_url") or parent.get("ssh_url") or parent.get("git_url")
        )
        if parent_owner and parent_repo and clone_url:
            base_remote_names = set(existing_remote_names(repo_dir))
            upstream_name = sanitize_remote_name(
                f"upstream_{parent_owner}_{parent_repo}"
            )
            uniq_upstream = upstream_name
            suffix = 1
            while uniq_upstream in base_remote_names:
                uniq_upstream = sanitize_remote_name(f"{upstream_name}_{suffix}")
                suffix += 1
            try:
                ensure_remote_with_refspec(repo_dir, uniq_upstream, clone_url)
                run(
                    ["git", "fetch", "--force", "--prune", "--tags", uniq_upstream],
                    cwd=repo_dir,
                )
                print(
                    f"Fetched upstream parent remote '{uniq_upstream}'.",
                    file=sys.stderr,
                )
            except RuntimeError:
                # Print error if upstream remote operations fail
                print("Failed to add/fetch upstream parent remote.", file=sys.stderr)

    # Discover forks for target and, if available, for parent
    print(f"Discovering forks for {owner}/{repo} via GitHub API...", file=sys.stderr)
    needed_total = max(0, forks_offset) + max(0, max_forks)
    forks_repo = list_github_forks(owner, repo, token, needed_total)
    forks_parent = []
    if parent_owner and parent_repo:
        print(
            f"Also discovering forks for parent {parent_owner}/{parent_repo}...",
            file=sys.stderr,
        )
        forks_parent = list_github_forks(parent_owner, parent_repo, token, needed_total)
    # Deduplicate by full_name with repo forks first (newest ordering preserved per source)
    seen_full = set()
    combined = []
    for arr in (forks_repo, forks_parent):
        for f in arr:
            fn = f.get("full_name") or ""
            if fn and fn not in seen_full:
                seen_full.add(fn)
                combined.append(f)
    forks = combined

    if not forks:
        msg = "No forks found or API unavailable."
        if info and bool(info.get("fork")) and parent_owner and parent_repo:
            msg += " Checked parent as well."
        print(msg, file=sys.stderr)
        return 0, 0, 0

    discovered_total = len(forks)
    start = max(0, forks_offset)
    end = start + max(0, max_forks)
    selected = forks[start:end]
    if not selected:
        print(
            f"No forks selected after applying offset={forks_offset} and limit={max_forks} (discovered={discovered_total}).",
            file=sys.stderr,
        )
        return 0, discovered_total, 0
    print(
        f"Applying forks offset={forks_offset}, limit={max_forks}: selected={len(selected)} of discovered={discovered_total}.",
        file=sys.stderr,
    )
    added = 0
    base_remote_names = set(existing_remote_names(repo_dir))
    for f in selected:
        try:
            owner_login = f.get("owner", {}).get("login") or "fork"
            fork_repo_name = f.get("name") or repo
            clone_url = f.get("clone_url") or f.get("ssh_url") or f.get("git_url")
        except (KeyError, AttributeError, TypeError) as e:
            # Skip this fork if data access fails due to malformed data
            print(f"Warning: Skipping fork due to data access error: {e}")
            continue
        if not clone_url:
            continue
        base = sanitize_remote_name(f"fork_{owner_login}_{fork_repo_name}")
        remote_name = base
        suffix = 1
        while remote_name in base_remote_names:
            remote_name = sanitize_remote_name(f"{base}_{suffix}")
            suffix += 1
        try:
            ensure_remote_with_refspec(repo_dir, remote_name, clone_url)
            run(
                ["git", "fetch", "--force", "--prune", "--tags", remote_name],
                cwd=repo_dir,
            )
            base_remote_names.add(remote_name)
            added += 1
        except RuntimeError:
            # Skip forks we can't access/fetch
            continue
    print(f"Fetched refs from {added} fork(s).", file=sys.stderr)
    return added, discovered_total, len(selected)
