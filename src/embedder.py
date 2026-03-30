"""Generate and cache embeddings for text chunks.

Uses sentence-transformers for local embedding generation.
Provides disk-based caching to avoid recomputing embeddings.
"""

import hashlib
import json
import pickle
from pathlib import Path
from typing import List, Dict, Optional

import numpy as np

from src.config import (
    EMBEDDING_MODEL,
    EMBEDDING_BATCH_SIZE,
    EMBEDDINGS_CACHE_DIR,
    ENABLE_EMBEDDING_CACHE,
    ensure_cache_dirs,
)


# Lazy-load the model to avoid import time cost
_model = None


def get_model():
    """Get or create the sentence transformer model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer(EMBEDDING_MODEL)
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )
    return _model


def embed_chunks(chunks: List[Dict[str, any]]) -> List[Dict[str, any]]:
    """Add embeddings to chunks, using cache when possible.

    Args:
        chunks: List of chunk dicts with at least a 'text' key.

    Returns:
        Same chunks with 'embedding' key added (numpy array).
    """
    if not chunks:
        return []

    ensure_cache_dirs()
    model = get_model()

    # Check cache for each chunk
    texts_to_embed = []
    text_to_chunk = {}

    for chunk in chunks:
        text = chunk["text"]
        cached_emb = _load_from_cache(text) if ENABLE_EMBEDDING_CACHE else None

        if cached_emb is not None:
            chunk["embedding"] = cached_emb
        else:
            texts_to_embed.append(text)
            text_to_chunk[text] = chunk

    # Embed uncached texts in batches
    if texts_to_embed:
        embeddings = model.encode(
            texts_to_embed,
            batch_size=EMBEDDING_BATCH_SIZE,
            show_progress_bar=False,
            convert_to_numpy=True,
        )

        # Store embeddings and cache them
        for text, embedding in zip(texts_to_embed, embeddings):
            chunk = text_to_chunk[text]
            chunk["embedding"] = embedding

            if ENABLE_EMBEDDING_CACHE:
                _save_to_cache(text, embedding)

    return chunks


def embed_query(query: str) -> np.ndarray:
    """Embed a single query string.

    Args:
        query: The query text to embed.

    Returns:
        Embedding as numpy array.
    """
    model = get_model()
    embedding = model.encode([query], convert_to_numpy=True)[0]
    return embedding


def _load_from_cache(text: str) -> Optional[np.ndarray]:
    """Load embedding from disk cache if available."""
    cache_path = _get_cache_path(text)
    if cache_path.exists():
        try:
            with open(cache_path, "rb") as f:
                return pickle.load(f)
        except Exception:
            return None
    return None


def _save_to_cache(text: str, embedding: np.ndarray):
    """Save embedding to disk cache."""
    cache_path = _get_cache_path(text)
    try:
        with open(cache_path, "wb") as f:
            pickle.dump(embedding, f)
    except Exception:
        pass  # Fail silently on cache errors


def _get_cache_path(text: str) -> Path:
    """Get cache file path for a given text."""
    # Use hash of text as filename to handle any characters
    text_hash = hashlib.sha256(text.encode()).hexdigest()
    return EMBEDDINGS_CACHE_DIR / f"{text_hash}.pkl"


def clear_embedding_cache():
    """Remove all cached embeddings."""
    if EMBEDDINGS_CACHE_DIR.exists():
        for cache_file in EMBEDDINGS_CACHE_DIR.glob("*.pkl"):
            cache_file.unlink()
