"""Tests for parse result model."""

from datetime import datetime, timezone

from tg_harvest.models.message import ParsedMessage
from tg_harvest.models.parse_result import ParseResult


class TestParseResult:
    def test_total_messages_computed(self, sample_parse_result):
        assert sample_parse_result.total_messages == 2

    def test_empty_result(self, sample_channel_info):
        result = ParseResult(
            channel=sample_channel_info,
            messages=[],
            parsed_at=datetime(2024, 6, 15, tzinfo=timezone.utc),
        )
        assert result.total_messages == 0
        assert result.from_date is None
        assert result.to_date is None

    def test_date_range(self, sample_parse_result):
        assert sample_parse_result.from_date.year == 2024
        assert sample_parse_result.to_date.month == 12

    def test_json_serialization(self, sample_parse_result):
        data = sample_parse_result.model_dump(mode="json")
        assert data["total_messages"] == 2
        assert data["channel"]["title"] == "Test Channel"
        assert len(data["messages"]) == 2
        assert "parsed_at" in data

    def test_single_message(self, sample_channel_info):
        msg = ParsedMessage(
            id=1,
            channel_id=123,
            date=datetime(2024, 3, 15, tzinfo=timezone.utc),
            text="One",
        )
        result = ParseResult(
            channel=sample_channel_info,
            messages=[msg],
            parsed_at=datetime.now(timezone.utc),
        )
        assert result.total_messages == 1
