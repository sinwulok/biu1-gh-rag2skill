"""Tests for src.cache — response caching logic."""

import pytest
import tempfile
from pathlib import Path

from src.cache import (
    get_cached_response,
    save_cached_response,
    create_prompt_key,
    clear_response_cache,
)


class TestPromptKey:
    def test_same_prompts_same_key(self):
        key1 = create_prompt_key("system", "user")
        key2 = create_prompt_key("system", "user")
        assert key1 == key2

    def test_different_prompts_different_key(self):
        key1 = create_prompt_key("system1", "user")
        key2 = create_prompt_key("system2", "user")
        assert key1 != key2

    def test_key_is_hash(self):
        key = create_prompt_key("system", "user")
        assert isinstance(key, str)
        assert len(key) == 64  # SHA-256 hex digest length


class TestResponseCache:
    def test_cache_miss_returns_none(self):
        key = "nonexistent_key_12345"
        result = get_cached_response(key)
        assert result is None

    def test_save_and_retrieve(self):
        key = create_prompt_key("test_system", "test_user")
        response = "This is a test response."

        save_cached_response(key, response)
        retrieved = get_cached_response(key)

        assert retrieved == response

    def test_different_keys_different_responses(self):
        key1 = create_prompt_key("system1", "user1")
        key2 = create_prompt_key("system2", "user2")

        save_cached_response(key1, "response1")
        save_cached_response(key2, "response2")

        assert get_cached_response(key1) == "response1"
        assert get_cached_response(key2) == "response2"

    def test_overwrite_existing(self):
        key = create_prompt_key("system", "user")

        save_cached_response(key, "first")
        save_cached_response(key, "second")

        assert get_cached_response(key) == "second"
