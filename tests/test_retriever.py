"""Tests for src.retriever — RAG retrieval logic."""

import pytest
from unittest.mock import MagicMock, patch

from src.retriever import Retriever, build_context_from_chunks


class TestBuildContext:
    def test_empty_chunks_returns_placeholder(self):
        result = build_context_from_chunks([])
        assert result == "(no relevant context found)"

    def test_single_chunk_formatted(self):
        chunks = [
            {
                "path": "test.py",
                "text": "def foo(): pass",
                "similarity": 0.95,
            }
        ]
        result = build_context_from_chunks(chunks)
        assert "test.py" in result
        assert "def foo(): pass" in result
        assert "0.95" in result

    def test_multiple_chunks_separated(self):
        chunks = [
            {"path": "a.py", "text": "code a", "similarity": 0.9},
            {"path": "b.py", "text": "code b", "similarity": 0.8},
        ]
        result = build_context_from_chunks(chunks)
        assert "a.py" in result
        assert "b.py" in result
        assert "code a" in result
        assert "code b" in result
        assert result.count("---") >= 1  # Separator present


class TestRetriever:
    def test_retriever_initialization(self):
        retriever = Retriever("owner/repo")
        assert retriever.repo_id == "owner/repo"
        assert retriever.vector_store is not None

    @patch("src.retriever.chunk_file")
    @patch("src.retriever.embed_chunks")
    def test_index_files(self, mock_embed, mock_chunk):
        # Setup mocks
        mock_chunk.return_value = [
            {"text": "chunk1", "path": "test.py", "chunk_id": 0}
        ]
        mock_embed.return_value = [
            {"text": "chunk1", "path": "test.py", "chunk_id": 0, "embedding": [0.1] * 384}
        ]

        retriever = Retriever("owner/repo")
        files = [{"path": "test.py", "content": "code"}]

        retriever.index_files(files)

        mock_chunk.assert_called_once()
        mock_embed.assert_called_once()

    def test_index_files_empty_content_skipped(self):
        retriever = Retriever("owner/repo")
        files = [{"path": "empty.py", "content": None}]

        # Should not raise error
        retriever.index_files(files)

    @patch("src.retriever.embed_query")
    def test_retrieve_with_query(self, mock_embed_query):
        mock_embed_query.return_value = [0.1] * 384

        retriever = Retriever("owner/repo")

        # Empty vector store should return empty results
        results = retriever.retrieve("test query")
        assert results == []
