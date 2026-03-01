"""Message splitting utilities for multi-part exports."""

from __future__ import annotations

from tg_harvest.models.message import ParsedMessage
from tg_harvest.models.parse_result import ParseResult


def split_messages(
    messages: list[ParsedMessage],
    parts: int,
) -> list[list[ParsedMessage]]:
    """Split messages into roughly-equal chunks preserving order.

    Distribution example: 10 messages / 3 parts -> [4, 3, 3].
    Empty parts are omitted, so actual count may be less than requested.
    """
    if parts <= 1:
        return [messages]
    total = len(messages)
    if total == 0:
        return [messages]

    chunk_size, remainder = divmod(total, parts)
    chunks: list[list[ParsedMessage]] = []
    offset = 0
    for i in range(parts):
        size = chunk_size + (1 if i < remainder else 0)
        chunk = messages[offset : offset + size]
        if chunk:
            chunks.append(chunk)
        offset += size
    return chunks


def make_part_suffix(part: int, total_parts: int) -> str:
    """Return '_part1of3' or '' if no split."""
    if total_parts <= 1:
        return ""
    return f"_part{part}of{total_parts}"


def make_part_result(
    original: ParseResult,
    messages: list[ParsedMessage],
) -> ParseResult:
    """Create a ParseResult with a subset of messages."""
    return ParseResult(
        channel=original.channel,
        messages=messages,
        parsed_at=original.parsed_at,
        from_date=original.from_date,
        to_date=original.to_date,
        download_stats=original.download_stats,
    )
