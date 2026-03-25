"""Tests for CLI formatters."""

from io import StringIO
from unittest.mock import patch

from rich.console import Console

from tg_harvest.cli.formatters import print_channel_table, print_parse_summary, print_queue_summary
from tg_harvest.models.channel import ChannelInfo
from tg_harvest.models.parse_result import ParseResult


class TestPrintChannelTable:
    def _capture(self, channels: list[ChannelInfo]) -> str:
        buf = StringIO()
        with patch("tg_harvest.cli.formatters.console", Console(file=buf, width=200)):
            print_channel_table(channels)
        return buf.getvalue()

    def test_empty_list(self):
        output = self._capture([])
        assert "Accessible Channels & Groups" in output

    def test_single_channel(self, sample_channel_info):
        output = self._capture([sample_channel_info])
        assert "Test Channel" in output
        assert "@test_channel" in output
        assert "Channel" in output
        assert "5000" in output

    def test_group_type(self):
        group = ChannelInfo(
            id=1, title="Test Group", is_channel=False, is_group=True, is_private=False
        )
        output = self._capture([group])
        assert "Group" in output

    def test_private_channel_shows_private(self):
        ch = ChannelInfo(id=1, title="Private", is_channel=True, is_private=True)
        output = self._capture([ch])
        assert "private" in output

    def test_restricted_channel(self):
        ch = ChannelInfo(id=1, title="Restricted", restricted=True)
        output = self._capture([ch])
        assert "Yes" in output

    def test_no_members_shows_dash(self):
        ch = ChannelInfo(id=1, title="NoMembers", members_count=None)
        output = self._capture([ch])
        assert "-" in output

    def test_multiple_channels(self):
        channels = [ChannelInfo(id=i, title=f"Channel {i}", username=f"ch{i}") for i in range(5)]
        output = self._capture(channels)
        for i in range(5):
            assert f"Channel {i}" in output


class TestPrintParseSummary:
    def _capture(self, result: ParseResult, files: list[str]) -> str:
        buf = StringIO()
        with patch("tg_harvest.cli.formatters.console", Console(file=buf, width=200)):
            print_parse_summary(result, files)
        return buf.getvalue()

    def test_basic_summary(self, sample_parse_result):
        output = self._capture(sample_parse_result, ["output/test.json"])
        assert "Test Channel" in output
        assert "2" in output  # total messages
        assert "output/test.json" in output
        assert "Parse Complete" in output

    def test_date_range_shown(self, sample_parse_result):
        output = self._capture(sample_parse_result, [])
        assert "2024-01-01" in output
        assert "2024-12-31" in output

    def test_multiple_output_files(self, sample_parse_result):
        files = ["out/test.json", "out/test.csv", "out/test.xlsx"]
        output = self._capture(sample_parse_result, files)
        for f in files:
            assert f in output

    def test_no_dates(self, sample_channel_info, sample_message):
        from datetime import datetime, timezone

        result = ParseResult(
            channel=sample_channel_info,
            messages=[sample_message],
            parsed_at=datetime(2024, 6, 15, 14, 0, 0, tzinfo=timezone.utc),
        )
        output = self._capture(result, ["test.json"])
        assert "Test Channel" in output
        assert "1" in output

    def test_oldest_newest_messages(self, sample_parse_result):
        output = self._capture(sample_parse_result, [])
        assert "Oldest message" in output
        assert "Newest message" in output


class TestPrintQueueSummary:
    def _capture(self, results, errors) -> str:
        buf = StringIO()
        with patch("tg_harvest.cli.formatters.console", Console(file=buf, width=200)):
            print_queue_summary(results, errors)
        return buf.getvalue()

    def test_all_success(self, sample_parse_result):
        results = [
            ("@chan1", sample_parse_result, ["f1.json"]),
            ("@chan2", sample_parse_result, ["f2.json"]),
        ]
        output = self._capture(results, [])
        assert "Queue Complete" in output
        assert "OK" in output
        assert "2 succeeded" in output
        assert "0 failed" in output

    def test_with_errors(self, sample_parse_result):
        results = [("@chan1", sample_parse_result, ["f1.json"])]
        errors = [("@chan2", "Not found")]
        output = self._capture(results, errors)
        assert "FAIL" in output
        assert "1 succeeded" in output
        assert "1 failed" in output

    def test_all_errors(self):
        errors = [("@c1", "err1"), ("@c2", "err2")]
        output = self._capture([], errors)
        assert "0 succeeded" in output
        assert "2 failed" in output
