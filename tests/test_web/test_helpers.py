"""Tests for web UI helpers."""

import pytest

from tg_harvest.web.helpers import truncate


class TestTruncate:
    def test_none_returns_empty(self):
        assert truncate(None) == ""

    def test_empty_returns_empty(self):
        assert truncate("") == ""

    def test_short_text_unchanged(self):
        assert truncate("hello") == "hello"

    def test_exact_limit_unchanged(self):
        text = "a" * 100
        assert truncate(text) == text

    def test_over_limit_truncated(self):
        text = "a" * 101
        result = truncate(text)
        assert len(result) == 103  # 100 + "..."
        assert result.endswith("...")

    def test_custom_limit(self):
        assert truncate("hello world", limit=5) == "hello..."

    def test_custom_limit_exact(self):
        assert truncate("hello", limit=5) == "hello"

    @pytest.mark.parametrize(
        "text,limit,expected",
        [
            ("abc", 10, "abc"),
            ("abcdefghijk", 10, "abcdefghij..."),
            (None, 50, ""),
            ("", 50, ""),
        ],
    )
    def test_parametrized(self, text, limit, expected):
        assert truncate(text, limit=limit) == expected
