"""Tests for CLI app structure."""

from click.testing import CliRunner

from tg_harvest import __version__
from tg_harvest.cli.app import cli


class TestCliApp:
    def setup_method(self):
        self.runner = CliRunner()

    def test_version(self):
        result = self.runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.output
        assert "tg-harvest" in result.output

    def test_help(self):
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Telegram" in result.output
        assert "harvester" in result.output

    def test_commands_registered(self):
        result = self.runner.invoke(cli, ["--help"])
        assert "auth" in result.output
        assert "channels" in result.output
        assert "parse" in result.output
        assert "search" in result.output
        assert "web" in result.output

    def test_verbose_flag(self):
        result = self.runner.invoke(cli, ["--help"])
        assert "--verbose" in result.output
        assert "-v" in result.output

    def test_auth_subcommands(self):
        result = self.runner.invoke(cli, ["auth", "--help"])
        assert result.exit_code == 0
        assert "login" in result.output
        assert "status" in result.output
        assert "logout" in result.output

    def test_channels_subcommands(self):
        result = self.runner.invoke(cli, ["channels", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output

    def test_parse_help(self):
        result = self.runner.invoke(cli, ["parse", "--help"])
        assert result.exit_code == 0
        assert "CHANNEL" in result.output
        assert "--from-date" in result.output
        assert "--to-date" in result.output
        assert "--limit" in result.output
        assert "--format" in result.output
        assert "--output" in result.output
        assert "--fields" in result.output

    def test_search_help(self):
        result = self.runner.invoke(cli, ["search", "--help"])
        assert result.exit_code == 0
        assert "QUERY" in result.output
        assert "--channel" in result.output
        assert "--media-type" in result.output
        assert "--min-views" in result.output

    def test_web_help(self):
        result = self.runner.invoke(cli, ["web", "--help"])
        assert result.exit_code == 0
        assert "--port" in result.output
