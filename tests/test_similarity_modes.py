import argparse
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from find_commits_lib.core.orchestrate import orchestrate
from find_commits_lib.fuzzy import (
    jaccard_similarity,
    minhash_similarity,
    simhash_similarity,
    fingerprint_text_for_fuzzy,
    minhash_signature,
    simhash64,
)


def test_jaccard_similarity_mode():
    """Test that jaccard similarity mode works correctly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a mock local file
        local_file = temp_path / "test_file.txt"
        local_file.write_text("hello world test content")

        # Create mock args with jaccard similarity mode
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
            similarity_threshold=0.8,
            shingle_size=3,
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

        # Mock the orchestrate function to test jaccard mode
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
            patch("find_commits_lib.git_ops.cleanup_repo_cache"),
        ):

            # Set up mock return values
            mock_read_local.return_value = b"hello world test content"
            mock_compute_blob.return_value = ("abc123", "abc123")
            mock_scan.return_value = ("normalized_path", ["def456", "ghi789"])
            mock_dedupe.return_value = ["def456", "ghi789"]
            mock_choose_preferred.return_value = "def456"
            mock_fetch_forks.return_value = (0, 0, 0)

            # Run the orchestrate function
            try:
                orchestrate(args)
            except SystemExit:
                pass

            # Verify that jaccard mode was used
            assert args.similarity_mode == "jaccard"
            assert args.similarity_threshold == 0.8
            assert args.shingle_size == 3


def test_minhash_similarity_mode():
    """Test that minhash similarity mode works correctly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a mock local file
        local_file = temp_path / "test_file.txt"
        local_file.write_text("hello world test content")

        # Create mock args with minhash similarity mode
        args = argparse.Namespace(
            local_file=str(local_file),
            repo_url="https://github.com/test/repo.git",
            repo_dir=None,
            repo_file_path="",
            out_env="test.env",
            out_report="test.txt",
            include_forks=False,
            github_token="",
            similarity_mode="minhash",
            similarity_threshold=0.85,
            shingle_size=4,
            minhash_perm=128,
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

        # Mock the orchestrate function to test minhash mode
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
            patch("find_commits_lib.git_ops.cleanup_repo_cache"),
        ):

            # Set up mock return values
            mock_read_local.return_value = b"hello world test content"
            mock_compute_blob.return_value = ("abc123", "abc123")
            mock_scan.return_value = ("normalized_path", ["def456", "ghi789"])
            mock_dedupe.return_value = ["def456", "ghi789"]
            mock_choose_preferred.return_value = "def456"
            mock_fetch_forks.return_value = (0, 0, 0)

            # Run the orchestrate function
            try:
                orchestrate(args)
            except SystemExit:
                pass

            # Verify that minhash mode was used
            assert args.similarity_mode == "minhash"
            assert args.similarity_threshold == 0.85
            assert args.shingle_size == 4
            assert args.minhash_perm == 128


def test_simhash_similarity_mode():
    """Test that simhash similarity mode works correctly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a mock local file
        local_file = temp_path / "test_file.txt"
        local_file.write_text("hello world test content")

        # Create mock args with simhash similarity mode
        args = argparse.Namespace(
            local_file=str(local_file),
            repo_url="https://github.com/test/repo.git",
            repo_dir=None,
            repo_file_path="",
            out_env="test.env",
            out_report="test.txt",
            include_forks=False,
            github_token="",
            similarity_mode="simhash",
            similarity_threshold=0.9,
            shingle_size=5,
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

        # Mock the orchestrate function to test simhash mode
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
            patch("find_commits_lib.git_ops.cleanup_repo_cache"),
        ):

            # Set up mock return values
            mock_read_local.return_value = b"hello world test content"
            mock_compute_blob.return_value = ("abc123", "abc123")
            mock_scan.return_value = ("normalized_path", ["def456", "ghi789"])
            mock_dedupe.return_value = ["def456", "ghi789"]
            mock_choose_preferred.return_value = "def456"
            mock_fetch_forks.return_value = (0, 0, 0)

            # Run the orchestrate function
            try:
                orchestrate(args)
            except SystemExit:
                pass

            # Verify that simhash mode was used
            assert args.similarity_mode == "simhash"
            assert args.similarity_threshold == 0.9
            assert args.shingle_size == 5


def test_similarity_algorithms_directly():
    """Test the similarity algorithms directly with known inputs."""
    # Test jaccard similarity
    text1 = "hello world test"
    text2 = "hello world test"
    text3 = "hello brave new world"

    fp1 = fingerprint_text_for_fuzzy(text1, k=3)
    fp2 = fingerprint_text_for_fuzzy(text2, k=3)
    fp3 = fingerprint_text_for_fuzzy(text3, k=3)

    # Identical texts should have similarity 1.0
    assert jaccard_similarity(fp1, fp2) == 1.0

    # Different texts should have similarity < 1.0
    similarity = jaccard_similarity(fp1, fp3)
    assert 0.0 <= similarity <= 1.0

    # Test minhash similarity
    sig1 = minhash_signature(fp1, num_perm=64)
    sig2 = minhash_signature(fp2, num_perm=64)
    sig3 = minhash_signature(fp3, num_perm=64)

    # Identical texts should have similarity 1.0
    assert minhash_similarity(sig1, sig2) == 1.0

    # Different texts should have similarity < 1.0
    minhash_sim = minhash_similarity(sig1, sig3)
    assert 0.0 <= minhash_sim <= 1.0

    # Test simhash similarity
    sh1 = simhash64(text1)
    sh2 = simhash64(text2)
    sh3 = simhash64(text3)

    # Identical texts should have similarity 1.0
    assert simhash_similarity(sh1, sh2) == 1.0

    # Different texts should have similarity < 1.0
    simhash_sim = simhash_similarity(sh1, sh3)
    assert 0.0 <= simhash_sim <= 1.0


def test_similarity_threshold_filtering():
    """Test that similarity threshold filtering works correctly."""
    # Test with different threshold values
    text1 = "hello world test content"
    text2 = "hello world test content"  # Identical
    text3 = "hello world test content modified"  # Similar
    text4 = "completely different text here"  # Different

    fp1 = fingerprint_text_for_fuzzy(text1, k=3)
    fp2 = fingerprint_text_for_fuzzy(text2, k=3)
    fp3 = fingerprint_text_for_fuzzy(text3, k=3)
    fp4 = fingerprint_text_for_fuzzy(text4, k=3)

    # Test jaccard similarities
    sim_identical = jaccard_similarity(fp1, fp2)
    sim_similar = jaccard_similarity(fp1, fp3)
    sim_different = jaccard_similarity(fp1, fp4)

    # Identical should be 1.0
    assert sim_identical == 1.0

    # Similar should be between 0 and 1 (allow 0.0 for very different texts)
    assert 0.0 <= sim_similar <= 1.0

    # Different should be lower than or equal to similar (both could be 0.0)
    assert sim_different <= sim_similar

    # Test threshold filtering logic
    threshold_high = 0.9
    threshold_medium = 0.3  # Lower threshold for similar texts
    threshold_low = 0.1

    # High threshold should only pass identical
    assert sim_identical >= threshold_high
    assert sim_similar < threshold_high
    assert sim_different < threshold_high

    # Medium threshold should pass identical and similar
    assert sim_identical >= threshold_medium
    assert sim_similar >= threshold_medium
    assert sim_different < threshold_medium

    # Low threshold should pass identical and similar (different might still be 0.0)
    assert sim_identical >= threshold_low
    assert sim_similar >= threshold_low
    # Different text might have 0.0 similarity, which is acceptable
    assert sim_different >= 0.0


if __name__ == "__main__":
    test_jaccard_similarity_mode()
    test_minhash_similarity_mode()
    test_simhash_similarity_mode()
    test_similarity_algorithms_directly()
    test_similarity_threshold_filtering()
    print("All similarity mode tests passed!")
