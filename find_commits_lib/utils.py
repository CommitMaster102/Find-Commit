import os
import re
import shutil
import stat
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional


def normalize_lf(content: bytes) -> bytes:
    return content.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def repo_basename_from_url(repo_url: str) -> str:
    """Return repository basename from a URL or SCP-like syntax.

    Examples:
      - https://github.com/org/repo.git -> repo
      - git@github.com:org/repo.git -> repo
      - /path/to/repo -> repo
    """
    cleaned = repo_url.rstrip("/")
    # Split on both '/' and ':' to handle scp-like URLs
    parts = re.split(r"[/:]", cleaned)
    name = parts[-1] if parts else "repo"
    if name.endswith(".git"):
        name = name[:-4]
    return name or "repo"


def default_repo_dir_for(repo_url: str) -> Path:
    """Choose a sensible local clone/cache directory for the given repo URL."""
    name = repo_basename_from_url(repo_url)
    return Path.cwd() / f".repo_{name}"


def force_remove_dir(path: Path) -> None:
    """Best-effort removal of a directory, handling Windows read-only files.

    Tries a few times; on error, flips the read-only bit and retries.
    """
    if not path.exists():
        return

    def on_rm_error(func, p, exc_info):
        try:
            os.chmod(p, stat.S_IWRITE)
            func(p)
        except (OSError, PermissionError):
            # Ignore errors when trying to change file permissions
            # This is expected on some systems or when files are in use
            pass

    for _ in range(3):
        try:
            shutil.rmtree(path, onexc=on_rm_error)
            return
        except Exception:
            # Wait before retrying directory removal
            time.sleep(0.2)
    # Final attempt ignoring errors
    shutil.rmtree(path, ignore_errors=True)


def cleanup_repo_cache(repo_dir: Path, repo_url: str) -> None:
    """Remove the default cache directory created for this repo.

    If the active repo_dir equals the default cache, remove it. Otherwise,
    remove the default cache directory if present (non-destructive for custom paths).
    """
    try:
        default_dir = default_repo_dir_for(repo_url)
        if repo_dir == default_dir:
            force_remove_dir(repo_dir)
        else:
            force_remove_dir(default_dir)
    except (OSError, PermissionError):
        # Ignore errors during cache cleanup - best effort only
        # This is expected when cache directories are in use or inaccessible
        pass


class Spinner:
    """Simple stderr spinner for long-running steps."""

    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled
        self._frames = ["-", "\\", "|", "/"]
        self._idx = 0

    def tick(self, label: str) -> None:
        if not self.enabled:
            return
        try:
            frame = self._frames[self._idx % len(self._frames)]
            self._idx += 1
            msg = f"\r[{frame}] {label}"
            os.write(2, msg.encode("utf-8", errors="ignore"))
        except (OSError, BrokenPipeError):
            # Ignore errors when writing to stderr (if stderr is closed)
            # This is expected when stderr is redirected or closed
            pass

    def clear(self) -> None:
        if not self.enabled:
            return
        try:
            os.write(2, b"\r\x1b[K")
        except (OSError, BrokenPipeError):
            # Ignore errors when clearing stderr (if stderr is closed)
            # This is expected when stderr is redirected or closed
            pass


def format_ms(dt_seconds: float) -> str:
    ms = int(round(dt_seconds * 1000.0))
    return f"{ms} ms"


def format_timestamp_ms(ts: Optional[float] = None) -> str:
    """Return local time formatted as yyyy-MM-dd HH:mm:ss.SSS"""
    if ts is None:
        dt = datetime.now()
    else:
        dt = datetime.fromtimestamp(ts)
    s = dt.strftime("%Y-%m-%d %H:%M:%S.%f")
    return s[:-3]


def format_duration_human(ms: int) -> str:
    """Format milliseconds as human-readable duration.

    For zero duration, return a semantic message indicating that the step wasn't applied or run.
    """
    if ms <= 0:
        return "wasn't applied or run"
    if ms < 1000:
        return f"Took {ms} milliseconds"

    seconds = ms // 1000
    remaining_ms = ms % 1000

    if seconds < 60:
        if remaining_ms == 0:
            return f"Took {seconds} seconds"
        else:
            return f"Took {seconds} seconds and {remaining_ms} milliseconds"

    minutes = seconds // 60
    remaining_seconds = seconds % 60

    if minutes < 60:
        parts = [f"Took {minutes} minute{'s' if minutes != 1 else ''}"]
        if remaining_seconds > 0:
            parts.append(
                f"{remaining_seconds} second{'s' if remaining_seconds != 1 else ''}"
            )
        if remaining_ms > 0:
            parts.append(
                f"{remaining_ms} millisecond{'s' if remaining_ms != 1 else ''}"
            )
        if len(parts) == 2:
            return " and ".join(parts)
        else:
            return ", ".join(parts[:-1]) + f", and {parts[-1]}"

    hours = minutes // 60
    remaining_minutes = minutes % 60

    parts = [f"Took {hours} hour{'s' if hours != 1 else ''}"]
    if remaining_minutes > 0:
        parts.append(
            f"{remaining_minutes} minute{'s' if remaining_minutes != 1 else ''}"
        )
    if remaining_seconds > 0:
        parts.append(
            f"{remaining_seconds} second{'s' if remaining_seconds != 1 else ''}"
        )
    if remaining_ms > 0:
        parts.append(f"{remaining_ms} millisecond{'s' if remaining_ms != 1 else ''}")
    if len(parts) == 2:
        return " and ".join(parts)
    else:
        return ", ".join(parts[:-1]) + f", and {parts[-1]}"


class AutoProgressBar:
    """Static-position ASCII progress bar with tight label brackets.

    - Draws to stderr to avoid interfering with normal stdout output.
    - If total<=0, shows an auto-pulsing bar.
    - Thread-based updater so it animates during blocking work.
    """

    BAR_CHAR = "="
    EMPTY_CHAR = "-"

    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled
        self._stop = False
        self._thread = None
        self._lock = None
        self._label = ""
        self._current = 0
        self._total = 0
        self._pulse = 0
        self._started = False
        self._last_len = 0
        self._label_w = int(os.environ.get("PROGRESS_LABEL_SLOT", "28") or 28)
        self._bar_w = int(os.environ.get("PROGRESS_BAR_WIDTH", "60") or 60)
        try:
            import threading

            self._threading = threading
            self._lock = threading.Lock()
        except (ImportError, OSError):
            # Disable progress bar if threading is not available
            # This can happen in some restricted environments
            self.enabled = False

    def _ellipsize_middle(self, text: str, max_len: int) -> str:
        if max_len <= 0:
            return ""
        if len(text) <= max_len:
            return text
        if max_len <= 3:
            return text[:max_len]
        keep = max_len - 3
        head = keep // 2
        tail = keep - head
        return text[:head] + "..." + text[-tail:]

    def _action_from_label(self, label: str) -> str:
        # Use the first word as the action if it looks like a verb; fallback to "Working"
        word = (label.strip().split(" ") or [""])[0]
        if not word:
            return "Working"
        # Normalize capitalization: keep as given if starts uppercase, else title-case
        if not word[0].isupper():
            word = word.title()
        return word

    def _draw_line(self) -> None:
        if not self.enabled:
            return
        try:
            with self._lock:  # type: ignore[attr-defined]
                label = self._label
                current = self._current
                total = self._total
                pulse = self._pulse
            if total <= 0:
                # Unknown total: static label on the left, animated status text inside bar
                label_text = self._ellipsize_middle(label, self._label_w)
                label_pad = max(0, self._label_w - len(label_text))
                action = self._action_from_label(label)
                dot_count = pulse % 4  # 0..3 dots
                # Use fixed width for status to prevent shifting
                max_dots = 3
                base_text = action + "." * max_dots  # Reserve space for max dots
                # Always pad status to the same width as base_text to prevent shifting
                status = action + "." * dot_count
                if len(status) < len(base_text):
                    status = status + " " * (len(base_text) - len(status))
                # Use a smaller, more compact bar for text-only display
                compact_w = min(self._bar_w, max(20, len(base_text) + 4))
                if len(base_text) > compact_w:
                    base_text = base_text[: compact_w - 3] + "..."
                    status = status[: compact_w - 3] + "..."
                # Center the status string within the compact bar (using base_text width for centering)
                left_pad = max(0, (compact_w - 2 - len(base_text)) // 2)
                right_pad = max(0, compact_w - 2 - len(base_text) - left_pad)
                filled = None  # not used in unknown total
            else:
                # Known total: show real percentage and keep static label
                label_text = self._ellipsize_middle(label, self._label_w)
                label_pad = max(0, self._label_w - len(label_text))
                frac = current / float(total)
                filled = int(self._bar_w * frac)
                filled = max(0, min(self._bar_w, filled))
            label_visual = f"[{label_text}]"
            if total <= 0:
                bar_visual = "[" + (" " * left_pad) + status + (" " * right_pad) + "]"
            else:
                bar_visual = (
                    "["
                    + (self.BAR_CHAR * filled)
                    + (self.EMPTY_CHAR * (self._bar_w - filled))
                    + "]"
                )
            percent = int(
                round(
                    100
                    * (0 if total <= 0 else min(1.0, max(0.0, current / float(total))))
                )
            )
            pct_field = f" {percent:3d}%" if total > 0 else ""
            line = f"{label_visual}{' ' * label_pad}  {bar_visual}{pct_field}"
            # Erase and draw on stderr
            out = "\r" + line
            os.write(2, out.encode("utf-8", errors="ignore"))
            # Track last len to clear if needed when stopping
            self._last_len = len(line)
        except (OSError, BrokenPipeError):
            # Ignore errors when drawing progress bar (if stderr is closed)
            # This is expected when stderr is redirected or closed
            pass

    def _run(self) -> None:
        try:
            while not self._stop:
                self._draw_line()
                with self._lock:  # type: ignore[attr-defined]
                    if self._total <= 0:
                        self._pulse = (self._pulse + 1) % (self._bar_w + 1)
                time.sleep(0.3)  # Slower animation
        except (OSError, BrokenPipeError):
            # Ignore errors in progress bar animation thread
            # This is expected when stderr is redirected or closed
            pass

    def start(self, label: str) -> None:
        if not self.enabled:
            return
        try:
            with self._lock:  # type: ignore[attr-defined]
                self._label = label
                self._current = 0
                self._total = 0
                self._pulse = 0
            if not self._thread:
                self._stop = False
                self._thread = self._threading.Thread(target=self._run, daemon=True)  # type: ignore[attr-defined]
                self._thread.start()
        except (OSError, RuntimeError):
            # Ignore errors when starting progress bar thread
            # This can happen if threading is not available or thread creation fails
            pass

    def update(self, current: int, total: int, label: Optional[str] = None) -> None:
        if not self.enabled:
            return
        try:
            with self._lock:  # type: ignore[attr-defined]
                if label is not None:
                    self._label = label
                self._current = current
                self._total = total
        except (OSError, RuntimeError):
            # Ignore errors when updating progress bar
            # This can happen if threading is not available or thread operations fail
            pass

    def stop(self) -> None:
        if not self.enabled:
            return
        try:
            self._stop = True
            if self._thread:
                self._thread.join(timeout=0.3)
        except (OSError, RuntimeError):
            # Ignore errors when stopping progress bar thread
            # This can happen if threading is not available or thread operations fail
            pass
        # Clear line to ensure next prints start cleanly
        try:
            os.write(2, b"\r\x1b[K")
        except (OSError, BrokenPipeError):
            # Ignore errors when clearing stderr after stopping progress bar
            # This is expected when stderr is redirected or closed
            pass
        self._thread = None


class StepDisplay:
    """Context manager: animate progress and record timings + wall timestamps."""

    def __init__(
        self,
        step_key: str,
        pretty_label: str,
        timings: dict,
        progress: AutoProgressBar,
        print_to_stderr: bool,
    ) -> None:
        self.step_key = step_key
        self.pretty_label = pretty_label
        self.timings = timings
        self.progress = progress
        self.print_to_stderr = print_to_stderr
        self._start_perf = 0.0
        self._start_wall = 0.0

    def __enter__(self):
        self._start_perf = time.perf_counter()
        self._start_wall = time.time()
        self.timings[f"{self.step_key}_start"] = format_timestamp_ms(self._start_wall)
        self.progress.start(self.pretty_label)
        return self

    def update(self, current: int, total: int, label: Optional[str] = None) -> None:
        self.progress.update(current, total, label)

    def __exit__(self, exc_type, exc, tb):
        end_perf = time.perf_counter()
        end_wall = time.time()
        self.progress.stop()
        dt = end_perf - self._start_perf
        ms = int(round(dt * 1000))
        self.timings[f"{self.step_key}_ms"] = ms
        self.timings[f"{self.step_key}_end"] = format_timestamp_ms(end_wall)
        if self.print_to_stderr:
            try:
                duration_human = format_duration_human(ms)
                # Ensure clean line before printing timing
                os.write(2, b"\r\x1b[K")
                os.write(
                    2,
                    f"{self.pretty_label} {duration_human}\n".encode(
                        "utf-8", errors="ignore"
                    ),
                )
            except (OSError, BrokenPipeError):
                # Ignore errors when writing timing info to stderr
                # This is expected when stderr is redirected or closed
                pass
        return False


class StepTimer:
    """Context manager to time steps with ms precision."""

    def __init__(
        self,
        name: str,
        on_done: Callable[[str, float], None],
        spinner: Spinner | None = None,
    ) -> None:
        self.name = name
        self.on_done = on_done
        self.spinner = spinner
        self._start = 0.0

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb):
        end = time.perf_counter()
        dt = end - self._start
        if self.spinner:
            self.spinner.clear()
        try:
            self.on_done(self.name, dt)
        except (OSError, RuntimeError):
            # Ignore errors in step timer callback
            # This can happen if threading is not available or callback fails
            pass
        return False
