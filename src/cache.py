"""Simple disk-based response cache.

Caches LLM generation results to avoid redundant API calls.
Uses file-based storage for simplicity.
"""

import hashlib
import json
from pathlib import Path
from typing import Optional

from src.config import RESPONSE_CACHE_DIR, ENABLE_RESPONSE_CACHE, ensure_cache_dirs


def get_cached_response(prompt_key: str) -> Optional[str]:
    """Get cached response for a prompt.

    Args:
        prompt_key: Unique key identifying the prompt (e.g., hash of prompts).

    Returns:
        Cached response text, or None if not found.
    """
    if not ENABLE_RESPONSE_CACHE:
        return None

    ensure_cache_dirs()
    cache_path = _get_cache_path(prompt_key)

    if cache_path.exists():
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("response")
        except Exception:
            return None

    return None


def save_cached_response(prompt_key: str, response: str):
    """Save response to cache.

    Args:
        prompt_key: Unique key identifying the prompt.
        response: Response text to cache.
    """
    if not ENABLE_RESPONSE_CACHE:
        return

    ensure_cache_dirs()
    cache_path = _get_cache_path(prompt_key)

    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump({"response": response}, f)
    except Exception:
        pass  # Fail silently on cache errors


def create_prompt_key(system_prompt: str, user_prompt: str) -> str:
    """Create a unique key for a prompt pair.

    Args:
        system_prompt: System prompt.
        user_prompt: User prompt.

    Returns:
        Hash-based unique key.
    """
    combined = f"{system_prompt}\n---\n{user_prompt}"
    return hashlib.sha256(combined.encode()).hexdigest()


def _get_cache_path(prompt_key: str) -> Path:
    """Get cache file path for a prompt key."""
    return RESPONSE_CACHE_DIR / f"{prompt_key}.json"


def clear_response_cache():
    """Remove all cached responses."""
    if RESPONSE_CACHE_DIR.exists():
        for cache_file in RESPONSE_CACHE_DIR.glob("*.json"):
            cache_file.unlink()
