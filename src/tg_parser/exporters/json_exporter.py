"""JSON export implementation."""

import json
from pathlib import Path

import aiofiles

from tg_parser.config.constants import DEFAULT_JSON_INDENT
from tg_parser.exporters.base import BaseExporter
from tg_parser.models.parse_result import ParseResult


class JsonExporter(BaseExporter):
    async def export(self, result: ParseResult, output_path: Path) -> Path:
        output_path.mkdir(parents=True, exist_ok=True)

        channel_name = result.channel.username or str(result.channel.id)
        timestamp = result.parsed_at.strftime("%Y%m%d_%H%M%S")
        file_path = output_path / f"{channel_name}_{timestamp}.json"

        data = result.model_dump(mode="json")

        async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
            await f.write(
                json.dumps(data, ensure_ascii=False, indent=DEFAULT_JSON_INDENT, default=str)
            )

        return file_path
