"""Tests for CSV exporter."""

import csv

import pytest

from tg_harvest.exporters.csv_exporter import CsvExporter


class TestCsvExporter:
    @pytest.fixture
    def exporter(self):
        return CsvExporter()

    @pytest.mark.asyncio
    async def test_export_creates_file(self, exporter, sample_parse_result, tmp_path):
        result_path = await exporter.export(sample_parse_result, tmp_path)
        assert result_path.exists()
        assert result_path.suffix == ".csv"

    @pytest.mark.asyncio
    async def test_export_filename_format(self, exporter, sample_parse_result, tmp_path):
        result_path = await exporter.export(sample_parse_result, tmp_path)
        assert "test_channel" in result_path.name

    @pytest.mark.asyncio
    async def test_export_has_header(self, exporter, sample_parse_result, tmp_path):
        result_path = await exporter.export(sample_parse_result, tmp_path)
        with open(result_path, encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            header = next(reader)

        assert "id" in header
        assert "date" in header
        assert "text" in header
        assert "views" in header
        assert "reactions_total" in header

    @pytest.mark.asyncio
    async def test_export_row_count(self, exporter, sample_parse_result, tmp_path):
        result_path = await exporter.export(sample_parse_result, tmp_path)
        with open(result_path, encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)

        # 1 header + 2 data rows
        assert len(rows) == 3

    @pytest.mark.asyncio
    async def test_export_message_data(self, exporter, sample_parse_result, tmp_path):
        result_path = await exporter.export(sample_parse_result, tmp_path)
        with open(result_path, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        first = rows[0]
        assert first["id"] == "1"
        assert first["text"] == "Hello world! Check https://example.com"
        assert first["views"] == "10000"
        assert first["is_pinned"] == "True"
        assert first["media_type"] == "photo"

    @pytest.mark.asyncio
    async def test_export_reactions_format(self, exporter, sample_parse_result, tmp_path):
        result_path = await exporter.export(sample_parse_result, tmp_path)
        with open(result_path, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        first = rows[0]
        assert first["reactions_total"] == "250"
        assert "\U0001f44d:150" in first["reactions_detail"]

    @pytest.mark.asyncio
    async def test_export_minimal_message(self, exporter, sample_parse_result, tmp_path):
        result_path = await exporter.export(sample_parse_result, tmp_path)
        with open(result_path, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        second = rows[1]
        assert second["text"] == "Simple message"
        assert second["media_type"] == ""
        assert second["reactions_total"] == "0"

    @pytest.mark.asyncio
    async def test_export_creates_directory(self, exporter, sample_parse_result, tmp_path):
        nested = tmp_path / "deep" / "path"
        result_path = await exporter.export(sample_parse_result, nested)
        assert result_path.exists()
