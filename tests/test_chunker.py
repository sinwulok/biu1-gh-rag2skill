"""Tests for src.chunker — text chunking logic."""

import pytest

from src.chunker import chunk_file, _split_with_overlap, _get_file_type


class TestChunkFile:
    def test_empty_content_returns_empty(self):
        chunks = chunk_file("test.py", "")
        assert chunks == []

    def test_chunks_have_required_fields(self):
        content = "def foo():\n    pass\n" * 50
        chunks = chunk_file("test.py", content)

        assert len(chunks) > 0
        for chunk in chunks:
            assert "text" in chunk
            assert "path" in chunk
            assert "chunk_id" in chunk
            assert "metadata" in chunk
            assert chunk["path"] == "test.py"

    def test_small_file_single_chunk(self):
        content = "def foo():\n    return 42"
        chunks = chunk_file("test.py", content)
        assert len(chunks) == 1
        assert chunks[0]["text"] == content

    def test_markdown_chunking(self):
        content = "# Header 1\n\nSome text.\n\n## Header 2\n\nMore text."
        chunks = chunk_file("README.md", content)
        assert len(chunks) >= 1

    def test_code_chunking(self):
        content = "def func1():\n    pass\n\ndef func2():\n    pass\n"
        chunks = chunk_file("code.py", content)
        assert len(chunks) >= 1

    def test_chunk_ids_sequential(self):
        content = "x" * 2000
        chunks = chunk_file("test.txt", content)
        for i, chunk in enumerate(chunks):
            assert chunk["chunk_id"] == i


class TestSplitWithOverlap:
    def test_short_text_no_split(self):
        text = "Hello, world!"
        chunks = _split_with_overlap(text, 100, 10)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_long_text_splits(self):
        text = "x" * 500
        chunks = _split_with_overlap(text, 100, 20)
        assert len(chunks) > 1

    def test_overlap_present(self):
        text = "abcdefghijklmnopqrstuvwxyz" * 10
        chunks = _split_with_overlap(text, 50, 10)
        # Check that chunks overlap
        if len(chunks) > 1:
            assert chunks[0][-5:] in chunks[1][:20]


class TestGetFileType:
    def test_documentation_files(self):
        assert _get_file_type("README.md") == "documentation"
        assert _get_file_type("docs/guide.rst") == "documentation"

    def test_code_files(self):
        assert _get_file_type("main.py") == "code"
        assert _get_file_type("src/app.js") == "code"
        assert _get_file_type("lib.go") == "code"

    def test_config_files(self):
        assert _get_file_type("package.json") == "config"
        assert _get_file_type("config.yaml") == "config"

    def test_other_files(self):
        assert _get_file_type("image.png") == "other"
        assert _get_file_type("data.csv") == "other"
