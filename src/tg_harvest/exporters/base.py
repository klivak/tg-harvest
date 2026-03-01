"""Base exporter interface and shared utilities."""

from abc import ABC, abstractmethod
from pathlib import Path

from tg_harvest.config.constants import ALL_EXPORT_FIELDS, DEFAULT_DATE_FORMAT
from tg_harvest.models.message import ParsedMessage
from tg_harvest.models.parse_result import ParseResult


def build_row(msg: ParsedMessage) -> dict:
    """Build a flat dict row from a ParsedMessage for tabular export."""
    reactions_detail = ""
    if msg.reactions and msg.reactions.reactions:
        parts = []
        for r in msg.reactions.reactions:
            label = r.emoji or f"custom:{r.custom_emoji_id}"
            parts.append(f"{label}:{r.count}")
        reactions_detail = "; ".join(parts)

    return {
        "id": msg.id,
        "date": msg.date.strftime(DEFAULT_DATE_FORMAT) if msg.date else "",
        "text": msg.text,
        "sender_id": msg.sender_id,
        "post_author": msg.post_author or "",
        "views": msg.views,
        "forwards": msg.forwards,
        "replies_count": msg.replies_count,
        "reactions_total": msg.reactions.total if msg.reactions else 0,
        "reactions_detail": reactions_detail,
        "media_type": msg.media.type if msg.media else "",
        "media_file_name": msg.media.file_name if msg.media else "",
        "media_url": msg.media.url if msg.media else "",
        "forward_from_id": msg.forward_info.from_id if msg.forward_info else "",
        "forward_from_name": msg.forward_info.from_name if msg.forward_info else "",
        "reply_to_msg_id": msg.reply_info.reply_to_msg_id if msg.reply_info else "",
        "reply_to_top_id": msg.reply_info.reply_to_top_id if msg.reply_info else "",
        "grouped_id": msg.grouped_id or "",
        "is_pinned": msg.is_pinned,
        "is_edited": msg.is_edited,
        "edit_date": msg.edit_date.strftime(DEFAULT_DATE_FORMAT) if msg.edit_date else "",
        "url": msg.url,
        "sender_username": msg.sender.username if msg.sender else "",
        "sender_name": msg.sender.display_name if msg.sender else "",
        "sender_is_bot": msg.sender.is_bot if msg.sender else "",
        "media_local_path": msg.media.local_path if msg.media else "",
    }


def filter_fields(row: dict, fields: list[str] | None) -> dict:
    """Filter row to only include specified fields. None means all fields."""
    if fields is None:
        return row
    return {k: v for k, v in row.items() if k in fields}


def resolve_fields(fields: list[str] | None) -> list[str]:
    """Resolve field list: None means all fields, otherwise validate and return."""
    if fields is None:
        return list(ALL_EXPORT_FIELDS)
    return [f for f in fields if f in ALL_EXPORT_FIELDS]


class BaseExporter(ABC):
    """Abstract base class for all exporters."""

    def __init__(self, fields: list[str] | None = None):
        self.fields = resolve_fields(fields)

    @abstractmethod
    async def export(self, result: ParseResult, output_path: Path, file_suffix: str = "") -> Path:
        """Export parse result to a file.

        Args:
            result: The parse result to export.
            output_path: Directory where the file will be saved.
            file_suffix: Optional suffix before extension (e.g. '_part1of3').

        Returns:
            Path to the created file.
        """
