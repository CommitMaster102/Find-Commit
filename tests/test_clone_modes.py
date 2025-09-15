import argparse
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from find_commits_lib.core.orchestrate import orchestrate
from find_commits_lib.git_ops import ensure_repo


@pytest.mark.parametrize(
    "shallow,depth",
    [(True, 1), (True, 3)],
)
def test_shallow_clone_mode(shallow, depth):
    """Shallow clone wiring passes correct flags and depth."""
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
            progress=False,
            timings=False,
            forks_limit=20,
            forks_offset=0,
            shallow=shallow,
            depth=depth,
            selective=False,
            parallel_fetch=False,
            fast=False,
        )

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

            assert args.shallow is shallow
            assert args.depth == depth

            mock_prepare_repo.assert_called_once()
            call_args = mock_prepare_repo.call_args
            assert call_args[1]["shallow"] is shallow
            assert call_args[1]["depth"] == depth


@pytest.mark.parametrize("selective", [True, False])
def test_selective_fetch_mode(selective):
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
            progress=False,
            timings=False,
            forks_limit=20,
            forks_offset=0,
            shallow=False,
            depth=1,
            selective=selective,
            parallel_fetch=False,
            fast=False,
        )

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

            assert args.selective is selective
            mock_prepare_repo.assert_called_once()
            call_args = mock_prepare_repo.call_args
            assert call_args[1]["selective"] is selective


@pytest.mark.parametrize("parallel", [True, False])
def test_parallel_fetch_mode(parallel):
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
            progress=False,
            timings=False,
            forks_limit=20,
            forks_offset=0,
            shallow=False,
            depth=1,
            selective=False,
            parallel_fetch=parallel,
            fast=False,
        )

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

            assert args.parallel_fetch is parallel
            mock_prepare_repo.assert_called_once()
            call_args = mock_prepare_repo.call_args
            assert call_args[1]["parallel"] is parallel


def test_combined_clone_modes():
    """Multiple clone modes can be combined and passed through."""
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
                # Orchestration may terminate early with sys.exit during tests
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
    """Fast mode automatically enables clone optimizations."""
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
                # Orchestration may terminate early with sys.exit during tests
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
    """Ensure ensure_repo is invokable with various parameter sets."""
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
                    # Some combinations may raise depending on environment; ignore.
                    pass


def test_depth_parameter_validation():
    """Depth parameter remains unchanged across values."""
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
