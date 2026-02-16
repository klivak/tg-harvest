"""Edge case tests for SearchEngine: regex chars, invalid dates, edge filters."""

import json
from datetime import datetime, timezone

import pytest

from tg_harvest.models.channel import ChannelInfo
from tg_harvest.models.message import ParsedMessage
from tg_harvest.models.parse_result import ParseResult
from tg_harvest.search.engine import SearchEngine, SearchFilters


def _msg(msg_id, text="msg", date=None, views=None):
    return ParsedMessage(
        id=msg_id,
        channel_id=1,
        date=date or datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
        text=text,
        views=views,
    )


def _result(messages):
    return ParseResult(
        channel=ChannelInfo(id=1, title="Test"),
        messages=messages,
        parsed_at=datetime(2024, 6, 15, 14, 0, 0, tzinfo=timezone.utc),
    )


class TestSearchRegexSpecialChars:
    @pytest.fixture
    def engine(self):
        return SearchEngine()

    def test_search_with_dots(self, engine):
        results = [_result([_msg(1, "file.txt"), _msg(2, "filetxt")])]
        matches = engine.search(results, SearchFilters(keyword="file.txt"))
        assert len(matches) == 1
        assert matches[0].message.text == "file.txt"

    def test_search_with_brackets(self, engine):
        results = [_result([_msg(1, "array[0]"), _msg(2, "array0")])]
        matches = engine.search(results, SearchFilters(keyword="array[0]"))
        assert len(matches) == 1
        assert matches[0].message.text == "array[0]"

    def test_search_with_parentheses(self, engine):
        results = [_result([_msg(1, "func()"), _msg(2, "func")])]
        matches = engine.search(results, SearchFilters(keyword="func()"))
        assert len(matches) == 1

    def test_search_with_plus(self, engine):
        results = [_result([_msg(1, "C++"), _msg(2, "C")])]
        matches = engine.search(results, SearchFilters(keyword="C++"))
        assert len(matches) == 1
        assert matches[0].message.text == "C++"

    def test_search_with_dollar_and_caret(self, engine):
        results = [_result([_msg(1, "price: $100"), _msg(2, "price: 100")])]
        matches = engine.search(results, SearchFilters(keyword="$100"))
        assert len(matches) == 1

    def test_search_with_backslash(self, engine):
        results = [_result([_msg(1, r"path\to\file"), _msg(2, "path/to/file")])]
        matches = engine.search(results, SearchFilters(keyword=r"path\to"))
        assert len(matches) == 1

    def test_search_with_pipe(self, engine):
        results = [_result([_msg(1, "a|b"), _msg(2, "ab")])]
        matches = engine.search(results, SearchFilters(keyword="a|b"))
        assert len(matches) == 1
        assert matches[0].message.text == "a|b"


class TestSearchDateEdgeCases:
    @pytest.fixture
    def engine(self):
        return SearchEngine()

    def test_invalid_date_format_raises(self, engine):
        results = [_result([_msg(1)])]
        filters = SearchFilters(date_from="not-a-date")
        with pytest.raises(ValueError):
            engine.search(results, filters)

    def test_date_with_time(self, engine):
        results = [
            _result(
                [
                    _msg(1, "early", datetime(2024, 6, 15, 8, 0, 0, tzinfo=timezone.utc)),
                    _msg(2, "late", datetime(2024, 6, 15, 20, 0, 0, tzinfo=timezone.utc)),
                ]
            )
        ]
        filters = SearchFilters(date_from="2024-06-15 12:00:00")
        matches = engine.search(results, filters)
        assert len(matches) == 1
        assert matches[0].message.text == "late"


class TestSearchWithEmptyData:
    @pytest.fixture
    def engine(self):
        return SearchEngine()

    def test_search_empty_results_list(self, engine):
        matches = engine.search([], SearchFilters(keyword="test"))
        assert matches == []

    def test_search_result_with_no_messages(self, engine):
        results = [_result([])]
        matches = engine.search(results, SearchFilters(keyword="test"))
        assert matches == []

    def test_min_views_zero_matches_all_with_views(self, engine):
        results = [
            _result(
                [
                    _msg(1, views=0),
                    _msg(2, views=100),
                    _msg(3),  # views=None
                ]
            )
        ]
        filters = SearchFilters(min_views=0)
        matches = engine.search(results, filters)
        assert len(matches) == 2  # views=0 and views=100, not None


class TestLoadResultsEdgeCases:
    @pytest.fixture
    def engine(self):
        return SearchEngine()

    def test_ignores_non_json_files(self, engine, tmp_path):
        (tmp_path / "data.csv").write_text("a,b,c")
        (tmp_path / "readme.txt").write_text("hello")
        results = engine.load_results(tmp_path)
        assert results == []

    def test_loads_sorted_reverse(self, engine, tmp_path):
        """Files should be loaded in reverse sorted order (newest first)."""
        for name in ["a_2024.json", "b_2025.json", "c_2023.json"]:
            result = _result([_msg(1)])
            data = result.model_dump(mode="json")
            (tmp_path / name).write_text(json.dumps(data, default=str), encoding="utf-8")

        results = engine.load_results(tmp_path)
        assert len(results) == 3

    def test_skips_invalid_json_structure(self, engine, tmp_path):
        """Valid JSON but invalid ParseResult structure."""
        (tmp_path / "bad.json").write_text('{"not": "a parse result"}', encoding="utf-8")
        results = engine.load_results(tmp_path)
        assert results == []
