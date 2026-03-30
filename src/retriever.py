"""RAG retrieval orchestration.

Coordinates the RAG pipeline:
- Chunks files
- Embeds chunks
- Indexes in vector store
- Retrieves relevant context for generation
"""

from typing import List, Dict

from src.chunker import chunk_file
from src.embedder import embed_chunks, embed_query
from src.vector_store import VectorStore
from src.config import TOP_K, MIN_SIMILARITY


class Retriever:
    """RAG retrieval coordinator."""

    def __init__(self, repo_id: str):
        """Initialize retriever for a repository.

        Args:
            repo_id: Repository identifier (e.g., "owner/repo").
        """
        self.repo_id = repo_id
        self.vector_store = VectorStore()

    def index_files(self, files: List[Dict[str, any]]):
        """Index files into the vector store.

        Args:
            files: List of file dicts with 'path' and 'content' keys.
        """
        all_chunks = []

        # Chunk all files
        for file in files:
            if file.get("content"):
                chunks = chunk_file(file["path"], file["content"])
                all_chunks.extend(chunks)

        if not all_chunks:
            return

        # Embed chunks
        all_chunks = embed_chunks(all_chunks)

        # Add to vector store
        self.vector_store.add_chunks(all_chunks)

    def retrieve(self, query: str, top_k: int = TOP_K) -> List[Dict[str, any]]:
        """Retrieve most relevant chunks for a query.

        Args:
            query: Query text.
            top_k: Number of chunks to retrieve.

        Returns:
            List of relevant chunks with similarity scores.
        """
        # Embed query
        query_embedding = embed_query(query)

        # Search vector store
        results = self.vector_store.search(query_embedding, top_k=top_k)

        # Filter by minimum similarity
        results = [r for r in results if r.get("similarity", 0) >= MIN_SIMILARITY]

        return results

    def save(self):
        """Save the vector store to disk."""
        self.vector_store.save(self.repo_id)

    def load(self) -> bool:
        """Load the vector store from disk.

        Returns:
            True if loaded successfully, False otherwise.
        """
        return self.vector_store.load(self.repo_id)


def build_context_from_chunks(chunks: List[Dict[str, any]]) -> str:
    """Build a formatted context string from retrieved chunks.

    Args:
        chunks: List of chunk dicts from retrieval.

    Returns:
        Formatted context string for LLM prompt.
    """
    if not chunks:
        return "(no relevant context found)"

    parts = []
    for i, chunk in enumerate(chunks, 1):
        path = chunk.get("path", "unknown")
        text = chunk.get("text", "")
        similarity = chunk.get("similarity", 0)

        parts.append(
            f"[{i}] {path} (relevance: {similarity:.2f})\n{text}\n"
        )

    return "\n---\n".join(parts)
