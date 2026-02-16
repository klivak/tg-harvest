"""Tests for message parser."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

from telethon.tl import types

from tg_harvest.parsers.message_parser import parse_message


def _make_message(**kwargs):
    """Create a mock Telethon Message with defaults."""
    defaults = {
        "id": 1,
        "message": "Test text",
        "date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
        "from_id": None,
        "post_author": None,
        "media": None,
        "views": None,
        "forwards": None,
        "replies": None,
        "reactions": None,
        "fwd_from": None,
        "reply_to": None,
        "grouped_id": None,
        "pinned": False,
        "edit_date": None,
        "entities": None,
    }
    defaults.update(kwargs)
    msg = MagicMock(spec=types.Message)
    for k, v in defaults.items():
        setattr(msg, k, v)
    return msg


class TestParseMessage:
    def test_basic_message(self):
        msg = _make_message(id=42, message="Hello world")
        result = parse_message(msg, channel_id=100)

        assert result is not None
        assert result.id == 42
        assert result.channel_id == 100
        assert result.text == "Hello world"
        assert result.media is None
        assert result.is_pinned is False

    def test_none_text_becomes_empty(self):
        msg = _make_message(message=None)
        result = parse_message(msg, channel_id=100)
        assert result.text == ""

    def test_pinned_message(self):
        msg = _make_message(pinned=True)
        result = parse_message(msg, channel_id=100)
        assert result.is_pinned is True

    def test_edited_message(self):
        edit_dt = datetime(2024, 6, 16, 10, 0, 0, tzinfo=timezone.utc)
        msg = _make_message(edit_date=edit_dt)
        result = parse_message(msg, channel_id=100)
        assert result.is_edited is True
        assert result.edit_date == edit_dt

    def test_not_edited(self):
        msg = _make_message(edit_date=None)
        result = parse_message(msg, channel_id=100)
        assert result.is_edited is False
        assert result.edit_date is None

    def test_views_and_forwards(self):
        msg = _make_message(views=5000, forwards=30)
        result = parse_message(msg, channel_id=100)
        assert result.views == 5000
        assert result.forwards == 30

    def test_grouped_id(self):
        msg = _make_message(grouped_id=12345678)
        result = parse_message(msg, channel_id=100)
        assert result.grouped_id == 12345678

    def test_post_author(self):
        msg = _make_message(post_author="John Doe")
        result = parse_message(msg, channel_id=100)
        assert result.post_author == "John Doe"

    def test_sender_peer_user(self):
        peer = MagicMock(spec=types.PeerUser)
        peer.user_id = 111222
        msg = _make_message(from_id=peer)
        result = parse_message(msg, channel_id=100)
        assert result.sender_id == 111222

    def test_sender_peer_channel(self):
        peer = MagicMock(spec=types.PeerChannel)
        peer.channel_id = 333444
        msg = _make_message(from_id=peer)
        result = parse_message(msg, channel_id=100)
        assert result.sender_id == 333444

    def test_sender_peer_chat(self):
        peer = MagicMock(spec=types.PeerChat)
        peer.chat_id = 555666
        msg = _make_message(from_id=peer)
        result = parse_message(msg, channel_id=100)
        assert result.sender_id == 555666

    def test_no_sender(self):
        msg = _make_message(from_id=None)
        result = parse_message(msg, channel_id=100)
        assert result.sender_id is None

    def test_service_message_returns_none(self):
        msg = MagicMock(spec=types.MessageService)
        result = parse_message(msg, channel_id=100)
        assert result is None

    def test_forward_info(self):
        fwd = MagicMock()
        fwd.from_id = MagicMock(spec=types.PeerChannel)
        fwd.from_id.channel_id = 9999
        fwd.from_name = "Source"
        fwd.channel_post = 42
        fwd.date = datetime(2024, 1, 1, tzinfo=timezone.utc)

        msg = _make_message(fwd_from=fwd)
        result = parse_message(msg, channel_id=100)
        assert result.forward_info is not None
        assert result.forward_info.from_id == 9999
        assert result.forward_info.from_name == "Source"
        assert result.forward_info.channel_post == 42

    def test_reply_info(self):
        reply = MagicMock(spec=types.MessageReplyHeader)
        reply.reply_to_msg_id = 50
        reply.reply_to_top_id = 10

        msg = _make_message(reply_to=reply)
        result = parse_message(msg, channel_id=100)
        assert result.reply_info is not None
        assert result.reply_info.reply_to_msg_id == 50
        assert result.reply_info.reply_to_top_id == 10

    def test_reactions(self):
        r1 = MagicMock()
        r1.count = 100
        r1.reaction = MagicMock(spec=types.ReactionEmoji)
        r1.reaction.emoticon = "\U0001f44d"

        r2 = MagicMock()
        r2.count = 50
        r2.reaction = MagicMock(spec=types.ReactionCustomEmoji)
        r2.reaction.document_id = 67890

        reactions = MagicMock()
        reactions.results = [r1, r2]

        msg = _make_message(reactions=reactions)
        result = parse_message(msg, channel_id=100)
        assert result.reactions is not None
        assert result.reactions.total == 150
        assert len(result.reactions.reactions) == 2
        assert result.reactions.reactions[0].emoji == "\U0001f44d"
        assert result.reactions.reactions[1].custom_emoji_id == 67890

    def test_replies_count(self):
        replies = MagicMock()
        replies.replies = 15
        msg = _make_message(replies=replies)
        result = parse_message(msg, channel_id=100)
        assert result.replies_count == 15

    def test_entities(self):
        e1 = MagicMock(spec=types.MessageEntityUrl)
        e1.__class__.__name__ = "MessageEntityUrl"
        e1.offset = 0
        e1.length = 20
        e1.url = None
        e1.user_id = None

        e2 = MagicMock(spec=types.MessageEntityTextUrl)
        e2.__class__.__name__ = "MessageEntityTextUrl"
        e2.offset = 25
        e2.length = 10
        e2.url = "https://example.com"
        e2.user_id = None

        msg = _make_message(entities=[e1, e2])
        result = parse_message(msg, channel_id=100)
        assert len(result.entities) == 2
        assert result.entities[1].url == "https://example.com"
