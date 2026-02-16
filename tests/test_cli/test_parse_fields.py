"""Tests for parse command --fields validation."""

from click.testing import CliRunner

from tg_harvest.cli.commands.parse import parse
from tg_harvest.config.constants import ALL_EXPORT_FIELDS


class TestParseFieldsValidation:
    """Test --fields option validation (no network needed)."""

    def setup_method(self):
        self.runner = CliRunner()

    def test_invalid_field_rejected(self):
        result = self.runner.invoke(parse, ["@test", "--fields", "nonexistent_field"])
        assert result.exit_code != 0
        assert "Unknown fields" in result.output

    def test_multiple_invalid_fields(self):
        result = self.runner.invoke(parse, ["@test", "--fields", "bad1,bad2,bad3"])
        assert result.exit_code != 0
        assert "bad1" in result.output
        assert "bad2" in result.output

    def test_mixed_valid_invalid_fields(self):
        result = self.runner.invoke(parse, ["@test", "--fields", "id,text,fake_field"])
        assert result.exit_code != 0
        assert "fake_field" in result.output

    def test_valid_fields_pass_validation(self):
        # This will fail at network level but NOT at field validation
        result = self.runner.invoke(parse, ["@test", "--fields", "id,text,date"])
        # Should not contain field validation error
        assert "Unknown fields" not in (result.output or "")

    def test_all_fields_valid(self):
        fields_str = ",".join(ALL_EXPORT_FIELDS)
        result = self.runner.invoke(parse, ["@test", "--fields", fields_str])
        assert "Unknown fields" not in (result.output or "")

    def test_help_shows_available_fields(self):
        result = self.runner.invoke(parse, ["--help"])
        assert result.exit_code == 0
        assert "--fields" in result.output
        assert "id" in result.output

    def test_format_option_choices(self):
        result = self.runner.invoke(parse, ["--help"])
        assert "json" in result.output
        assert "csv" in result.output
        assert "xlsx" in result.output
        assert "all" in result.output

    def test_invalid_format_rejected(self):
        result = self.runner.invoke(parse, ["@test", "--format", "xml"])
        assert result.exit_code != 0

    def test_incremental_flag(self):
        result = self.runner.invoke(parse, ["--help"])
        assert "--incremental" in result.output
        assert "-i" in result.output
