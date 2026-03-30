"""Tests for src.generator — SKILL.md generation (LLM mocked)."""

from unittest.mock import MagicMock, patch

import pytest

from src.generator import generate_skill_md, _generate_template, _build_context


_REPO = "owner/myrepo"

_FILES = [
    {
        "path": "README.md",
        "size": 400,
        "content": "# myrepo\nA tool that does something useful.\n",
    },
    {
        "path": "src/main.py",
        "size": 800,
        "content": "def main():\n    pass\n",
    },
]


class TestBuildContext:
    def test_contains_repo_name(self):
        ctx = _build_context(_REPO, _FILES)
        assert _REPO in ctx

    def test_contains_file_paths(self):
        ctx = _build_context(_REPO, _FILES)
        assert "README.md" in ctx
        assert "src/main.py" in ctx

    def test_contains_file_content(self):
        ctx = _build_context(_REPO, _FILES)
        assert "A tool that does something useful" in ctx

    def test_unavailable_content_placeholder(self):
        files = [{"path": "README.md", "size": 0, "content": None}]
        ctx = _build_context(_REPO, files)
        assert "(content unavailable)" in ctx


class TestGenerateTemplate:
    def test_contains_repo_name(self):
        md = _generate_template(_REPO, _FILES)
        assert "myrepo" in md

    def test_contains_required_sections(self):
        md = _generate_template(_REPO, _FILES)
        assert "## What this skill does" in md
        assert "## When to use it" in md
        assert "## Key idea" in md
        assert "## Important files" in md

    def test_lists_important_files(self):
        md = _generate_template(_REPO, _FILES)
        assert "README.md" in md
        assert "src/main.py" in md

    def test_includes_readme_excerpt(self):
        md = _generate_template(_REPO, _FILES)
        assert "A tool that does something useful" in md

    def test_no_readme_excerpt_fallback(self):
        files = [{"path": "src/app.py", "size": 100, "content": "# code"}]
        md = _generate_template(_REPO, files)
        assert "## What this skill does" in md


class TestGenerateSkillMd:
    def test_falls_back_to_template_when_openai_missing(self):
        """generate_skill_md must not raise even when openai is unavailable."""
        with patch("src.generator._generate_with_openai", side_effect=ImportError("no openai")):
            md = generate_skill_md(_REPO, _FILES)
        assert "## What this skill does" in md

    def test_uses_openai_when_available(self):
        expected = "# Mocked SKILL\n## What this skill does\nFoo."

        with patch("src.generator._generate_with_openai", return_value=expected):
            md = generate_skill_md(_REPO, _FILES)

        assert "# Mocked SKILL" in md

    def test_openai_error_falls_back_to_template(self):
        with patch("src.generator._generate_with_openai", side_effect=Exception("API error")):
            md = generate_skill_md(_REPO, _FILES)
        assert "## What this skill does" in md
