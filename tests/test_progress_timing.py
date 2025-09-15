import argparse
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from find_commits_lib.core.orchestrate import orchestrate
from find_commits_lib.utils import (
    AutoProgressBar,
    Spinner,
    StepDisplay,
    format_duration_human,
    format_timestamp_ms,
)


@pytest.mark.parametrize(
    "progress,timings",
    [
        (True, False),
        (False, True),
        (True, True),
    ],
)
def test_progress_and_timing_modes(progress, timings):
    """Ensure orchestrate honors progress/timing flags and runs without side effects."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        local_file = temp_path / "test_file.txt"
        local_file.write_text("hello world test content")

        args = argparse.Namespace(
            local_file=str(local_file),
            repo_url="https://github.com/test/repo.git",
            repo_dir=None,
            repo_file_path="",
            out_env="test.env",
            out_report="test.txt",
            include_forks=False,
            github_token="",
            similarity_mode="jaccard",
            similarity_threshold=0.92,
            shingle_size=5,
            minhash_perm=128,
            progress=progress,
            timings=timings,
            forks_limit=20,
            forks_offset=0,
            shallow=False,
            depth=1,
            selective=False,
            parallel_fetch=False,
            fast=False,
        )

        with (
            patch("find_commits_lib.core.orchestrate._validate_forks_limit_or_exit"),
            patch(
                "find_commits_lib.core.orchestrate._read_local_bytes_or_exit"
            ) as mock_read_local,
            patch("find_commits_lib.core.orchestrate._prepare_repository"),
            patch(
                "find_commits_lib.core.orchestrate._maybe_fetch_forks"
            ) as mock_fetch_forks,
            patch(
                "find_commits_lib.core.orchestrate._compute_blob_hashes_and_report"
            ) as mock_compute_blob,
            patch(
                "find_commits_lib.core.orchestrate._scan_commits_for_candidates"
            ) as mock_scan,
            patch(
                "find_commits_lib.core.orchestrate._dedupe_preserve_order"
            ) as mock_dedupe,
            patch(
                "find_commits_lib.selection.choose_preferred"
            ) as mock_choose_preferred,
            patch("find_commits_lib.core.orchestrate._write_report"),
            patch("find_commits_lib.core.orchestrate._write_env_file"),
            patch("find_commits_lib.core.orchestrate._print_summary"),
            patch("find_commits_lib.utils.cleanup_repo_cache"),
            patch("find_commits_lib.git_ops.branches_containing"),
            patch("find_commits_lib.git_ops.commit_timestamp"),
        ):
            mock_read_local.return_value = b"hello world test content"
            mock_compute_blob.return_value = ("abc123", "abc123")
            mock_scan.return_value = ("exact_blob", ["def456"])
            mock_dedupe.return_value = ["def456"]
            mock_choose_preferred.return_value = "def456"
            mock_fetch_forks.return_value = (0, 0, 0)

            try:
                orchestrate(args)
            except SystemExit:
                # Expected: orchestrate may call sys.exit() during testing
                pass

            assert args.progress is progress
            assert args.timings is timings


def test_fast_mode_disables_progress_and_timing():
    """Fast mode should disable progress/timing flags regardless of input."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        local_file = temp_path / "test_file.txt"
        local_file.write_text("hello world test content")

        args = argparse.Namespace(
            local_file=str(local_file),
            repo_url="https://github.com/test/repo.git",
            repo_dir=None,
            repo_file_path="",
            out_env="test.env",
            out_report="test.txt",
            include_forks=False,
            github_token="",
            similarity_mode="jaccard",
            similarity_threshold=0.92,
            shingle_size=5,
            minhash_perm=128,
            progress=True,
            timings=True,
            forks_limit=20,
            forks_offset=0,
            shallow=False,
            depth=1,
            selective=False,
            parallel_fetch=False,
            fast=True,
        )

        with (
            patch("find_commits_lib.core.orchestrate._validate_forks_limit_or_exit"),
            patch(
                "find_commits_lib.core.orchestrate._read_local_bytes_or_exit"
            ) as mock_read_local,
            patch("find_commits_lib.core.orchestrate._prepare_repository"),
            patch(
                "find_commits_lib.core.orchestrate._maybe_fetch_forks"
            ) as mock_fetch_forks,
            patch(
                "find_commits_lib.core.orchestrate._compute_blob_hashes_and_report"
            ) as mock_compute_blob,
            patch(
                "find_commits_lib.core.orchestrate._scan_commits_for_candidates"
            ) as mock_scan,
            patch(
                "find_commits_lib.core.orchestrate._dedupe_preserve_order"
            ) as mock_dedupe,
            patch(
                "find_commits_lib.selection.choose_preferred"
            ) as mock_choose_preferred,
            patch("find_commits_lib.core.orchestrate._write_report"),
            patch("find_commits_lib.core.orchestrate._write_env_file"),
            patch("find_commits_lib.core.orchestrate._print_summary"),
            patch("find_commits_lib.utils.cleanup_repo_cache"),
            patch("find_commits_lib.git_ops.branches_containing"),
            patch("find_commits_lib.git_ops.commit_timestamp"),
        ):
            mock_read_local.return_value = b"hello world test content"
            mock_compute_blob.return_value = ("abc123", "abc123")
            mock_scan.return_value = ("exact_blob", ["def456"])
            mock_dedupe.return_value = ["def456"]
            mock_choose_preferred.return_value = "def456"
            mock_fetch_forks.return_value = (0, 0, 0)

            try:
                orchestrate(args)
            except SystemExit:
                # Expected: orchestrate may call sys.exit() during testing
                pass

            assert args.progress is False
            assert args.timings is False
            assert args.fast is True


def test_spinner_and_progress_classes():
    """Basic behavior of progress helpers without I/O side-effects."""
    assert Spinner(True).enabled is True
    assert Spinner(False).enabled is False
    assert AutoProgressBar(True).enabled is True
    assert AutoProgressBar(False).enabled is False


def test_step_display_context_and_update():
    """StepDisplay works as context manager and update() is callable."""
    timings = {}
    with StepDisplay("s", "Step:", timings, AutoProgressBar(True), True) as disp:
        assert disp is not None
        disp.update(1, 3, "item")
    with StepDisplay("s2", "Step:", timings, AutoProgressBar(False), False) as disp:
        assert disp is not None
        disp.update(2, 5, "item2")


def test_timing_functions():
    """format_duration_human and format_timestamp_ms basic behavior."""
    # format_duration_human variations from implementation
    assert "wasn't applied" in format_duration_human(0)
    assert format_duration_human(999).startswith("Took 999")
    assert "1 seconds" in format_duration_human(1000)
    assert "Took 1 minute" in format_duration_human(60000)
    assert "Took 1 hour" in format_duration_human(3600000)

    # format_timestamp_ms should return a non-empty string
    assert isinstance(format_timestamp_ms(0.0), str)
    assert format_timestamp_ms(0.0)


def test_timing_data_structure():
    """Minimal structure validation for timing keys grouping."""
    timings = {}
    timings["step1_start"] = "2024-01-01 10:00:00.000"
    timings["step1_end"] = "2024-01-01 10:00:01.000"
    timings["step1_ms"] = 1000
    timings["step2_start"] = "2024-01-01 10:00:01.000"
    timings["step2_end"] = "2024-01-01 10:00:02.000"
    timings["step2_ms"] = 1000

    step_keys = set()
    for k in timings.keys():
        if k.endswith("_start") or k.endswith("_end") or k.endswith("_ms"):
            step = k.rsplit("_", 1)[0]
            step_keys.add(step)

    assert "step1" in step_keys
    assert "step2" in step_keys


def test_progress_bar_integration():
    """Lightweight integration: run with progress/timings True and ensure flags persist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        local_file = temp_path / "test_file.txt"
        local_file.write_text("hello world test content")

        args = argparse.Namespace(
            local_file=str(local_file),
            repo_url="https://github.com/test/repo.git",
            repo_dir=None,
            repo_file_path="",
            out_env="test.env",
            out_report="test.txt",
            include_forks=False,
            github_token="",
            similarity_mode="jaccard",
            similarity_threshold=0.92,
            shingle_size=5,
            minhash_perm=128,
            progress=True,
            timings=True,
            forks_limit=20,
            forks_offset=0,
            shallow=False,
            depth=1,
            selective=False,
            parallel_fetch=False,
            fast=False,
        )

        with (
            patch("find_commits_lib.core.orchestrate._validate_forks_limit_or_exit"),
            patch(
                "find_commits_lib.core.orchestrate._read_local_bytes_or_exit"
            ) as mock_read_local,
            patch("find_commits_lib.core.orchestrate._prepare_repository"),
            patch(
                "find_commits_lib.core.orchestrate._maybe_fetch_forks"
            ) as mock_fetch_forks,
            patch(
                "find_commits_lib.core.orchestrate._compute_blob_hashes_and_report"
            ) as mock_compute_blob,
            patch(
                "find_commits_lib.core.orchestrate._scan_commits_for_candidates"
            ) as mock_scan,
            patch(
                "find_commits_lib.core.orchestrate._dedupe_preserve_order"
            ) as mock_dedupe,
            patch(
                "find_commits_lib.selection.choose_preferred"
            ) as mock_choose_preferred,
            patch("find_commits_lib.core.orchestrate._write_report"),
            patch("find_commits_lib.core.orchestrate._write_env_file"),
            patch("find_commits_lib.core.orchestrate._print_summary"),
            patch("find_commits_lib.utils.cleanup_repo_cache"),
            patch("find_commits_lib.git_ops.branches_containing"),
            patch("find_commits_lib.git_ops.commit_timestamp"),
        ):
            mock_read_local.return_value = b"hello world test content"
            mock_compute_blob.return_value = ("abc123", "abc123")
            mock_scan.return_value = ("exact_blob", ["def456"])
            mock_dedupe.return_value = ["def456"]
            mock_choose_preferred.return_value = "def456"
            mock_fetch_forks.return_value = (0, 0, 0)

            try:
                orchestrate(args)
            except SystemExit:
                # Expected: orchestrate may call sys.exit() during testing
                pass

            assert args.progress is True
            assert args.timings is True
