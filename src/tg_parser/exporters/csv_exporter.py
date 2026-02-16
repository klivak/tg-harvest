"""CSV export implementation."""

import csv
import io
from pathlib import Path

import aiofiles

from tg_parser.config.constants import DEFAULT_CSV_DELIMITER, DEFAULT_DATE_FORMAT
from tg_parser.exporters.base import BaseExporter
from tg_parser.models.parse_result import ParseResult

CSV_COLUMNS = [
    "id",
    "date",
    "text",
    "sender_id",
    "post_author",
    "views",
    "forwards",
    "replies_count",
    "reactions_total",
    "reactions_detail",
    "media_type",
    "media_file_name",
    "media_url",
    "forward_from_id",
    "forward_from_name",
    "reply_to_msg_id",
    "grouped_id",
    "is_pinned",
    "is_edited",
    "edit_date",
]


class CsvExporter(BaseExporter):
    async def export(self, result: ParseResult, output_path: Path) -> Path:
        output_path.mkdir(parents=True, exist_ok=True)

        channel_name = result.channel.username or str(result.channel.id)
        timestamp = result.parsed_at.strftime("%Y%m%d_%H%M%S")
        file_path = output_path / f"{channel_name}_{timestamp}.csv"

        output = io.StringIO()
        writer = csv.DictWriter(
            output, fieldnames=CSV_COLUMNS, delimiter=DEFAULT_CSV_DELIMITER, extrasaction="ignore"
        )
        writer.writeheader()

        for msg in result.messages:
            row = {
                "id": msg.id,
                "date": msg.date.strftime(DEFAULT_DATE_FORMAT) if msg.date else "",
                "text": msg.text,
                "sender_id": msg.sender_id,
                "post_author": msg.post_author or "",
                "views": msg.views,
                "forwards": msg.forwards,
                "replies_count": msg.replies_count,
                "reactions_total": msg.reactions.total if msg.reactions else 0,
                "reactions_detail": _format_reactions(msg.reactions),
                "media_type": msg.media.type if msg.media else "",
                "media_file_name": msg.media.file_name if msg.media else "",
                "media_url": msg.media.url if msg.media else "",
                "forward_from_id": msg.forward_info.from_id if msg.forward_info else "",
                "forward_from_name": msg.forward_info.from_name if msg.forward_info else "",
                "reply_to_msg_id": msg.reply_info.reply_to_msg_id if msg.reply_info else "",
                "grouped_id": msg.grouped_id or "",
                "is_pinned": msg.is_pinned,
                "is_edited": msg.is_edited,
                "edit_date": (msg.edit_date.strftime(DEFAULT_DATE_FORMAT) if msg.edit_date else ""),
            }
            writer.writerow(row)

        async with aiofiles.open(file_path, "w", encoding="utf-8-sig", newline="") as f:
            await f.write(output.getvalue())

        return file_path


def _format_reactions(reactions) -> str:
    if not reactions or not reactions.reactions:
        return ""
    parts = []
    for r in reactions.reactions:
        label = r.emoji or f"custom:{r.custom_emoji_id}"
        parts.append(f"{label}:{r.count}")
    return "; ".join(parts)
