<div align="center">

# 🔎 Find-Commit

*A small CLI to locate the Git commit(s) that contain the exact (or near-exact) contents of a local file and optionally across a repository’s forks.*

<!-- Badges -->
<a href="https://github.com/CommitMaster102/Find-Commit/blob/main/LICENSE">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-blue.svg">
</a>
<a href="https://www.python.org/">
  <img alt="Python" src="https://img.shields.io/badge/Python-%E2%89%A53.10-3776AB?logo=python&logoColor=white">
</a>
<img alt="OS" src="https://img.shields.io/badge/OS-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey">
<a href="https://github.com/CommitMaster102/Find-Commit/stargazers">
  <img alt="GitHub stars" src="https://img.shields.io/github/stars/CommitMaster102/Find-Commit?logo=github">
</a>
</div>

---

## ✨ Features

- **Exact blob match** search across the repo’s history.
- **Fallback approximate** matching (Jaccard, MinHash, SimHash) when no exact blob is found.
- **Fork discovery** (optional) to look across GitHub forks under rate limits.
- **Actionable report** + `.env` output with timing breakdowns.
- **Fast paths**: shallow/selective fetch and parallel operations for speed.

---

## 🚀 Quickstart

```bash
# Clone and run
git clone https://github.com/CommitMaster102/Find-Commit.git
cd Find-Commit
python find_commits.py <local_file> <repo_url> --timings
````

> **Requirements:** Python ≥ 3.10 and Git available on your PATH.
> **Tip:** For GitHub API calls (fork discovery), set `GITHUB_TOKEN` to raise rate limits.

---

## 🧭 Usage

```bash
python find_commits.py <local_file> <repo_url> \
  [--repo-dir DIR] [--repo-file-path PATH] \
  [--out-env PATH] [--out-report PATH] \
  [--include-forks] [--github-token TOKEN] [--forks-limit N] [--forks-offset N] \
  [--similarity-mode {jaccard,minhash,simhash,charjaccard,winnow}] [--similarity-threshold FLOAT] \
  [--shingle-size INT] [--char-ngram-size INT] [--winnow-window INT] [--minhash-perm INT] \
  [--progress] [--timings] \
  [--shallow] [--depth INT] [--selective] [--parallel-fetch] [--fast]
```

**Outputs:** a recommended commit in the terminal and two files:

* `find_commits.txt` — human-readable report
* `find_commits.env` — env-style key/values (timings, etc.)

---

## ⚙️ Options (at a glance)

| Option                   | Type / Values                       |            Default | Description                                                |
| ------------------------ | ----------------------------------- | -----------------: | ---------------------------------------------------------- |
| `local_file`             | path or `-`                         |                  — | File to match (use `-` to read from `stdin`).              |
| `repo_url`               | URL                                 |                  — | Target Git repo, e.g., `https://github.com/org/repo.git`.  |
| `--repo-dir`             | path                                |     `.repo_<name>` | Local clone/cache directory.                               |
| `--repo-file-path`       | path                                |                  — | Hint path inside repo for fallback scan.                   |
| `--out-env`              | path                                | `find_commits.env` | Where to write env output.                                 |
| `--out-report`           | path                                | `find_commits.txt` | Where to write the report.                                 |
| `--include-forks`        | flag                                |                off | Discover & fetch GitHub forks before searching.            |
| `--github-token`         | string                              |    `$GITHUB_TOKEN` | Token to raise API rate limits.                            |
| `--forks-limit`          | int \[1–99]                         |               `20` | Max forks to fetch when including forks.                   |
| `--forks-offset`         | int                                 |                `0` | Offset into de-duplicated fork list.                       |
| `--similarity-mode`      | `jaccard` \| `minhash` \| `simhash` \| `charjaccard` \| `winnow` |          `jaccard` | Fallback similarity algorithm.                             |
| `--similarity-threshold` | float \[0,1]                        |             `0.92` | Selection threshold in fallback mode.                      |
| `--shingle-size`         | int                                 |                `5` | Token shingle size for Jaccard/MinHash/Winnow.             |
| `--char-ngram-size`      | int                                 |                `5` | Character n-gram size for `charjaccard`.                   |
| `--winnow-window`        | int                                 |                `4` | Window size for `winnow` (winnowing over token shingles).  |
| `--minhash-perm`         | int                                 |              `128` | Number of permutations for MinHash.                        |
| `--progress`             | flag                                |                off | Simple spinner/progress indicators.                        |
| `--timings`              | flag                                |                off | Print per-step timings to terminal.                        |
| `--shallow`              | flag                                |                off | Shallow clone for faster download (may miss some commits). |
| `--depth`                | int                                 |                `1` | Depth for shallow clone.                                   |
| `--selective`            | flag                                |                off | Fetch main branch + tags only.                             |
| `--parallel-fetch`       | flag                                |                off | Parallel fetching (experimental).                          |
| `--fast`                 | flag                                |                off | Shortcut: shallow + minimal fetching + no progress bars.   |

> **Notes:** The tool first searches for exact blob matches. If none are found, it scans commits touching candidate paths and applies the chosen similarity mode. During fallback, a quick blob-id check avoids unnecessary content reads.

---

## ⏱ Timings

When `--timings` is used, per-step durations (milliseconds) are:

* Printed to the terminal,
* Written to `find_commits.txt` as `prepare_repo_xx=1234`,
* Written to `find_commits.env` as `PREPARE_REPO_XX=1234`.

- Recorded keys may include:
  - `read_local_file_ms`, `prepare_repo_ms`, `fetch_forks_ms`, `compute_local_blobs_ms`,
    `search_exact_ms`, `build_candidate_paths_ms`, `collect_touches_ms`, `prepare_fingerprints_ms`,
    `evaluate_candidates_ms`, `apply_fuzzy_threshold_ms`, `process_candidates_ms`,
    `choose_preferred_ms`, `write_report_ms`, `write_env_ms`, `cleanup_ms`, `total_ms`
  - Each timing key also has corresponding `_start` and `_end` timestamps

---

## 📦 Examples

**Basic exact search**

```bash
python find_commits.py path/to/local/file.txt https://github.com/org/repo.git --timings
```

**Read file from stdin**

```bash
# Windows (PowerShell)
type path\to\local\file.txt | python find_commits.py - https://github.com/org/repo.git --timings

# Unix
cat path/to/local/file.txt | python find_commits.py - https://github.com/org/repo.git --timings
```

**Provide an explicit repo path hint for fallback**

```bash
python find_commits.py file.txt https://github.com/org/repo.git --repo-file-path src/file.txt --timings
```

**Include forks with token and selection window**

```bash
python find_commits.py file.txt https://github.com/org/repo.git \
  --include-forks --github-token "$GITHUB_TOKEN" --forks-limit 30 --forks-offset 10 --timings
```

**Use MinHash for faster approximate matching**

```bash
python find_commits.py file.txt https://github.com/org/repo.git \
  --similarity-mode minhash --similarity-threshold 0.9 --shingle-size 5 --minhash-perm 128 --timings --progress
```

**Use SimHash for near-duplicate detection**

```bash
python find_commits.py file.txt https://github.com/org/repo.git \
  --similarity-mode simhash --similarity-threshold 0.9 --timings --progress
```

**Customize output paths & repo cache directory**

```bash
python find_commits.py file.txt https://github.com/org/repo.git \
  --repo-dir .repo_tmp --out-report report.txt --out-env env.out --timings
```

**Shallow clone for faster initial download**

```bash
python find_commits.py file.txt https://github.com/org/repo.git --shallow --depth 10 --timings
```

**Fast mode for quick execution**

```bash
python find_commits.py file.txt https://github.com/org/repo.git --fast --timings
```

**Selective fetching for better performance**

```bash
python find_commits.py file.txt https://github.com/org/repo.git --selective --parallel-fetch --timings
```

**Use char n-gram Jaccard (robust for small edits/spacing)**

```bash
python find_commits.py file.txt https://github.com/org/repo.git \
  --similarity-mode charjaccard --char-ngram-size 5 --similarity-threshold 0.9 --timings
```

**Use Winnowing over token shingles (compact fingerprinting)**

```bash
python find_commits.py file.txt https://github.com/org/repo.git \
  --similarity-mode winnow --shingle-size 5 --winnow-window 4 --similarity-threshold 0.9 --timings
```

---

## 🛠 How it works

1. **Prepare repo** — clone/update a cached working copy (optionally shallow/selective).
2. **Compute local blob(s)** — normalize line endings and compute blob IDs for the local file.
3. **Exact search** — try to resolve exact blob matches quickly across reachable refs.
4. **Fallback** — if no exact match: identify candidate paths, scan touching commits, and score with the selected similarity algorithm (Jaccard/MinHash/SimHash).
5. **Choose preferred** — pick the most likely commit, then write the report and env outputs.
