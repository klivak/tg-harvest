"""Edge case tests for ChannelStats: None views, 24h coverage, custom emojis."""

from datetime import datetime, timezone

from tg_harvest.analytics.stats import ChannelStats
from tg_harvest.models.channel import ChannelInfo
from tg_harvest.models.media import MediaInfo, MediaType
from tg_harvest.models.message import ParsedMessage
from tg_harvest.models.parse_result import ParseResult
from tg_harvest.models.reaction import ReactionCount, ReactionsInfo


def _msg(msg_id, text="msg", date=None, views=None, media=None, reactions=None, **kwargs):
    return ParsedMessage(
        id=msg_id,
        channel_id=1,
        date=date or datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
        text=text,
        views=views,
        media=media,
        reactions=reactions,
        **kwargs,
    )


def _result(messages):
    return ParseResult(
        channel=ChannelInfo(id=1, title="Test"),
        messages=messages,
        parsed_at=datetime(2024, 6, 15, 14, 0, 0, tzinfo=timezone.utc),
    )


class TestActivityByHour:
    def test_always_returns_24_hours(self):
        """Even with a single message, all 24 hours should be present."""
        result = _result([_msg(1, date=datetime(2024, 6, 15, 10, 0, 0, tzinfo=timezone.utc))])
        stats = ChannelStats(result)
        by_hour = stats.activity_by_hour()

        assert len(by_hour) == 24
        for h in range(24):
            assert h in by_hour
        assert by_hour[10] == 1
        assert sum(by_hour.values()) == 1

    def test_empty_returns_24_zeros(self):
        result = _result([])
        stats = ChannelStats(result)
        by_hour = stats.activity_by_hour()

        assert len(by_hour) == 24
        assert all(v == 0 for v in by_hour.values())


class TestTopByViewsEdgeCases:
    def test_all_none_views(self):
        """When no messages have views, top_by_views returns empty."""
        messages = [_msg(i) for i in range(5)]  # All views=None
        stats = ChannelStats(_result(messages))
        assert stats.top_by_views() == []

    def test_some_none_views(self):
        messages = [
            _msg(1, views=100),
            _msg(2),  # views=None
            _msg(3, views=50),
        ]
        stats = ChannelStats(_result(messages))
        top = stats.top_by_views()
        assert len(top) == 2
        assert top[0].views == 100
        assert top[1].views == 50

    def test_views_zero_included(self):
        """Messages with views=0 should be included (not filtered out)."""
        messages = [_msg(1, views=0), _msg(2, views=10)]
        stats = ChannelStats(_result(messages))
        top = stats.top_by_views()
        assert len(top) == 2

    def test_top_n_limits(self):
        messages = [_msg(i, views=i * 10) for i in range(20)]
        stats = ChannelStats(_result(messages))
        top5 = stats.top_by_views(n=5)
        assert len(top5) == 5
        assert top5[0].views == 190


class TestTopByReactionsEdgeCases:
    def test_all_no_reactions(self):
        messages = [_msg(i) for i in range(3)]  # All reactions=None
        stats = ChannelStats(_result(messages))
        assert stats.top_by_reactions() == []

    def test_reactions_total_zero_excluded(self):
        """Messages with reactions.total=0 should be excluded."""
        zero_reactions = ReactionsInfo(total=0, reactions=[])
        messages = [_msg(1, reactions=zero_reactions)]
        stats = ChannelStats(_result(messages))
        assert stats.top_by_reactions() == []


class TestMediaDistribution:
    def test_all_text_only(self):
        messages = [_msg(i) for i in range(5)]  # All media=None
        stats = ChannelStats(_result(messages))
        dist = stats.media_distribution()
        assert dist == {"text_only": 5}

    def test_mixed_media_types(self):
        messages = [
            _msg(1, media=MediaInfo(type=MediaType.PHOTO)),
            _msg(2, media=MediaInfo(type=MediaType.PHOTO)),
            _msg(3, media=MediaInfo(type=MediaType.VIDEO)),
            _msg(4),  # text_only
        ]
        stats = ChannelStats(_result(messages))
        dist = stats.media_distribution()
        assert dist["photo"] == 2
        assert dist["video"] == 1
        assert dist["text_only"] == 1

    def test_all_media_types(self):
        """All media types should be counted correctly."""
        messages = [
            _msg(1, media=MediaInfo(type=MediaType.PHOTO)),
            _msg(2, media=MediaInfo(type=MediaType.VIDEO)),
            _msg(3, media=MediaInfo(type=MediaType.AUDIO)),
            _msg(4, media=MediaInfo(type=MediaType.STICKER)),
            _msg(5, media=MediaInfo(type=MediaType.GIF)),
            _msg(6, media=MediaInfo(type=MediaType.VOICE)),
        ]
        stats = ChannelStats(_result(messages))
        dist = stats.media_distribution()
        assert len(dist) == 6


class TestReactionsSummary:
    def test_custom_emoji_format(self):
        reactions = ReactionsInfo(
            total=10,
            reactions=[ReactionCount(custom_emoji_id=12345, count=10)],
        )
        messages = [_msg(1, reactions=reactions)]
        stats = ChannelStats(_result(messages))
        summary = stats.reactions_summary()
        assert "custom:12345" in summary
        assert summary["custom:12345"] == 10

    def test_aggregates_across_messages(self):
        r1 = ReactionsInfo(total=10, reactions=[ReactionCount(emoji="👍", count=10)])
        r2 = ReactionsInfo(total=5, reactions=[ReactionCount(emoji="👍", count=5)])
        messages = [_msg(1, reactions=r1), _msg(2, reactions=r2)]
        stats = ChannelStats(_result(messages))
        summary = stats.reactions_summary()
        assert summary["👍"] == 15

    def test_empty_reactions(self):
        stats = ChannelStats(_result([]))
        assert stats.reactions_summary() == {}


class TestAvgViews:
    def test_all_none(self):
        messages = [_msg(i) for i in range(3)]
        stats = ChannelStats(_result(messages))
        assert stats.avg_views() == 0.0

    def test_mixed_none_and_values(self):
        messages = [_msg(1, views=100), _msg(2), _msg(3, views=200)]
        stats = ChannelStats(_result(messages))
        assert stats.avg_views() == 150.0

    def test_single_message(self):
        messages = [_msg(1, views=42)]
        stats = ChannelStats(_result(messages))
        assert stats.avg_views() == 42.0


class TestAvgReactions:
    def test_all_none(self):
        messages = [_msg(i) for i in range(3)]
        stats = ChannelStats(_result(messages))
        assert stats.avg_reactions() == 0.0


class TestForwardedAndEdited:
    def test_forward_count_with_dict(self):
        """forward_info as dict (Pydantic coercion)."""
        messages = [
            _msg(1, forward_info={"from_id": 1, "from_name": "src"}),
            _msg(2),
            _msg(3, forward_info={"from_id": 2, "from_name": "src2"}),
        ]
        stats = ChannelStats(_result(messages))
        assert stats.forwarded_count() == 2

    def test_edited_count(self):
        messages = [
            _msg(1, is_edited=True, edit_date=datetime(2024, 6, 16, tzinfo=timezone.utc)),
            _msg(2, is_edited=False),
            _msg(3, is_edited=True, edit_date=datetime(2024, 6, 17, tzinfo=timezone.utc)),
        ]
        stats = ChannelStats(_result(messages))
        assert stats.edited_count() == 2


class TestMessagesPerDay:
    def test_sorted_by_date(self):
        messages = [
            _msg(1, date=datetime(2024, 6, 20, tzinfo=timezone.utc)),
            _msg(2, date=datetime(2024, 6, 10, tzinfo=timezone.utc)),
            _msg(3, date=datetime(2024, 6, 15, tzinfo=timezone.utc)),
        ]
        stats = ChannelStats(_result(messages))
        per_day = stats.messages_per_day()
        dates = list(per_day.keys())
        assert dates == sorted(dates)

    def test_multiple_on_same_day(self):
        messages = [
            _msg(1, date=datetime(2024, 6, 15, 8, 0, tzinfo=timezone.utc)),
            _msg(2, date=datetime(2024, 6, 15, 12, 0, tzinfo=timezone.utc)),
            _msg(3, date=datetime(2024, 6, 15, 18, 0, tzinfo=timezone.utc)),
        ]
        stats = ChannelStats(_result(messages))
        per_day = stats.messages_per_day()
        assert per_day["2024-06-15"] == 3
