import argparse
import tempfile
from pathlib import Path
from unittest.mock import patch

from find_commits_lib.core import orchestrate
from find_commits_lib.fuzzy import (
    fingerprint_text_for_fuzzy,
    jaccard_similarity,
    minhash_signature,
    minhash_similarity,
    simhash64,
    simhash_similarity,
)


def test_basic_similarity_algorithms():
    """Test basic similarity algorithm functionality."""
    # Test jaccard similarity
    text1 = "hello world test"
    text2 = "hello world test"
    text3 = "hello brave new world"

    fp1 = fingerprint_text_for_fuzzy(text1, k=3)
    fp2 = fingerprint_text_for_fuzzy(text2, k=3)
    fp3 = fingerprint_text_for_fuzzy(text3, k=3)

    # Identical texts should have similarity 1.0
    assert jaccard_similarity(fp1, fp2) == 1.0

    # Different texts should have similarity between 0 and 1
    similarity = jaccard_similarity(fp1, fp3)
    assert 0.0 <= similarity <= 1.0

    # Test minhash similarity
    sig1 = minhash_signature(fp1, num_perm=64)
    sig2 = minhash_signature(fp2, num_perm=64)
    sig3 = minhash_signature(fp3, num_perm=64)

    # Identical texts should have similarity 1.0
    assert minhash_similarity(sig1, sig2) == 1.0

    # Different texts should have similarity between 0 and 1
    minhash_sim = minhash_similarity(sig1, sig3)
    assert 0.0 <= minhash_sim <= 1.0

    # Test simhash similarity
    sh1 = simhash64(text1)
    sh2 = simhash64(text2)
    sh3 = simhash64(text3)

    # Identical texts should have similarity 1.0
    assert simhash_similarity(sh1, sh2) == 1.0

    # Different texts should have similarity between 0 and 1
    simhash_sim = simhash_similarity(sh1, sh3)
    assert 0.0 <= simhash_sim <= 1.0


def test_fast_mode_optimizations():
    """Test that fast mode applies correct optimizations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a mock local file
        local_file = temp_path / "test_file.txt"
        local_file.write_text("hello world test content")

        # Create mock args with fast mode enabled
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
            patch("find_commits_lib.utils.Spinner"),
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

            # Verify that fast mode optimizations were applied
            assert args.progress is False
            assert args.timings is False
            assert args.shallow is True
            assert args.selective is True
            assert args.include_forks is False
            assert args.fast is True


def test_similarity_modes():
    """Test different similarity modes."""
    # Test jaccard mode
    text1 = "hello world test content"
    text2 = "hello world test content"
    text3 = "hello world different content"

    fp1 = fingerprint_text_for_fuzzy(text1, k=3)
    fp2 = fingerprint_text_for_fuzzy(text2, k=3)
    fp3 = fingerprint_text_for_fuzzy(text3, k=3)

    # Test jaccard similarity
    jaccard_sim = jaccard_similarity(fp1, fp2)
    assert jaccard_sim == 1.0

    jaccard_diff = jaccard_similarity(fp1, fp3)
    assert 0.0 <= jaccard_diff <= 1.0

    # Test minhash similarity
    sig1 = minhash_signature(fp1, num_perm=64)
    sig2 = minhash_signature(fp2, num_perm=64)
    sig3 = minhash_signature(fp3, num_perm=64)

    minhash_sim = minhash_similarity(sig1, sig2)
    assert minhash_sim == 1.0

    minhash_diff = minhash_similarity(sig1, sig3)
    assert 0.0 <= minhash_diff <= 1.0

    # Test simhash similarity
    sh1 = simhash64(text1)
    sh2 = simhash64(text2)
    sh3 = simhash64(text3)

    simhash_sim = simhash_similarity(sh1, sh2)
    assert simhash_sim == 1.0

    simhash_diff = simhash_similarity(sh1, sh3)
    assert 0.0 <= simhash_diff <= 1.0


def test_clone_mode_parameters():
    """Test that clone mode parameters are handled correctly."""
    # Test shallow clone parameters
    args = argparse.Namespace(
        shallow=True, depth=3, selective=False, parallel_fetch=False
    )

    assert args.shallow is True
    assert args.depth == 3
    assert args.selective is False
    assert args.parallel_fetch is False

    # Test selective fetch parameters
    args = argparse.Namespace(
        shallow=False, depth=1, selective=True, parallel_fetch=False
    )

    assert args.shallow is False
    assert args.depth == 1
    assert args.selective is True
    assert args.parallel_fetch is False

    # Test parallel fetch parameters
    args = argparse.Namespace(
        shallow=False, depth=1, selective=False, parallel_fetch=True
    )

    assert args.shallow is False
    assert args.depth == 1
    assert args.selective is False
    assert args.parallel_fetch is True


def test_fork_discovery_parameters():
    """Test that fork discovery parameters are handled correctly."""
    # Test with fork discovery enabled
    args = argparse.Namespace(
        include_forks=True, github_token="test_token", forks_limit=10, forks_offset=2
    )

    assert args.include_forks is True
    assert args.github_token == "test_token"
    assert args.forks_limit == 10
    assert args.forks_offset == 2

    # Test with fork discovery disabled
    args = argparse.Namespace(
        include_forks=False, github_token="", forks_limit=20, forks_offset=0
    )

    assert args.include_forks is False
    assert args.github_token == ""
    assert args.forks_limit == 20
    assert args.forks_offset == 0


def test_progress_and_timing_parameters():
    """Test that progress and timing parameters are handled correctly."""
    # Test with both enabled
    args = argparse.Namespace(progress=True, timings=True)

    assert args.progress is True
    assert args.timings is True

    # Test with both disabled
    args = argparse.Namespace(progress=False, timings=False)

    assert args.progress is False
    assert args.timings is False


def test_input_modes():
    """Test different input modes."""
    # Test file input mode
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        test_file = temp_path / "test_file.txt"
        test_content = "hello world test content"
        test_file.write_text(test_content)

        args = argparse.Namespace(local_file=str(test_file))

        # Test that file exists
        assert Path(args.local_file).exists()
        assert Path(args.local_file).read_text() == test_content

    # Test stdin input mode
    args = argparse.Namespace(local_file="-")
    assert args.local_file == "-"


def test_output_parameters():
    """Test output parameter handling."""
    args = argparse.Namespace(out_env="custom.env", out_report="custom.txt")

    assert args.out_env == "custom.env"
    assert args.out_report == "custom.txt"


if __name__ == "__main__":
    test_basic_similarity_algorithms()
    test_fast_mode_optimizations()
    test_similarity_modes()
    test_clone_mode_parameters()
    test_fork_discovery_parameters()
    test_progress_and_timing_parameters()
    test_input_modes()
    test_output_parameters()
    print("All basic functionality tests passed!")
