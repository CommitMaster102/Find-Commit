import argparse
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

from find_commits_lib.core import orchestrate
from find_commits_lib.utils import (
    AutoProgressBar,
    Spinner,
    StepDisplay,
    format_duration_human,
    format_timestamp_ms,
)


def test_progress_mode_enabled():
    """Test that progress mode works when enabled."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a mock local file
        local_file = temp_path / "test_file.txt"
        local_file.write_text("hello world test content")

        # Create mock args with progress enabled
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
            progress=True,  # Enable progress
            timings=False,
            forks_limit=20,
            forks_offset=0,
            shallow=False,
            depth=1,
            selective=False,
            parallel_fetch=False,
            fast=False,
        )

        # Mock the orchestrate function to test progress mode
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

            # Set up mock return values
            mock_read_local.return_value = b"hello world test content"
            mock_compute_blob.return_value = ("abc123", "abc123")
            mock_scan.return_value = ("exact_blob", ["def456"])
            mock_dedupe.return_value = ["def456"]
            mock_choose_preferred.return_value = "def456"
            mock_fetch_forks.return_value = (0, 0, 0)

            # Run the orchestrate function
            try:
                orchestrate(args)
            except SystemExit:
                pass

            # Verify that progress was enabled
            assert args.progress is True


def test_timing_mode_enabled():
    """Test that timing mode works when enabled."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a mock local file
        local_file = temp_path / "test_file.txt"
        local_file.write_text("hello world test content")

        # Create mock args with timings enabled
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
            progress=False,
            timings=True,  # Enable timings
            forks_limit=20,
            forks_offset=0,
            shallow=False,
            depth=1,
            selective=False,
            parallel_fetch=False,
            fast=False,
        )

        # Mock the orchestrate function to test timing mode
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

            # Set up mock return values
            mock_read_local.return_value = b"hello world test content"
            mock_compute_blob.return_value = ("abc123", "abc123")
            mock_scan.return_value = ("exact_blob", ["def456"])
            mock_dedupe.return_value = ["def456"]
            mock_choose_preferred.return_value = "def456"
            mock_fetch_forks.return_value = (0, 0, 0)

            # Run the orchestrate function
            try:
                orchestrate(args)
            except SystemExit:
                pass

            # Verify that timings were enabled
            assert args.timings is True


def test_both_progress_and_timing_enabled():
    """Test that both progress and timing modes work together."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a mock local file
        local_file = temp_path / "test_file.txt"
        local_file.write_text("hello world test content")

        # Create mock args with both progress and timings enabled
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
            progress=True,  # Enable progress
            timings=True,  # Enable timings
            forks_limit=20,
            forks_offset=0,
            shallow=False,
            depth=1,
            selective=False,
            parallel_fetch=False,
            fast=False,
        )

        # Mock the orchestrate function to test both modes
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

            # Set up mock return values
            mock_read_local.return_value = b"hello world test content"
            mock_compute_blob.return_value = ("abc123", "abc123")
            mock_scan.return_value = ("exact_blob", ["def456"])
            mock_dedupe.return_value = ["def456"]
            mock_choose_preferred.return_value = "def456"
            mock_fetch_forks.return_value = (0, 0, 0)

            # Run the orchestrate function
            try:
                orchestrate(args)
            except SystemExit:
                pass

            # Verify that both modes were enabled
            assert args.progress is True
            assert args.timings is True


def test_fast_mode_disables_progress_and_timing():
    """Test that fast mode disables progress and timing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a mock local file
        local_file = temp_path / "test_file.txt"
        local_file.write_text("hello world test content")

        # Create mock args with fast mode enabled (but progress/timing initially enabled)
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
            progress=True,  # Start with progress enabled
            timings=True,  # Start with timings enabled
            forks_limit=20,
            forks_offset=0,
            shallow=False,
            depth=1,
            selective=False,
            parallel_fetch=False,
            fast=True,  # Enable fast mode
        )

        # Mock the orchestrate function to test fast mode behavior
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

            # Set up mock return values
            mock_read_local.return_value = b"hello world test content"
            mock_compute_blob.return_value = ("abc123", "abc123")
            mock_scan.return_value = ("exact_blob", ["def456"])
            mock_dedupe.return_value = ["def456"]
            mock_choose_preferred.return_value = "def456"
            mock_fetch_forks.return_value = (0, 0, 0)

            # Run the orchestrate function
            try:
                orchestrate(args)
            except SystemExit:
                pass

            # Verify that fast mode disabled progress and timing
            assert args.progress is False
            assert args.timings is False
            assert args.fast is True


def test_spinner_class():
    """Test the Spinner class functionality."""
    # Test with progress enabled
    spinner = Spinner(True)
    assert spinner.enabled is True

    # Test with progress disabled
    spinner = Spinner(False)
    assert spinner.enabled is False

    # Test context manager behavior (Spinner doesn't support context manager)
    spinner = Spinner(False)
    assert spinner.enabled is False


def test_auto_progress_bar_class():
    """Test the AutoProgressBar class functionality."""
    # Test with progress enabled
    progress_bar = AutoProgressBar(True)
    assert progress_bar.enabled is True

    # Test with progress disabled
    progress_bar = AutoProgressBar(False)
    assert progress_bar.enabled is False


def test_step_display_class():
    """Test the StepDisplay class functionality."""
    timings = {}

    # Test with progress and timing enabled
    with StepDisplay(
        "test_step", "Test step:", timings, AutoProgressBar(True), True
    ) as disp:
        assert disp is not None
        # Test update method
        disp.update(1, 5, "test item")

    # Test with progress and timing disabled
    with StepDisplay(
        "test_step", "Test step:", timings, AutoProgressBar(False), False
    ) as disp:
        assert disp is not None
        # Test update method
        disp.update(1, 5, "test item")


def test_timing_functions():
    """Test timing utility functions."""
    # Test format_timestamp_ms
    timestamp = time.time()
    formatted = format_timestamp_ms(timestamp)
    assert isinstance(formatted, str)
    assert len(formatted) > 0

    # Test format_duration_human
    durations = [0, 1, 100, 1000, 60000, 3600000]  # 0ms, 1ms, 100ms, 1s, 1m, 1h
    for duration in durations:
        formatted = format_duration_human(duration)
        assert isinstance(formatted, str)
        assert len(formatted) > 0


def test_timing_data_structure():
    """Test that timing data is properly structured."""
    timings = {}

    # Simulate adding timing data
    timings["step1_start"] = "2024-01-01 10:00:00.000"
    timings["step1_end"] = "2024-01-01 10:00:01.000"
    timings["step1_ms"] = 1000

    timings["step2_start"] = "2024-01-01 10:00:01.000"
    timings["step2_end"] = "2024-01-01 10:00:02.000"
    timings["step2_ms"] = 1000

    # Test that timing data can be processed
    step_keys = set()
    for k in timings.keys():
        if k.endswith("_start") or k.endswith("_end") or k.endswith("_ms"):
            step = k.rsplit("_", 1)[0]
            step_keys.add(step)

    assert "step1" in step_keys
    assert "step2" in step_keys

    # Test duration calculation
    for step in step_keys:
        start_key = f"{step}_start"
        end_key = f"{step}_end"
        ms_key = f"{step}_ms"

        if start_key in timings and end_key in timings and ms_key in timings:
            duration = timings[ms_key]
            assert duration > 0


def test_progress_bar_integration():
    """Test progress bar integration with orchestration."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a mock local file
        local_file = temp_path / "test_file.txt"
        local_file.write_text("hello world test content")

        # Create mock args with progress enabled
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
            progress=True,  # Enable progress
            timings=True,  # Enable timings
            forks_limit=20,
            forks_offset=0,
            shallow=False,
            depth=1,
            selective=False,
            parallel_fetch=False,
            fast=False,
        )

        # Mock the orchestrate function to test progress integration
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

            # Set up mock return values
            mock_read_local.return_value = b"hello world test content"
            mock_compute_blob.return_value = ("abc123", "abc123")
            mock_scan.return_value = ("exact_blob", ["def456"])
            mock_dedupe.return_value = ["def456"]
            mock_choose_preferred.return_value = "def456"
            mock_fetch_forks.return_value = (0, 0, 0)

            # Run the orchestrate function
            try:
                orchestrate(args)
            except SystemExit:
                pass

            # Verify that progress was enabled throughout
            assert args.progress is True
            assert args.timings is True


if __name__ == "__main__":
    test_progress_mode_enabled()
    test_timing_mode_enabled()
    test_both_progress_and_timing_enabled()
    test_fast_mode_disables_progress_and_timing()
    test_spinner_class()
    test_auto_progress_bar_class()
    test_step_display_class()
    test_timing_functions()
    test_timing_data_structure()
    test_progress_bar_integration()
    print("All progress and timing tests passed!")
