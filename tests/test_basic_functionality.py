import argparse
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from find_commits_lib.core.orchestrate import orchestrate
from find_commits_lib.fuzzy import (
    fingerprint_text_for_fuzzy,
    jaccard_similarity,
    minhash_signature,
    minhash_similarity,
    simhash64,
    simhash_similarity,
)


@pytest.mark.parametrize(
    "text1,text2,k,perm",
    [
        ("hello world test", "hello world test", 3, 64),
        ("hello brave new world", "hello world test", 3, 64),
    ],
)
def test_basic_similarity_algorithms(text1, text2, k, perm):
    fp1 = fingerprint_text_for_fuzzy(text1, k=k)
    fp2 = fingerprint_text_for_fuzzy(text2, k=k)

    jacc = jaccard_similarity(fp1, fp2)
    assert 0.0 <= jacc <= 1.0
    if text1 == text2:
        assert jacc == 1.0

    sig1 = minhash_signature(fp1, num_perm=perm)
    sig2 = minhash_signature(fp2, num_perm=perm)
    mh = minhash_similarity(sig1, sig2)
    assert 0.0 <= mh <= 1.0
    if text1 == text2:
        assert mh == 1.0

    sh1 = simhash64(text1)
    sh2 = simhash64(text2)
    shs = simhash_similarity(sh1, sh2)
    assert 0.0 <= shs <= 1.0
    if text1 == text2:
        assert shs == 1.0


def test_orchestrate_smoke_jaccard_calls_outputs():
    """Run orchestrate with jaccard and verify output hooks are called."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        local_file = temp_path / "test_file.txt"
        local_file.write_text("hello world test content")

        args = argparse.Namespace(
            local_file=str(local_file),
            repo_url="https://github.com/test/repo.git",
            repo_dir=None,
            repo_file_path="",
            out_env=str(temp_path / "out.env"),
            out_report=str(temp_path / "out.txt"),
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
            patch(
                "find_commits_lib.core.orchestrate._write_report"
            ) as mock_write_report,
            patch(
                "find_commits_lib.core.orchestrate._write_env_file"
            ) as mock_write_env,
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
                # Expected: orchestrate may call sys.exit() during testing
                pass

            mock_write_report.assert_called_once()
            mock_write_env.assert_called_once()
