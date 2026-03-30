"""Tests for src.fetcher — GitHub API interaction (mocked)."""

import base64
from unittest.mock import MagicMock, patch

import pytest

from src.fetcher import fetch_repo_files, fetch_file_content


_REPO = "owner/myrepo"


def _mock_get(url, **kwargs):
    """Return fake GitHub API responses based on URL."""
    mock = MagicMock()
    mock.raise_for_status = MagicMock()

    if url.endswith(f"/repos/{_REPO}"):
        mock.json.return_value = {"default_branch": "main"}
    elif "git/trees" in url:
        mock.json.return_value = {
            "tree": [
                {"type": "blob", "path": "README.md", "size": 500, "sha": "abc"},
                {"type": "blob", "path": "src/main.py", "size": 1200, "sha": "def"},
                {"type": "tree", "path": "src", "size": 0, "sha": "ghi"},
            ]
        }
    elif url.endswith(f"/repos/{_REPO}/contents/README.md"):
        content = base64.b64encode(b"# My Repo\nHello world").decode()
        mock.status_code = 200
        mock.json.return_value = {"encoding": "base64", "content": content}
    else:
        mock.status_code = 404
        mock.json.return_value = {}

    return mock


class TestFetchRepoFiles:
    @patch("src.fetcher.requests.get", side_effect=_mock_get)
    def test_returns_only_blobs(self, _mock):
        files = fetch_repo_files(_REPO)
        paths = [f["path"] for f in files]
        assert "README.md" in paths
        assert "src/main.py" in paths
        # Tree entries (directories) should not appear
        assert "src" not in paths

    @patch("src.fetcher.requests.get", side_effect=_mock_get)
    def test_content_is_none_initially(self, _mock):
        files = fetch_repo_files(_REPO)
        for f in files:
            assert f["content"] is None

    @patch("src.fetcher.requests.get", side_effect=_mock_get)
    def test_auth_header_added_with_token(self, mock_get):
        fetch_repo_files(_REPO, token="mytoken")
        for call in mock_get.call_args_list:
            headers = call.kwargs.get("headers", {})
            assert headers.get("Authorization") == "token mytoken"


class TestFetchFileContent:
    @patch("src.fetcher.requests.get", side_effect=_mock_get)
    def test_decodes_base64_content(self, _mock):
        content = fetch_file_content(_REPO, "README.md")
        assert content == "# My Repo\nHello world"

    @patch("src.fetcher.requests.get", side_effect=_mock_get)
    def test_returns_none_on_404(self, _mock):
        content = fetch_file_content(_REPO, "nonexistent.txt")
        assert content is None
