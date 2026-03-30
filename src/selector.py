"""Select the most relevant files from a repository file tree."""

import os
import re

# Files that are always considered high priority regardless of path depth.
_HIGH_PRIORITY_FILENAMES = {
    "README.md",
    "README.rst",
    "README.txt",
    "CONTRIBUTING.md",
    "ARCHITECTURE.md",
    "setup.py",
    "setup.cfg",
    "pyproject.toml",
    "package.json",
    "Cargo.toml",
    "go.mod",
    "Makefile",
    "Dockerfile",
}

# Regex patterns matched against the full path.
_HIGH_PRIORITY_PATH_PATTERNS = [
    r"^docs?/",
    r"^examples?/",
    r"^src/main\.",
    r"^src/index\.",
    r"^src/app\.",
    r"^main\.",
    r"^index\.",
    r"^app\.",
]

# File extensions worth including.
_VALUABLE_EXTENSIONS = {
    ".py", ".js", ".ts", ".go", ".rs", ".java", ".rb", ".cs",
    ".md", ".rst", ".txt",
}

# Patterns that indicate generated, vendored, or noisy files to skip.
_IGNORE_PATTERNS = [
    r"node_modules/",
    r"\.git/",
    r"(^|/)venv/",
    r"__pycache__/",
    r"\.pyc$",
    r"(^|/)dist/",
    r"(^|/)build/",
    r"\.min\.(js|css)$",
    r"package-lock\.json$",
    r"yarn\.lock$",
    r"Pipfile\.lock$",
    r"poetry\.lock$",
    r"\.egg-info/",
    r"(^|/)coverage/",
    r"\.coverage$",
]

# Limits
MAX_FILE_SIZE = 50_000   # bytes — skip very large files
MAX_FILES = 10            # maximum number of files to select
MAX_CONTENT_PER_FILE = 3_000  # characters kept per file when truncating


def score_file(path: str, size: int) -> int:
    """Return a relevance score for a file (higher is better; -1 means skip).

    Args:
        path: Repository-relative file path.
        size: File size in bytes as reported by the GitHub API.

    Returns:
        Integer score, or ``-1`` if the file should be excluded.
    """
    if size == 0 or size > MAX_FILE_SIZE:
        return -1

    for pattern in _IGNORE_PATTERNS:
        if re.search(pattern, path):
            return -1

    filename = os.path.basename(path)
    ext = os.path.splitext(filename)[1].lower()

    score = 0

    # README gets the highest priority to maximize its selection likelihood.
    if filename.lower().startswith("readme"):
        score += 200

    if filename in _HIGH_PRIORITY_FILENAMES:
        score += 100

    for pattern in _HIGH_PRIORITY_PATH_PATTERNS:
        if re.search(pattern, path):
            score += 50
            break

    if ext in _VALUABLE_EXTENSIONS:
        score += 20

    # Penalise deeply nested files; top-level files are usually more important.
    depth = path.count("/")
    score -= depth * 5

    # Prefer smaller files (easier to process and more likely to be summaries).
    if size < 5_000:
        score += 10

    return score


def select_files(files: list, max_files: int = MAX_FILES) -> list:
    """Select the most relevant files from a repository file tree.

    Files are scored with :func:`score_file` and the top *max_files* are
    returned. The README (if present) is always placed first.

    Args:
        files: List of file dicts as returned by :func:`~src.fetcher.fetch_repo_files`.
        max_files: Maximum number of files to include.

    Returns:
        Sorted list of selected file dicts (README first).
    """
    scored = [
        (score_file(f["path"], f.get("size", 0)), f)
        for f in files
        if score_file(f["path"], f.get("size", 0)) >= 0
    ]
    scored.sort(key=lambda x: x[0], reverse=True)

    selected = [f for _, f in scored[:max_files]]

    # Ensure README comes first for maximum context at the start of the prompt.
    selected.sort(key=lambda f: 0 if os.path.basename(f["path"]).lower().startswith("readme") else 1)

    return selected


def truncate_content(content: str, max_chars: int = MAX_CONTENT_PER_FILE) -> str:
    """Truncate *content* to at most *max_chars* characters.

    A short notice is appended when truncation occurs so the LLM is aware
    that the file continues beyond the excerpt.

    Args:
        content: Raw file text.
        max_chars: Maximum number of characters to keep.

    Returns:
        Possibly truncated string.
    """
    if len(content) <= max_chars:
        return content
    return content[:max_chars] + "\n...[truncated]"
