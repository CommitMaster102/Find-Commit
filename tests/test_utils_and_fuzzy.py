from find_commits_lib.utils import normalize_lf, repo_basename_from_url
from find_commits_lib.fuzzy import (
    tokenize_for_fuzzy,
    shingle_tokens,
    fingerprint_text_for_fuzzy,
    jaccard_similarity,
    minhash_signature,
    minhash_similarity,
    simhash64,
    simhash_similarity,
)
from find_commits_lib.github_api import parse_github_owner_repo


def test_normalize_lf():
    data = b"a\r\nb\rc\n"
    out = normalize_lf(data)
    assert out == b"a\nb\nc\n"


def test_repo_basename_from_url():
    assert repo_basename_from_url("https://github.com/org/repo.git") == "repo"
    assert repo_basename_from_url("git@github.com:org/repo.git") == "repo"
    assert repo_basename_from_url("/path/to/repo") == "repo"


def test_tokenize_and_shingles():
    tokens = tokenize_for_fuzzy("Hello, world_123!")
    assert tokens == ["Hello", "world_123"]
    shingles = shingle_tokens(["a", "b", "c", "d"], k=2)
    assert shingles == ["a b", "b c", "c d"]


def test_fingerprint_and_jaccard():
    a = fingerprint_text_for_fuzzy("hello world")
    b = fingerprint_text_for_fuzzy("hello world")
    c = fingerprint_text_for_fuzzy("hello brave new world")
    assert jaccard_similarity(a, b) == 1.0
    assert 0.0 <= jaccard_similarity(a, c) <= 1.0


def test_minhash_similarity():
    a = fingerprint_text_for_fuzzy("hello world")
    b = fingerprint_text_for_fuzzy("hello world")
    sig_a = minhash_signature(a, num_perm=16)
    sig_b = minhash_signature(b, num_perm=16)
    assert minhash_similarity(sig_a, sig_b) == 1.0


def test_simhash_similarity():
    sh_a = simhash64("hello world")
    sh_b = simhash64("hello world")
    assert simhash_similarity(sh_a, sh_b) == 1.0


def test_parse_github_owner_repo():
    assert parse_github_owner_repo("https://github.com/owner/repo.git") == ("owner", "repo")
    assert parse_github_owner_repo("git@github.com:owner/repo.git") == ("owner", "repo")
    assert parse_github_owner_repo("ssh://git@github.com/owner/repo") == ("owner", "repo")
    assert parse_github_owner_repo("https://example.com/notgithub/repo.git") is None


