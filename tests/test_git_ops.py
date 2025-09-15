from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import find_commits_lib.git_ops as git_ops


def test_run_validates_git_and_errors():
    # Non-git command rejected
    with pytest.raises(ValueError):
        git_ops.run(["echo", "hi"])  # type: ignore[arg-type]

    # subprocess non-zero -> RuntimeError
    with patch("subprocess.run") as m:
        m.return_value = MagicMock(returncode=1, stderr=b"boom", stdout=b"")
        with pytest.raises(RuntimeError):
            git_ops.run(["git", "status"])  # allowed prefix


def test_run_progress_flags_for_clone_and_fetch():
    with patch("subprocess.run") as m:
        m.return_value = MagicMock(returncode=0, stdout=b"ok", stderr=b"")
        out = git_ops.run(["git", "clone", "url", "dir"], show_progress=True)
        assert out == "ok"
        args = m.call_args[0][0]
        # should include --progress after verb
        assert args[:3] == ["git", "clone", "--progress"]

    with patch("subprocess.run") as m:
        m.return_value = MagicMock(returncode=0, stdout=b"ok", stderr=b"")
        git_ops.run(["git", "fetch", "origin"], show_progress=True)
        args = m.call_args[0][0]
        assert args[:3] == ["git", "fetch", "--progress"]


def test_ensure_repo_clone_and_config_paths(tmp_path: Path):
    repo_dir = tmp_path / ".repo"
    # Simulate: repo doesn't exist -> run clone
    with patch("find_commits_lib.git_ops.run") as run:
        run.return_value = ""
        git_ops.ensure_repo(repo_dir, "https://example/repo.git", shallow=True, depth=3)
        assert run.call_args_list[0].args[0][:3] == ["git", "clone", "--depth"]
        # After clone, config calls should be made
        verbs = [c.args[0][1] for c in run.call_args_list if c.args[0][0] == "git"]
        assert "config" in verbs

    # Simulate: repo exists and shallow -> attempt unshallow (ignore failure)
    repo_dir.mkdir()
    with (
        patch("find_commits_lib.git_ops._is_shallow_repo", return_value=True),
        patch("find_commits_lib.git_ops._is_repo_fresh", return_value=False),
        patch(
            "find_commits_lib.git_ops.run",
            side_effect=[RuntimeError("fail"), "", "", "", "", "", "", "", ""],
        ),
    ):
        git_ops.ensure_repo(repo_dir, "url", shallow=True)


def test_compute_blob_hash_bytes_removes_temp():
    with (
        patch("find_commits_lib.git_ops.run", return_value="abcd"),
        patch("os.remove") as rm,
    ):
        out = git_ops.compute_blob_hash_bytes(b"hi")
        assert out == "abcd"
        assert rm.called


def test_discover_and_content_and_ids():
    repo_dir = Path(".")
    # discover_paths_by_filename parses object list
    out = """
deadbeef path/one.txt
feedbeef file.txt
badline
beadfeed other/file.txt
"""
    with patch("find_commits_lib.git_ops.run", return_value=out):
        paths = git_ops.discover_paths_by_filename(repo_dir, "file.txt")
        assert paths == ["file.txt", "other/file.txt"]
    with patch("find_commits_lib.git_ops.run", side_effect=RuntimeError("x")):
        assert git_ops.discover_paths_by_filename(repo_dir, "x") == []

    # file_content_at returns bytes; RuntimeError -> None
    with patch("find_commits_lib.git_ops.run", return_value="hello"):
        assert git_ops.file_content_at(repo_dir, "c", "p") == b"hello"
    with patch("find_commits_lib.git_ops.run", side_effect=RuntimeError("x")):
        assert git_ops.file_content_at(repo_dir, "c", "p") is None

    # blob_id_at requires 40-hex-like length
    with patch("find_commits_lib.git_ops.run", return_value="a" * 40):
        assert git_ops.blob_id_at(repo_dir, "c", "p") == "a" * 40
    with patch("find_commits_lib.git_ops.run", return_value="short"):
        assert git_ops.blob_id_at(repo_dir, "c", "p") is None
    with patch("find_commits_lib.git_ops.run", side_effect=RuntimeError("x")):
        assert git_ops.blob_id_at(repo_dir, "c", "p") is None


def test_branches_and_timestamp_and_existing_remote_names():
    repo_dir = Path(".")
    with patch("find_commits_lib.git_ops.run", return_value="origin/a\norigin/b\n"):
        assert git_ops.branches_containing(repo_dir, "c") == ["origin/a", "origin/b"]
    with patch("find_commits_lib.git_ops.run", side_effect=RuntimeError("x")):
        assert git_ops.branches_containing(repo_dir, "c") == []

    with patch("find_commits_lib.git_ops.run", return_value="1700000000"):
        assert git_ops.commit_timestamp(repo_dir, "c") == 1700000000
    with patch("find_commits_lib.git_ops.run", return_value="notint"):
        assert git_ops.commit_timestamp(repo_dir, "c") == 0

    with patch("find_commits_lib.git_ops.run", return_value="origin\nupstream\n"):
        assert git_ops.existing_remote_names(repo_dir) == ["origin", "upstream"]
    with patch("find_commits_lib.git_ops.run", side_effect=RuntimeError("x")):
        assert git_ops.existing_remote_names(repo_dir) == []


def test_sanitize_remote_name_rules():
    assert git_ops.sanitize_remote_name("a b/c") == "a_b_c"
    assert git_ops.sanitize_remote_name(".hidden") == "_hidden"
    long = "x" * 300
    assert len(git_ops.sanitize_remote_name(long)) == 200


def test_ensure_remote_with_refspec_add_and_update(tmp_path: Path):
    repo_dir = tmp_path
    # Remote exists: update URL + reset fetch + add refspecs
    with (
        patch(
            "find_commits_lib.git_ops.existing_remote_names", return_value=["origin"]
        ),
        patch("find_commits_lib.git_ops.run") as run,
    ):
        git_ops.ensure_remote_with_refspec(repo_dir, "origin", "url")
        verbs = [c.args[0][1] for c in run.call_args_list]
        assert "remote" in verbs and "config" in verbs

    # Remote missing: add then config
    with (
        patch("find_commits_lib.git_ops.existing_remote_names", return_value=[]),
        patch("find_commits_lib.git_ops.run") as run,
    ):
        git_ops.ensure_remote_with_refspec(repo_dir, "new", "url")
        cmds = [c.args[0] for c in run.call_args_list]
        assert ["git", "remote", "add", "new", "url"] in cmds


def test_is_repo_fresh_true_false(tmp_path: Path):
    repo_dir = tmp_path
    with patch("find_commits_lib.git_ops.run", return_value=str(10_000_000_000)):
        assert git_ops._is_repo_fresh(repo_dir, max_age_hours=24) is True
    with patch("find_commits_lib.git_ops.run", return_value=str(0)):
        assert git_ops._is_repo_fresh(repo_dir, max_age_hours=24) is False
    with patch("find_commits_lib.git_ops.run", side_effect=RuntimeError("x")):
        assert git_ops._is_repo_fresh(repo_dir) is False
