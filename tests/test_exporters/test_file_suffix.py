"""Tests for file_suffix parameter across all exporters."""

import pytest

from tg_harvest.exporters.csv_exporter import CsvExporter
from tg_harvest.exporters.json_exporter import JsonExporter
from tg_harvest.exporters.xlsx_exporter import XlsxExporter


class TestFileSuffix:
    @pytest.mark.asyncio
    async def test_json_suffix_in_filename(self, sample_parse_result, tmp_path):
        path = await JsonExporter().export(sample_parse_result, tmp_path, "_part1of3")
        assert "_part1of3.json" in path.name

    @pytest.mark.asyncio
    async def test_json_no_suffix(self, sample_parse_result, tmp_path):
        path = await JsonExporter().export(sample_parse_result, tmp_path)
        assert "_part" not in path.name
        assert path.name.endswith(".json")

    @pytest.mark.asyncio
    async def test_csv_suffix_in_filename(self, sample_parse_result, tmp_path):
        path = await CsvExporter().export(sample_parse_result, tmp_path, "_part2of5")
        assert "_part2of5.csv" in path.name

    @pytest.mark.asyncio
    async def test_csv_no_suffix(self, sample_parse_result, tmp_path):
        path = await CsvExporter().export(sample_parse_result, tmp_path)
        assert "_part" not in path.name
        assert path.name.endswith(".csv")

    @pytest.mark.asyncio
    async def test_xlsx_suffix_in_filename(self, sample_parse_result, tmp_path):
        path = await XlsxExporter().export(sample_parse_result, tmp_path, "_part3of3")
        assert "_part3of3.xlsx" in path.name

    @pytest.mark.asyncio
    async def test_xlsx_no_suffix(self, sample_parse_result, tmp_path):
        path = await XlsxExporter().export(sample_parse_result, tmp_path)
        assert "_part" not in path.name
        assert path.name.endswith(".xlsx")
