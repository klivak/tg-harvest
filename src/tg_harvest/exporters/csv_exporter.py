"""CSV export implementation."""

import csv
import io
from pathlib import Path

import aiofiles

from tg_harvest.config.constants import DEFAULT_CSV_DELIMITER
from tg_harvest.exporters.base import BaseExporter, build_row, filter_fields
from tg_harvest.models.parse_result import ParseResult


class CsvExporter(BaseExporter):
    async def export(self, result: ParseResult, output_path: Path, file_suffix: str = "") -> Path:
        output_path.mkdir(parents=True, exist_ok=True)

        channel_name = result.channel.username or str(result.channel.id)
        timestamp = result.parsed_at.strftime("%Y%m%d_%H%M%S")
        file_path = output_path / f"{channel_name}_{timestamp}{file_suffix}.csv"

        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=self.fields,
            delimiter=DEFAULT_CSV_DELIMITER,
            extrasaction="ignore",
        )
        writer.writeheader()

        for msg in result.messages:
            row = filter_fields(build_row(msg), self.fields)
            writer.writerow(row)

        async with aiofiles.open(file_path, "w", encoding="utf-8-sig", newline="") as f:
            await f.write(output.getvalue())

        return file_path
