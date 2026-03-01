"""Tests for CLI export command."""

import json
from datetime import datetime, timezone

from click.testing import CliRunner

from tg_harvest.cli.app import cli
from tg_harvest.models.channel import ChannelInfo
from tg_harvest.models.message import ParsedMessage
from tg_harvest.models.parse_result import ParseResult


def _make_parse_result_json() -> str:
    """Create a minimal valid ParseResult JSON string."""
    channel = ChannelInfo(id=1234567890, title="Test Channel", username="test_channel")
    messages = [
        ParsedMessage(
            id=1,
            channel_id=1234567890,
            date=datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
            text="Hello export world",
            views=500,
        ),
        ParsedMessage(
            id=2,
            channel_id=1234567890,
            date=datetime(2024, 6, 16, 10, 0, 0, tzinfo=timezone.utc),
            text="Second message",
        ),
    ]
    result = ParseResult(
        channel=channel,
        messages=messages,
        parsed_at=datetime(2024, 6, 17, 0, 0, 0, tzinfo=timezone.utc),
    )
    return json.dumps(result.model_dump(mode="json"))


class TestExportCommand:
    def setup_method(self):
        self.runner = CliRunner()

    def test_export_help(self):
        result = self.runner.invoke(cli, ["export", "--help"])
        assert result.exit_code == 0
        assert "--format" in result.output

    def test_export_registered(self):
        result = self.runner.invoke(cli, ["--help"])
        assert "export" in result.output

    def test_export_json_to_csv(self, tmp_path):
        json_path = tmp_path / "test_channel_20240617_000000.json"
        json_path.write_text(_make_parse_result_json(), encoding="utf-8")

        result = self.runner.invoke(
            cli,
            ["export", str(json_path), "--format", "csv"],
        )
        assert result.exit_code == 0
        csv_files = list(tmp_path.glob("*.csv"))
        assert len(csv_files) == 1

    def test_export_json_to_html(self, tmp_path):
        json_path = tmp_path / "test_channel_20240617_000000.json"
        json_path.write_text(_make_parse_result_json(), encoding="utf-8")

        result = self.runner.invoke(
            cli,
            ["export", str(json_path), "--format", "html"],
        )
        assert result.exit_code == 0
        html_files = list(tmp_path.glob("*.html"))
        assert len(html_files) == 1

    def test_export_with_fields(self, tmp_path):
        json_path = tmp_path / "test_channel_20240617_000000.json"
        json_path.write_text(_make_parse_result_json(), encoding="utf-8")

        result = self.runner.invoke(
            cli,
            ["export", str(json_path), "--format", "csv", "--fields", "id,text,date"],
        )
        assert result.exit_code == 0
        csv_files = list(tmp_path.glob("*.csv"))
        assert len(csv_files) == 1

    def test_export_invalid_fields(self, tmp_path):
        json_path = tmp_path / "test_channel_20240617_000000.json"
        json_path.write_text(_make_parse_result_json(), encoding="utf-8")

        result = self.runner.invoke(
            cli,
            ["export", str(json_path), "--format", "csv", "--fields", "nonexistent_field"],
        )
        assert result.exit_code != 0
        assert "nonexistent_field" in result.output
