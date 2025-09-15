import argparse
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from find_commits_lib.core.orchestrate import orchestrate
from find_commits_lib.selection import choose_preferred


def _base_args(tmp: Path, mode: str, extra: dict | None = None):
    d = dict(
        local_file=str(tmp / "local.txt"),
        repo_url="https://github.com/test/repo.git",
        repo_dir=None,
        repo_file_path="",
        out_env=str(tmp / "out.env"),
        out_report=str(tmp / "out.txt"),
        include_forks=False,
        github_token="",
        similarity_mode=mode,
        similarity_threshold=0.2,
        shingle_size=2,
        minhash_perm=64,
        progress=False,
        timings=False,
        forks_limit=20,
        forks_offset=0,
        shallow=False,
        depth=1,
        selective=False,
        parallel_fetch=False,
        fast=False,
    )
    if extra:
        d.update(extra)
    return argparse.Namespace(**d)


def test_charjaccard_scoring_threshold_includes_better_match():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        (tmp / "local.txt").write_text("alpha beta gamma")
        args = _base_args(
            tmp, "charjaccard", {"char_ngram_size": 3, "similarity_threshold": 0.2}
        )
        commit_map = {
            "c1": b"alpha beta gamma delta",  # similar
            "c2": b"unrelated words here",  # dissimilar
        }
        with (
            patch("find_commits_lib.core.orchestrate._validate_forks_limit_or_exit"),
            patch(
                "find_commits_lib.core.orchestrate._read_local_bytes_or_exit",
                return_value=b"alpha beta gamma",
            ),
            patch("find_commits_lib.core.orchestrate._prepare_repository"),
            patch(
                "find_commits_lib.core.orchestrate._maybe_fetch_forks",
                return_value=(0, 0, 0),
            ),
            patch(
                "find_commits_lib.core.orchestrate._compute_blob_hashes_and_report",
                return_value=("abc", "abc"),
            ),
            patch(
                "find_commits_lib.core.orchestrate.find_exact_blob_commits",
                return_value=[],
            ),
            patch(
                "find_commits_lib.core.orchestrate.discover_paths_by_filename",
                return_value=["local.txt"],
            ),
            patch(
                "find_commits_lib.core.orchestrate.commits_touching_path",
                return_value=["c1", "c2"],
            ),
            patch("find_commits_lib.core.orchestrate.blob_id_at", return_value=None),
            patch(
                "find_commits_lib.core.orchestrate.file_content_at",
                side_effect=lambda repo_dir, c, p: commit_map.get(c),
            ),
            patch(
                "find_commits_lib.core.orchestrate._write_report"
            ) as mock_write_report,
            patch("find_commits_lib.core.orchestrate._write_env_file"),
            patch("find_commits_lib.core.orchestrate._print_summary"),
            patch("find_commits_lib.utils.cleanup_repo_cache"),
            patch("find_commits_lib.git_ops.branches_containing", return_value=[]),
            patch(
                "find_commits_lib.git_ops.commit_timestamp",
                side_effect=lambda _r, c: {"c1": 2, "c2": 1}[c],
            ),
        ):
            try:
                orchestrate(args)
            except SystemExit:
                # Suppress sys.exit from orchestrate to allow assertions below
                pass
            # Inspect candidates passed to report writer
            assert mock_write_report.called
            call = mock_write_report.call_args
            # candidates is the 9th positional arg (index 9 including kwargs: args,mode,preferred,blob_norm,blob_raw,forks_fetched, forks_discovered,forks_selected,candidates,...)
            candidates = call[1].get("candidates") or call[0][8]
            assert candidates == ["c1"]


def test_winnow_scoring_threshold_selects_high_overlap():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        (tmp / "local.txt").write_text("one two three four")
        # Use punctuation in c1 so tokens match local but bytes differ (avoid exact match)
        args = _base_args(
            tmp,
            "winnow",
            {"winnow_window": 4, "shingle_size": 2, "similarity_threshold": 0.5},
        )
        commit_map = {
            "c1": b"one-two-three-four",  # identical tokens -> high overlap
            "c2": b"red green blue yellow",  # low overlap
        }
        with (
            patch("find_commits_lib.core.orchestrate._validate_forks_limit_or_exit"),
            patch(
                "find_commits_lib.core.orchestrate._read_local_bytes_or_exit",
                return_value=b"one two three four",
            ),
            patch("find_commits_lib.core.orchestrate._prepare_repository"),
            patch(
                "find_commits_lib.core.orchestrate._maybe_fetch_forks",
                return_value=(0, 0, 0),
            ),
            patch(
                "find_commits_lib.core.orchestrate._compute_blob_hashes_and_report",
                return_value=("abc", "abc"),
            ),
            patch(
                "find_commits_lib.core.orchestrate.find_exact_blob_commits",
                return_value=[],
            ),
            patch(
                "find_commits_lib.core.orchestrate.discover_paths_by_filename",
                return_value=["local.txt"],
            ),
            patch(
                "find_commits_lib.core.orchestrate.commits_touching_path",
                return_value=["c1", "c2"],
            ),
            patch("find_commits_lib.core.orchestrate.blob_id_at", return_value=None),
            patch(
                "find_commits_lib.core.orchestrate.file_content_at",
                side_effect=lambda repo_dir, c, p: commit_map.get(c),
            ),
            patch(
                "find_commits_lib.core.orchestrate._write_report"
            ) as mock_write_report,
            patch("find_commits_lib.core.orchestrate._write_env_file"),
            patch("find_commits_lib.core.orchestrate._print_summary"),
            patch("find_commits_lib.utils.cleanup_repo_cache"),
            patch("find_commits_lib.git_ops.branches_containing", return_value=[]),
            patch(
                "find_commits_lib.git_ops.commit_timestamp",
                side_effect=lambda _r, c: {"c1": 2, "c2": 1}[c],
            ),
        ):
            try:
                orchestrate(args)
            except SystemExit:
                # Expected: orchestrate() may call sys.exit(). Swallowing for test assertions below.
                pass
            assert mock_write_report.called
            call = mock_write_report.call_args
            candidates = call[1].get("candidates") or call[0][8]
            assert candidates == ["c1"]


def test_minhash_threshold_includes_only_better():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        (tmp / "local.txt").write_text("a b c d")
        args = _base_args(
            tmp,
            "minhash",
            {"shingle_size": 2, "minhash_perm": 32, "similarity_threshold": 0.3},
        )
        commit_map = {
            "c1": b"a b c e",  # overlapping shingles
            "c2": b"x y z w",  # no overlap
        }
        with (
            patch("find_commits_lib.core.orchestrate._validate_forks_limit_or_exit"),
            patch(
                "find_commits_lib.core.orchestrate._read_local_bytes_or_exit",
                return_value=b"a b c d",
            ),
            patch("find_commits_lib.core.orchestrate._prepare_repository"),
            patch(
                "find_commits_lib.core.orchestrate._maybe_fetch_forks",
                return_value=(0, 0, 0),
            ),
            patch(
                "find_commits_lib.core.orchestrate._compute_blob_hashes_and_report",
                return_value=("abc", "abc"),
            ),
            patch(
                "find_commits_lib.core.orchestrate.find_exact_blob_commits",
                return_value=[],
            ),
            patch(
                "find_commits_lib.core.orchestrate.discover_paths_by_filename",
                return_value=["local.txt"],
            ),
            patch(
                "find_commits_lib.core.orchestrate.commits_touching_path",
                return_value=["c1", "c2"],
            ),
            patch("find_commits_lib.core.orchestrate.blob_id_at", return_value=None),
            patch(
                "find_commits_lib.core.orchestrate.file_content_at",
                side_effect=lambda repo_dir, c, p: commit_map.get(c),
            ),
            patch(
                "find_commits_lib.core.orchestrate._write_report"
            ) as mock_write_report,
            patch("find_commits_lib.core.orchestrate._write_env_file"),
            patch("find_commits_lib.core.orchestrate._print_summary"),
            patch("find_commits_lib.utils.cleanup_repo_cache"),
            patch("find_commits_lib.git_ops.branches_containing", return_value=[]),
            patch(
                "find_commits_lib.git_ops.commit_timestamp",
                side_effect=lambda _r, c: {"c1": 2, "c2": 1}[c],
            ),
        ):
            try:
                orchestrate(args)
            except SystemExit:
                # We suppress SystemExit here to allow inspection of side effects after orchestrate() exits.
                pass
            call = mock_write_report.call_args
            candidates = call[1].get("candidates") or call[0][8]
            assert candidates == ["c1"]


def test_normalized_path_order_descending_similarity():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        (tmp / "local.txt").write_text("a b c d")
        args = _base_args(
            tmp, "jaccard", {"shingle_size": 2, "similarity_threshold": 0.0001}
        )
        commit_map = {
            "best": b"a-b-c-d",  # identical tokens via punctuation to avoid exact match
            "mid": b"a b c e",  # medium
            "low": b"a b x y",  # lower
        }
        with (
            patch("find_commits_lib.core.orchestrate._validate_forks_limit_or_exit"),
            patch(
                "find_commits_lib.core.orchestrate._read_local_bytes_or_exit",
                return_value=b"a b c d",
            ),
            patch("find_commits_lib.core.orchestrate._prepare_repository"),
            patch(
                "find_commits_lib.core.orchestrate._maybe_fetch_forks",
                return_value=(0, 0, 0),
            ),
            patch(
                "find_commits_lib.core.orchestrate._compute_blob_hashes_and_report",
                return_value=("abc", "abc"),
            ),
            patch(
                "find_commits_lib.core.orchestrate.find_exact_blob_commits",
                return_value=[],
            ),
            patch(
                "find_commits_lib.core.orchestrate.discover_paths_by_filename",
                return_value=["local.txt"],
            ),
            patch(
                "find_commits_lib.core.orchestrate.commits_touching_path",
                return_value=["best", "mid", "low"],
            ),
            patch("find_commits_lib.core.orchestrate.blob_id_at", return_value=None),
            patch(
                "find_commits_lib.core.orchestrate.file_content_at",
                side_effect=lambda repo_dir, c, p: commit_map.get(c),
            ),
            patch(
                "find_commits_lib.core.orchestrate._write_report"
            ) as mock_write_report,
            patch("find_commits_lib.core.orchestrate._write_env_file"),
            patch("find_commits_lib.core.orchestrate._print_summary"),
            patch("find_commits_lib.utils.cleanup_repo_cache"),
            patch("find_commits_lib.git_ops.branches_containing", return_value=[]),
            patch(
                "find_commits_lib.git_ops.commit_timestamp",
                side_effect=lambda _r, c: {"best": 30, "mid": 20, "low": 10}[c],
            ),
        ):
            try:
                orchestrate(args)
            except SystemExit:
                # SystemExit is expected here if orchestrate decides to exit the process.
                pass
            call = mock_write_report.call_args
            mode = call[1].get("mode") or call[0][1]
            candidates = call[1].get("candidates") or call[0][8]
            assert mode == "normalized_path"
            assert candidates == ["best", "mid", "low"]


def test_selection_choose_preferred_priority_and_recency():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        repo_dir = tmp
        # Priority branch match returns immediately
        with (
            patch(
                "find_commits_lib.git_ops.branches_containing",
                return_value=["origin/main", "origin/feature/x"],
            ),
            patch("find_commits_lib.git_ops.commit_timestamp"),
        ):
            out = choose_preferred(repo_dir, ["a", "b"])
            assert out == "a"

        # No priority branch: falls back to most recent by timestamp
        def fake_branches(_repo, _c):
            return ["origin/feature/x"]

        with (
            patch(
                "find_commits_lib.git_ops.branches_containing",
                side_effect=fake_branches,
            ),
            patch(
                "find_commits_lib.git_ops.commit_timestamp",
                side_effect=lambda _r, c: {"a": 10, "b": 20}[c],
            ),
        ):
            out = choose_preferred(repo_dir, ["a", "b"])
            assert out == "b"


def test_orchestrate_errors_validate_forks_limit_and_no_candidates():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        # 1) forks_limit > 99 should exit with code 2
        args = argparse.Namespace(
            local_file=str(tmp / "any.txt"),
            repo_url="https://github.com/test/repo.git",
            include_forks=True,
            forks_limit=100,
            repo_dir=None,
            repo_file_path="",
            out_env=str(tmp / "out.env"),
            out_report=str(tmp / "out.txt"),
            github_token="",
            similarity_mode="jaccard",
            similarity_threshold=0.8,
            shingle_size=3,
            minhash_perm=64,
            progress=False,
            timings=False,
            forks_offset=0,
            shallow=False,
            depth=1,
            selective=False,
            parallel_fetch=False,
            fast=False,
        )
        (tmp / "any.txt").write_text("x")
        with (
            patch("find_commits_lib.utils.cleanup_repo_cache"),
            patch(
                "find_commits_lib.core.orchestrate._read_local_bytes_or_exit",
                return_value=b"x",
            ),
        ):
            with pytest.raises(SystemExit) as e:
                orchestrate(args)
            assert int(e.value.code) == 2

        # 2) No candidate paths discovered -> exit 1
        args2 = _base_args(tmp, "jaccard")
        with (
            patch("find_commits_lib.core.orchestrate._validate_forks_limit_or_exit"),
            patch(
                "find_commits_lib.core.orchestrate._read_local_bytes_or_exit",
                return_value=b"x",
            ),
            patch("find_commits_lib.core.orchestrate._prepare_repository"),
            patch(
                "find_commits_lib.core.orchestrate._maybe_fetch_forks",
                return_value=(0, 0, 0),
            ),
            patch(
                "find_commits_lib.core.orchestrate._compute_blob_hashes_and_report",
                return_value=("a", "a"),
            ),
            patch(
                "find_commits_lib.core.orchestrate.find_exact_blob_commits",
                return_value=[],
            ),
            patch(
                "find_commits_lib.core.orchestrate.discover_paths_by_filename",
                return_value=[],
            ),
            patch("find_commits_lib.core.orchestrate._write_report"),
            patch("find_commits_lib.core.orchestrate._write_env_file"),
            patch("find_commits_lib.core.orchestrate._print_summary"),
            patch("find_commits_lib.utils.cleanup_repo_cache"),
        ):
            with pytest.raises(SystemExit) as e:
                orchestrate(args2)
            assert int(e.value.code) == 1

        # 3) Candidate paths but no candidates found -> exit 1
        args3 = _base_args(tmp, "jaccard")
        with (
            patch("find_commits_lib.core.orchestrate._validate_forks_limit_or_exit"),
            patch(
                "find_commits_lib.core.orchestrate._read_local_bytes_or_exit",
                return_value=b"x",
            ),
            patch("find_commits_lib.core.orchestrate._prepare_repository"),
            patch(
                "find_commits_lib.core.orchestrate._maybe_fetch_forks",
                return_value=(0, 0, 0),
            ),
            patch(
                "find_commits_lib.core.orchestrate._compute_blob_hashes_and_report",
                return_value=("a", "a"),
            ),
            patch(
                "find_commits_lib.core.orchestrate.find_exact_blob_commits",
                return_value=[],
            ),
            patch(
                "find_commits_lib.core.orchestrate.discover_paths_by_filename",
                return_value=["local.txt"],
            ),
            patch(
                "find_commits_lib.core.orchestrate.commits_touching_path",
                return_value=[],
            ),
            patch("find_commits_lib.core.orchestrate._write_report"),
            patch("find_commits_lib.core.orchestrate._write_env_file"),
            patch("find_commits_lib.core.orchestrate._print_summary"),
            patch("find_commits_lib.utils.cleanup_repo_cache"),
        ):
            with pytest.raises(SystemExit) as e:
                orchestrate(args3)
            assert int(e.value.code) == 1
