import argparse
import os
import sys
from pathlib import Path
from typing import List, Tuple, Optional

from find_commits_lib import (
    normalize_lf,
    ensure_repo,
    compute_blob_hash_bytes,
    find_exact_blob_commits,
    commits_touching_path,
    discover_paths_by_filename,
    file_content_at,
    blob_id_at,
    branches_containing,
    commit_timestamp,
    choose_preferred,
    choose_branch_for_commit,
    default_repo_dir_for,
    cleanup_repo_cache,
    fingerprint_text_for_fuzzy,
    jaccard_similarity,
    minhash_signature,
    minhash_similarity,
    simhash64,
    simhash_similarity,
    fetch_forks_into_repo,
)
from find_commits_lib.utils import (
    Spinner,
    AutoProgressBar,
    StepDisplay,
    format_timestamp_ms,
    format_duration_human,
)


def _parse_repo_dir(args: argparse.Namespace) -> Path:
    return Path(args.repo_dir) if args.repo_dir else default_repo_dir_for(args.repo_url)


def _parse_repo_file_path(args: argparse.Namespace) -> str:
    return args.repo_file_path if args.repo_file_path else ""


def _validate_forks_limit_or_exit(args: argparse.Namespace, repo_dir: Path) -> None:
    if not getattr(args, "include_forks", False):
        return
    try:
        fl = int(getattr(args, "forks_limit", 20) or 20)
    except Exception:
        fl = 20
    if fl > 99:
        print("--forks-limit cannot be greater than 99.", file=sys.stderr)
        cleanup_repo_cache(repo_dir, args.repo_url)
        sys.exit(2)


def _read_local_bytes_or_exit(args: argparse.Namespace) -> bytes:
    # Read local content from a file path or stdin
    if args.local_file == "-":
        return normalize_lf(sys.stdin.buffer.read())
    local_path = Path(args.local_file)
    if not local_path.exists():
        print(f"Local file not found: {local_path}", file=sys.stderr)
        sys.exit(2)

    f = None
    try:
        f = open(local_path, "rb")
        return normalize_lf(f.read())
    finally:
        if f is not None:
            f.close()


def _prepare_repository(
    repo_dir: Path,
    repo_url: str,
    shallow: bool = False,
    depth: int = 1,
    selective: bool = False,
    parallel: bool = False,
    show_progress: bool = False,
    fast_mode: bool = False,
) -> None:
    ensure_repo(
        repo_dir,
        repo_url,
        shallow=shallow,
        depth=depth,
        selective=selective,
        parallel=parallel,
        show_progress=show_progress,
        fast_mode=fast_mode,
    )


def _maybe_fetch_forks(
    args: argparse.Namespace, repo_dir: Path
) -> Tuple[int, int, int]:
    if not getattr(args, "include_forks", False):
        return (0, 0, 0)
    token = (
        getattr(args, "github_token", "") or os.environ.get("GITHUB_TOKEN", "")
    ).strip()
    limit = max(1, int(getattr(args, "forks_limit", 20) or 20))
    offset = int(getattr(args, "forks_offset", 0) or 0)
    return fetch_forks_into_repo(repo_dir, args.repo_url, token or None, limit, offset)


def _compute_blob_hashes_and_report(local_bytes: bytes) -> Tuple[str, str]:
    # Compute both normalized and a CRLF variant to account for line-ending differences
    blob_hash_norm = compute_blob_hash_bytes(local_bytes)
    blob_hash_raw = blob_hash_norm
    if os.name == "nt":
        try:
            crlf_bytes = local_bytes.replace(b"\n", b"\r\n")
            blob_hash_raw = compute_blob_hash_bytes(crlf_bytes)
        except Exception:
            blob_hash_raw = blob_hash_norm
    return blob_hash_norm, blob_hash_raw


def _build_candidate_paths(args: argparse.Namespace, repo_file_path: str) -> List[str]:
    candidate_paths: List[str] = []
    if repo_file_path:
        candidate_paths.append(repo_file_path)

    base_name = ""
    if args.local_file != "-":
        base_name = Path(args.local_file).name
    if not base_name and repo_file_path:
        base_name = Path(repo_file_path).name

    if base_name:
        discovered = discover_paths_by_filename(_parse_repo_dir(args), base_name)
        for p in discovered:
            if p not in candidate_paths:
                candidate_paths.append(p)

    return candidate_paths


def _search_exact_blob_matches(
    repo_dir: Path, blob_hash_norm: str, blob_hash_raw: str
) -> List[str]:
    exact_norm = find_exact_blob_commits(repo_dir, blob_hash_norm)
    exact_raw = (
        []
        if blob_hash_raw == blob_hash_norm
        else find_exact_blob_commits(repo_dir, blob_hash_raw)
    )
    exact = list(dict.fromkeys(exact_norm + exact_raw))
    return exact


def _scan_commits_for_candidates(
    repo_dir: Path,
    args: argparse.Namespace,
    local_bytes: bytes,
    blob_hash_norm: str,
    blob_hash_raw: str,
    repo_file_path: str,
    timings: dict,
    spinner: Spinner,
) -> Tuple[str, List[str]]:
    """
    Returns: (mode, candidates)
      mode ∈ {"exact_blob", "normalized_path"}
    """
    # 1) Try exact blob matches (timed)
    with StepDisplay(
        "search_exact",
        "Searching exact blob matches:",
        timings,
        AutoProgressBar(getattr(args, "progress", False)),
        getattr(args, "timings", False),
    ) as disp:
        exact = _search_exact_blob_matches(repo_dir, blob_hash_norm, blob_hash_raw)
    if exact:
        return "exact_blob", exact

    # 2) Fallback: scan by normalized path touches + fuzzy
    mode = "normalized_path"
    with StepDisplay(
        "build_candidate_paths",
        "Building candidate paths:",
        timings,
        AutoProgressBar(getattr(args, "progress", False)),
        getattr(args, "timings", False),
    ):
        candidate_paths = _build_candidate_paths(args, repo_file_path)

    if not candidate_paths:
        print(
            "No exact blob match found and no candidate paths discovered.",
            file=sys.stderr,
        )
        cleanup_repo_cache(repo_dir, args.repo_url)
        sys.exit(1)

    print(
        "No exact blob match found. \nScanning commits touching candidate paths...",
        file=sys.stderr,
    )

    # Collect all commits touching any candidate path (timed)
    touched_all: List[str] = []
    seen_paths = set()
    with StepDisplay(
        "collect_touches",
        "Collecting commits touching candidate paths:",
        timings,
        AutoProgressBar(getattr(args, "progress", False)),
        getattr(args, "timings", False),
    ) as disp:
        total = len(candidate_paths) if candidate_paths else 1
        for i, p in enumerate(candidate_paths, 1):
            disp.update(i, total, p)
            if p in seen_paths:
                continue
            seen_paths.add(p)
            touched_all.extend(commits_touching_path(repo_dir, p))
    touched = list(dict.fromkeys(touched_all))

    # Prepare local fingerprints for fuzzy fallback according to mode
    with StepDisplay(
        "prepare_fingerprints",
        "Preparing local fingerprints:",
        timings,
        AutoProgressBar(getattr(args, "progress", False)),
        getattr(args, "timings", False),
    ):
        mode_choice = getattr(args, "similarity_mode", "jaccard")
        shingle_k = max(1, int(getattr(args, "shingle_size", 5) or 5))
        local_text = local_bytes.decode(errors="ignore")
        local_fp = fingerprint_text_for_fuzzy(local_text, k=shingle_k)
        local_mh = (
            minhash_signature(
                local_fp,
                num_perm=max(1, int(getattr(args, "minhash_perm", 128) or 128)),
            )
            if mode_choice == "minhash"
            else None
        )
        local_sh = simhash64(local_text) if mode_choice == "simhash" else None

    candidates: List[str] = []
    best_fuzzy: List[Tuple[float, str]] = []  # (score, commit)
    seen_commits = set()

    with StepDisplay(
        "evaluate_candidates",
        "Evaluating candidates:",
        timings,
        AutoProgressBar(getattr(args, "progress", False)),
        getattr(args, "timings", False),
    ) as disp:
        total_c = len(touched) if touched else 1
        for idx, c in enumerate(touched, 1):
            disp.update(idx, total_c, c)
            if c in seen_commits:
                continue
            seen_commits.add(c)

            content: Optional[bytes] = None
            normalized: Optional[bytes] = None
            # Fast path: try to resolve blob id without reading content
            matched_by_blob = False
            for p in candidate_paths:
                oid = blob_id_at(repo_dir, c, p)
                if oid and oid in (blob_hash_norm, blob_hash_raw):
                    candidates.append(c)
                    matched_by_blob = True
                    break
            if matched_by_blob:
                continue

            # Fallback: read content once (first path that exists)
            for p in candidate_paths:
                content = file_content_at(repo_dir, c, p)
                if content is not None:
                    normalized = normalize_lf(content)
                    break
            if normalized is None:
                continue

            # Exact by content hash if needed
            if compute_blob_hash_bytes(normalized) in (blob_hash_norm, blob_hash_raw):
                candidates.append(c)
                continue

            # Fuzzy similarity (selected mode)
            repo_text = normalized.decode(errors="ignore")
            if mode_choice == "jaccard":
                repo_fp = fingerprint_text_for_fuzzy(repo_text, k=shingle_k)
                score = jaccard_similarity(local_fp, repo_fp)
            elif mode_choice == "minhash":
                repo_fp = fingerprint_text_for_fuzzy(repo_text, k=shingle_k)
                repo_mh = minhash_signature(
                    repo_fp,
                    num_perm=max(1, int(getattr(args, "minhash_perm", 128) or 128)),
                )
                score = minhash_similarity(local_mh or [], repo_mh)
            else:  # simhash
                repo_sh = simhash64(repo_text)
                score = simhash_similarity(local_sh or 0, repo_sh)
            best_fuzzy.append((score, c))

    # If no exact candidates, pick top fuzzy matches above a threshold
    if not candidates and best_fuzzy:
        with StepDisplay(
            "apply_fuzzy_threshold",
            "Applying fuzzy matching threshold:",
            timings,
            AutoProgressBar(getattr(args, "progress", False)),
            getattr(args, "timings", False),
        ):
            best_fuzzy.sort(key=lambda t: t[0], reverse=True)
            threshold = float(getattr(args, "similarity_threshold", 0.92) or 0.92)
            for score, c in best_fuzzy:
                if score < threshold:
                    break
                candidates.append(c)

    return mode, candidates


def _dedupe_preserve_order(items: List[str]) -> List[str]:
    deduped: List[str] = []
    seen = set()
    for x in items:
        if x not in seen:
            seen.add(x)
            deduped.append(x)
    return deduped


def _write_report(
    args: argparse.Namespace,
    mode: str,
    preferred: str,
    blob_hash_norm: str,
    blob_hash_raw: str,
    forks_fetched: int,
    forks_discovered: int,
    forks_selected: int,
    candidates: List[str],
    repo_dir: Path,
    timings: dict,
) -> None:
    fast_mode = getattr(args, "fast", False)
    report_lines: List[str] = []
    report_lines.append(f"mode={mode}")
    report_lines.append(f"preferred={preferred}")
    report_lines.append(f"local_blob_norm={blob_hash_norm}")
    if blob_hash_raw != blob_hash_norm:
        report_lines.append(f"local_blob_raw={blob_hash_raw}")
    try:
        report_lines.append(f"forks_fetched={forks_fetched}")
        report_lines.append(f"forks_discovered={forks_discovered}")
        report_lines.append(f"forks_selected={forks_selected}")
    except NameError:
        # Fork-related variables may not be defined if fork fetching was skipped
        pass
    report_lines.append(f"candidates_count={len(candidates)}")

    # Skip detailed timings in fast mode
    if not fast_mode:
        # timings: group by step and show start, end, duration
        step_keys = set()
        for k in timings.keys():
            if k.endswith("_start") or k.endswith("_end") or k.endswith("_ms"):
                step = k.rsplit("_", 1)[0]
                step_keys.add(step)

        for step in sorted(step_keys):
            start_key = f"{step}_start"
            end_key = f"{step}_end"
            ms_key = f"{step}_ms"

            if start_key in timings:
                report_lines.append(f"{start_key}={timings[start_key]}")
            if end_key in timings:
                report_lines.append(f"{end_key}={timings[end_key]}")
            if ms_key in timings:
                duration_human = format_duration_human(timings[ms_key])
                report_lines.append(f"{step}_difference_time={duration_human}")

    report_lines.append("candidates:")
    # In fast mode, skip expensive branch lookups for each candidate
    if fast_mode:
        for c in candidates:
            report_lines.append(f"  - commit={c}")
    else:
        for c in candidates:
            ts = commit_timestamp(repo_dir, c)
            br = branches_containing(repo_dir, c)
            branches = "\t\n".join(br)
            report_lines.append(f"  - commit={c} ts={ts} branches={branches}")

    Path(args.out_report).write_text("\n".join(report_lines), encoding="utf-8")


def _write_env_file(
    args: argparse.Namespace,
    mode: str,
    preferred: str,
    candidates: List[str],
    forks_fetched: int,
    forks_discovered: int,
    forks_selected: int,
    repo_dir: Path,
    timings: dict,
) -> None:
    fast_mode = getattr(args, "fast", False)
    candidates_str = "\t\n".join(candidates)
    env_lines = [
        f"PREFERRED_COMMIT={preferred}",
        f'CANDIDATE_COMMITS= -> \n"{candidates_str}"',
        f"MATCH_MODE={mode}",
    ]
    try:
        env_lines.append(f"FORKS_FETCHED={forks_fetched}")
        env_lines.append(f"FORKS_DISCOVERED={forks_discovered}")
        env_lines.append(f"FORKS_SELECTED={forks_selected}")
    except NameError:
        # Fork-related variables may not be defined if fork fetching was skipped
        pass
    # Skip expensive branch lookups in fast mode
    if not fast_mode:
        used_branch = choose_branch_for_commit(repo_dir, preferred)
        if used_branch:
            env_lines.append(f"PREFERRED_BRANCH={used_branch}")
            all_branches_for_preferred = branches_containing(repo_dir, preferred)
            branches_joined = "\t\n".join(all_branches_for_preferred)
            env_lines.append(f'PREFERRED_BRANCHES="{branches_joined}"')

    # Skip detailed timings in fast mode
    if not fast_mode:
        # timings into env: group by step and show start, end, duration
        step_keys = set()
        for k in timings.keys():
            if k.endswith("_start") or k.endswith("_end") or k.endswith("_ms"):
                step = k.rsplit("_", 1)[0]
                step_keys.add(step)

        for step in sorted(step_keys):
            start_key = f"{step}_start"
            end_key = f"{step}_end"
            ms_key = f"{step}_ms"

            if start_key in timings:
                env_lines.append(f"{start_key.upper()}={timings[start_key]}")
            if end_key in timings:
                env_lines.append(f"{end_key.upper()}={timings[end_key]}")
            if ms_key in timings:
                duration_human = format_duration_human(timings[ms_key])
                env_lines.append(f"{step.upper()}_DIFFERENCE_TIME={duration_human}")

    Path(args.out_env).write_text("\n".join(env_lines), encoding="utf-8")


def _write_final_timing_data(args: argparse.Namespace, timings: dict) -> None:
    """Write final timing data to both report files after all steps complete."""
    # Skip timing data in fast mode
    if getattr(args, "fast", False):
        return

    # Read existing report file and append timing data
    if Path(args.out_report).exists():
        existing_content = Path(args.out_report).read_text(encoding="utf-8")
        lines = existing_content.split("\n")

        # Find where to insert timing data (before candidates section)
        insert_idx = len(lines)
        for i, line in enumerate(lines):
            if line.startswith("candidates:"):
                insert_idx = i
                break

        # Add timing data
        timing_lines = []
        for key in sorted(timings.keys()):
            if key.endswith("_start") or key.endswith("_end"):
                timing_lines.append(f"{key}={timings[key]}")
            elif key.endswith("_ms"):
                step = key.rsplit("_", 1)[0]
                duration_human = format_duration_human(timings[key])
                timing_lines.append(f"{step}_difference_time={duration_human}")

        # Insert timing data
        new_lines = lines[:insert_idx] + timing_lines + lines[insert_idx:]
        Path(args.out_report).write_text("\n".join(new_lines), encoding="utf-8")

    # Read existing env file and append timing data
    if Path(args.out_env).exists():
        existing_content = Path(args.out_env).read_text(encoding="utf-8")
        lines = existing_content.split("\n")

        # Add timing data
        timing_lines = []
        for key in sorted(timings.keys()):
            if key.endswith("_start") or key.endswith("_end"):
                timing_lines.append(f"{key.upper()}={timings[key]}")
            elif key.endswith("_ms"):
                step = key.rsplit("_", 1)[0]
                duration_human = format_duration_human(timings[key])
                timing_lines.append(f"{step.upper()}_DIFFERENCE_TIME={duration_human}")

        # Append timing data
        new_lines = lines + timing_lines
        Path(args.out_env).write_text("\n".join(new_lines), encoding="utf-8")


def _print_summary(preferred: str, candidates: List[str]) -> None:
    print(f"Recommended commit: {preferred}")
    print("Candidates:")
    for c in candidates:
        print(f"  - {c}")


def orchestrate(args: argparse.Namespace) -> None:
    repo_dir = _parse_repo_dir(args)
    repo_file_path = _parse_repo_file_path(args)
    timings: dict = {}

    # Fast mode optimizations
    fast_mode = getattr(args, "fast", False)
    if fast_mode:
        # Disable progress bars and timings in fast mode
        args.progress = False
        args.timings = False
        # Enable shallow clone and selective fetch for speed
        args.shallow = True
        args.depth = 1
        args.selective = True
        # Disable fork fetching in fast mode
        args.include_forks = False

    spinner = Spinner(getattr(args, "progress", False))

    _validate_forks_limit_or_exit(args, repo_dir)

    total_start_wall = __import__("time").time()

    with StepDisplay(
        "read_local_file",
        "Reading local file:",
        timings,
        AutoProgressBar(getattr(args, "progress", False)),
        getattr(args, "timings", False),
    ):
        local_bytes = _read_local_bytes_or_exit(args)
    with StepDisplay(
        "prepare_repo",
        "Preparing repository:",
        timings,
        AutoProgressBar(getattr(args, "progress", False)),
        getattr(args, "timings", False),
    ):
        shallow = getattr(args, "shallow", False)
        depth = getattr(args, "depth", 1)
        selective = getattr(args, "selective", False)
        parallel = getattr(args, "parallel_fetch", False)
        show_progress = getattr(args, "progress", False)
        _prepare_repository(
            repo_dir,
            args.repo_url,
            shallow=shallow,
            depth=depth,
            selective=selective,
            parallel=parallel,
            show_progress=show_progress,
            fast_mode=fast_mode,
        )

    if getattr(args, "include_forks", False):
        with StepDisplay(
            "fetch_forks",
            "Fetching forks:",
            timings,
            AutoProgressBar(getattr(args, "progress", False)),
            getattr(args, "timings", False),
        ):
            forks_fetched, forks_discovered, forks_selected = _maybe_fetch_forks(
                args, repo_dir
            )
    else:
        forks_fetched, forks_discovered, forks_selected = (0, 0, 0)

    with StepDisplay(
        "compute_local_blobs",
        "Computing local blob ids:",
        timings,
        AutoProgressBar(getattr(args, "progress", False)),
        getattr(args, "timings", False),
    ):
        blob_hash_norm, blob_hash_raw = _compute_blob_hashes_and_report(local_bytes)

    # Restore single call: delegate timed scanning to helper
    mode, candidates = _scan_commits_for_candidates(
        repo_dir=repo_dir,
        args=args,
        local_bytes=local_bytes,
        blob_hash_norm=blob_hash_norm,
        blob_hash_raw=blob_hash_raw,
        repo_file_path=repo_file_path,
        timings=timings,
        spinner=spinner,
    )

    with StepDisplay(
        "process_candidates",
        "Processing candidates:",
        timings,
        AutoProgressBar(getattr(args, "progress", False)),
        getattr(args, "timings", False),
    ):
        candidates = _dedupe_preserve_order(candidates)

    if not candidates:
        print("No commit found containing the requested content.", file=sys.stderr)
        cleanup_repo_cache(repo_dir, args.repo_url)
        sys.exit(1)

    with StepDisplay(
        "choose_preferred",
        "Choosing preferred:",
        timings,
        AutoProgressBar(getattr(args, "progress", False)),
        getattr(args, "timings", False),
    ):
        preferred = choose_preferred(repo_dir, candidates)

    with StepDisplay(
        "write_report",
        "Writing report:",
        timings,
        AutoProgressBar(getattr(args, "progress", False)),
        getattr(args, "timings", False),
    ):
        _write_report(
            args=args,
            mode=mode,
            preferred=preferred,
            blob_hash_norm=blob_hash_norm,
            blob_hash_raw=blob_hash_raw,
            forks_fetched=forks_fetched,
            forks_discovered=forks_discovered,
            forks_selected=forks_selected,
            candidates=candidates,
            repo_dir=repo_dir,
            timings=timings,
        )

    with StepDisplay(
        "write_env",
        "Writing env:",
        timings,
        AutoProgressBar(getattr(args, "progress", False)),
        getattr(args, "timings", False),
    ):
        _write_env_file(
            args=args,
            mode=mode,
            preferred=preferred,
            candidates=candidates,
            forks_fetched=forks_fetched,
            forks_discovered=forks_discovered,
            forks_selected=forks_selected,
            repo_dir=repo_dir,
            timings=timings,
        )

    # Print summary without progress/timing wrapper
    _print_summary(preferred, candidates)

    # Cleanup: always remove the default cache directory at the end of success path.
    with StepDisplay(
        "cleanup",
        "Cleanup cache:",
        timings,
        AutoProgressBar(getattr(args, "progress", False)),
        getattr(args, "timings", False),
    ):
        cleanup_repo_cache(repo_dir, args.repo_url)

    total_end_wall = __import__("time").time()

    # Calculate sum of individual step timings for verification
    individual_sum = sum(
        ms for key, ms in timings.items() if key.endswith("_ms") and key != "total_ms"
    )

    # Use the individual sum as the total to ensure consistency
    timings["total_ms"] = individual_sum

    # Add total timing to timings dict for reporting
    timings["total_start"] = format_timestamp_ms(total_start_wall)
    timings["total_end"] = format_timestamp_ms(total_end_wall)

    # Print total time if timings are enabled
    if getattr(args, "timings", False):
        total_duration = format_duration_human(individual_sum)
        print(f"Total execution time: {total_duration}", file=sys.stderr)

    # Write final timing data to both report files
    _write_final_timing_data(args, timings)
