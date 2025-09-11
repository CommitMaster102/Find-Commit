# Find commits

A small utility to find Git commits in a repository that contain the exact contents of a local file, with optional fuzzy matching and GitHub forks discovery.

## Usage

```bash
python find_commits.py <local_file> <repo_url> \
  [--repo-dir DIR] [--repo-file-path PATH] \
  [--out-env PATH] [--out-report PATH] \
  [--include-forks] [--github-token TOKEN] [--forks-limit N] [--forks-offset N] \
  [--similarity-mode {jaccard,minhash,simhash}] [--similarity-threshold FLOAT] \
  [--shingle-size INT] [--minhash-perm INT] \
  [--progress] [--timings]
```

Outputs a recommended commit and writes a report (find_commits.txt) and an env file (find_commits.env).

## Options

- local_file: Path to the local file to match, or '-' to read from stdin.
- repo_url: Git repository URL (e.g., https://github.com/org/repo.git).
- --repo-dir DIR: Directory for local clone/cache. Defaults to `.repo_<name>` in CWD.
- --repo-file-path PATH: Hint path inside the repo for fallback scan when no exact blob match is found.
- --out-env PATH: Path to write env variables file. Default: `find_commits.env`.
- --out-report PATH: Path to write text report. Default: `find_commits.txt`.
- --include-forks: If set, discover GitHub forks and fetch their refs before searching.
- --github-token TOKEN: GitHub token (or set `GITHUB_TOKEN`) to raise API rate limits.
- --forks-limit N: Max forks to fetch when `--include-forks` is set. Default: 20 (1-99).
- --forks-offset N: Offset into the deduplicated forks list before selecting. Default: 0.
- --similarity-mode {jaccard,minhash,simhash}: Fallback similarity algorithm. Default: `jaccard`.
- --similarity-threshold FLOAT: Threshold in [0,1] for selecting candidates in fallback mode. Default: 0.92.
- --shingle-size INT: Token shingle size k for jaccard/minhash. Default: 5.
- --minhash-perm INT: Number of permutations for MinHash. Default: 128.
- --progress: Show a simple spinner during long steps.
- --timings: Print per-step timings to the terminal (always written to report and env).

Notes:
- The tool first searches for exact blob matches. Only if none are found does it scan commits touching candidate paths and apply the chosen similarity mode.
- A fast exact check is used during fallback via blob-id resolution to avoid unnecessary content reads.

## Timings

- Per-step timings (milliseconds) are recorded and output to:
  - Terminal (when `--timings` is provided)
  - Report (`find_commits.txt`) as lines like `prepare_repo_ms=1234`
  - Env file (`find_commits.env`) as uppercase keys like `PREPARE_REPO_MS=1234`
- Recorded keys may include:
  - `prepare_repo_ms`, `fetch_forks_ms`, `compute_local_blobs_ms`, `search_exact_ms`,
    `collect_touches_ms`, `evaluate_candidates_ms`, `choose_preferred_ms`, `write_report_ms`,
    `write_env_ms`, `cleanup_ms`, `total_ms`

## Examples

Basic exact search:
```bash
python find_commits.py path/to/local/file.txt https://github.com/org/repo.git --timings
```

Read file content from stdin:
```bash
type path\to\local\file.txt | python find_commits.py - https://github.com/org/repo.git --timings
```

Provide an explicit repo path hint for fallback:
```bash
python find_commits.py file.txt https://github.com/org/repo.git --repo-file-path src/file.txt --timings
```

Include forks with token and selection window:
```bash
python find_commits.py file.txt https://github.com/org/repo.git --include-forks --github-token %GITHUB_TOKEN% --forks-limit 30 --forks-offset 10 --timings
```

Use MinHash for faster approximate matching:
```bash
python find_commits.py file.txt https://github.com/org/repo.git --similarity-mode minhash --similarity-threshold 0.9 --shingle-size 5 --minhash-perm 128 --timings --progress
```

Use SimHash for near-duplicate detection:
```bash
python find_commits.py file.txt https://github.com/org/repo.git --similarity-mode simhash --similarity-threshold 0.9 --timings --progress
```

Customize output paths and repo cache directory:
```bash
python find_commits.py file.txt https://github.com/org/repo.git --repo-dir .repo_tmp --out-report report.txt --out-env env.out --timings
```

