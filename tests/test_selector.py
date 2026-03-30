"""Tests for src.selector — file scoring and selection logic."""

import pytest

from src.selector import score_file, select_files, truncate_content, MAX_FILE_SIZE


# ---------------------------------------------------------------------------
# score_file
# ---------------------------------------------------------------------------

class TestScoreFile:
    def test_readme_gets_highest_score(self):
        score = score_file("README.md", 500)
        assert score >= 200

    def test_nested_readme_still_high(self):
        score = score_file("docs/README.md", 500)
        assert score > 0

    def test_zero_size_is_excluded(self):
        assert score_file("README.md", 0) == -1

    def test_oversized_file_is_excluded(self):
        assert score_file("big.py", MAX_FILE_SIZE + 1) == -1

    def test_node_modules_excluded(self):
        assert score_file("node_modules/lodash/index.js", 1000) == -1

    def test_pycache_excluded(self):
        assert score_file("src/__pycache__/module.cpython-311.pyc", 200) == -1

    def test_lock_file_excluded(self):
        assert score_file("package-lock.json", 5000) == -1
        assert score_file("poetry.lock", 8000) == -1

    def test_minified_js_excluded(self):
        assert score_file("static/app.min.js", 3000) == -1

    def test_setup_py_is_high_priority(self):
        score = score_file("setup.py", 1000)
        assert score >= 100

    def test_docs_directory_bonus(self):
        score_docs = score_file("docs/usage.md", 800)
        score_other = score_file("internal/usage.md", 800)
        assert score_docs > score_other

    def test_top_level_preferred_over_nested(self):
        score_top = score_file("main.py", 1000)
        score_nested = score_file("a/b/c/main.py", 1000)
        assert score_top > score_nested

    def test_small_file_bonus(self):
        score_small = score_file("src/utils.py", 2000)
        score_large = score_file("src/utils.py", 40000)
        assert score_small > score_large

    def test_valuable_extension_adds_score(self):
        score_py = score_file("tool.py", 1000)
        score_bin = score_file("tool.bin", 1000)
        assert score_py > score_bin


# ---------------------------------------------------------------------------
# select_files
# ---------------------------------------------------------------------------

class TestSelectFiles:
    def _make_file(self, path, size=1000):
        return {"path": path, "size": size, "sha": "", "content": None}

    def test_readme_comes_first(self):
        files = [
            self._make_file("src/main.py"),
            self._make_file("docs/guide.md"),
            self._make_file("README.md"),
        ]
        selected = select_files(files)
        assert selected[0]["path"] == "README.md"

    def test_noisy_files_excluded(self):
        files = [
            self._make_file("README.md"),
            self._make_file("node_modules/index.js"),
            self._make_file("package-lock.json"),
        ]
        selected = select_files(files)
        paths = [f["path"] for f in selected]
        assert "node_modules/index.js" not in paths
        assert "package-lock.json" not in paths

    def test_max_files_respected(self):
        files = [self._make_file(f"src/file{i}.py") for i in range(50)]
        selected = select_files(files, max_files=5)
        assert len(selected) <= 5

    def test_empty_input_returns_empty(self):
        assert select_files([]) == []

    def test_all_ignored_returns_empty(self):
        files = [
            self._make_file("node_modules/a.js"),
            self._make_file("__pycache__/b.pyc"),
        ]
        assert select_files(files) == []

    def test_oversized_files_excluded(self):
        files = [
            self._make_file("huge.py", MAX_FILE_SIZE + 1),
            self._make_file("README.md", 500),
        ]
        selected = select_files(files)
        paths = [f["path"] for f in selected]
        assert "huge.py" not in paths
        assert "README.md" in paths


# ---------------------------------------------------------------------------
# truncate_content
# ---------------------------------------------------------------------------

class TestTruncateContent:
    def test_short_content_unchanged(self):
        text = "Hello, world!"
        assert truncate_content(text, max_chars=100) == text

    def test_long_content_truncated(self):
        text = "x" * 5000
        result = truncate_content(text, max_chars=100)
        assert len(result) > 100  # includes the notice
        assert result.startswith("x" * 100)
        assert "[truncated]" in result

    def test_exact_length_unchanged(self):
        text = "y" * 3000
        assert truncate_content(text, max_chars=3000) == text

    def test_empty_string(self):
        assert truncate_content("") == ""
