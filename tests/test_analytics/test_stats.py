"""Tests for ChannelStats."""

from datetime import datetime, timezone

import pytest

from tg_harvest.analytics.stats import ChannelStats
from tg_harvest.models.channel import ChannelInfo
from tg_harvest.models.media import MediaInfo, MediaType
from tg_harvest.models.message import ParsedMessage
from tg_harvest.models.parse_result import ParseResult
from tg_harvest.models.reaction import ReactionCount, ReactionsInfo


@pytest.fixture
def rich_result():
    """Parse result with varied messages for analytics testing."""
    channel = ChannelInfo(id=1, title="Analytics Test")
    messages = [
        ParsedMessage(
            id=1,
            channel_id=1,
            date=datetime(2024, 6, 15, 10, 0, 0, tzinfo=timezone.utc),
            text="Morning post",
            views=5000,
            forwards=10,
            reactions=ReactionsInfo(
                total=100,
                reactions=[
                    ReactionCount(emoji="\U0001f44d", count=80),
                    ReactionCount(emoji="\u2764\ufe0f", count=20),
                ],
            ),
            media=MediaInfo(type=MediaType.PHOTO),
        ),
        ParsedMessage(
            id=2,
            channel_id=1,
            date=datetime(2024, 6, 15, 14, 0, 0, tzinfo=timezone.utc),
            text="Afternoon post",
            views=3000,
            is_edited=True,
            edit_date=datetime(2024, 6, 15, 15, 0, 0, tzinfo=timezone.utc),
        ),
        ParsedMessage(
            id=3,
            channel_id=1,
            date=datetime(2024, 6, 16, 10, 0, 0, tzinfo=timezone.utc),
            text="Next day post",
            views=8000,
            reactions=ReactionsInfo(
                total=200,
                reactions=[
                    ReactionCount(emoji="\U0001f44d", count=150),
                    ReactionCount(emoji="\U0001f525", count=50),
                ],
            ),
            media=MediaInfo(type=MediaType.VIDEO, duration=120),
            forward_info=None,
        ),
        ParsedMessage(
            id=4,
            channel_id=1,
            date=datetime(2024, 6, 16, 22, 0, 0, tzinfo=timezone.utc),
            text="Forwarded late post",
            views=1000,
            forward_info={"from_id": 999, "from_name": "Source"},
        ),
    ]
    return ParseResult(
        channel=channel,
        messages=messages,
        parsed_at=datetime(2024, 6, 17, tzinfo=timezone.utc),
    )


class TestChannelStats:
    def test_total(self, rich_result):
        stats = ChannelStats(rich_result)
        assert stats.total == 4

    def test_messages_per_day(self, rich_result):
        stats = ChannelStats(rich_result)
        per_day = stats.messages_per_day()
        assert per_day["2024-06-15"] == 2
        assert per_day["2024-06-16"] == 2

    def test_activity_by_hour(self, rich_result):
        stats = ChannelStats(rich_result)
        by_hour = stats.activity_by_hour()
        assert by_hour[10] == 2  # Two messages at 10:00
        assert by_hour[14] == 1
        assert by_hour[22] == 1
        assert by_hour[0] == 0  # No messages at midnight
        assert len(by_hour) == 24

    def test_top_by_views(self, rich_result):
        stats = ChannelStats(rich_result)
        top = stats.top_by_views(n=2)
        assert len(top) == 2
        assert top[0].views == 8000
        assert top[1].views == 5000

    def test_top_by_reactions(self, rich_result):
        stats = ChannelStats(rich_result)
        top = stats.top_by_reactions(n=2)
        assert len(top) == 2
        assert top[0].reactions.total == 200
        assert top[1].reactions.total == 100

    def test_media_distribution(self, rich_result):
        stats = ChannelStats(rich_result)
        dist = stats.media_distribution()
        assert dist["text_only"] == 2
        assert dist["photo"] == 1
        assert dist["video"] == 1

    def test_reactions_summary(self, rich_result):
        stats = ChannelStats(rich_result)
        summary = stats.reactions_summary()
        assert summary["\U0001f44d"] == 230  # 80 + 150
        assert summary["\U0001f525"] == 50
        assert summary["\u2764\ufe0f"] == 20

    def test_forwarded_count(self, rich_result):
        stats = ChannelStats(rich_result)
        assert stats.forwarded_count() == 1

    def test_edited_count(self, rich_result):
        stats = ChannelStats(rich_result)
        assert stats.edited_count() == 1

    def test_avg_views(self, rich_result):
        stats = ChannelStats(rich_result)
        avg = stats.avg_views()
        assert avg == (5000 + 3000 + 8000 + 1000) / 4

    def test_avg_reactions(self, rich_result):
        stats = ChannelStats(rich_result)
        avg = stats.avg_reactions()
        assert avg == (100 + 200) / 2

    def test_empty_result(self):
        channel = ChannelInfo(id=1, title="Empty")
        result = ParseResult(
            channel=channel,
            messages=[],
            parsed_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        stats = ChannelStats(result)
        assert stats.total == 0
        assert stats.messages_per_day() == {}
        assert stats.top_by_views() == []
        assert stats.top_by_reactions() == []
        assert stats.avg_views() == 0.0
        assert stats.avg_reactions() == 0.0
        assert stats.forwarded_count() == 0
        assert stats.edited_count() == 0

    @pytest.fixture
    def empty_stats(self):
        channel = ChannelInfo(id=1, title="Empty")
        result = ParseResult(
            channel=channel,
            messages=[],
            parsed_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        return ChannelStats(result)

    def test_messages_per_week(self, rich_result):
        stats = ChannelStats(rich_result)
        per_week = stats.messages_per_week()
        assert isinstance(per_week, dict)
        assert all(isinstance(k, str) for k in per_week.keys())
        assert all(isinstance(v, int) for v in per_week.values())

    def test_messages_per_month(self, rich_result):
        stats = ChannelStats(rich_result)
        per_month = stats.messages_per_month()
        assert "2024-06" in per_month

    def test_top_by_forwards(self, rich_result):
        stats = ChannelStats(rich_result)
        top = stats.top_by_forwards()
        # Only message id=1 has forwards=10; others have None
        assert len(top) == 1
        assert top[0].forwards == 10

    def test_engagement_rate(self, rich_result):
        stats = ChannelStats(rich_result)
        rate = stats.engagement_rate()
        assert isinstance(rate, float)
        assert rate >= 0

    def test_avg_message_length(self, rich_result):
        stats = ChannelStats(rich_result)
        avg_len = stats.avg_message_length()
        assert isinstance(avg_len, float)
        assert avg_len > 0

    def test_empty_engagement_rate(self, empty_stats):
        assert empty_stats.engagement_rate() == 0.0

    def test_empty_avg_message_length(self, empty_stats):
        assert empty_stats.avg_message_length() == 0.0
