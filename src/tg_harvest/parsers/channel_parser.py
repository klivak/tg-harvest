"""Channel parsing orchestrator."""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from telethon import TelegramClient
from telethon.tl import types

from tg_harvest.client.rate_limiter import RateLimiter
from tg_harvest.config.constants import DEFAULT_DIALOG_LIMIT, DEFAULT_ITER_WAIT_TIME
from tg_harvest.models.channel import ChannelInfo
from tg_harvest.models.media import MediaType
from tg_harvest.models.message import ParsedMessage
from tg_harvest.models.parse_result import ParseResult
from tg_harvest.parsers.message_parser import parse_message
from tg_harvest.parsers.parse_options import ParseOptions

logger = logging.getLogger(__name__)


def _build_user_info(entity, description: str | None = None) -> ChannelInfo:
    """Build ChannelInfo from a Telethon User entity."""
    first = getattr(entity, "first_name", "") or ""
    last = getattr(entity, "last_name", "") or ""
    title = f"{first} {last}".strip() or "Unknown"
    return ChannelInfo(
        id=entity.id,
        title=title,
        username=getattr(entity, "username", None),
        is_channel=False,
        is_group=False,
        is_bot=getattr(entity, "bot", False),
        is_private=not getattr(entity, "username", None),
        description=description,
        verified=getattr(entity, "verified", False),
    )


def _build_channel_info(entity, *, is_basic_chat: bool = False, **extra) -> ChannelInfo:
    """Build ChannelInfo from a Telethon Channel/Chat entity."""
    is_channel = isinstance(entity, types.Channel)
    is_group = is_channel and entity.megagroup
    return ChannelInfo(
        id=entity.id,
        title=entity.title,
        username=getattr(entity, "username", None),
        is_channel=is_channel and not is_group,
        is_group=is_group or is_basic_chat,
        is_private=not getattr(entity, "username", None),
        members_count=getattr(entity, "participants_count", None),
        description=getattr(entity, "about", None),
        restricted=getattr(entity, "restricted", False),
        scam=getattr(entity, "scam", False),
        verified=getattr(entity, "verified", False),
        **extra,
    )


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

        if isinstance(entity, types.User):
            return _build_user_info(entity, description=getattr(full, "about", None))

        return _build_channel_info(
            entity,
            created_at=getattr(entity, "date", None),
        )

    async def list_channels(self, limit: int = DEFAULT_DIALOG_LIMIT) -> list[ChannelInfo]:
        """List all accessible channels, groups, bots, and private chats.

        Args:
            limit: Maximum number of dialogs to scan.

        Returns:
            List of ChannelInfo for channels, groups, bots, and private chats.
        """
        result: list[ChannelInfo] = []
        async for dialog in self._client.iter_dialogs(limit=limit):
            entity = dialog.entity

            if isinstance(entity, types.User):
                result.append(_build_user_info(entity))
            elif isinstance(entity, (types.Channel, types.Chat)):
                result.append(
                    _build_channel_info(entity, is_basic_chat=isinstance(entity, types.Chat))
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
        options: ParseOptions | None = None,
    ) -> ParseResult:
        """Parse messages from a channel within the specified date range.

        Args:
            channel: Channel username (@channel) or numeric ID.
            from_date: Start date (inclusive), UTC.
            to_date: End date (inclusive), UTC.
            limit: Maximum number of messages (0 = no limit).
            min_id: Only fetch messages with ID greater than this (for incremental parsing).
            on_progress: Callback called with current message count.
            options: Extended parsing options (media download, sender enrichment, etc.).

        Returns:
            ParseResult with channel info and parsed messages.
        """
        options = options or ParseOptions()
        channel_info = await self.get_channel_info(channel)
        logger.info("Parsing channel: %s (id=%d)", channel_info.title, channel_info.id)

        # Initialize media downloader if requested
        downloader = None
        if options.download_media:
            from tg_harvest.parsers.media_downloader import MediaDownloader

            media_dir = options.media_output_dir or (
                Path("./output") / "media" / (channel_info.username or str(channel_info.id))
            )
            downloader = MediaDownloader(self._client, media_dir, options.max_media_size_mb)

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
            # Stop if message is older than from_date
            if from_date and msg.date and msg.date < from_date:
                break

            parsed = parse_message(
                msg, channel_info.id, channel_info.username, text_only=options.text_only
            )
            if parsed is not None:
                # Download media inline if requested
                if downloader and parsed.media and parsed.media.type != MediaType.NONE:
                    local_path = await downloader.download(msg, parsed.media)
                    if local_path:
                        parsed.media.local_path = local_path

                messages.append(parsed)
                count += 1

                if on_progress:
                    on_progress(count)

        logger.info("Parsed %d messages from %s", count, channel_info.title)

        # Sender enrichment (post-parse, batch)
        if options.enrich_senders and messages:
            await self._enrich_senders(messages, options)

        result = ParseResult(
            channel=channel_info,
            messages=messages,
            parsed_at=datetime.now(timezone.utc),
            from_date=from_date,
            to_date=to_date,
        )

        if downloader:
            result.download_stats = downloader.stats

        # Reply thread fetching (post-parse, opt-in)
        if options.fetch_replies and messages:
            await self._fetch_replies(channel, channel_info, messages)

        return result

    async def _enrich_senders(self, messages: list[ParsedMessage], options: ParseOptions) -> None:
        """Resolve sender IDs to usernames/names."""
        from tg_harvest.parsers.sender_enricher import SenderEnricher
        from tg_harvest.storage.user_cache import UserCache

        cache_dir = options.media_output_dir or Path("./output")
        cache_path = cache_dir / ".users_cache.json"
        cache = UserCache(cache_path)
        enricher = SenderEnricher(self._client, cache)
        resolved = await enricher.enrich(messages)
        logger.info("Resolved %d new sender(s)", resolved)

    async def _fetch_replies(
        self,
        channel: str | int,
        channel_info: ChannelInfo,
        messages: list[ParsedMessage],
    ) -> None:
        """Fetch reply thread messages for top-level thread starters."""
        top_ids = list(
            {
                m.reply_info.reply_to_top_id
                for m in messages
                if m.reply_info and m.reply_info.reply_to_top_id
            }
        )
        if not top_ids:
            return

        logger.info("Fetching replies for %d threads...", len(top_ids))
        existing_ids = {m.id for m in messages}

        for top_id in top_ids:
            try:
                async for msg in self._client.iter_messages(channel, reply_to=top_id):
                    if msg.id in existing_ids:
                        continue
                    parsed = parse_message(msg, channel_info.id, channel_info.username)
                    if parsed is not None:
                        messages.append(parsed)
                        existing_ids.add(parsed.id)
            except Exception:
                logger.warning(
                    "Failed to fetch replies for thread %d",
                    top_id,
                    exc_info=True,
                )
