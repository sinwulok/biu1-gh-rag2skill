"""Fetch repository files from the GitHub API."""

import base64
from typing import Optional

import requests

GITHUB_API = "https://api.github.com"


def fetch_repo_files(repo: str, token: Optional[str] = None) -> list:
    """Return the file tree for a GitHub repository.

    Each entry is a dict with keys: path, size, sha, content (None until fetched).

    Args:
        repo: Owner/repo string, e.g. ``"openai/openai-python"``.
        token: Optional GitHub personal access token to raise rate limits.

    Returns:
        List of file dicts from the repository tree.

    Raises:
        requests.HTTPError: If the GitHub API returns an error status.
    """
    headers = _auth_headers(token)

    repo_resp = requests.get(f"{GITHUB_API}/repos/{repo}", headers=headers, timeout=15)
    repo_resp.raise_for_status()
    default_branch = repo_resp.json().get("default_branch", "main")

    tree_resp = requests.get(
        f"{GITHUB_API}/repos/{repo}/git/trees/{default_branch}",
        headers=headers,
        params={"recursive": "1"},
        timeout=15,
    )
    tree_resp.raise_for_status()

    return [
        {
            "path": item["path"],
            "size": item.get("size", 0),
            "sha": item.get("sha", ""),
            "content": None,
        }
        for item in tree_resp.json().get("tree", [])
        if item["type"] == "blob"
    ]


def fetch_file_content(repo: str, path: str, token: Optional[str] = None) -> Optional[str]:
    """Fetch the decoded text content of a single file.

    Args:
        repo: Owner/repo string.
        path: File path within the repository.
        token: Optional GitHub personal access token.

    Returns:
        Decoded file content as a string, or ``None`` on failure.
    """
    headers = _auth_headers(token)

    resp = requests.get(
        f"{GITHUB_API}/repos/{repo}/contents/{path}",
        headers=headers,
        timeout=15,
    )
    if resp.status_code != 200:
        return None

    data = resp.json()
    if data.get("encoding") == "base64":
        try:
            return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        except Exception:
            return None
    return data.get("content")


def _auth_headers(token: Optional[str]) -> dict:
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    return headers
