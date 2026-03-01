"""JSON export implementation."""

import json
from pathlib import Path

import aiofiles

from tg_harvest.config.constants import ALL_EXPORT_FIELDS, DEFAULT_JSON_INDENT
from tg_harvest.exporters.base import BaseExporter, build_row, filter_fields
from tg_harvest.models.parse_result import ParseResult


class JsonExporter(BaseExporter):
    async def export(self, result: ParseResult, output_path: Path, file_suffix: str = "") -> Path:
        output_path.mkdir(parents=True, exist_ok=True)

        channel_name = result.channel.username or str(result.channel.id)
        timestamp = result.parsed_at.strftime("%Y%m%d_%H%M%S")
        file_path = output_path / f"{channel_name}_{timestamp}{file_suffix}.json"

        data = result.model_dump(mode="json")

        # If user selected specific fields, replace messages with flat filtered rows
        if set(self.fields) != set(ALL_EXPORT_FIELDS):
            data["messages"] = [
                filter_fields(build_row(msg), self.fields) for msg in result.messages
            ]

        async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
            await f.write(
                json.dumps(data, ensure_ascii=False, indent=DEFAULT_JSON_INDENT, default=str)
            )

        return file_path
