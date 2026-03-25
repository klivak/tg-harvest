"""Tests for multi-channel queue parsing in CLI."""

from click.testing import CliRunner

from tg_harvest.cli.commands.parse import parse


class TestParseMultiChannel:
    """Test multi-channel CLI argument handling (no network needed)."""

    def setup_method(self):
        self.runner = CliRunner()

    def test_help_shows_channels_argument(self):
        result = self.runner.invoke(parse, ["--help"])
        assert result.exit_code == 0
        assert "CHANNELS" in result.output

    def test_no_channel_shows_error(self):
        result = self.runner.invoke(parse, [])
        assert result.exit_code != 0

    def test_single_channel_accepted(self):
        # Should pass argument validation (fails at network level)
        result = self.runner.invoke(parse, ["@test"])
        assert "Unknown fields" not in (result.output or "")

    def test_multiple_channels_accepted(self):
        # Should pass argument validation (fails at network level)
        result = self.runner.invoke(parse, ["@chan1", "@chan2", "@chan3"])
        assert "Unknown fields" not in (result.output or "")

    def test_multiple_channels_with_options(self):
        result = self.runner.invoke(
            parse,
            ["@chan1", "@chan2", "--format", "json", "--limit", "100"],
        )
        # Should not fail on argument parsing
        assert "Unknown fields" not in (result.output or "")
        assert "no such option" not in (result.output or "").lower()

    def test_multiple_channels_with_fields(self):
        result = self.runner.invoke(
            parse,
            ["@chan1", "@chan2", "--fields", "id,text,date"],
        )
        assert "Unknown fields" not in (result.output or "")

    def test_multiple_channels_invalid_fields_still_rejected(self):
        result = self.runner.invoke(
            parse,
            ["@chan1", "@chan2", "--fields", "bad_field"],
        )
        assert result.exit_code != 0
        assert "Unknown fields" in result.output
