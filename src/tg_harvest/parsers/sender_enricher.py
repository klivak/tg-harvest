"""Resolve sender_id to user info via Telethon."""

import logging

from telethon import TelegramClient
from telethon.tl import types

from tg_harvest.models.message import ParsedMessage, SenderInfo
from tg_harvest.storage.user_cache import UserCache

logger = logging.getLogger(__name__)

BATCH_SIZE = 200


class SenderEnricher:
    """Enriches messages with sender username/name from Telegram API."""

    def __init__(self, client: TelegramClient, cache: UserCache):
        self._client = client
        self._cache = cache

    async def enrich(self, messages: list[ParsedMessage]) -> int:
        """Enrich messages with sender info. Returns count of newly resolved users."""
        sender_ids = {m.sender_id for m in messages if m.sender_id is not None}
        if not sender_ids:
            return 0

        to_fetch = self._cache.get_missing(sender_ids)
        resolved = 0
        if to_fetch:
            resolved = await self._batch_fetch(to_fetch)

        # Apply cached info to messages
        for msg in messages:
            if msg.sender_id is not None:
                cached = self._cache.get(msg.sender_id)
                if cached:
                    msg.sender = SenderInfo(
                        id=msg.sender_id,
                        username=cached.get("username"),
                        first_name=cached.get("first_name"),
                        last_name=cached.get("last_name"),
                        is_bot=cached.get("is_bot", False),
                    )

        return resolved

    async def _batch_fetch(self, user_ids: set[int]) -> int:
        """Fetch user entities from Telegram in batches."""
        resolved = 0
        id_list = list(user_ids)

        for i in range(0, len(id_list), BATCH_SIZE):
            batch = id_list[i : i + BATCH_SIZE]
            try:
                entities = await self._client.get_entity(batch)
                if not isinstance(entities, list):
                    entities = [entities]
                for entity in entities:
                    if isinstance(entity, types.User):
                        self._cache.put(
                            entity.id,
                            {
                                "username": entity.username,
                                "first_name": entity.first_name,
                                "last_name": entity.last_name,
                                "is_bot": getattr(entity, "bot", False),
                            },
                        )
                        resolved += 1
            except Exception:
                logger.warning(
                    "Failed to fetch batch of %d users",
                    len(batch),
                    exc_info=True,
                )

        self._cache.save()
        return resolved
