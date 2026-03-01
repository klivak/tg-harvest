"""Tests for thread statistics in ChannelStats."""

from datetime import datetime, timezone

from tg_harvest.analytics.stats import ChannelStats
from tg_harvest.models.channel import ChannelInfo
from tg_harvest.models.message import ParsedMessage, ReplyInfo
from tg_harvest.models.parse_result import ParseResult


def _make_channel():
    return ChannelInfo(id=1, title="Test")


def _make_msg(msg_id, reply_to_msg_id=None, reply_to_top_id=None):
    reply_info = None
    if reply_to_msg_id or reply_to_top_id:
        reply_info = ReplyInfo(
            reply_to_msg_id=reply_to_msg_id,
            reply_to_top_id=reply_to_top_id,
        )
    return ParsedMessage(
        id=msg_id,
        channel_id=1,
        date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        reply_info=reply_info,
    )


def _make_result(messages):
    return ParseResult(
        channel=_make_channel(),
        messages=messages,
        parsed_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )


class TestThreadStats:
    def test_empty_messages(self):
        stats = ChannelStats(_make_result([]))
        result = stats.thread_stats()
        assert result["total_threads"] == 0
        assert result["avg_replies"] == 0.0
        assert result["max_replies"] == 0

    def test_no_replies(self):
        msgs = [_make_msg(1), _make_msg(2), _make_msg(3)]
        stats = ChannelStats(_make_result(msgs))
        result = stats.thread_stats()
        assert result["total_threads"] == 0

    def test_single_thread(self):
        msgs = [
            _make_msg(1),  # thread starter
            _make_msg(2, reply_to_msg_id=1, reply_to_top_id=1),
            _make_msg(3, reply_to_msg_id=1, reply_to_top_id=1),
            _make_msg(4, reply_to_msg_id=2, reply_to_top_id=1),
        ]
        stats = ChannelStats(_make_result(msgs))
        result = stats.thread_stats()
        assert result["total_threads"] == 1
        assert result["avg_replies"] == 3.0
        assert result["max_replies"] == 3

    def test_multiple_threads(self):
        msgs = [
            _make_msg(1),
            _make_msg(10),
            _make_msg(2, reply_to_msg_id=1, reply_to_top_id=1),
            _make_msg(3, reply_to_msg_id=1, reply_to_top_id=1),
            _make_msg(11, reply_to_msg_id=10, reply_to_top_id=10),
        ]
        stats = ChannelStats(_make_result(msgs))
        result = stats.thread_stats()
        assert result["total_threads"] == 2
        assert result["avg_replies"] == 1.5  # (2 + 1) / 2
        assert result["max_replies"] == 2

    def test_reply_without_top_id_not_counted(self):
        """Messages with reply_to_msg_id but no reply_to_top_id are not threads."""
        msgs = [
            _make_msg(1),
            _make_msg(2, reply_to_msg_id=1, reply_to_top_id=None),
        ]
        stats = ChannelStats(_make_result(msgs))
        result = stats.thread_stats()
        assert result["total_threads"] == 0


class TestTopThreads:
    def test_empty_messages(self):
        stats = ChannelStats(_make_result([]))
        assert stats.top_threads() == []

    def test_returns_sorted_by_count(self):
        msgs = [
            _make_msg(2, reply_to_msg_id=1, reply_to_top_id=1),
            _make_msg(3, reply_to_msg_id=1, reply_to_top_id=1),
            _make_msg(4, reply_to_msg_id=1, reply_to_top_id=1),
            _make_msg(11, reply_to_msg_id=10, reply_to_top_id=10),
        ]
        stats = ChannelStats(_make_result(msgs))
        result = stats.top_threads(n=5)
        assert len(result) == 2
        assert result[0] == (1, 3)  # thread 1 has 3 replies
        assert result[1] == (10, 1)  # thread 10 has 1 reply

    def test_respects_limit(self):
        msgs = [
            _make_msg(2, reply_to_msg_id=1, reply_to_top_id=1),
            _make_msg(11, reply_to_msg_id=10, reply_to_top_id=10),
            _make_msg(21, reply_to_msg_id=20, reply_to_top_id=20),
        ]
        stats = ChannelStats(_make_result(msgs))
        result = stats.top_threads(n=2)
        assert len(result) == 2
