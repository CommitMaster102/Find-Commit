from pathlib import Path
from unittest.mock import patch

from find_commits_lib.selection import choose_branch_for_commit, choose_preferred


def test_choose_branch_for_commit_prefers_primary_then_pr_then_first():
    repo_dir = Path(".")

    # Primary match
    with patch(
        "find_commits_lib.git_ops.branches_containing",
        return_value=[
            "origin/feature/x",
            "origin/master",
        ],
    ):
        assert choose_branch_for_commit(repo_dir, "c1") == "origin/master"

    # PR-like match when no primary
    with patch(
        "find_commits_lib.git_ops.branches_containing",
        return_value=[
            "origin/pr/123/head",
            "origin/feature/x",
        ],
    ):
        assert choose_branch_for_commit(repo_dir, "c2") == "origin/pr/123/head"

    # Fallback to first branch
    with patch(
        "find_commits_lib.git_ops.branches_containing",
        return_value=[
            "origin/feature/a",
            "origin/feature/b",
        ],
    ):
        assert choose_branch_for_commit(repo_dir, "c3") == "origin/feature/a"


def test_choose_preferred_prioritizes_trunk_release_version_then_recency():
    repo_dir = Path(".")

    # Prefer origin/trunk if present
    with (
        patch(
            "find_commits_lib.git_ops.branches_containing",
            side_effect=lambda _r, c: {
                "a": ["origin/feature/x"],
                "b": ["origin/trunk"],
            }[c],
        ),
        patch("find_commits_lib.git_ops.commit_timestamp", return_value=1),
    ):
        assert choose_preferred(repo_dir, ["a", "b"]) == "b"

    # Prefer release/x.y pattern over others
    with (
        patch(
            "find_commits_lib.git_ops.branches_containing",
            side_effect=lambda _r, c: {
                "a": ["origin/release/1.2"],
                "b": ["origin/feature/x"],
            }[c],
        ),
        patch("find_commits_lib.git_ops.commit_timestamp", return_value=1),
    ):
        assert choose_preferred(repo_dir, ["a", "b"]) == "a"

    # No preferred branch: pick most recent by timestamp
    with (
        patch(
            "find_commits_lib.git_ops.branches_containing",
            return_value=["origin/feature/x"],
        ),
        patch(
            "find_commits_lib.git_ops.commit_timestamp",
            side_effect=lambda _r, c: {"a": 10, "b": 20}[c],
        ),
    ):
        assert choose_preferred(repo_dir, ["a", "b"]) == "b"
