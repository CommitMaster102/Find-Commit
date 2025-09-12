import argparse
import tempfile
from pathlib import Path
from unittest.mock import patch

from find_commits_lib.core import orchestrate


def test_fast_mode_flag_application():
    """Test that fast mode correctly applies optimizations to args."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a mock local file
        local_file = temp_path / "test_file.txt"
        local_file.write_text("test content")

        # Create mock args with fast mode enabled
        args = argparse.Namespace(
            local_file=str(local_file),
            repo_url="https://github.com/test/repo.git",
            repo_dir=None,
            repo_file_path="",
            out_env="test.env",
            out_report="test.txt",
            include_forks=True,  # Start with forks enabled
            github_token="",
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

        # Mock the orchestrate function to just test the fast mode logic
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
            mock_read_local.return_value = b"test content"
            mock_compute_blob.return_value = ("abc123", "abc123")
            mock_scan.return_value = ("exact_blob", ["abc123"])
            mock_dedupe.return_value = ["abc123"]
            mock_choose_preferred.return_value = "abc123"
            mock_fetch_forks.return_value = (0, 0, 0)

            # Run the orchestrate function
            try:
                orchestrate(args)
            except SystemExit:
                pass

            # Verify that fast mode optimizations were applied
            # 1. Progress and timings should be disabled
            assert args.progress is False
            assert args.timings is False

            # 2. Shallow clone and selective fetch should be enabled
            assert args.shallow is True
            assert args.selective is True

            # 3. Fork fetching should be disabled
            assert args.include_forks is False

            # 4. _prepare_repository should be called with fast_mode=True
            mock_prepare_repo.assert_called_once()
            call_args = mock_prepare_repo.call_args
            assert call_args[1]["fast_mode"] is True


def test_fast_mode_file_writing_optimizations():
    """Test that fast mode skips expensive file writing operations."""
    from find_commits_lib.core.orchestrate import _write_env_file, _write_report

    # Create mock args with fast mode enabled
    args = argparse.Namespace(
        fast=True, out_report="test_report.txt", out_env="test_env.env"
    )

    # Mock data
    mode = "exact_blob"
    preferred = "abc123"
    blob_hash_norm = "abc123"
    blob_hash_raw = "abc123"
    forks_fetched = 0
    forks_discovered = 0
    forks_selected = 0
    candidates = ["abc123", "def456"]
    repo_dir = Path(".")
    timings = {
        "step1_start": "2024-01-01 10:00:00.000",
        "step1_end": "2024-01-01 10:00:01.000",
        "step1_ms": 1000,
        "step2_start": "2024-01-01 10:00:01.000",
        "step2_end": "2024-01-01 10:00:02.000",
        "step2_ms": 1000,
    }

    # Mock the expensive git operations that would be skipped in fast mode
    with (
        patch("find_commits_lib.git_ops.commit_timestamp") as mock_timestamp,
        patch("find_commits_lib.git_ops.branches_containing") as mock_branches,
        patch(
            "find_commits_lib.selection.choose_branch_for_commit"
        ) as mock_choose_branch,
    ):

        # Set up mock return values
        mock_timestamp.return_value = 1234567890
        mock_branches.return_value = ["origin/main"]
        mock_choose_branch.return_value = "main"

        # Test report writing
        _write_report(
            args,
            mode,
            preferred,
            blob_hash_norm,
            blob_hash_raw,
            forks_fetched,
            forks_discovered,
            forks_selected,
            candidates,
            repo_dir,
            timings,
        )

        # Test env file writing
        _write_env_file(
            args,
            mode,
            preferred,
            candidates,
            forks_fetched,
            forks_discovered,
            forks_selected,
            repo_dir,
            timings,
        )

        # Verify that expensive operations were skipped in fast mode
        # These should not be called because we're in fast mode
        mock_timestamp.assert_not_called()
        mock_branches.assert_not_called()
        mock_choose_branch.assert_not_called()

        # Check that files were created
        assert Path("test_report.txt").exists()
        assert Path("test_env.env").exists()

        # Check report content - should not contain detailed timing info
        report_content = Path("test_report.txt").read_text()
        assert "mode=exact_blob" in report_content
        assert "preferred=abc123" in report_content
        assert "candidates_count=2" in report_content
        # Should not contain detailed timing information in fast mode
        assert "_start=" not in report_content
        assert "_end=" not in report_content
        assert "_difference_time=" not in report_content

        # Check env content - should not contain branch information
        env_content = Path("test_env.env").read_text()
        assert "PREFERRED_COMMIT=abc123" in env_content
        assert "MATCH_MODE=exact_blob" in env_content
        # Should not contain branch information in fast mode
        assert "PREFERRED_BRANCH=" not in env_content
        assert "PREFERRED_BRANCHES=" not in env_content

        # Clean up test files
        Path("test_report.txt").unlink(missing_ok=True)
        Path("test_env.env").unlink(missing_ok=True)


if __name__ == "__main__":
    test_fast_mode_flag_application()
    test_fast_mode_file_writing_optimizations()
    print("All fast mode tests passed!")
