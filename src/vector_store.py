"""Local vector store using FAISS for similarity search.

Simple, file-based vector store that:
- Stores embeddings and metadata locally
- Supports saving/loading from disk
- Provides fast similarity search via FAISS
"""

import pickle
from pathlib import Path
from typing import List, Dict, Optional

import numpy as np

from src.config import VECTOR_STORE_DIR, ensure_cache_dirs


class VectorStore:
    """Local vector store for chunk embeddings."""

    def __init__(self):
        """Initialize empty vector store."""
        self.index = None
        self.chunks = []  # Store chunk metadata alongside embeddings
        self.dimension = None

    def add_chunks(self, chunks: List[Dict[str, any]]):
        """Add chunks with embeddings to the vector store.

        Args:
            chunks: List of chunk dicts with 'embedding' key (numpy array).
        """
        if not chunks:
            return

        # Extract embeddings
        embeddings = np.array([c["embedding"] for c in chunks], dtype=np.float32)

        if self.index is None:
            # Create new index
            self.dimension = embeddings.shape[1]
            self.index = self._create_index(self.dimension)

        # Add to index
        self.index.add(embeddings)

        # Store chunk metadata (without embeddings to save space)
        for chunk in chunks:
            chunk_copy = {k: v for k, v in chunk.items() if k != "embedding"}
            self.chunks.append(chunk_copy)

    def search(self, query_embedding: np.ndarray, top_k: int = 10) -> List[Dict[str, any]]:
        """Search for most similar chunks.

        Args:
            query_embedding: Query embedding as numpy array.
            top_k: Number of results to return.

        Returns:
            List of chunk dicts with 'similarity' score added.
        """
        if self.index is None or self.index.ntotal == 0:
            return []

        # Ensure query is 2D
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)

        query_embedding = query_embedding.astype(np.float32)

        # Search
        top_k = min(top_k, self.index.ntotal)
        distances, indices = self.index.search(query_embedding, top_k)

        # Build results
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.chunks):
                chunk = self.chunks[idx].copy()
                # FAISS L2 distance -> similarity score (lower distance = higher similarity)
                chunk["similarity"] = 1.0 / (1.0 + dist)
                results.append(chunk)

        return results

    def save(self, repo_id: str):
        """Save vector store to disk.

        Args:
            repo_id: Repository identifier (e.g., "owner/repo").
        """
        if self.index is None:
            return

        ensure_cache_dirs()
        base_path = VECTOR_STORE_DIR / self._sanitize_repo_id(repo_id)

        # Save FAISS index
        try:
            import faiss
            faiss.write_index(self.index, str(base_path) + ".index")
        except ImportError:
            raise ImportError(
                "faiss-cpu not installed. "
                "Install with: pip install faiss-cpu"
            )

        # Save chunks metadata
        with open(str(base_path) + ".meta", "wb") as f:
            pickle.dump({"chunks": self.chunks, "dimension": self.dimension}, f)

    def load(self, repo_id: str) -> bool:
        """Load vector store from disk.

        Args:
            repo_id: Repository identifier.

        Returns:
            True if loaded successfully, False otherwise.
        """
        base_path = VECTOR_STORE_DIR / self._sanitize_repo_id(repo_id)
        index_path = Path(str(base_path) + ".index")
        meta_path = Path(str(base_path) + ".meta")

        if not index_path.exists() or not meta_path.exists():
            return False

        try:
            import faiss

            # Load FAISS index
            self.index = faiss.read_index(str(index_path))

            # Load metadata
            with open(meta_path, "rb") as f:
                data = pickle.load(f)
                self.chunks = data["chunks"]
                self.dimension = data["dimension"]

            return True
        except Exception:
            return False

    def _create_index(self, dimension: int):
        """Create a new FAISS index.

        Uses IndexFlatL2 for exact search - simple and good enough for
        small to medium datasets (thousands to tens of thousands of chunks).
        """
        try:
            import faiss
            return faiss.IndexFlatL2(dimension)
        except ImportError:
            raise ImportError(
                "faiss-cpu not installed. "
                "Install with: pip install faiss-cpu"
            )

    def _sanitize_repo_id(self, repo_id: str) -> str:
        """Convert repo ID to filesystem-safe name."""
        return repo_id.replace("/", "_").replace("\\", "_")

    def clear(self):
        """Clear all data from the vector store."""
        self.index = None
        self.chunks = []
        self.dimension = None
