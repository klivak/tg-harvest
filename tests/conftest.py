"""Shared test fixtures."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from tg_harvest.models.channel import ChannelInfo
from tg_harvest.models.media import MediaInfo, MediaType
from tg_harvest.models.message import EntityInfo, ForwardInfo, ParsedMessage, ReplyInfo
from tg_harvest.models.parse_result import ParseResult
from tg_harvest.models.reaction import ReactionCount, ReactionsInfo


@pytest.fixture
def sample_channel_info():
    return ChannelInfo(
        id=1234567890,
        title="Test Channel",
        username="test_channel",
        is_channel=True,
        is_group=False,
        is_private=False,
        members_count=5000,
        description="A test channel",
        restricted=False,
        verified=True,
    )


@pytest.fixture
def sample_media_photo():
    return MediaInfo(
        type=MediaType.PHOTO,
        file_size=102400,
        width=1920,
        height=1080,
    )


@pytest.fixture
def sample_media_video():
    return MediaInfo(
        type=MediaType.VIDEO,
        file_name="video.mp4",
        file_size=5242880,
        mime_type="video/mp4",
        duration=120,
        width=1280,
        height=720,
    )


@pytest.fixture
def sample_reactions():
    return ReactionsInfo(
        total=250,
        reactions=[
            ReactionCount(emoji="\U0001f44d", count=150),
            ReactionCount(emoji="\u2764\ufe0f", count=80),
            ReactionCount(custom_emoji_id=12345, count=20),
        ],
    )


@pytest.fixture
def sample_forward_info():
    return ForwardInfo(
        from_id=9876543,
        from_name="Source Channel",
        channel_post=42,
        date=datetime(2024, 1, 10, 8, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def sample_reply_info():
    return ReplyInfo(reply_to_msg_id=99, reply_to_top_id=50)


@pytest.fixture
def sample_message(sample_media_photo, sample_reactions, sample_forward_info, sample_reply_info):
    return ParsedMessage(
        id=1,
        channel_id=1234567890,
        date=datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
        text="Hello world! Check https://example.com",
        sender_id=111222,
        post_author="Author Name",
        media=sample_media_photo,
        views=10000,
        forwards=50,
        replies_count=25,
        reactions=sample_reactions,
        forward_info=sample_forward_info,
        reply_info=sample_reply_info,
        grouped_id=None,
        is_pinned=True,
        is_edited=True,
        edit_date=datetime(2024, 6, 15, 13, 0, 0, tzinfo=timezone.utc),
        entities=[
            EntityInfo(type="texturl", offset=20, length=19, url="https://example.com"),
        ],
    )


@pytest.fixture
def sample_message_minimal():
    return ParsedMessage(
        id=2,
        channel_id=1234567890,
        date=datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
        text="Simple message",
    )


@pytest.fixture
def sample_parse_result(sample_channel_info, sample_message, sample_message_minimal):
    return ParseResult(
        channel=sample_channel_info,
        messages=[sample_message, sample_message_minimal],
        parsed_at=datetime(2024, 6, 15, 14, 0, 0, tzinfo=timezone.utc),
        from_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        to_date=datetime(2024, 12, 31, tzinfo=timezone.utc),
    )


def make_telethon_message(
    msg_id=1,
    message="Test message",
    date=None,
    from_id=None,
    post_author=None,
    media=None,
    views=None,
    forwards=None,
    replies=None,
    reactions=None,
    fwd_from=None,
    reply_to=None,
    grouped_id=None,
    pinned=False,
    edit_date=None,
    entities=None,
):
    """Create a mock Telethon Message object."""
    mock = MagicMock()
    mock.id = msg_id
    mock.message = message
    mock.date = date or datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    mock.from_id = from_id
    mock.post_author = post_author
    mock.media = media
    mock.views = views
    mock.forwards = forwards
    mock.replies = replies
    mock.reactions = reactions
    mock.fwd_from = fwd_from
    mock.reply_to = reply_to
    mock.grouped_id = grouped_id
    mock.pinned = pinned
    mock.edit_date = edit_date
    mock.entities = entities

    # Make isinstance checks work for types.Message
    mock.__class__ = MagicMock
    return mock
