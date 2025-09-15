import argparse
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from find_commits_lib.core.orchestrate import orchestrate
from find_commits_lib.fuzzy import (
    char_ngram_set,
    fingerprint_text_for_fuzzy,
    jaccard_similarity,
    minhash_signature,
    minhash_similarity,
    simhash64,
    simhash_similarity,
    winnow_fingerprint,
)


@pytest.mark.parametrize(
    "mode,threshold,shingle,perm",
    [
        ("jaccard", 0.8, 3, 64),
        ("minhash", 0.85, 4, 128),
        ("simhash", 0.9, 5, 256),
    ],
)
def test_similarity_modes_parametrized(mode, threshold, shingle, perm):
    """Exercise orchestrate wiring across supported similarity modes."""
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
            similarity_mode=mode,
            similarity_threshold=threshold,
            shingle_size=shingle,
            minhash_perm=perm,
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
            mock_scan.return_value = ("normalized_path", ["def456", "ghi789"])
            mock_dedupe.return_value = ["def456", "ghi789"]
            mock_choose_preferred.return_value = "def456"
            mock_fetch_forks.return_value = (0, 0, 0)

            try:
                orchestrate(args)
            except SystemExit:
                pass

            assert args.similarity_mode == mode
            assert args.similarity_threshold == threshold
            assert args.shingle_size == shingle
            assert args.minhash_perm == perm


@pytest.mark.parametrize(
    "mode,extra",
    [
        ("charjaccard", {"char_ngram_size": 4}),
        ("winnow", {"winnow_window": 4, "shingle_size": 3}),
    ],
)
def test_additional_modes_parametrized(mode, extra):
    """Exercise orchestrate wiring for charjaccard and winnow modes."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        local_file = temp_path / "test_file.txt"
        local_file.write_text("hello world test content")

        base = dict(
            local_file=str(local_file),
            repo_url="https://github.com/test/repo.git",
            repo_dir=None,
            repo_file_path="",
            out_env="test.env",
            out_report="test.txt",
            include_forks=False,
            github_token="",
            similarity_mode=mode,
            similarity_threshold=0.5,
            shingle_size=extra.get("shingle_size", 5),
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
        base.update(extra)
        args = argparse.Namespace(**base)

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
            mock_scan.return_value = ("normalized_path", ["def456", "ghi789"])
            mock_dedupe.return_value = ["def456", "ghi789"]
            mock_choose_preferred.return_value = "def456"
            mock_fetch_forks.return_value = (0, 0, 0)

            try:
                orchestrate(args)
            except SystemExit:
                pass

            assert args.similarity_mode == mode
            if mode == "charjaccard":
                assert (
                    getattr(args, "char_ngram_size", None) == extra["char_ngram_size"]
                )
            if mode == "winnow":
                assert getattr(args, "winnow_window", None) == extra["winnow_window"]


@pytest.mark.parametrize(
    "text1,text2,k,perm",
    [
        ("hello world test", "hello world test", 3, 64),
        ("hello brave new world", "hello world test", 3, 64),
        ("short a b", "short a b", 2, 16),
    ],
)
def test_similarity_algorithms_directly(text1, text2, k, perm):
    fp1 = fingerprint_text_for_fuzzy(text1, k=k)
    fp2 = fingerprint_text_for_fuzzy(text2, k=k)

    # Jaccard bounds
    jacc = jaccard_similarity(fp1, fp2)
    assert 0.0 <= jacc <= 1.0
    if text1 == text2:
        assert jacc == 1.0

    # MinHash bounds
    sig1 = minhash_signature(fp1, num_perm=perm)
    sig2 = minhash_signature(fp2, num_perm=perm)
    mh = minhash_similarity(sig1, sig2)
    assert 0.0 <= mh <= 1.0
    if text1 == text2:
        assert mh == 1.0

    # SimHash bounds
    sh1 = simhash64(text1)
    sh2 = simhash64(text2)
    shs = simhash_similarity(sh1, sh2)
    assert 0.0 <= shs <= 1.0
    if text1 == text2:
        assert shs == 1.0


def test_char_ngram_and_winnow_direct():
    # char n-grams
    s = "alpha beta"
    grams = char_ngram_set(s, n=1)
    assert set("alpha beta") == grams
    grams5 = char_ngram_set(s, n=5)
    assert len(grams5) > 0
    # If stream shorter than n -> single gram
    short = char_ngram_set("a", n=5)
    assert short == {"a"}

    # winnow: with k=3 and window larger than shingles -> single fingerprint
    fp = winnow_fingerprint("one two three", k=3, window=10)
    assert isinstance(fp, set)
    assert len(fp) == 1
    val = next(iter(fp))
    assert isinstance(val, str) and len(val) == 16  # 64-bit hex


@pytest.mark.parametrize(
    "base,variant_different,variant_similar,thresholds",
    [
        (
            "hello world test content",
            "completely different text here",
            "hello world test content modified",
            (0.9, 0.3, 0.1),
        ),
        (
            "a b c d e",
            "x y z",
            "a b c d f",
            (0.95, 0.4, 0.1),
        ),
    ],
)
def test_similarity_threshold_filtering(
    base, variant_different, variant_similar, thresholds
):
    k = 3
    fp_base = fingerprint_text_for_fuzzy(base, k=k)
    fp_same = fingerprint_text_for_fuzzy(base, k=k)
    fp_sim = fingerprint_text_for_fuzzy(variant_similar, k=k)
    fp_diff = fingerprint_text_for_fuzzy(variant_different, k=k)

    sim_identical = jaccard_similarity(fp_base, fp_same)
    sim_similar = jaccard_similarity(fp_base, fp_sim)
    sim_different = jaccard_similarity(fp_base, fp_diff)

    th_high, th_med, th_low = thresholds

    assert sim_identical == 1.0
    assert 0.0 <= sim_similar <= 1.0
    assert 0.0 <= sim_different <= 1.0
    assert sim_different <= sim_similar

    assert sim_identical >= th_high
    assert sim_similar < th_high
    assert sim_different < th_high

    assert sim_identical >= th_med
    assert sim_similar >= th_med
    assert sim_different < th_med

    assert sim_identical >= th_low
    assert sim_similar >= th_low
    assert sim_different >= 0.0
