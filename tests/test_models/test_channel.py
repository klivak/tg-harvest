"""Tests for channel model."""

from datetime import datetime, timezone

from tg_harvest.models.channel import ChannelInfo


class TestChannelInfo:
    def test_full_channel(self, sample_channel_info):
        assert sample_channel_info.id == 1234567890
        assert sample_channel_info.title == "Test Channel"
        assert sample_channel_info.username == "test_channel"
        assert sample_channel_info.is_channel is True
        assert sample_channel_info.is_group is False
        assert sample_channel_info.members_count == 5000
        assert sample_channel_info.verified is True

    def test_private_group(self):
        ch = ChannelInfo(
            id=999,
            title="Private Group",
            is_channel=False,
            is_group=True,
            is_private=True,
        )
        assert ch.username is None
        assert ch.is_private is True
        assert ch.is_group is True

    def test_defaults(self):
        ch = ChannelInfo(id=1, title="Test")
        assert ch.is_channel is True
        assert ch.is_group is False
        assert ch.is_private is False
        assert ch.members_count is None
        assert ch.restricted is False
        assert ch.scam is False
        assert ch.verified is False

    def test_json_serialization(self, sample_channel_info):
        data = sample_channel_info.model_dump(mode="json")
        assert data["id"] == 1234567890
        assert data["title"] == "Test Channel"
        assert data["username"] == "test_channel"

    def test_with_created_at(self):
        ch = ChannelInfo(
            id=1,
            title="Ch",
            created_at=datetime(2020, 5, 1, tzinfo=timezone.utc),
        )
        assert ch.created_at.year == 2020
