"""Edge case tests for message parser: error handling, unknown types, None values."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

from telethon.tl import types

from tg_harvest.parsers.message_parser import parse_message


def _msg(**kwargs):
    defaults = {
        "id": 1,
        "message": "text",
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


class TestParseMessageErrorHandling:
    def test_exception_in_parsing_returns_none(self):
        """If something unexpected happens, parse_message should return None."""
        msg = MagicMock(spec=types.Message)
        msg.id = 1
        # date is required but set to an invalid type that will fail
        msg.date = "not-a-datetime"
        msg.message = "text"
        msg.from_id = None
        msg.post_author = None
        msg.media = None
        msg.views = None
        msg.forwards = None
        msg.replies = None
        msg.reactions = None
        msg.fwd_from = None
        msg.reply_to = None
        msg.grouped_id = None
        msg.pinned = False
        msg.edit_date = None
        msg.entities = None

        result = parse_message(msg, channel_id=100)
        assert result is None

    def test_non_message_type_returns_none(self):
        """Random object that's not Message or MessageService."""
        msg = MagicMock()  # No spec — won't match isinstance checks
        result = parse_message(msg, channel_id=100)
        assert result is None


class TestExtractPeerIdEdgeCases:
    def test_unknown_peer_type_returns_none(self):
        """An unknown peer type should result in sender_id=None."""
        unknown_peer = MagicMock()  # Not PeerUser, PeerChannel, or PeerChat
        msg = _msg(from_id=unknown_peer)
        result = parse_message(msg, channel_id=100)
        assert result.sender_id is None


class TestExtractReactionsEdgeCases:
    def test_reactions_with_empty_results(self):
        """Reactions object with empty results list."""
        reactions = MagicMock()
        reactions.results = []
        msg = _msg(reactions=reactions)
        result = parse_message(msg, channel_id=100)
        assert result.reactions is None  # Empty results → None

    def test_reactions_with_none_results(self):
        reactions = MagicMock()
        reactions.results = None
        msg = _msg(reactions=reactions)
        result = parse_message(msg, channel_id=100)
        assert result.reactions is None

    def test_unknown_reaction_type_uses_str(self):
        """Reaction that's neither ReactionEmoji nor ReactionCustomEmoji."""
        r = MagicMock()
        r.count = 5
        r.reaction = MagicMock()  # Unknown type
        r.reaction.__str__ = lambda self: "PaidReaction"

        reactions = MagicMock()
        reactions.results = [r]

        msg = _msg(reactions=reactions)
        result = parse_message(msg, channel_id=100)
        assert result.reactions is not None
        assert result.reactions.total == 5
        assert result.reactions.reactions[0].emoji is not None


class TestExtractRepliesEdgeCases:
    def test_replies_with_no_replies_attr(self):
        """Replies object that doesn't have a 'replies' attribute."""
        replies = MagicMock(spec=[])  # Empty spec — no attributes
        msg = _msg(replies=replies)
        result = parse_message(msg, channel_id=100)
        assert result.replies_count is None

    def test_replies_zero(self):
        replies = MagicMock()
        replies.replies = 0
        msg = _msg(replies=replies)
        result = parse_message(msg, channel_id=100)
        assert result.replies_count == 0


class TestExtractReplyEdgeCases:
    def test_reply_to_not_reply_header(self):
        """reply_to that isn't MessageReplyHeader should return None."""
        reply = MagicMock()  # Not spec=types.MessageReplyHeader
        msg = _msg(reply_to=reply)
        result = parse_message(msg, channel_id=100)
        assert result.reply_info is None


class TestExtractEntitiesEdgeCases:
    def test_empty_entities_list(self):
        msg = _msg(entities=[])
        result = parse_message(msg, channel_id=100)
        assert result.entities == []

    def test_entity_without_url_and_user_id(self):
        entity = MagicMock()
        entity.__class__.__name__ = "MessageEntityBold"
        entity.offset = 0
        entity.length = 5
        # Simulate no url/user_id attributes
        entity.url = None
        entity.user_id = None

        msg = _msg(entities=[entity])
        result = parse_message(msg, channel_id=100)
        assert len(result.entities) == 1
        assert result.entities[0].type == "bold"
        assert result.entities[0].url is None


class TestExtractForwardEdgeCases:
    def test_forward_with_none_fields(self):
        fwd = MagicMock()
        fwd.from_id = None
        fwd.from_name = None
        fwd.channel_post = None
        fwd.date = None

        msg = _msg(fwd_from=fwd)
        result = parse_message(msg, channel_id=100)
        assert result.forward_info is not None
        assert result.forward_info.from_id is None
        assert result.forward_info.from_name is None

    def test_forward_from_user(self):
        peer = MagicMock(spec=types.PeerUser)
        peer.user_id = 42

        fwd = MagicMock()
        fwd.from_id = peer
        fwd.from_name = "User"
        fwd.channel_post = None
        fwd.date = datetime(2024, 1, 1, tzinfo=timezone.utc)

        msg = _msg(fwd_from=fwd)
        result = parse_message(msg, channel_id=100)
        assert result.forward_info.from_id == 42


class TestPinnedEdgeCases:
    def test_pinned_none_becomes_false(self):
        """pinned=None should become False (not None)."""
        msg = _msg(pinned=None)
        result = parse_message(msg, channel_id=100)
        assert result.is_pinned is False
