"""Configuration for the v2 RAG pipeline.

Central place for all tunable parameters. Defaults are chosen for:
- Local development
- Minimal resource usage
- Simple deployment
- Good-enough quality
"""

import os
from pathlib import Path

# Cache directories
CACHE_DIR = Path(os.getenv("RAG_CACHE_DIR", ".cache"))
EMBEDDINGS_CACHE_DIR = CACHE_DIR / "embeddings"
RESPONSE_CACHE_DIR = CACHE_DIR / "responses"
VECTOR_STORE_DIR = CACHE_DIR / "vector_store"

# Chunking settings
CHUNK_SIZE = 800  # characters per chunk
CHUNK_OVERLAP = 100  # overlap between chunks to preserve context
MAX_CHUNKS_PER_FILE = 50  # prevent massive files from dominating

# Embedding settings
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Fast, 384-dim embeddings
EMBEDDING_BATCH_SIZE = 32

# Retrieval settings
TOP_K = 8  # number of chunks to retrieve
MIN_SIMILARITY = 0.3  # filter out low-relevance chunks

# LLM settings
VLLM_API_BASE = os.getenv("VLLM_API_BASE", "http://localhost:8000/v1")
VLLM_MODEL = os.getenv("VLLM_MODEL", "meta-llama/Llama-3.1-8B-Instruct")
USE_VLLM = os.getenv("USE_VLLM", "false").lower() in ("true", "1", "yes")

# Generation settings
MAX_GENERATION_TOKENS = 1000
GENERATION_TEMPERATURE = 0.3

# Enable caching by default
ENABLE_EMBEDDING_CACHE = True
ENABLE_RESPONSE_CACHE = True


def ensure_cache_dirs():
    """Create cache directories if they don't exist."""
    EMBEDDINGS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    RESPONSE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
