"""Tests for JSON exporter."""

import json

import pytest

from tg_harvest.exporters.json_exporter import JsonExporter


class TestJsonExporter:
    @pytest.fixture
    def exporter(self):
        return JsonExporter()

    @pytest.mark.asyncio
    async def test_export_creates_file(self, exporter, sample_parse_result, tmp_path):
        result_path = await exporter.export(sample_parse_result, tmp_path)
        assert result_path.exists()
        assert result_path.suffix == ".json"

    @pytest.mark.asyncio
    async def test_export_filename_format(self, exporter, sample_parse_result, tmp_path):
        result_path = await exporter.export(sample_parse_result, tmp_path)
        assert "test_channel" in result_path.name
        assert result_path.name.endswith(".json")

    @pytest.mark.asyncio
    async def test_export_valid_json(self, exporter, sample_parse_result, tmp_path):
        result_path = await exporter.export(sample_parse_result, tmp_path)
        with open(result_path, encoding="utf-8") as f:
            data = json.load(f)

        assert "channel" in data
        assert "messages" in data
        assert "total_messages" in data
        assert "parsed_at" in data

    @pytest.mark.asyncio
    async def test_export_message_count(self, exporter, sample_parse_result, tmp_path):
        result_path = await exporter.export(sample_parse_result, tmp_path)
        with open(result_path, encoding="utf-8") as f:
            data = json.load(f)

        assert data["total_messages"] == 2
        assert len(data["messages"]) == 2

    @pytest.mark.asyncio
    async def test_export_channel_info(self, exporter, sample_parse_result, tmp_path):
        result_path = await exporter.export(sample_parse_result, tmp_path)
        with open(result_path, encoding="utf-8") as f:
            data = json.load(f)

        ch = data["channel"]
        assert ch["id"] == 1234567890
        assert ch["title"] == "Test Channel"
        assert ch["username"] == "test_channel"

    @pytest.mark.asyncio
    async def test_export_message_fields(self, exporter, sample_parse_result, tmp_path):
        result_path = await exporter.export(sample_parse_result, tmp_path)
        with open(result_path, encoding="utf-8") as f:
            data = json.load(f)

        msg = data["messages"][0]
        assert msg["id"] == 1
        assert msg["text"] == "Hello world! Check https://example.com"
        assert msg["views"] == 10000
        assert msg["is_pinned"] is True
        assert msg["media"]["type"] == "photo"
        assert msg["reactions"]["total"] == 250

    @pytest.mark.asyncio
    async def test_export_creates_directory(self, exporter, sample_parse_result, tmp_path):
        nested = tmp_path / "sub" / "dir"
        result_path = await exporter.export(sample_parse_result, nested)
        assert result_path.exists()
        assert nested.exists()

    @pytest.mark.asyncio
    async def test_export_utf8_content(self, exporter, sample_parse_result, tmp_path):
        sample_parse_result.messages[0].text = "Привіт світ! \U0001f44d"
        result_path = await exporter.export(sample_parse_result, tmp_path)
        with open(result_path, encoding="utf-8") as f:
            content = f.read()
        assert "Привіт світ!" in content
        assert "\U0001f44d" in content
