"""Tests for HTML exporter."""

from datetime import datetime, timezone

import pytest

from tg_harvest.exporters.html_exporter import HtmlExporter
from tg_harvest.models.channel import ChannelInfo
from tg_harvest.models.message import ParsedMessage
from tg_harvest.models.parse_result import ParseResult


class TestHtmlExporter:
    @pytest.fixture
    def exporter(self):
        return HtmlExporter()

    @pytest.mark.asyncio
    async def test_export_creates_file(self, exporter, sample_parse_result, tmp_path):
        result_path = await exporter.export(sample_parse_result, tmp_path)
        assert result_path.exists()
        assert result_path.suffix == ".html"

    @pytest.mark.asyncio
    async def test_export_filename_format(self, exporter, sample_parse_result, tmp_path):
        result_path = await exporter.export(sample_parse_result, tmp_path)
        assert "test_channel" in result_path.name

    @pytest.mark.asyncio
    async def test_export_contains_channel_title(self, exporter, sample_parse_result, tmp_path):
        result_path = await exporter.export(sample_parse_result, tmp_path)
        content = result_path.read_text(encoding="utf-8")
        assert "Test Channel" in content

    @pytest.mark.asyncio
    async def test_export_contains_message_data(self, exporter, sample_parse_result, tmp_path):
        result_path = await exporter.export(sample_parse_result, tmp_path)
        content = result_path.read_text(encoding="utf-8")
        assert "Hello world" in content
        assert "10000" in content

    @pytest.mark.asyncio
    async def test_export_is_self_contained(self, exporter, sample_parse_result, tmp_path):
        result_path = await exporter.export(sample_parse_result, tmp_path)
        content = result_path.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content
        assert "<style>" in content
        assert "<script>" in content

    @pytest.mark.asyncio
    async def test_export_has_theme_toggle(self, exporter, sample_parse_result, tmp_path):
        result_path = await exporter.export(sample_parse_result, tmp_path)
        content = result_path.read_text(encoding="utf-8")
        assert "theme" in content

    @pytest.mark.asyncio
    async def test_export_with_field_selection(self, sample_parse_result, tmp_path):
        exporter = HtmlExporter(fields=["id", "text", "date"])
        result_path = await exporter.export(sample_parse_result, tmp_path)
        assert result_path.exists()
        content = result_path.read_text(encoding="utf-8")
        assert "<th>id</th>" in content
        assert "<th>text</th>" in content
        assert "<th>date</th>" in content
        assert "<th>views</th>" not in content

    @pytest.mark.asyncio
    async def test_export_escapes_html(self, tmp_path):
        channel = ChannelInfo(id=1, title="Escape Test")
        msg = ParsedMessage(
            id=1,
            channel_id=1,
            date=datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
            text="<script>alert(1)</script>",
        )
        result = ParseResult(
            channel=channel,
            messages=[msg],
            parsed_at=datetime(2024, 6, 15, 14, 0, 0, tzinfo=timezone.utc),
        )
        exporter = HtmlExporter()
        result_path = await exporter.export(result, tmp_path)
        content = result_path.read_text(encoding="utf-8")
        assert "<script>alert(1)</script>" not in content
        assert "&lt;script&gt;" in content

    @pytest.mark.asyncio
    async def test_export_creates_directory(self, exporter, sample_parse_result, tmp_path):
        nested = tmp_path / "deep" / "path"
        result_path = await exporter.export(sample_parse_result, nested)
        assert result_path.exists()

    @pytest.mark.asyncio
    async def test_empty_messages(self, tmp_path):
        channel = ChannelInfo(id=1, title="Empty Channel")
        result = ParseResult(
            channel=channel,
            messages=[],
            parsed_at=datetime(2024, 6, 15, 14, 0, 0, tzinfo=timezone.utc),
        )
        exporter = HtmlExporter()
        result_path = await exporter.export(result, tmp_path)
        assert result_path.exists()
        content = result_path.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content
        assert "Empty Channel" in content
