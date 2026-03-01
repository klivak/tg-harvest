"""Extended tests for ChannelParser: incremental mode, list_channels, limits."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tg_harvest.client.rate_limiter import RateLimiter
from tg_harvest.models.message import ParsedMessage
from tg_harvest.parsers.channel_parser import ChannelParser


def _entity(
    entity_id=100,
    title="Ch",
    username="ch",
    megagroup=False,
    about=None,
    participants_count=100,
    restricted=False,
    scam=False,
    verified=False,
):
    e = MagicMock()
    e.id = entity_id
    e.title = title
    e.username = username
    e.megagroup = megagroup
    e.about = about
    e.date = datetime(2023, 1, 1, tzinfo=timezone.utc)
    e.participants_count = participants_count
    e.restricted = restricted
    e.scam = scam
    e.verified = verified
    return e


def _tel_msg(msg_id, text="msg", date=None):
    m = MagicMock()
    m.id = msg_id
    m.message = text
    m.date = date or datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    return m


def _parsed(msg_id, text="msg", date=None):
    return ParsedMessage(
        id=msg_id,
        channel_id=100,
        date=date or datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
        text=text,
    )


async def _aiter(items):
    for item in items:
        yield item


class TestParseIncrementalMode:
    """Test that min_id parameter is correctly passed to iter_messages."""

    @pytest.fixture
    def parser(self):
        client = AsyncMock()
        return ChannelParser(client, RateLimiter(delay=0))

    @pytest.mark.asyncio
    async def test_min_id_passed_to_iter_messages(self, parser):
        entity = _entity()
        msgs = [_tel_msg(101), _tel_msg(102)]
        parsed = [_parsed(101), _parsed(102)]

        with (
            patch("tg_harvest.parsers.channel_parser.types") as mt,
            patch("tg_harvest.parsers.channel_parser.parse_message", side_effect=parsed),
        ):
            mt.Channel = type(entity)
            mt.User = type(None)
            parser._client.get_entity = AsyncMock(return_value=entity)
            parser._client.iter_messages = MagicMock(return_value=_aiter(msgs))

            await parser.parse(channel="@ch", min_id=100)

        call_kwargs = parser._client.iter_messages.call_args[1]
        assert call_kwargs["min_id"] == 100

    @pytest.mark.asyncio
    async def test_min_id_zero_not_passed(self, parser):
        entity = _entity()

        with patch("tg_harvest.parsers.channel_parser.types") as mt:
            mt.Channel = type(entity)
            mt.User = type(None)
            parser._client.get_entity = AsyncMock(return_value=entity)
            parser._client.iter_messages = MagicMock(return_value=_aiter([]))

            await parser.parse(channel="@ch", min_id=0)

        call_kwargs = parser._client.iter_messages.call_args[1]
        assert "min_id" not in call_kwargs

    @pytest.mark.asyncio
    async def test_limit_passed_to_iter_messages(self, parser):
        entity = _entity()

        with patch("tg_harvest.parsers.channel_parser.types") as mt:
            mt.Channel = type(entity)
            mt.User = type(None)
            parser._client.get_entity = AsyncMock(return_value=entity)
            parser._client.iter_messages = MagicMock(return_value=_aiter([]))

            await parser.parse(channel="@ch", limit=50)

        call_kwargs = parser._client.iter_messages.call_args[1]
        assert call_kwargs["limit"] == 50

    @pytest.mark.asyncio
    async def test_limit_zero_not_passed(self, parser):
        """limit=0 means no limit, should NOT be passed to iter_messages."""
        entity = _entity()

        with patch("tg_harvest.parsers.channel_parser.types") as mt:
            mt.Channel = type(entity)
            mt.User = type(None)
            parser._client.get_entity = AsyncMock(return_value=entity)
            parser._client.iter_messages = MagicMock(return_value=_aiter([]))

            await parser.parse(channel="@ch", limit=0)

        call_kwargs = parser._client.iter_messages.call_args[1]
        assert "limit" not in call_kwargs

    @pytest.mark.asyncio
    async def test_to_date_as_offset_date(self, parser):
        entity = _entity()
        to_dt = datetime(2024, 12, 31, tzinfo=timezone.utc)

        with patch("tg_harvest.parsers.channel_parser.types") as mt:
            mt.Channel = type(entity)
            mt.User = type(None)
            parser._client.get_entity = AsyncMock(return_value=entity)
            parser._client.iter_messages = MagicMock(return_value=_aiter([]))

            await parser.parse(channel="@ch", to_date=to_dt)

        call_kwargs = parser._client.iter_messages.call_args[1]
        assert call_kwargs["offset_date"] == to_dt


class TestListChannelsWithData:
    @pytest.fixture
    def parser(self):
        client = AsyncMock()
        return ChannelParser(client, RateLimiter(delay=0))

    @pytest.mark.asyncio
    async def test_list_channels_returns_channels(self, parser):
        # Both entities must share the same class for isinstance to work
        channel_mock = type("ChannelMock", (), {})
        ch1 = channel_mock()
        ch1.id = 1
        ch1.title = "Channel 1"
        ch1.username = "ch1"
        ch1.megagroup = False
        ch1.participants_count = 100
        ch1.about = None
        ch1.restricted = False
        ch1.scam = False
        ch1.verified = False

        ch2 = channel_mock()
        ch2.id = 2
        ch2.title = "Channel 2"
        ch2.username = "ch2"
        ch2.megagroup = True
        ch2.participants_count = 50
        ch2.about = None
        ch2.restricted = False
        ch2.scam = False
        ch2.verified = False

        dialog1 = MagicMock()
        dialog1.entity = ch1
        dialog2 = MagicMock()
        dialog2.entity = ch2

        with patch("tg_harvest.parsers.channel_parser.types") as mt:
            mt.Channel = channel_mock
            mt.Chat = type(None)
            mt.User = type(None)
            parser._client.iter_dialogs = MagicMock(return_value=_aiter([dialog1, dialog2]))

            result = await parser.list_channels()

        assert len(result) == 2
        assert result[0].title == "Channel 1"
        assert result[0].is_channel is True
        assert result[0].is_group is False
        assert result[1].title == "Channel 2"
        assert result[1].is_group is True

    @pytest.mark.asyncio
    async def test_list_channels_skips_unknown_entities(self, parser):
        """Unknown entity types (not Channel, Chat, or User) should be skipped."""
        unknown_entity = MagicMock()
        dialog = MagicMock()
        dialog.entity = unknown_entity

        with patch("tg_harvest.parsers.channel_parser.types") as mt:
            mt.Channel = type(None)
            mt.Chat = type(None)
            mt.User = type(None)
            parser._client.iter_dialogs = MagicMock(return_value=_aiter([dialog]))

            result = await parser.list_channels()

        assert result == []

    @pytest.mark.asyncio
    async def test_list_channels_limit(self, parser):
        """Limit parameter is passed to iter_dialogs."""
        with patch("tg_harvest.parsers.channel_parser.types") as mt:
            mt.Channel = type(None)
            mt.Chat = type(None)
            mt.User = type(None)
            parser._client.iter_dialogs = MagicMock(return_value=_aiter([]))

            await parser.list_channels(limit=50)

        parser._client.iter_dialogs.assert_called_once_with(limit=50)

    @pytest.mark.asyncio
    async def test_list_channels_includes_description(self, parser):
        ch = _entity(about="Channel description")
        dialog = MagicMock()
        dialog.entity = ch

        with patch("tg_harvest.parsers.channel_parser.types") as mt:
            mt.Channel = type(ch)
            mt.Chat = type(None)
            mt.User = type(None)
            parser._client.iter_dialogs = MagicMock(return_value=_aiter([dialog]))

            result = await parser.list_channels()

        assert result[0].description == "Channel description"

    @pytest.mark.asyncio
    async def test_list_channels_private(self, parser):
        ch = _entity(username=None)
        dialog = MagicMock()
        dialog.entity = ch

        with patch("tg_harvest.parsers.channel_parser.types") as mt:
            mt.Channel = type(ch)
            mt.Chat = type(None)
            mt.User = type(None)
            parser._client.iter_dialogs = MagicMock(return_value=_aiter([dialog]))

            result = await parser.list_channels()

        assert result[0].is_private is True
        assert result[0].username is None


class TestGetChannelInfoEdgeCases:
    @pytest.fixture
    def parser(self):
        client = AsyncMock()
        return ChannelParser(client, RateLimiter(delay=0))

    @pytest.mark.asyncio
    async def test_numeric_channel_id(self, parser):
        entity = _entity(entity_id=12345)

        with patch("tg_harvest.parsers.channel_parser.types") as mt:
            mt.Channel = type(entity)
            mt.User = type(None)
            parser._client.get_entity = AsyncMock(return_value=entity)

            info = await parser.get_channel_info(12345)

        assert info.id == 12345

    @pytest.mark.asyncio
    async def test_channel_with_no_optional_fields(self, parser):
        """Entity with None for all optional fields."""
        entity = _entity(username=None, about=None, participants_count=None)
        entity.date = None

        with patch("tg_harvest.parsers.channel_parser.types") as mt:
            mt.Channel = type(entity)
            mt.User = type(None)
            parser._client.get_entity = AsyncMock(return_value=entity)

            info = await parser.get_channel_info("@test")

        assert info.username is None
        assert info.description is None
        assert info.members_count is None
        assert info.created_at is None
