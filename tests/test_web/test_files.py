"""Tests for web files page helper functions."""

import json

from tg_harvest.web.views.files import _format_size, _scan_files


class TestScanFiles:
    def test_scan_files_empty_dir(self, tmp_path):
        result = _scan_files(tmp_path)
        assert result == []

    def test_scan_files_with_json(self, tmp_path):
        data = {
            "channel": {"id": 1, "title": "My Test Channel"},
            "messages": [],
            "parsed_at": "2024-06-15T14:00:00+00:00",
            "total_messages": 0,
        }
        json_file = tmp_path / "my_test_channel_20240615_140000.json"
        json_file.write_text(json.dumps(data), encoding="utf-8")

        result = _scan_files(tmp_path)
        assert len(result) == 1
        assert result[0]["channel_title"] == "My Test Channel"
        assert result[0]["ext"] == ".json"

    def test_scan_files_with_multiple_formats(self, tmp_path):
        data = {
            "channel": {"id": 1, "title": "Multi Format"},
            "messages": [],
            "parsed_at": "2024-06-15T14:00:00+00:00",
            "total_messages": 0,
        }
        (tmp_path / "data.json").write_text(json.dumps(data), encoding="utf-8")
        (tmp_path / "data.csv").write_text("id,text\n1,hello\n", encoding="utf-8")
        (tmp_path / "data.xlsx").write_bytes(b"PK\x03\x04")  # minimal xlsx-like bytes

        result = _scan_files(tmp_path)
        exts = {f["ext"] for f in result}
        assert ".json" in exts
        assert ".csv" in exts
        assert ".xlsx" in exts

    def test_scan_files_invalid_json(self, tmp_path):
        bad_json = tmp_path / "corrupt.json"
        bad_json.write_text("not valid json {{{{", encoding="utf-8")

        result = _scan_files(tmp_path)
        assert len(result) == 1
        assert result[0]["channel_title"] == ""

    def test_scan_files_invalid_json_no_crash(self, tmp_path):
        bad_json = tmp_path / "corrupt.json"
        bad_json.write_text("not valid json {{{{", encoding="utf-8")

        # Must not raise any exception
        result = _scan_files(tmp_path)
        assert isinstance(result, list)


class TestFormatSize:
    def test_format_size_bytes(self):
        assert _format_size(500) == "500 B"

    def test_format_size_zero(self):
        assert _format_size(0) == "0 B"

    def test_format_size_1023_bytes(self):
        assert _format_size(1023) == "1023 B"

    def test_format_size_kb(self):
        assert "KB" in _format_size(2048)

    def test_format_size_exact_kb(self):
        result = _format_size(1024)
        assert "KB" in result
        assert "1.0" in result

    def test_format_size_mb(self):
        assert "MB" in _format_size(2 * 1024 * 1024)

    def test_format_size_exact_mb(self):
        result = _format_size(1024 * 1024)
        assert "MB" in result
        assert "1.0" in result
