from pathlib import Path
from unittest.mock import MagicMock, patch

import find_commits_lib.utils as U


def test_normalize_and_basename_and_default_dir(tmp_path: Path):
    assert U.normalize_lf(b"a\r\nb\rc") == b"a\nb\nc"
    assert U.repo_basename_from_url("https://x/y/z.git") == "z"
    assert U.repo_basename_from_url("git@h:x/y/z") == "z"
    assert U.repo_basename_from_url("/") == "repo"
    d = U.default_repo_dir_for("https://x/y/z")
    assert d.name.startswith(".repo_") and "z" in d.name


def test_force_remove_dir_paths(tmp_path: Path):
    # path not exists -> no error
    U.force_remove_dir(tmp_path / "missing")

    # Exists; first two attempts raise, third succeeds; final ignored
    target = tmp_path / "dir"
    target.mkdir()
    calls = {"n": 0}

    def fake_rmtree(p, onexc=None, ignore_errors=False):
        calls["n"] += 1
        if calls["n"] < 3:
            raise OSError("fail")
        return None

    with patch("shutil.rmtree", side_effect=fake_rmtree), patch("time.sleep") as slp:
        U.force_remove_dir(target)
        assert calls["n"] >= 3
        assert slp.called


def test_cleanup_repo_cache_branches(tmp_path: Path):
    def_repo = tmp_path / ".repo_name"
    other_repo = tmp_path / "custom"
    with (
        patch("find_commits_lib.utils.default_repo_dir_for", return_value=def_repo),
        patch("find_commits_lib.utils.force_remove_dir") as rm,
    ):
        U.cleanup_repo_cache(def_repo, "https://x/y/name")
        assert rm.call_args[0][0] == def_repo
        U.cleanup_repo_cache(other_repo, "https://x/y/name")
        # second call removes default dir
        assert rm.call_args[0][0] == def_repo
    # Exceptions swallowed
    with patch(
        "find_commits_lib.utils.default_repo_dir_for", side_effect=PermissionError()
    ):
        U.cleanup_repo_cache(other_repo, "https://x/y/name")


def test_spinner_writes_and_ignores_errors():
    s = U.Spinner(True)
    with patch("os.write") as w:
        s.tick("Doing")
        s.clear()
        assert w.called
    # disabled does nothing
    s2 = U.Spinner(False)
    with patch("os.write") as w2:
        s2.tick("Doing")
        s2.clear()
        assert not w2.called
    # broken pipe tolerated
    with patch("os.write", side_effect=BrokenPipeError()):
        s.tick("Doing")
        s.clear()


def test_format_helpers():
    assert U.format_ms(1.234) == "1234 ms"
    assert isinstance(U.format_timestamp_ms(0.0), str)
    # duration variants
    assert "Took 999 milliseconds" in U.format_duration_human(999)
    assert "Took 1 seconds" in U.format_duration_human(1000)
    assert "Took 1 minute" in U.format_duration_human(60_000)
    assert "Took 1 hour" in U.format_duration_human(3_600_000)


def test_autoprogressbar_draw_and_helpers():
    ap = U.AutoProgressBar(True)
    # set lock to dummy context manager
    ap._lock = MagicMock()
    ap._lock.__enter__.return_value = ap._lock
    ap._label = "processing long filename.txt"
    ap._current = 0
    ap._total = 0
    ap._pulse = 0
    with patch("os.write") as w:
        ap._draw_line()  # unknown total branch
        assert w.called
    ap._total = 10
    ap._current = 5
    with patch("os.write") as w2:
        ap._draw_line()  # known total branch
        assert w2.called
    # helpers
    assert ap._ellipsize_middle("abcdef", 4) == "...f"
    assert ap._ellipsize_middle("abc", 10) == "abc"
    assert ap._action_from_label("download file") == "Download"
    assert ap._action_from_label("") == "Working"


def test_stepdisplay_records_timings_and_prints():
    timings = {}
    ap = U.AutoProgressBar(False)
    with (
        patch("time.perf_counter", side_effect=[0.0, 0.5]),
        patch("time.time", side_effect=[1000.0, 1000.5]),
        patch("os.write") as w,
    ):
        with U.StepDisplay("step", "Label:", timings, ap, True) as disp:
            disp.update(1, 2, "lbl")
        # timings populated
        assert timings["step_ms"] == 500
        assert "step_start" in timings and "step_end" in timings
        assert w.called


def test_steptimer_calls_callback_and_clears_spinner():
    out = {}

    def cb(name, dt):
        out["name"] = name
        out["dt"] = dt

    sp = U.Spinner(True)
    with patch("os.write"):  # clear writes
        with patch("time.perf_counter", side_effect=[0.0, 0.1]):
            with U.StepTimer("n", cb, sp):
                pass
    assert out["name"] == "n" and out["dt"] > 0

    # callback error swallowed
    def boom(name, dt):
        raise RuntimeError("x")

    with patch("time.perf_counter", side_effect=[0.0, 0.1]):
        with U.StepTimer("n", boom, sp):
            pass
