import re
from typing import List
import hashlib
import random


def tokenize_for_fuzzy(text: str) -> List[str]:
    # Keep only alphanumerics and underscores as tokens
    return re.findall(r"[A-Za-z0-9_]+", text)


def shingle_tokens(tokens: List[str], k: int = 5) -> List[str]:
    if len(tokens) < k:
        return [" ".join(tokens)] if tokens else []
    return [" ".join(tokens[i : i + k]) for i in range(0, len(tokens) - k + 1)]


def fingerprint_text_for_fuzzy(text: str, k: int = 5) -> set[str]:
    tokens = tokenize_for_fuzzy(text)
    shingles = shingle_tokens(tokens, k)
    return set(shingles)


def jaccard_similarity(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


# ----------------------
# MinHash (Jaccard LSH)
# ----------------------

_MINHASH_PARAMS_CACHE: dict[int, tuple[list[int], list[int]]] = {}
_UINT64_MASK = (1 << 64) - 1


def _stable_hash64(s: str) -> int:
    """Deterministic 64-bit hash for strings (stable across runs/OS).

    Uses SHA-1 and takes the first 8 bytes as a big-endian integer.
    """
    h = hashlib.sha1(s.encode("utf-8", errors="ignore")).digest()
    return int.from_bytes(h[:8], "big", signed=False)


def _get_minhash_params(num_perm: int) -> tuple[list[int], list[int]]:
    """Return (a, b) parameter arrays for MinHash permutations.

    Parameters are generated deterministically from a fixed seed.
    """
    if num_perm in _MINHASH_PARAMS_CACHE:
        return _MINHASH_PARAMS_CACHE[num_perm]
    rnd = random.Random(0xC0FFEE)
    a: list[int] = []
    b: list[int] = []
    for _ in range(num_perm):
        # Ensure 'a' is odd to improve distribution under modulo 2^64
        ai = rnd.getrandbits(64) | 1
        bi = rnd.getrandbits(64)
        a.append(ai & _UINT64_MASK)
        b.append(bi & _UINT64_MASK)
    _MINHASH_PARAMS_CACHE[num_perm] = (a, b)
    return a, b


def minhash_signature(shingles: set[str], num_perm: int = 128) -> list[int]:
    """Compute MinHash signature for a set of shingles.

    Returns a list of length num_perm with 64-bit integers.
    If the input set is empty, returns all zeros for determinism.
    """
    if not shingles:
        return [0] * num_perm
    a, b = _get_minhash_params(num_perm)
    signature = [_UINT64_MASK] * num_perm
    for sh in shingles:
        x = _stable_hash64(sh)
        for i in range(num_perm):
            # Linear hash family over 64-bit space
            hv = (a[i] * x + b[i]) & _UINT64_MASK
            if hv < signature[i]:
                signature[i] = hv
    return signature


def minhash_similarity(sig_a: list[int], sig_b: list[int]) -> float:
    """Estimate Jaccard similarity from two MinHash signatures."""
    if not sig_a and not sig_b:
        return 1.0
    if not sig_a or not sig_b:
        return 0.0
    n = min(len(sig_a), len(sig_b))
    if n == 0:
        return 0.0
    equal = 0
    for i in range(n):
        if sig_a[i] == sig_b[i]:
            equal += 1
    return equal / n


# ---------------
# SimHash (64-bit)
# ---------------


def simhash64_from_tokens(tokens: List[str]) -> int:
    """Compute 64-bit SimHash from a list of tokens (with unit weights)."""
    if not tokens:
        return 0
    accum = [0] * 64
    for tok in tokens:
        hv = _stable_hash64(tok)
        for bit in range(64):
            if (hv >> bit) & 1:
                accum[bit] += 1
            else:
                accum[bit] -= 1
    out = 0
    for bit in range(64):
        if accum[bit] > 0:
            out |= 1 << bit
    return out


def simhash64(text: str) -> int:
    return simhash64_from_tokens(tokenize_for_fuzzy(text))


def _hamming_distance64(a: int, b: int) -> int:
    return (a ^ b).bit_count()


def simhash_similarity(a: int, b: int) -> float:
    """Return similarity in [0,1] as 1 - HammingDistance/64."""
    return 1.0 - (_hamming_distance64(a, b) / 64.0)
