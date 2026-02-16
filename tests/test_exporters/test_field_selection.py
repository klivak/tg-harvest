"""Tests for field selection and shared exporter utilities."""

import csv
import json

import pytest

from tg_harvest.config.constants import ALL_EXPORT_FIELDS
from tg_harvest.exporters.base import build_row, filter_fields, resolve_fields
from tg_harvest.exporters.csv_exporter import CsvExporter
from tg_harvest.exporters.json_exporter import JsonExporter


class TestBuildRow:
    def test_build_row_all_fields(self, sample_message):
        row = build_row(sample_message)
        assert row["id"] == 1
        assert row["text"] == "Hello world! Check https://example.com"
        assert row["views"] == 10000
        assert row["is_pinned"] is True
        assert row["media_type"] == "photo"
        assert row["reactions_total"] == 250
        assert "\U0001f44d:150" in row["reactions_detail"]

    def test_build_row_minimal_message(self, sample_message_minimal):
        row = build_row(sample_message_minimal)
        assert row["id"] == 2
        assert row["text"] == "Simple message"
        assert row["media_type"] == ""
        assert row["reactions_total"] == 0
        assert row["reactions_detail"] == ""
        assert row["forward_from_id"] == ""

    def test_build_row_has_all_fields(self, sample_message):
        row = build_row(sample_message)
        for field in ALL_EXPORT_FIELDS:
            assert field in row, f"Missing field: {field}"


class TestFilterFields:
    def test_filter_none_returns_all(self):
        row = {"a": 1, "b": 2, "c": 3}
        assert filter_fields(row, None) == row

    def test_filter_specific_fields(self):
        row = {"a": 1, "b": 2, "c": 3}
        assert filter_fields(row, ["a", "c"]) == {"a": 1, "c": 3}

    def test_filter_empty_list(self):
        row = {"a": 1, "b": 2}
        assert filter_fields(row, []) == {}

    def test_filter_nonexistent_field(self):
        row = {"a": 1, "b": 2}
        assert filter_fields(row, ["a", "x"]) == {"a": 1}


class TestResolveFields:
    def test_none_returns_all_fields(self):
        result = resolve_fields(None)
        assert result == list(ALL_EXPORT_FIELDS)

    def test_valid_fields(self):
        result = resolve_fields(["id", "text", "date"])
        assert result == ["id", "text", "date"]

    def test_invalid_fields_filtered(self):
        result = resolve_fields(["id", "nonexistent", "text"])
        assert result == ["id", "text"]

    def test_empty_list(self):
        result = resolve_fields([])
        assert result == []


class TestCsvFieldSelection:
    @pytest.mark.asyncio
    async def test_csv_with_selected_fields(self, sample_parse_result, tmp_path):
        exporter = CsvExporter(fields=["id", "text", "date"])
        result_path = await exporter.export(sample_parse_result, tmp_path)

        with open(result_path, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert set(rows[0].keys()) == {"id", "text", "date"}
        assert rows[0]["id"] == "1"
        assert rows[0]["text"] == "Hello world! Check https://example.com"

    @pytest.mark.asyncio
    async def test_csv_default_all_fields(self, sample_parse_result, tmp_path):
        exporter = CsvExporter()
        result_path = await exporter.export(sample_parse_result, tmp_path)

        with open(result_path, encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            header = next(reader)

        assert len(header) == len(ALL_EXPORT_FIELDS)


class TestJsonFieldSelection:
    @pytest.mark.asyncio
    async def test_json_with_selected_fields(self, sample_parse_result, tmp_path):
        exporter = JsonExporter(fields=["id", "text", "views"])
        result_path = await exporter.export(sample_parse_result, tmp_path)

        with open(result_path, encoding="utf-8") as f:
            data = json.load(f)

        msg = data["messages"][0]
        assert set(msg.keys()) == {"id", "text", "views"}
        assert msg["id"] == 1
        assert msg["text"] == "Hello world! Check https://example.com"

    @pytest.mark.asyncio
    async def test_json_default_full_structure(self, sample_parse_result, tmp_path):
        exporter = JsonExporter()
        result_path = await exporter.export(sample_parse_result, tmp_path)

        with open(result_path, encoding="utf-8") as f:
            data = json.load(f)

        # Full export preserves nested structure
        msg = data["messages"][0]
        assert "media" in msg
        assert "reactions" in msg
        assert isinstance(msg["media"], dict)
