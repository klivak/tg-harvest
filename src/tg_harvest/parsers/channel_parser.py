"""Channel parsing orchestrator."""

import logging
from datetime import datetime, timezone
from typing import Callable

from telethon import TelegramClient
from telethon.tl import types

from tg_harvest.client.rate_limiter import RateLimiter
from tg_harvest.config.constants import DEFAULT_ITER_WAIT_TIME
from tg_harvest.models.channel import ChannelInfo
from tg_harvest.models.message import ParsedMessage
from tg_harvest.models.parse_result import ParseResult
from tg_harvest.parsers.message_parser import parse_message

logger = logging.getLogger(__name__)


class ChannelParser:
    """Parses messages from a Telegram channel or group."""

    def __init__(
        self,
        client: TelegramClient,
        rate_limiter: RateLimiter | None = None,
    ):
        self._client = client
        self._rate_limiter = rate_limiter or RateLimiter()

    async def get_channel_info(self, channel: str | int) -> ChannelInfo:
        """Resolve channel identifier and return channel metadata."""
        entity = await self._client.get_entity(channel)
        full = await self._client.get_entity(entity)

        is_channel = isinstance(entity, types.Channel)
        is_group = is_channel and entity.megagroup

        return ChannelInfo(
            id=entity.id,
            title=entity.title,
            username=getattr(entity, "username", None),
            is_channel=is_channel and not is_group,
            is_group=is_group,
            is_private=not getattr(entity, "username", None),
            members_count=getattr(full, "participants_count", None),
            description=getattr(entity, "about", None),
            created_at=getattr(entity, "date", None),
            restricted=getattr(entity, "restricted", False),
            scam=getattr(entity, "scam", False),
            verified=getattr(entity, "verified", False),
        )

    async def list_channels(self, limit: int = 100) -> list[ChannelInfo]:
        """List all accessible channels and groups.

        Args:
            limit: Maximum number of dialogs to scan.

        Returns:
            List of ChannelInfo for channels and groups.
        """
        result: list[ChannelInfo] = []
        async for dialog in self._client.iter_dialogs(limit=limit):
            entity = dialog.entity
            if not isinstance(entity, (types.Channel, types.Chat)):
                continue

            is_channel = isinstance(entity, types.Channel)
            is_group = is_channel and entity.megagroup

            result.append(
                ChannelInfo(
                    id=entity.id,
                    title=entity.title,
                    username=getattr(entity, "username", None),
                    is_channel=is_channel and not is_group,
                    is_group=is_group or isinstance(entity, types.Chat),
                    is_private=not getattr(entity, "username", None),
                    members_count=getattr(entity, "participants_count", None),
                    description=getattr(entity, "about", None),
                    restricted=getattr(entity, "restricted", False),
                    scam=getattr(entity, "scam", False),
                    verified=getattr(entity, "verified", False),
                )
            )

        return result

    async def parse(
        self,
        channel: str | int,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        limit: int = 0,
        min_id: int = 0,
        on_progress: Callable[[int], None] | None = None,
    ) -> ParseResult:
        """Parse messages from a channel within the specified date range.

        Args:
            channel: Channel username (@channel) or numeric ID.
            from_date: Start date (inclusive), UTC.
            to_date: End date (inclusive), UTC.
            limit: Maximum number of messages (0 = no limit).
            min_id: Only fetch messages with ID greater than this (for incremental parsing).
            on_progress: Callback called with current message count.

        Returns:
            ParseResult with channel info and parsed messages.
        """
        channel_info = await self.get_channel_info(channel)
        logger.info("Parsing channel: %s (id=%d)", channel_info.title, channel_info.id)

        messages: list[ParsedMessage] = []
        count = 0

        # Telethon iter_messages: offset_date returns messages BEFORE that date
        # So we use to_date as offset_date and filter from_date manually
        iter_kwargs: dict = {
            "entity": channel,
            "wait_time": DEFAULT_ITER_WAIT_TIME,
            "reverse": False,
        }

        if to_date:
            iter_kwargs["offset_date"] = to_date

        if limit > 0:
            iter_kwargs["limit"] = limit

        if min_id > 0:
            iter_kwargs["min_id"] = min_id

        async for msg in self._client.iter_messages(**iter_kwargs):
            await self._rate_limiter.wait()

            # Stop if message is older than from_date
            if from_date and msg.date and msg.date < from_date:
                break

            parsed = parse_message(msg, channel_info.id)
            if parsed is not None:
                messages.append(parsed)
                count += 1

                if on_progress:
                    on_progress(count)

        logger.info("Parsed %d messages from %s", count, channel_info.title)

        return ParseResult(
            channel=channel_info,
            messages=messages,
            parsed_at=datetime.now(timezone.utc),
            from_date=from_date,
            to_date=to_date,
        )
