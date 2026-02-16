"""Tests for SearchEngine."""

import json

import pytest

from tg_harvest.models.media import MediaType
from tg_harvest.search.engine import SearchEngine, SearchFilters


class TestSearchEngine:
    @pytest.fixture
    def engine(self):
        return SearchEngine()

    @pytest.fixture
    def sample_json(self, sample_parse_result, tmp_path):
        """Write sample parse result to a JSON file and return the dir."""
        data = sample_parse_result.model_dump(mode="json")
        (tmp_path / "test_channel_20240615.json").write_text(
            json.dumps(data, default=str), encoding="utf-8"
        )
        return tmp_path

    def test_load_results_empty_dir(self, engine, tmp_path):
        results = engine.load_results(tmp_path)
        assert results == []

    def test_load_results_nonexistent_dir(self, engine, tmp_path):
        results = engine.load_results(tmp_path / "nonexistent")
        assert results == []

    def test_load_results(self, engine, sample_json):
        results = engine.load_results(sample_json)
        assert len(results) == 1
        assert results[0].channel.title == "Test Channel"
        assert results[0].total_messages == 2

    def test_search_by_keyword(self, engine, sample_json):
        results = engine.load_results(sample_json)
        filters = SearchFilters(keyword="Hello")
        matches = engine.search(results, filters)
        assert len(matches) == 1
        assert "Hello" in matches[0].message.text

    def test_search_case_insensitive(self, engine, sample_json):
        results = engine.load_results(sample_json)
        filters = SearchFilters(keyword="hello")
        matches = engine.search(results, filters)
        assert len(matches) == 1

    def test_search_no_match(self, engine, sample_json):
        results = engine.load_results(sample_json)
        filters = SearchFilters(keyword="nonexistent_xyz")
        matches = engine.search(results, filters)
        assert len(matches) == 0

    def test_search_empty_keyword(self, engine, sample_json):
        results = engine.load_results(sample_json)
        filters = SearchFilters(keyword="")
        matches = engine.search(results, filters)
        assert len(matches) == 2  # All messages

    def test_search_by_min_views(self, engine, sample_json):
        results = engine.load_results(sample_json)
        filters = SearchFilters(min_views=5000)
        matches = engine.search(results, filters)
        assert len(matches) == 1
        assert matches[0].message.views >= 5000

    def test_search_has_reactions(self, engine, sample_json):
        results = engine.load_results(sample_json)
        filters = SearchFilters(has_reactions=True)
        matches = engine.search(results, filters)
        assert len(matches) == 1
        assert matches[0].message.reactions is not None

    def test_search_by_media_type(self, engine, sample_json):
        results = engine.load_results(sample_json)
        filters = SearchFilters(media_type=MediaType.PHOTO)
        matches = engine.search(results, filters)
        assert len(matches) == 1
        assert matches[0].message.media.type == MediaType.PHOTO

    def test_search_result_has_channel_info(self, engine, sample_json):
        results = engine.load_results(sample_json)
        filters = SearchFilters(keyword="Simple")
        matches = engine.search(results, filters)
        assert len(matches) == 1
        assert matches[0].channel_title == "Test Channel"
        assert matches[0].channel_username == "test_channel"

    def test_search_sorted_by_date_desc(self, engine, sample_json):
        results = engine.load_results(sample_json)
        filters = SearchFilters()
        matches = engine.search(results, filters)
        if len(matches) >= 2:
            assert matches[0].message.date >= matches[1].message.date

    def test_search_skips_invalid_json(self, engine, tmp_path):
        (tmp_path / "bad.json").write_text("not json", encoding="utf-8")
        results = engine.load_results(tmp_path)
        assert results == []
