#!/usr/bin/env python3
import argparse
import os
import sys
from pathlib import Path

from find_commits_lib import cleanup_repo_cache, default_repo_dir_for


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Find Git commits in a repository that contain the exact contents of a "
            "local file. Provide the file path (or '-' to read from stdin) and the "
            "repository URL. Optionally provide a path inside the repo to scan when "
            "no exact blob match is found."
        )
    )
    parser.add_argument(
        "local_file",
        help="Local file path to match, or '-' to read content from stdin",
    )
    parser.add_argument(
        "repo_url",
        help="Git repository URL to search (e.g. https://github.com/org/repo.git)",
    )

    # Optional arguments
    parser.add_argument(
        "--repo-dir",
        help=(
            "Local directory for the repository clone/cache. "
            "Defaults to .repo_<name> in the current directory."
        ),
    )
    parser.add_argument(
        "--repo-file-path",
        help=(
            "Path of the file inside the repository. Only needed for the fallback "
            "scan when no exact blob match is found."
        ),
    )
    parser.add_argument(
        "--out-env",
        default="find_commits.env",
        help="Path to write environment variables file (default: find_commits.env)",
    )
    parser.add_argument(
        "--out-report",
        default="find_commits.txt",
        help="Path to write a text report (default: find_commits.txt)",
    )
    parser.add_argument(
        "--include-forks",
        action="store_true",
        help=(
            "If set, discover GitHub forks of the repository and fetch their heads "
            "as additional remotes before searching."
        ),
    )
    parser.add_argument(
        "--github-token",
        default=os.environ.get("GITHUB_TOKEN", ""),
        help=(
            "GitHub token to increase API rate limit when using --include-forks. "
            "Defaults to $GITHUB_TOKEN if present."
        ),
    )
    parser.add_argument(
        "--similarity-mode",
        choices=["jaccard", "minhash", "simhash", "charjaccard", "winnow"],
        default="jaccard",
        help=(
            "Similarity algorithm for fallback scan: jaccard (default), minhash, simhash, "
            "charjaccard (char n-gram Jaccard), or winnow (winnowing over token shingles)."
        ),
    )
    parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=0.92,
        help="Similarity threshold in [0,1] for selecting candidates in fallback mode.",
    )
    parser.add_argument(
        "--shingle-size",
        type=int,
        default=5,
        help="Token shingle size (k) for jaccard/minhash (default: 5).",
    )
    parser.add_argument(
        "--char-ngram-size",
        type=int,
        default=5,
        help="Character n-gram size for charjaccard mode (default: 5).",
    )
    parser.add_argument(
        "--winnow-window",
        type=int,
        default=4,
        help="Window size for winnow mode over token shingles (default: 4).",
    )
    parser.add_argument(
        "--minhash-perm",
        type=int,
        default=128,
        help="Number of permutations for MinHash (default: 128).",
    )
    parser.add_argument(
        "--progress",
        action="store_true",
        help="Show spinner progress animation during long steps.",
    )
    parser.add_argument(
        "--timings",
        action="store_true",
        help="Print per-step timings to terminal (always included in report/env).",
    )
    parser.add_argument(
        "--forks-limit",
        type=int,
        default=20,
        help="Maximum number of forks to fetch when --include-forks is set (1-99, default: 20)",
    )
    parser.add_argument(
        "--forks-offset",
        type=int,
        default=0,
        help="Offset into the forks list before selecting (applied after deduplication)",
    )
    parser.add_argument(
        "--shallow",
        action="store_true",
        help="Use shallow clone for faster initial repository download (may miss some commits)",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=1,
        help="Depth for shallow clone (default: 1, only latest commit per branch)",
    )
    parser.add_argument(
        "--selective",
        action="store_true",
        help="Use selective fetching (only main branch and tags) for faster preparation",
    )
    parser.add_argument(
        "--parallel-fetch",
        action="store_true",
        help="Use parallel fetching for better performance (experimental)",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Fast mode: skip expensive operations for quicker execution (shallow clone, minimal fetching, no progress bars)",
    )
    args = parser.parse_args()

    # Guard for unexpected exceptions: cleanup repo cache before exiting
    try:
        inner(args)
    except SystemExit:
        # Already handled cleanup at exit points
        raise
    except Exception as e:
        try:
            print(f"Unexpected error: {e}", file=sys.stderr)
        except Exception:
            # Ignore errors when printing error message to stderr
            pass
        try:
            repo_dir = (
                Path(args.repo_dir)
                if args.repo_dir
                else default_repo_dir_for(args.repo_url)
            )
            cleanup_repo_cache(repo_dir, args.repo_url)
        except Exception:
            # Ignore errors during cleanup - best effort only
            pass
        sys.exit(1)


def inner(args: argparse.Namespace) -> None:
    # Import the callable directly from the submodule to avoid importing
    # the module object itself (which would be non-callable).
    from find_commits_lib.core.orchestrate import orchestrate as _inner

    _inner(args)


if __name__ == "__main__":
    main()
