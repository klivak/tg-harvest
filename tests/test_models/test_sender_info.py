"""Tests for SenderInfo model."""

from datetime import datetime, timezone

from tg_harvest.models.message import ParsedMessage, SenderInfo


class TestSenderInfo:
    def test_basic_creation(self):
        sender = SenderInfo(id=1, username="alice", first_name="Alice", last_name="Smith")
        assert sender.id == 1
        assert sender.username == "alice"
        assert sender.first_name == "Alice"
        assert sender.last_name == "Smith"
        assert sender.is_bot is False

    def test_display_name_full(self):
        sender = SenderInfo(id=1, first_name="Alice", last_name="Smith")
        assert sender.display_name == "Alice Smith"

    def test_display_name_first_only(self):
        sender = SenderInfo(id=1, first_name="Alice")
        assert sender.display_name == "Alice"

    def test_display_name_fallback_to_username(self):
        sender = SenderInfo(id=1, username="alice")
        assert sender.display_name == "alice"

    def test_display_name_fallback_to_id(self):
        sender = SenderInfo(id=42)
        assert sender.display_name == "42"

    def test_bot_flag(self):
        sender = SenderInfo(id=1, is_bot=True)
        assert sender.is_bot is True

    def test_json_roundtrip(self):
        sender = SenderInfo(id=1, username="bot", first_name="Test", last_name="Bot", is_bot=True)
        data = sender.model_dump(mode="json")
        restored = SenderInfo.model_validate(data)
        assert restored.id == 1
        assert restored.username == "bot"
        assert restored.is_bot is True
        assert restored.display_name == "Test Bot"


class TestParsedMessageWithSender:
    def test_message_without_sender(self):
        msg = ParsedMessage(id=1, channel_id=100, date=datetime(2024, 1, 1, tzinfo=timezone.utc))
        assert msg.sender is None

    def test_message_with_sender(self):
        sender = SenderInfo(id=42, username="alice", first_name="Alice")
        msg = ParsedMessage(
            id=1,
            channel_id=100,
            date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            sender_id=42,
            sender=sender,
        )
        assert msg.sender is not None
        assert msg.sender.username == "alice"

    def test_json_roundtrip_with_sender(self):
        sender = SenderInfo(id=42, username="alice", first_name="Alice")
        msg = ParsedMessage(
            id=1,
            channel_id=100,
            date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            sender_id=42,
            sender=sender,
        )
        data = msg.model_dump(mode="json")
        restored = ParsedMessage.model_validate(data)
        assert restored.sender is not None
        assert restored.sender.username == "alice"
        assert restored.sender.display_name == "Alice"

    def test_json_roundtrip_without_sender(self):
        msg = ParsedMessage(id=1, channel_id=100, date=datetime(2024, 1, 1, tzinfo=timezone.utc))
        data = msg.model_dump(mode="json")
        restored = ParsedMessage.model_validate(data)
        assert restored.sender is None
