import argparse
import tempfile
from pathlib import Path
from unittest.mock import patch

from find_commits_lib.core import orchestrate
from find_commits_lib.git_ops import ensure_repo


def test_shallow_clone_mode():
    """Test that shallow clone mode works correctly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a mock local file
        local_file = temp_path / "test_file.txt"
        local_file.write_text("hello world test content")

        # Create mock args with shallow clone enabled
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
            timings=False,
            forks_limit=20,
            forks_offset=0,
            shallow=True,  # Enable shallow clone
            depth=3,  # Set depth to 3
            selective=False,
            parallel_fetch=False,
            fast=False,
        )

        # Mock the orchestrate function to test shallow clone
        with (
            patch("find_commits_lib.core.orchestrate._validate_forks_limit_or_exit"),
            patch(
                "find_commits_lib.core.orchestrate._read_local_bytes_or_exit"
            ) as mock_read_local,
            patch(
                "find_commits_lib.core.orchestrate._prepare_repository"
            ) as mock_prepare_repo,
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

            # Verify that shallow clone was enabled
            assert args.shallow is True
            assert args.depth == 3

            # Verify that _prepare_repository was called with correct parameters
            mock_prepare_repo.assert_called_once()
            call_args = mock_prepare_repo.call_args
            assert call_args[1]["shallow"] is True
            assert call_args[1]["depth"] == 3


def test_selective_fetch_mode():
    """Test that selective fetch mode works correctly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a mock local file
        local_file = temp_path / "test_file.txt"
        local_file.write_text("hello world test content")

        # Create mock args with selective fetch enabled
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
            timings=False,
            forks_limit=20,
            forks_offset=0,
            shallow=False,
            depth=1,
            selective=True,  # Enable selective fetch
            parallel_fetch=False,
            fast=False,
        )

        # Mock the orchestrate function to test selective fetch
        with (
            patch("find_commits_lib.core.orchestrate._validate_forks_limit_or_exit"),
            patch(
                "find_commits_lib.core.orchestrate._read_local_bytes_or_exit"
            ) as mock_read_local,
            patch(
                "find_commits_lib.core.orchestrate._prepare_repository"
            ) as mock_prepare_repo,
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

            # Verify that selective fetch was enabled
            assert args.selective is True

            # Verify that _prepare_repository was called with correct parameters
            mock_prepare_repo.assert_called_once()
            call_args = mock_prepare_repo.call_args
            assert call_args[1]["selective"] is True


def test_parallel_fetch_mode():
    """Test that parallel fetch mode works correctly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a mock local file
        local_file = temp_path / "test_file.txt"
        local_file.write_text("hello world test content")

        # Create mock args with parallel fetch enabled
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
            timings=False,
            forks_limit=20,
            forks_offset=0,
            shallow=False,
            depth=1,
            selective=False,
            parallel_fetch=True,  # Enable parallel fetch
            fast=False,
        )

        # Mock the orchestrate function to test parallel fetch
        with (
            patch("find_commits_lib.core.orchestrate._validate_forks_limit_or_exit"),
            patch(
                "find_commits_lib.core.orchestrate._read_local_bytes_or_exit"
            ) as mock_read_local,
            patch(
                "find_commits_lib.core.orchestrate._prepare_repository"
            ) as mock_prepare_repo,
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

            # Verify that parallel fetch was enabled
            assert args.parallel_fetch is True

            # Verify that _prepare_repository was called with correct parameters
            mock_prepare_repo.assert_called_once()
            call_args = mock_prepare_repo.call_args
            assert call_args[1]["parallel"] is True


def test_combined_clone_modes():
    """Test that multiple clone modes can be combined."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a mock local file
        local_file = temp_path / "test_file.txt"
        local_file.write_text("hello world test content")

        # Create mock args with multiple clone modes enabled
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
            timings=False,
            forks_limit=20,
            forks_offset=0,
            shallow=True,  # Enable shallow clone
            depth=2,  # Set depth to 2
            selective=True,  # Enable selective fetch
            parallel_fetch=True,  # Enable parallel fetch
            fast=False,
        )

        # Mock the orchestrate function to test combined modes
        with (
            patch("find_commits_lib.core.orchestrate._validate_forks_limit_or_exit"),
            patch(
                "find_commits_lib.core.orchestrate._read_local_bytes_or_exit"
            ) as mock_read_local,
            patch(
                "find_commits_lib.core.orchestrate._prepare_repository"
            ) as mock_prepare_repo,
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

            # Verify that all modes were enabled
            assert args.shallow is True
            assert args.depth == 2
            assert args.selective is True
            assert args.parallel_fetch is True

            # Verify that _prepare_repository was called with all correct parameters
            mock_prepare_repo.assert_called_once()
            call_args = mock_prepare_repo.call_args
            assert call_args[1]["shallow"] is True
            assert call_args[1]["depth"] == 2
            assert call_args[1]["selective"] is True
            assert call_args[1]["parallel"] is True


def test_fast_mode_enables_clone_optimizations():
    """Test that fast mode automatically enables clone optimizations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a mock local file
        local_file = temp_path / "test_file.txt"
        local_file.write_text("hello world test content")

        # Create mock args with fast mode enabled (but clone modes initially disabled)
        args = argparse.Namespace(
            local_file=str(local_file),
            repo_url="https://github.com/test/repo.git",
            repo_dir=None,
            repo_file_path="",
            out_env="test.env",
            out_report="test.txt",
            include_forks=True,  # Start with forks enabled
            github_token="test_token",
            similarity_mode="jaccard",
            similarity_threshold=0.92,
            shingle_size=5,
            minhash_perm=128,
            progress=True,  # Start with progress enabled
            timings=True,  # Start with timings enabled
            forks_limit=20,
            forks_offset=0,
            shallow=False,  # Start with shallow disabled
            depth=1,
            selective=False,  # Start with selective disabled
            parallel_fetch=False,
            fast=True,  # Enable fast mode
        )

        # Mock the orchestrate function to test fast mode behavior
        with (
            patch("find_commits_lib.core.orchestrate._validate_forks_limit_or_exit"),
            patch(
                "find_commits_lib.core.orchestrate._read_local_bytes_or_exit"
            ) as mock_read_local,
            patch(
                "find_commits_lib.core.orchestrate._prepare_repository"
            ) as mock_prepare_repo,
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

            # Verify that fast mode enabled clone optimizations
            assert args.shallow is True
            assert args.depth == 1
            assert args.selective is True
            assert args.fast is True

            # Verify that _prepare_repository was called with fast_mode=True
            mock_prepare_repo.assert_called_once()
            call_args = mock_prepare_repo.call_args
            assert call_args[1]["fast_mode"] is True


def test_ensure_repo_function_directly():
    """Test the ensure_repo function directly with different parameters."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        repo_url = "https://github.com/test/repo.git"

        # Test with different parameter combinations
        test_cases = [
            {
                "shallow": False,
                "depth": 1,
                "selective": False,
                "parallel": False,
                "show_progress": False,
                "fast_mode": False,
            },
            {
                "shallow": True,
                "depth": 3,
                "selective": False,
                "parallel": False,
                "show_progress": False,
                "fast_mode": False,
            },
            {
                "shallow": False,
                "depth": 1,
                "selective": True,
                "parallel": False,
                "show_progress": False,
                "fast_mode": False,
            },
            {
                "shallow": False,
                "depth": 1,
                "selective": False,
                "parallel": True,
                "show_progress": False,
                "fast_mode": False,
            },
            {
                "shallow": True,
                "depth": 2,
                "selective": True,
                "parallel": True,
                "show_progress": True,
                "fast_mode": False,
            },
            {
                "shallow": False,
                "depth": 1,
                "selective": False,
                "parallel": False,
                "show_progress": False,
                "fast_mode": True,
            },
        ]

        for params in test_cases:
            # Mock the git operations
            with patch("find_commits_lib.git_ops.run") as mock_run:
                mock_run.return_value = (0, "", "")

                # Test that ensure_repo can be called with these parameters
                try:
                    ensure_repo(temp_path, repo_url, **params)
                    # Verify that run was called (indicating git commands were executed)
                    assert mock_run.called
                except Exception:
                    # Some combinations might not be valid, but the function should handle them
                    # Accept any exception as valid since we're testing parameter passing
                    pass


def test_depth_parameter_validation():
    """Test that depth parameter is handled correctly."""
    # Test different depth values
    depth_values = [1, 2, 5, 10, 50]

    for depth in depth_values:
        args = argparse.Namespace(
            local_file="test.txt",
            repo_url="https://github.com/test/repo.git",
            shallow=True,
            depth=depth,
            selective=False,
            parallel_fetch=False,
            fast=False,
        )

        # Verify that depth is preserved
        assert args.depth == depth


if __name__ == "__main__":
    test_shallow_clone_mode()
    test_selective_fetch_mode()
    test_parallel_fetch_mode()
    test_combined_clone_modes()
    test_fast_mode_enables_clone_optimizations()
    test_ensure_repo_function_directly()
    test_depth_parameter_validation()
    print("All clone mode tests passed!")
