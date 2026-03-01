"""Tests for SenderEnricher."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tg_harvest.models.message import ParsedMessage
from tg_harvest.parsers.sender_enricher import SenderEnricher
from tg_harvest.storage.user_cache import UserCache


def _make_msg(msg_id, sender_id=None):
    return ParsedMessage(
        id=msg_id,
        channel_id=100,
        date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        sender_id=sender_id,
    )


def _make_user_entity(user_id, username="user", first_name="Test", last_name=None, bot=False):
    entity = MagicMock()
    entity.id = user_id
    entity.username = username
    entity.first_name = first_name
    entity.last_name = last_name
    entity.bot = bot
    return entity


class TestSenderEnricher:
    @pytest.fixture
    def cache(self, tmp_path):
        return UserCache(tmp_path / "cache.json")

    @pytest.fixture
    def client(self):
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_empty_messages(self, client, cache):
        enricher = SenderEnricher(client, cache)
        result = await enricher.enrich([])
        assert result == 0

    @pytest.mark.asyncio
    async def test_no_sender_ids(self, client, cache):
        msgs = [_make_msg(1, sender_id=None), _make_msg(2, sender_id=None)]
        enricher = SenderEnricher(client, cache)
        result = await enricher.enrich(msgs)
        assert result == 0

    @pytest.mark.asyncio
    async def test_fetch_and_enrich(self, client, cache):
        msgs = [_make_msg(1, sender_id=42), _make_msg(2, sender_id=42)]

        user_entity = _make_user_entity(42, username="alice", first_name="Alice")

        with patch("tg_harvest.parsers.sender_enricher.types") as mock_types:
            mock_types.User = type(user_entity)
            client.get_entity = AsyncMock(return_value=[user_entity])

            enricher = SenderEnricher(client, cache)
            result = await enricher.enrich(msgs)

        assert result == 1
        assert msgs[0].sender is not None
        assert msgs[0].sender.username == "alice"
        assert msgs[0].sender.first_name == "Alice"
        assert msgs[1].sender is not None
        assert msgs[1].sender.username == "alice"

    @pytest.mark.asyncio
    async def test_cache_hit_no_api_call(self, client, cache):
        # Pre-populate cache
        cache.put(42, {"username": "cached_user", "first_name": "Cached", "is_bot": False})

        msgs = [_make_msg(1, sender_id=42)]
        enricher = SenderEnricher(client, cache)
        result = await enricher.enrich(msgs)

        assert result == 0  # No new fetches
        client.get_entity.assert_not_awaited()
        assert msgs[0].sender is not None
        assert msgs[0].sender.username == "cached_user"

    @pytest.mark.asyncio
    async def test_partial_cache(self, client, cache):
        cache.put(1, {"username": "cached", "first_name": "A", "is_bot": False})

        user_entity = _make_user_entity(2, username="fetched", first_name="B")

        msgs = [_make_msg(1, sender_id=1), _make_msg(2, sender_id=2)]

        with patch("tg_harvest.parsers.sender_enricher.types") as mock_types:
            mock_types.User = type(user_entity)
            client.get_entity = AsyncMock(return_value=[user_entity])

            enricher = SenderEnricher(client, cache)
            result = await enricher.enrich(msgs)

        assert result == 1  # Only 1 new fetch
        assert msgs[0].sender.username == "cached"
        assert msgs[1].sender.username == "fetched"

    @pytest.mark.asyncio
    async def test_api_failure_graceful(self, client, cache):
        msgs = [_make_msg(1, sender_id=999)]

        client.get_entity = AsyncMock(side_effect=ValueError("Cannot find any entity"))

        enricher = SenderEnricher(client, cache)
        result = await enricher.enrich(msgs)

        assert result == 0
        assert msgs[0].sender is None

    @pytest.mark.asyncio
    async def test_enriches_bot_flag(self, client, cache):
        msgs = [_make_msg(1, sender_id=50)]
        user_entity = _make_user_entity(50, username="botuser", bot=True)

        with patch("tg_harvest.parsers.sender_enricher.types") as mock_types:
            mock_types.User = type(user_entity)
            client.get_entity = AsyncMock(return_value=[user_entity])

            enricher = SenderEnricher(client, cache)
            await enricher.enrich(msgs)

        assert msgs[0].sender.is_bot is True

    @pytest.mark.asyncio
    async def test_deduplicates_sender_ids(self, client, cache):
        """Multiple messages from same sender should result in one API call."""
        msgs = [_make_msg(i, sender_id=42) for i in range(5)]
        user_entity = _make_user_entity(42, username="alice")

        with patch("tg_harvest.parsers.sender_enricher.types") as mock_types:
            mock_types.User = type(user_entity)
            client.get_entity = AsyncMock(return_value=[user_entity])

            enricher = SenderEnricher(client, cache)
            await enricher.enrich(msgs)

        # get_entity should only be called once (one batch with one unique ID)
        assert client.get_entity.await_count == 1
        # All messages should be enriched
        assert all(m.sender is not None for m in msgs)
