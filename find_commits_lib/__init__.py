# Main package exports
from .fuzzy import (
    fingerprint_text_for_fuzzy,
    jaccard_similarity,
    minhash_signature,
    minhash_similarity,
    simhash64,
    simhash_similarity,
)
from .git_ops import (
    blob_id_at,
    branches_containing,
    commit_timestamp,
    commits_touching_path,
    compute_blob_hash_bytes,
    discover_paths_by_filename,
    ensure_repo,
    file_content_at,
    find_exact_blob_commits,
)
from .github_api import fetch_forks_into_repo
from .selection import choose_branch_for_commit, choose_preferred
from .utils import (
    cleanup_repo_cache,
    default_repo_dir_for,
    format_duration_human,
    format_timestamp_ms,
    normalize_lf,
)

__all__ = [
    # Fuzzy matching
    "fingerprint_text_for_fuzzy",
    "jaccard_similarity",
    "minhash_signature",
    "minhash_similarity",
    "simhash64",
    "simhash_similarity",
    # Git operations
    "blob_id_at",
    "branches_containing",
    "commit_timestamp",
    "commits_touching_path",
    "compute_blob_hash_bytes",
    "discover_paths_by_filename",
    "ensure_repo",
    "file_content_at",
    "find_exact_blob_commits",
    # GitHub API
    "fetch_forks_into_repo",
    # Selection
    "choose_branch_for_commit",
    "choose_preferred",
    # Utils
    "cleanup_repo_cache",
    "default_repo_dir_for",
    "format_duration_human",
    "format_timestamp_ms",
    "normalize_lf",
]
