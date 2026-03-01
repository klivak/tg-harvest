"""Tests for UserCache."""

import json

import pytest

from tg_harvest.storage.user_cache import UserCache


@pytest.fixture
def cache_path(tmp_path):
    return tmp_path / "users_cache.json"


class TestUserCache:
    def test_empty_cache_returns_none(self, cache_path):
        cache = UserCache(cache_path)
        assert cache.get(123) is None

    def test_put_and_get(self, cache_path):
        cache = UserCache(cache_path)
        cache.put(123, {"username": "alice", "first_name": "Alice", "is_bot": False})
        result = cache.get(123)
        assert result is not None
        assert result["username"] == "alice"
        assert result["first_name"] == "Alice"
        assert "cached_at" in result

    def test_persistence(self, cache_path):
        cache1 = UserCache(cache_path)
        cache1.put(456, {"username": "bob", "first_name": "Bob", "is_bot": True})
        cache1.save()

        cache2 = UserCache(cache_path)
        result = cache2.get(456)
        assert result is not None
        assert result["username"] == "bob"

    def test_get_missing_returns_missing_ids(self, cache_path):
        cache = UserCache(cache_path)
        cache.put(1, {"username": "a"})
        cache.put(2, {"username": "b"})

        missing = cache.get_missing({1, 2, 3, 4})
        assert missing == {3, 4}

    def test_get_missing_all_cached(self, cache_path):
        cache = UserCache(cache_path)
        cache.put(10, {"username": "x"})
        assert cache.get_missing({10}) == set()

    def test_get_missing_none_cached(self, cache_path):
        cache = UserCache(cache_path)
        assert cache.get_missing({100, 200}) == {100, 200}

    def test_corrupt_file_starts_fresh(self, cache_path):
        cache_path.write_text("not json at all", encoding="utf-8")
        cache = UserCache(cache_path)
        assert cache.get(1) is None

    def test_non_dict_file_starts_fresh(self, cache_path):
        cache_path.write_text("[1, 2, 3]", encoding="utf-8")
        cache = UserCache(cache_path)
        assert cache.get(1) is None

    def test_save_creates_parent_dirs(self, tmp_path):
        deep_path = tmp_path / "a" / "b" / "c" / "cache.json"
        cache = UserCache(deep_path)
        cache.put(1, {"username": "test"})
        cache.save()
        assert deep_path.exists()
        data = json.loads(deep_path.read_text(encoding="utf-8"))
        assert "1" in data

    def test_overwrite_existing_entry(self, cache_path):
        cache = UserCache(cache_path)
        cache.put(1, {"username": "old"})
        cache.put(1, {"username": "new"})
        result = cache.get(1)
        assert result["username"] == "new"
