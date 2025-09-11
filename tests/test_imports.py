def test_imports():
    from find_commits_lib import (
        normalize_lf,
        fingerprint_text_for_fuzzy,
        jaccard_similarity,
        minhash_signature,
        minhash_similarity,
        simhash64,
        simhash_similarity,
    )

    assert callable(normalize_lf)
    a = fingerprint_text_for_fuzzy("hello world")
    b = fingerprint_text_for_fuzzy("hello world")
    assert jaccard_similarity(a, b) == 1.0

    sig_a = minhash_signature(a, num_perm=16)
    sig_b = minhash_signature(b, num_perm=16)
    assert minhash_similarity(sig_a, sig_b) == 1.0

    sh_a = simhash64("hello world")
    sh_b = simhash64("hello world")
    assert simhash_similarity(sh_a, sh_b) == 1.0

