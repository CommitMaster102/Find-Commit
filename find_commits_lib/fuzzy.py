import hashlib
import random
import re
import unicodedata
from typing import List


def _split_identifier(token: str) -> List[str]:
    """Split a single identifier into constituent parts.

    - Splits on underscores first.
    - Then splits each chunk into camelCase/PascalCase and numeric runs.
    - Preserves order; returns lowercase parts.
    """
    parts: list[str] = []
    for chunk in token.split("_"):
        if not chunk:
            continue
        # Regex splits: acronyms, words, trailing all-caps, and digits
        for p in re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+", chunk):
            if p:
                parts.append(p.lower())
    return parts


def tokenize_for_fuzzy(text: str) -> List[str]:
    """Tokenize text for fuzzy matching.

    - Normalizes Unicode to NFKC for stability across inputs.
    - Lowercases tokens to reduce case-sensitivity.
    - Keeps only alphanumerics and underscores as tokens.
    """
    if not text:
        return []
    normalized = unicodedata.normalize("NFKC", text)
    raw_tokens = re.findall(r"[A-Za-z0-9_]+", normalized)
    tokens: list[str] = []
    for tok in raw_tokens:
        # Split identifiers into meaningful parts
        parts = _split_identifier(tok)
        if parts:
            tokens.extend(parts)
    return tokens


def shingle_tokens(tokens: List[str], k: int = 5) -> List[str]:
    """Create contiguous k-gram shingles from a token list.

    Behavior:
    - If k <= 1, each token is its own shingle (returns the tokens).
    - If 1 < k and len(tokens) < k, returns a single shingle joining all tokens.
    - Otherwise, returns sliding-window shingles with stride 1.
    """
    if not tokens:
        return []
    if k <= 1:
        return list(tokens)
    if len(tokens) < k:
        return [" ".join(tokens)]
    return [" ".join(tokens[i : i + k]) for i in range(0, len(tokens) - k + 1)]


def fingerprint_text_for_fuzzy(text: str, k: int = 5) -> set[str]:
    """Compute a set of token shingles for fuzzy matching.

    This function is a thin pipeline:
    1) Tokenize with `tokenize_for_fuzzy` (NFKC normalization, lowercasing,
       and identifier splitting for snake_case/camelCase/acronyms/digits).
    2) Build contiguous k-gram shingles with `shingle_tokens`.

    Parameters:
    - text: Input text to fingerprint.
    - k: Shingle size. If k <= 1, shingles are unigrams. If the token list is
         shorter than k, a single joined shingle is produced. See `shingle_tokens`.

    Returns:
    - A set of unique shingles (strings). Empty set for empty input.

    Example:
    - text = "HTTPRequest2ID_manager", k = 3
      tokens   -> ["http", "request", "2", "id", "manager"]
      shingles -> ["http request 2", "request 2 id", "2 id manager"]
      return set(shingles)

    Notes:
    - Deterministic and stable across runs/OS.
    - For large-scale similarity, compute `minhash_signature` over this set and
      compare via `minhash_similarity`. For near-duplicate detection, consider
      `simhash64`/`simhash_similarity`.
    """
    tokens = tokenize_for_fuzzy(text)
    shingles = shingle_tokens(tokens, k)
    return set(shingles)


def jaccard_similarity(a: set[str], b: set[str]) -> float:
    """Compute Jaccard similarity of two sets without materializing intersection/union.

    This implementation counts the intersection by iterating over the smaller set
    and uses |A| + |B| - |A ∩ B| to derive the union cardinality.
    """
    len_a = len(a)
    len_b = len(b)
    if len_a == 0 and len_b == 0:
        return 1.0
    if len_a == 0 or len_b == 0:
        return 0.0
    # Iterate over the smaller set for fewer checks.
    if len_a > len_b:
        a, b = b, a
        len_a, len_b = len_b, len_a
    inter = 0
    for element in a:
        if element in b:
            inter += 1
    union = len_a + len_b - inter
    return inter / union if union else 0.0


# ----------------------
# MinHash (Jaccard LSH)
# ----------------------

_MINHASH_PARAMS_CACHE: dict[int, tuple[list[int], list[int]]] = {}
_UINT64_MASK = (1 << 64) - 1


def _stable_hash64(s: str) -> int:
    """Deterministic 64-bit hash for strings (stable across runs/OS).

    Uses SHA-1 (non-cryptographic) and takes the first 8 bytes as a big-endian integer.
    """
    h = hashlib.sha1(s.encode("utf-8", errors="ignore"), usedforsecurity=False).digest()
    return int.from_bytes(h[:8], "big", signed=False)


def _get_minhash_params(num_perm: int) -> tuple[list[int], list[int]]:
    """Return (a, b) parameter arrays for MinHash permutations.

    Parameters are generated deterministically from a fixed seed.
    """
    if num_perm in _MINHASH_PARAMS_CACHE:
        return _MINHASH_PARAMS_CACHE[num_perm]
    # Use deterministic seed for consistent MinHash parameters
    # This is not for cryptographic purposes but for consistent hashing
    rnd = random.Random(
        42
    )  # nosec B311 - deterministic seed for consistent hashing, not crypto
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


def _normalized_ascii_stream(text: str) -> str:
    """Normalize to NFKC, lowercase, and join tokens as a space-separated stream."""
    toks = tokenize_for_fuzzy(text)
    return " ".join(toks)


def char_ngram_set(text: str, n: int = 5) -> set[str]:
    """Return set of contiguous character n-grams from normalized token stream.

    - Uses tokenize_for_fuzzy + join with single spaces to form a consistent stream.
    - If stream length < n and not empty, returns the whole stream as a single gram.
    - Returns empty set for empty input.
    """
    stream = _normalized_ascii_stream(text)
    if not stream:
        return set()
    if n <= 1:
        return set(stream)
    if len(stream) < n:
        return {stream}
    return {stream[i : i + n] for i in range(0, len(stream) - n + 1)}


def winnow_fingerprint(text: str, k: int = 5, window: int = 4) -> set[str]:
    """Winnowing-based fingerprint over token k-gram shingles.

    - Build token shingles of size k.
    - Hash each shingle with a stable 64-bit hash.
    - Slide a window of size `window` over the hash list and select the minimum
      hash in each window (rightmost in ties) as the fingerprint.
    - Returns a set of hex-encoded 64-bit hashes as strings.
    """
    tokens = tokenize_for_fuzzy(text)
    shingles = shingle_tokens(tokens, k)
    if not shingles:
        return set()
    hashes = [_stable_hash64(s) for s in shingles]
    w = max(1, int(window or 1))
    picked: set[int] = set()
    if len(hashes) <= w:
        picked.add(min(hashes))
    else:
        # Winnowing: choose minima per window, rightmost in ties
        for i in range(0, len(hashes) - w + 1):
            window_slice = hashes[i : i + w]
            min_val = min(window_slice)
            # choose rightmost index with min_val within the window
            for j in range(w - 1, -1, -1):
                if window_slice[j] == min_val:
                    picked.add(window_slice[j])
                    break
    return {f"{h:016x}" for h in picked}
