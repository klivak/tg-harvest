"""Tests for ChannelParser with mocked Telethon client."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tg_harvest.client.rate_limiter import RateLimiter
from tg_harvest.models.message import ParsedMessage
from tg_harvest.parsers.channel_parser import ChannelParser


def _make_channel_entity(
    entity_id=100,
    title="Test Channel",
    username="test_ch",
    megagroup=False,
    participants_count=500,
    about="Test description",
    restricted=False,
    scam=False,
    verified=True,
):
    """Create a mock Telethon Channel entity."""
    entity = MagicMock()
    entity.id = entity_id
    entity.title = title
    entity.username = username
    entity.megagroup = megagroup
    entity.participants_count = participants_count
    entity.about = about
    entity.date = datetime(2023, 1, 1, tzinfo=timezone.utc)
    entity.restricted = restricted
    entity.scam = scam
    entity.verified = verified
    return entity


def _make_telethon_msg(msg_id, text="Test", date=None):
    """Create a simple mock Telethon message."""
    msg = MagicMock()
    msg.id = msg_id
    msg.message = text
    msg.date = date or datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    return msg


def _make_parsed_message(msg_id, text="Test", date=None):
    """Create a ParsedMessage matching the telethon mock."""
    return ParsedMessage(
        id=msg_id,
        channel_id=100,
        date=date or datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
        text=text,
    )


async def _async_iter(items):
    """Helper to create an async iterator from a list."""
    for item in items:
        yield item


class TestGetChannelInfo:
    @pytest.fixture
    def parser(self):
        client = AsyncMock()
        return ChannelParser(client, RateLimiter(delay=0))

    @pytest.mark.asyncio
    async def test_get_channel_info_basic(self, parser):
        entity = _make_channel_entity()

        with patch("tg_harvest.parsers.channel_parser.types") as mock_types:
            mock_types.Channel = type(entity)
            parser._client.get_entity = AsyncMock(return_value=entity)

            info = await parser.get_channel_info("@test_ch")

        assert info.id == 100
        assert info.title == "Test Channel"
        assert info.username == "test_ch"
        assert info.is_channel is True
        assert info.is_group is False
        assert info.description == "Test description"
        assert info.verified is True

    @pytest.mark.asyncio
    async def test_get_channel_info_group(self, parser):
        entity = _make_channel_entity(megagroup=True)

        with patch("tg_harvest.parsers.channel_parser.types") as mock_types:
            mock_types.Channel = type(entity)
            parser._client.get_entity = AsyncMock(return_value=entity)

            info = await parser.get_channel_info("@group")

        assert info.is_channel is False
        assert info.is_group is True

    @pytest.mark.asyncio
    async def test_get_channel_info_private(self, parser):
        entity = _make_channel_entity(username=None)

        with patch("tg_harvest.parsers.channel_parser.types") as mock_types:
            mock_types.Channel = type(entity)
            parser._client.get_entity = AsyncMock(return_value=entity)

            info = await parser.get_channel_info(12345)

        assert info.is_private is True
        assert info.username is None

    @pytest.mark.asyncio
    async def test_get_channel_info_restricted(self, parser):
        entity = _make_channel_entity(restricted=True, scam=True)

        with patch("tg_harvest.parsers.channel_parser.types") as mock_types:
            mock_types.Channel = type(entity)
            parser._client.get_entity = AsyncMock(return_value=entity)

            info = await parser.get_channel_info("@restricted")

        assert info.restricted is True
        assert info.scam is True


class TestParse:
    @pytest.fixture
    def parser(self):
        client = AsyncMock()
        return ChannelParser(client, RateLimiter(delay=0))

    @pytest.mark.asyncio
    async def test_parse_returns_messages(self, parser):
        entity = _make_channel_entity()
        telethon_msgs = [_make_telethon_msg(i, f"Message {i}") for i in range(3)]
        parsed_msgs = [_make_parsed_message(i, f"Message {i}") for i in range(3)]

        with (
            patch("tg_harvest.parsers.channel_parser.types") as mock_types,
            patch(
                "tg_harvest.parsers.channel_parser.parse_message",
                side_effect=parsed_msgs,
            ),
        ):
            mock_types.Channel = type(entity)
            parser._client.get_entity = AsyncMock(return_value=entity)
            parser._client.iter_messages = MagicMock(return_value=_async_iter(telethon_msgs))

            result = await parser.parse(channel="@test_ch")

        assert result.channel.title == "Test Channel"
        assert len(result.messages) == 3

    @pytest.mark.asyncio
    async def test_parse_empty_channel(self, parser):
        entity = _make_channel_entity()

        with patch("tg_harvest.parsers.channel_parser.types") as mock_types:
            mock_types.Channel = type(entity)
            parser._client.get_entity = AsyncMock(return_value=entity)
            parser._client.iter_messages = MagicMock(return_value=_async_iter([]))

            result = await parser.parse(channel="@empty")

        assert len(result.messages) == 0
        assert result.total_messages == 0

    @pytest.mark.asyncio
    async def test_parse_with_progress_callback(self, parser):
        entity = _make_channel_entity()
        telethon_msgs = [_make_telethon_msg(i) for i in range(5)]
        parsed_msgs = [_make_parsed_message(i) for i in range(5)]
        progress_counts = []

        with (
            patch("tg_harvest.parsers.channel_parser.types") as mock_types,
            patch(
                "tg_harvest.parsers.channel_parser.parse_message",
                side_effect=parsed_msgs,
            ),
        ):
            mock_types.Channel = type(entity)
            parser._client.get_entity = AsyncMock(return_value=entity)
            parser._client.iter_messages = MagicMock(return_value=_async_iter(telethon_msgs))

            result = await parser.parse(
                channel="@test", on_progress=lambda c: progress_counts.append(c)
            )

        assert len(result.messages) == 5
        assert progress_counts == [1, 2, 3, 4, 5]

    @pytest.mark.asyncio
    async def test_parse_skips_none_from_parse_message(self, parser):
        """parse_message returns None for service messages — they should be skipped."""
        entity = _make_channel_entity()
        telethon_msgs = [_make_telethon_msg(i) for i in range(3)]

        with (
            patch("tg_harvest.parsers.channel_parser.types") as mock_types,
            patch(
                "tg_harvest.parsers.channel_parser.parse_message",
                side_effect=[_make_parsed_message(0), None, _make_parsed_message(2)],
            ),
        ):
            mock_types.Channel = type(entity)
            parser._client.get_entity = AsyncMock(return_value=entity)
            parser._client.iter_messages = MagicMock(return_value=_async_iter(telethon_msgs))

            result = await parser.parse(channel="@test")

        assert len(result.messages) == 2

    @pytest.mark.asyncio
    async def test_parse_respects_from_date(self, parser):
        entity = _make_channel_entity()
        old_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        new_date = datetime(2024, 6, 15, tzinfo=timezone.utc)
        old_msg = _make_telethon_msg(1, "old", old_date)
        new_msg = _make_telethon_msg(2, "new", new_date)
        # iter_messages returns newest first; parser breaks on old messages
        telethon_msgs = [new_msg, old_msg]

        with (
            patch("tg_harvest.parsers.channel_parser.types") as mock_types,
            patch(
                "tg_harvest.parsers.channel_parser.parse_message",
                side_effect=[_make_parsed_message(2, "new", new_date)],
            ),
        ):
            mock_types.Channel = type(entity)
            parser._client.get_entity = AsyncMock(return_value=entity)
            parser._client.iter_messages = MagicMock(return_value=_async_iter(telethon_msgs))

            result = await parser.parse(
                channel="@test",
                from_date=datetime(2024, 6, 1, tzinfo=timezone.utc),
            )

        assert len(result.messages) == 1
        assert result.messages[0].text == "new"

    @pytest.mark.asyncio
    async def test_parse_sets_dates_in_result(self, parser):
        entity = _make_channel_entity()

        with patch("tg_harvest.parsers.channel_parser.types") as mock_types:
            mock_types.Channel = type(entity)
            parser._client.get_entity = AsyncMock(return_value=entity)
            parser._client.iter_messages = MagicMock(return_value=_async_iter([]))

            from_dt = datetime(2024, 1, 1, tzinfo=timezone.utc)
            to_dt = datetime(2024, 12, 31, tzinfo=timezone.utc)
            result = await parser.parse(channel="@test", from_date=from_dt, to_date=to_dt)

        assert result.from_date == from_dt
        assert result.to_date == to_dt


class TestListChannels:
    @pytest.fixture
    def parser(self):
        client = AsyncMock()
        return ChannelParser(client, RateLimiter(delay=0))

    @pytest.mark.asyncio
    async def test_list_channels_empty(self, parser):
        parser._client.iter_dialogs = MagicMock(return_value=_async_iter([]))

        with patch("tg_harvest.parsers.channel_parser.types") as mock_types:
            mock_types.Channel = type(None)
            mock_types.Chat = type(None)
            result = await parser.list_channels()

        assert result == []
