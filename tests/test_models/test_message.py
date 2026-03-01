"""Tests for message models."""

from datetime import datetime, timezone

from tg_harvest.models.message import EntityInfo, ForwardInfo, ParsedMessage, ReplyInfo


class TestForwardInfo:
    def test_full_forward(self, sample_forward_info):
        assert sample_forward_info.from_id == 9876543
        assert sample_forward_info.from_name == "Source Channel"
        assert sample_forward_info.channel_post == 42
        assert sample_forward_info.date is not None

    def test_minimal_forward(self):
        fwd = ForwardInfo(from_name="Someone")
        assert fwd.from_id is None
        assert fwd.from_name == "Someone"
        assert fwd.channel_post is None


class TestReplyInfo:
    def test_reply(self, sample_reply_info):
        assert sample_reply_info.reply_to_msg_id == 99
        assert sample_reply_info.reply_to_top_id == 50

    def test_reply_minimal(self):
        reply = ReplyInfo(reply_to_msg_id=10)
        assert reply.reply_to_msg_id == 10
        assert reply.reply_to_top_id is None


class TestEntityInfo:
    def test_url_entity(self):
        e = EntityInfo(type="texturl", offset=0, length=10, url="https://example.com")
        assert e.type == "texturl"
        assert e.url == "https://example.com"

    def test_mention_entity(self):
        e = EntityInfo(type="mentionname", offset=5, length=8, user_id=12345)
        assert e.user_id == 12345


class TestParsedMessage:
    def test_full_message(self, sample_message):
        assert sample_message.id == 1
        assert sample_message.channel_id == 1234567890
        assert sample_message.text == "Hello world! Check https://example.com"
        assert sample_message.views == 10000
        assert sample_message.forwards == 50
        assert sample_message.is_pinned is True
        assert sample_message.is_edited is True
        assert sample_message.media is not None
        assert sample_message.reactions is not None
        assert sample_message.forward_info is not None
        assert sample_message.reply_info is not None
        assert len(sample_message.entities) == 1

    def test_minimal_message(self, sample_message_minimal):
        assert sample_message_minimal.id == 2
        assert sample_message_minimal.text == "Simple message"
        assert sample_message_minimal.media is None
        assert sample_message_minimal.reactions is None
        assert sample_message_minimal.views is None
        assert sample_message_minimal.is_pinned is False
        assert sample_message_minimal.entities == []

    def test_default_text_is_empty(self):
        msg = ParsedMessage(
            id=3,
            channel_id=123,
            date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        assert msg.text == ""

    def test_json_roundtrip(self, sample_message):
        data = sample_message.model_dump(mode="json")
        restored = ParsedMessage.model_validate(data)
        assert restored.id == sample_message.id
        assert restored.text == sample_message.text
        assert restored.views == sample_message.views
        assert restored.media.type == sample_message.media.type
        assert restored.reactions.total == sample_message.reactions.total
        assert len(restored.entities) == len(sample_message.entities)

    def test_edit_date_implies_is_edited(self):
        msg = ParsedMessage(
            id=4,
            channel_id=123,
            date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            is_edited=True,
            edit_date=datetime(2024, 1, 2, tzinfo=timezone.utc),
        )
        assert msg.is_edited is True
        assert msg.edit_date is not None

    def test_url_with_username(self):
        msg = ParsedMessage(
            id=1,
            channel_id=987654321,
            channel_username="test_ch",
            date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        assert msg.url == "https://t.me/test_ch/1"

    def test_url_without_username(self):
        msg = ParsedMessage(
            id=42,
            channel_id=123456789,
            date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        assert msg.url.startswith("https://t.me/c/")
        assert "42" in msg.url

    def test_url_in_serialization(self):
        msg = ParsedMessage(
            id=5,
            channel_id=111,
            channel_username="my_chan",
            date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        data = msg.model_dump(mode="json")
        assert "url" in data
        assert data["url"] == "https://t.me/my_chan/5"

    def test_channel_username_field(self):
        msg = ParsedMessage(
            id=1,
            channel_id=123,
            date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        assert msg.channel_username is None
