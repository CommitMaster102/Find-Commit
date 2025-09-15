import io
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import find_commits_lib.github_api as gh


def test_parse_github_owner_repo_variants():
    assert gh.parse_github_owner_repo("https://github.com/a/b.git") == ("a", "b")
    assert gh.parse_github_owner_repo("git@github.com:a/b.git") == ("a", "b")
    assert gh.parse_github_owner_repo("ssh://git@github.com/a/b") == ("a", "b")
    assert gh.parse_github_owner_repo("https://example.com/x/y") is None


def test_github_api_get_validates_scheme_and_handles_errors():
    with pytest.raises(ValueError):
        gh.github_api_get("http://github.com/x", None)

    # Success path
    mock_resp = MagicMock()
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.status = 200
    mock_resp.read.return_value = b"{}"
    with patch("find_commits_lib.github_api.urlopen", return_value=mock_resp):
        status, data = gh.github_api_get("https://api.github.com/", None)
        assert status == 200 and data == b"{}"

    # HTTPError returns code and body
    from urllib.error import HTTPError

    err = HTTPError("https://x", 404, "not found", hdrs=None, fp=io.BytesIO(b"msg"))
    with patch("find_commits_lib.github_api.urlopen", side_effect=err):
        status, data = gh.github_api_get("https://api.github.com/x", None)
        assert status == 404 and data == b"msg"

    # URLError returns (0, b"")
    from urllib.error import URLError

    with patch("find_commits_lib.github_api.urlopen", side_effect=URLError("x")):
        status, data = gh.github_api_get("https://api.github.com/x", None)
        assert status == 0 and data == b""


def test_list_github_forks_pagination_and_limits():
    # First page shorter than per_page triggers break; returns that page
    page1 = json.dumps([{"full_name": "o/r1"}, {"full_name": "o/r2"}]).encode()
    seq = [(200, page1)]
    with patch("find_commits_lib.github_api.github_api_get", side_effect=seq):
        out = gh.list_github_forks("o", "r", None, max_forks=5)
        assert [x["full_name"] for x in out] == ["o/r1", "o/r2"]

    # Error status breaks
    with patch("find_commits_lib.github_api.github_api_get", return_value=(500, b"")):
        assert gh.list_github_forks("o", "r", None, 5) == []

    # Malformed JSON breaks
    with patch(
        "find_commits_lib.github_api.github_api_get", return_value=(200, b"notjson")
    ):
        assert gh.list_github_forks("o", "r", None, 5) == []


def test_github_repo_details_success_and_errors(capsys):
    # Success
    body = json.dumps({"name": "r"}).encode()
    with patch("find_commits_lib.github_api.github_api_get", return_value=(200, body)):
        status, info = gh.github_repo_details("o", "r", None)
        assert status == 200 and info == {"name": "r"}

    # Error with message
    err = json.dumps({"message": "boom"}).encode()
    with patch("find_commits_lib.github_api.github_api_get", return_value=(404, err)):
        status, info = gh.github_repo_details("o", "r", None)
        assert status == 404 and info is None
    # Malformed JSON on error
    with patch(
        "find_commits_lib.github_api.github_api_get", return_value=(500, b"notjson")
    ):
        status, info = gh.github_repo_details("o", "r", None)
        assert status == 500 and info is None

    # Success but bad JSON prints message
    with patch(
        "find_commits_lib.github_api.github_api_get", return_value=(200, b"notjson")
    ):
        status, info = gh.github_repo_details("o", "r", None)
        assert status == 200 and info is None


def test_fetch_forks_into_repo_main_paths(tmp_path: Path):
    repo_dir = tmp_path
    # Not a GitHub URL -> returns zeros
    assert gh.fetch_forks_into_repo(repo_dir, "https://example.com/x", None, 5, 0) == 0

    # Set up a GitHub URL flow with parent and forks
    forks = [
        {
            "full_name": "u1/r1",
            "owner": {"login": "u1"},
            "name": "r1",
            "clone_url": "https://x/u1/r1.git",
        },
        {
            "full_name": "u2/r2",
            "owner": {"login": "u2"},
            "name": "r2",
            "clone_url": "https://x/u2/r2.git",
        },
    ]
    parent = {
        "fork": True,
        "parent": {
            "full_name": "po/pr",
            "clone_url": "https://x/po/pr.git",
        },
    }

    # Compose side effects for list calls: repo forks then parent forks
    with (
        patch(
            "find_commits_lib.github_api.github_repo_details",
            return_value=(200, parent),
        ),
        patch(
            "find_commits_lib.github_api.list_github_forks", side_effect=[forks, forks]
        ),
        patch(
            "find_commits_lib.github_api.existing_remote_names", return_value=["origin"]
        ),
        patch(
            "find_commits_lib.github_api.ensure_remote_with_refspec"
        ) as ensure_remote,
        patch("find_commits_lib.github_api.run") as run,
    ):
        run.return_value = ""
        added, discovered, selected = gh.fetch_forks_into_repo(
            repo_dir,
            "https://github.com/o/r.git",
            token=None,
            max_forks=2,
            forks_offset=0,
        )
        # 2 forks discovered; offset 0, limit 2 => selected 2
        assert (added, discovered, selected) == (2, 2, 2)
        # ensure remotes added and fetched
        assert ensure_remote.called
        assert any(cmd.args[0][1] == "fetch" for cmd in run.call_args_list)

    # No forks found -> zeros with message
    with (
        patch(
            "find_commits_lib.github_api.github_repo_details", return_value=(200, {})
        ),
        patch("find_commits_lib.github_api.list_github_forks", return_value=[]),
    ):
        assert gh.fetch_forks_into_repo(
            repo_dir, "https://github.com/o/r", None, 5, 0
        ) == (0, 0, 0)


def test_fetch_forks_offset_beyond_discovered_returns_zero(tmp_path: Path):
    repo_dir = tmp_path
    forks = [
        {
            "full_name": "u1/r1",
            "owner": {"login": "u1"},
            "name": "r1",
            "clone_url": "https://x/u1/r1.git",
        },
        {
            "full_name": "u2/r2",
            "owner": {"login": "u2"},
            "name": "r2",
            "clone_url": "https://x/u2/r2.git",
        },
        {
            "full_name": "u3/r3",
            "owner": {"login": "u3"},
            "name": "r3",
            "clone_url": "https://x/u3/r3.git",
        },
    ]
    with (
        patch(
            "find_commits_lib.github_api.github_repo_details", return_value=(200, {})
        ),
        patch("find_commits_lib.github_api.list_github_forks", return_value=forks),
    ):
        added, discovered, selected = gh.fetch_forks_into_repo(
            repo_dir, "https://github.com/o/r", token=None, max_forks=2, forks_offset=10
        )
        assert (added, discovered, selected) == (0, 3, 0)


def test_fetch_forks_limit_zero_selects_none(tmp_path: Path):
    repo_dir = tmp_path
    forks = [
        {
            "full_name": "u1/r1",
            "owner": {"login": "u1"},
            "name": "r1",
            "clone_url": "https://x/u1/r1.git",
        },
    ]
    with (
        patch(
            "find_commits_lib.github_api.github_repo_details", return_value=(200, {})
        ),
        patch("find_commits_lib.github_api.list_github_forks", return_value=forks),
    ):
        added, discovered, selected = gh.fetch_forks_into_repo(
            repo_dir, "https://github.com/o/r", token=None, max_forks=0, forks_offset=0
        )
        # still discovered but none selected or fetched
        assert (added, discovered, selected) == (0, 1, 0)


def test_fetch_forks_remote_name_collision_uses_suffix(tmp_path: Path):
    repo_dir = tmp_path
    forks = [
        {
            "full_name": "u1/r",
            "owner": {"login": "u1"},
            "name": "r",
            "clone_url": "https://x/u1/r.git",
        },
    ]
    with (
        patch(
            "find_commits_lib.github_api.github_repo_details", return_value=(200, {})
        ),
        patch("find_commits_lib.github_api.list_github_forks", return_value=forks),
        patch(
            "find_commits_lib.github_api.existing_remote_names",
            return_value=["origin", "fork_u1_r"],
        ),
        patch(
            "find_commits_lib.github_api.ensure_remote_with_refspec"
        ) as ensure_remote,
        patch("find_commits_lib.github_api.run") as run,
    ):
        run.return_value = ""
        gh.fetch_forks_into_repo(
            repo_dir, "https://github.com/o/r", None, max_forks=1, forks_offset=0
        )
        # Should add a suffixed name since base exists
        assert ensure_remote.called
        name_arg = ensure_remote.call_args[0][1]
        assert name_arg.startswith("fork_u1_r_")
