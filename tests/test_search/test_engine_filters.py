"""Tests for SearchEngine date and combined filters."""

import json
from datetime import datetime, timezone

import pytest

from tg_harvest.models.channel import ChannelInfo
from tg_harvest.models.media import MediaInfo, MediaType
from tg_harvest.models.message import ParsedMessage
from tg_harvest.models.parse_result import ParseResult
from tg_harvest.models.reaction import ReactionCount, ReactionsInfo
from tg_harvest.search.engine import SearchEngine, SearchFilters


def _msg(msg_id, text="msg", date_str="2024-06-15", views=None, media=None, reactions=None):
    date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return ParsedMessage(
        id=msg_id,
        channel_id=1,
        date=date,
        text=text,
        views=views,
        media=media,
        reactions=reactions,
    )


def _result(messages, channel_id=1, title="Ch", username="ch"):
    return ParseResult(
        channel=ChannelInfo(id=channel_id, title=title, username=username),
        messages=messages,
        parsed_at=datetime(2024, 6, 15, 14, 0, 0, tzinfo=timezone.utc),
    )


class TestDateFilters:
    @pytest.fixture
    def engine(self):
        return SearchEngine()

    @pytest.fixture
    def results_with_dates(self):
        messages = [
            _msg(1, "jan", "2024-01-15"),
            _msg(2, "mar", "2024-03-15"),
            _msg(3, "jun", "2024-06-15"),
            _msg(4, "sep", "2024-09-15"),
            _msg(5, "dec", "2024-12-15"),
        ]
        return [_result(messages)]

    def test_filter_date_from(self, engine, results_with_dates):
        filters = SearchFilters(date_from="2024-06-01")
        matches = engine.search(results_with_dates, filters)
        assert len(matches) == 3
        for m in matches:
            assert m.message.date >= datetime(2024, 6, 1, tzinfo=timezone.utc)

    def test_filter_date_to(self, engine, results_with_dates):
        filters = SearchFilters(date_to="2024-06-30")
        matches = engine.search(results_with_dates, filters)
        assert len(matches) == 3
        for m in matches:
            assert m.message.date <= datetime(2024, 6, 30, tzinfo=timezone.utc)

    def test_filter_date_range(self, engine, results_with_dates):
        filters = SearchFilters(date_from="2024-03-01", date_to="2024-09-30")
        matches = engine.search(results_with_dates, filters)
        assert len(matches) == 3  # mar, jun, sep

    def test_filter_date_exact_day(self, engine, results_with_dates):
        filters = SearchFilters(date_from="2024-06-15", date_to="2024-06-15")
        matches = engine.search(results_with_dates, filters)
        assert len(matches) == 1
        assert matches[0].message.text == "jun"

    def test_filter_date_no_match(self, engine, results_with_dates):
        filters = SearchFilters(date_from="2025-01-01")
        matches = engine.search(results_with_dates, filters)
        assert len(matches) == 0


class TestCombinedFilters:
    @pytest.fixture
    def engine(self):
        return SearchEngine()

    @pytest.fixture
    def mixed_results(self):
        photo = MediaInfo(type=MediaType.PHOTO)
        video = MediaInfo(type=MediaType.VIDEO)
        reactions = ReactionsInfo(total=10, reactions=[ReactionCount(emoji="👍", count=10)])

        messages = [
            _msg(1, "photo post", views=100, media=photo),
            _msg(2, "viral photo", views=5000, media=photo, reactions=reactions),
            _msg(3, "video post", views=200, media=video),
            _msg(4, "text only", views=50),
            _msg(5, "popular text", views=10000, reactions=reactions),
        ]
        return [_result(messages)]

    def test_keyword_and_media_type(self, engine, mixed_results):
        filters = SearchFilters(keyword="photo", media_type=MediaType.PHOTO)
        matches = engine.search(mixed_results, filters)
        assert len(matches) == 2
        for m in matches:
            assert "photo" in m.message.text.lower()
            assert m.message.media.type == MediaType.PHOTO

    def test_min_views_and_has_reactions(self, engine, mixed_results):
        filters = SearchFilters(min_views=1000, has_reactions=True)
        matches = engine.search(mixed_results, filters)
        assert len(matches) == 2  # viral photo + popular text
        for m in matches:
            assert m.message.views >= 1000
            assert m.message.reactions is not None

    def test_channel_filter(self, engine):
        results = [
            _result([_msg(1, "ch1 msg")], channel_id=1, title="Ch1"),
            _result([_msg(2, "ch2 msg")], channel_id=2, title="Ch2"),
        ]
        filters = SearchFilters(channel_id=1)
        matches = engine.search(results, filters)
        assert len(matches) == 1
        assert matches[0].channel_title == "Ch1"


class TestLoadResults:
    @pytest.fixture
    def engine(self):
        return SearchEngine()

    def test_load_multiple_files(self, engine, tmp_path):
        for i in range(3):
            result = _result([_msg(i, f"msg {i}")], channel_id=i, title=f"Ch{i}")
            data = result.model_dump(mode="json")
            (tmp_path / f"ch{i}.json").write_text(json.dumps(data, default=str), encoding="utf-8")

        results = engine.load_results(tmp_path)
        assert len(results) == 3

    def test_skips_non_json_files(self, engine, tmp_path):
        result = _result([_msg(1, "test")])
        data = result.model_dump(mode="json")
        (tmp_path / "valid.json").write_text(json.dumps(data, default=str), encoding="utf-8")
        (tmp_path / "readme.txt").write_text("not json", encoding="utf-8")

        results = engine.load_results(tmp_path)
        assert len(results) == 1
