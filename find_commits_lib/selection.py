import re
from pathlib import Path
from typing import List, Tuple

from find_commits_lib import git_ops


def choose_preferred(repo_dir: Path, candidates: List[str]) -> str:
    priority = re.compile(r"origin/(trunk|main|master|release|[0-9]+\.[0-9]+)")
    for c in candidates:
        brs = git_ops.branches_containing(repo_dir, c)
        if any(priority.search(b) for b in brs):
            return c
    # fallback to most recent
    dated: List[Tuple[int, str]] = [
        (git_ops.commit_timestamp(repo_dir, c), c) for c in candidates
    ]
    dated.sort(key=lambda t: t[0], reverse=True)
    return dated[0][1]


def choose_branch_for_commit(repo_dir: Path, commit: str) -> str:
    """Pick a representative branch name for a commit.

    Preference order:
      - origin/trunk, origin/main, origin/master, origin/release/*, origin/<x.y>
      - PR refs (origin/pr/* or origin/pr-merge/*)
      - otherwise, first remote branch containing the commit
    """
    brs = git_ops.branches_containing(repo_dir, commit)
    if not brs:
        return ""
    primary = re.compile(r"origin/(trunk|main|master|release|[0-9]+\.[0-9]+)")
    for b in brs:
        if primary.search(b):
            return b
    pr_like = re.compile(r"origin/(pr-|pr/)\d+/(head|merge)?")
    for b in brs:
        if pr_like.search(b):
            return b
    return brs[0]
