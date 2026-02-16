"""Tests that verify all modules import correctly and architecture rules are followed."""

import ast
import importlib
from pathlib import Path

import pytest

SRC = Path(__file__).parent.parent.parent / "src" / "tg_harvest"


class TestModuleImports:
    """Verify all modules can be imported without errors."""

    @pytest.mark.parametrize(
        "module",
        [
            "tg_harvest",
            "tg_harvest.config",
            "tg_harvest.config.settings",
            "tg_harvest.config.constants",
            "tg_harvest.models",
            "tg_harvest.models.channel",
            "tg_harvest.models.message",
            "tg_harvest.models.media",
            "tg_harvest.models.reaction",
            "tg_harvest.models.parse_result",
            "tg_harvest.exporters",
            "tg_harvest.exporters.base",
            "tg_harvest.exporters.json_exporter",
            "tg_harvest.exporters.csv_exporter",
            "tg_harvest.exporters.xlsx_exporter",
            "tg_harvest.storage",
            "tg_harvest.storage.state",
            "tg_harvest.search",
            "tg_harvest.search.engine",
            "tg_harvest.analytics",
            "tg_harvest.analytics.stats",
            "tg_harvest.utils",
            "tg_harvest.utils.logging",
            "tg_harvest.utils.date_utils",
            "tg_harvest.cli",
            "tg_harvest.cli.app",
            "tg_harvest.cli.formatters",
            "tg_harvest.cli.commands.parse",
            "tg_harvest.cli.commands.auth",
            "tg_harvest.cli.commands.channels",
            "tg_harvest.cli.commands.search",
            "tg_harvest.cli.commands.web",
            "tg_harvest.client",
            "tg_harvest.client.session",
            "tg_harvest.client.rate_limiter",
            "tg_harvest.parsers",
            "tg_harvest.parsers.channel_parser",
            "tg_harvest.parsers.message_parser",
            "tg_harvest.parsers.media_parser",
        ],
    )
    def test_module_imports(self, module):
        """Every module in the project should import without errors."""
        importlib.import_module(module)


class TestTelethonIsolation:
    """Verify that Telethon is only imported in client/ and parsers/."""

    ALLOWED_DIRS = {"client", "parsers"}

    def _get_all_py_files(self):
        """Get all .py files in src/tg_harvest, excluding __pycache__."""
        return [p for p in SRC.rglob("*.py") if "__pycache__" not in str(p)]

    def _get_imports(self, filepath: Path) -> list[str]:
        """Extract all import module names from a Python file."""
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(filepath))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        return imports

    def _get_package_dir(self, filepath: Path) -> str | None:
        """Get the top-level package directory relative to tg_harvest/."""
        relative = filepath.relative_to(SRC)
        parts = relative.parts
        if len(parts) > 1:
            return parts[0]
        return None

    def test_telethon_only_in_allowed_dirs(self):
        """Telethon imports must only appear in client/ and parsers/."""
        violations = []
        for py_file in self._get_all_py_files():
            imports = self._get_imports(py_file)
            has_telethon = any(imp.startswith("telethon") for imp in imports)
            if has_telethon:
                pkg_dir = self._get_package_dir(py_file)
                if pkg_dir not in self.ALLOWED_DIRS:
                    violations.append(str(py_file.relative_to(SRC)))

        assert violations == [], (
            f"Telethon imported outside allowed dirs ({self.ALLOWED_DIRS}): {violations}"
        )


class TestExporterConsistency:
    """Verify exporter classes follow the expected interface."""

    def test_all_exporters_in_init(self):
        from tg_harvest.exporters import __all__

        assert "JsonExporter" in __all__
        assert "CsvExporter" in __all__
        assert "XlsxExporter" in __all__

    def test_exporters_inherit_base(self):
        from tg_harvest.exporters.base import BaseExporter
        from tg_harvest.exporters.csv_exporter import CsvExporter
        from tg_harvest.exporters.json_exporter import JsonExporter
        from tg_harvest.exporters.xlsx_exporter import XlsxExporter

        assert issubclass(CsvExporter, BaseExporter)
        assert issubclass(JsonExporter, BaseExporter)
        assert issubclass(XlsxExporter, BaseExporter)

    def test_exporters_accept_fields(self):
        from tg_harvest.exporters.csv_exporter import CsvExporter
        from tg_harvest.exporters.json_exporter import JsonExporter
        from tg_harvest.exporters.xlsx_exporter import XlsxExporter

        fields = ["id", "text", "date"]
        csv_exp = CsvExporter(fields=fields)
        json_exp = JsonExporter(fields=fields)
        xlsx_exp = XlsxExporter(fields=fields)

        assert csv_exp.fields == fields
        assert json_exp.fields == fields
        assert xlsx_exp.fields == fields

    def test_exporters_default_all_fields(self):
        from tg_harvest.config.constants import ALL_EXPORT_FIELDS
        from tg_harvest.exporters.csv_exporter import CsvExporter
        from tg_harvest.exporters.json_exporter import JsonExporter
        from tg_harvest.exporters.xlsx_exporter import XlsxExporter

        all_fields = list(ALL_EXPORT_FIELDS)
        assert CsvExporter().fields == all_fields
        assert JsonExporter().fields == all_fields
        assert XlsxExporter().fields == all_fields


class TestModelConsistency:
    """Verify Pydantic models are properly defined."""

    def test_all_models_in_init(self):
        from tg_harvest.models import __all__

        expected = [
            "ChannelInfo",
            "ForwardInfo",
            "MediaInfo",
            "MediaType",
            "ParsedMessage",
            "ParseResult",
            "ReactionCount",
            "ReactionsInfo",
            "ReplyInfo",
        ]
        for name in expected:
            assert name in __all__, f"Missing from models __all__: {name}"

    def test_models_are_pydantic(self):
        from pydantic import BaseModel

        from tg_harvest.models.channel import ChannelInfo
        from tg_harvest.models.media import MediaInfo
        from tg_harvest.models.message import ForwardInfo, ParsedMessage, ReplyInfo
        from tg_harvest.models.parse_result import ParseResult
        from tg_harvest.models.reaction import ReactionCount, ReactionsInfo

        for model in [
            ChannelInfo,
            MediaInfo,
            ParsedMessage,
            ForwardInfo,
            ReplyInfo,
            ParseResult,
            ReactionCount,
            ReactionsInfo,
        ]:
            assert issubclass(model, BaseModel), f"{model.__name__} is not a Pydantic model"

    def test_models_no_telethon_imports(self):
        """Models package must not import Telethon (pure data layer)."""
        models_dir = SRC / "models"
        for py_file in models_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            source = py_file.read_text(encoding="utf-8")
            assert "telethon" not in source.lower(), (
                f"Telethon import found in models: {py_file.name}"
            )


class TestCLIStructure:
    """Verify CLI commands are properly registered."""

    def test_cli_has_all_commands(self):
        from tg_harvest.cli.app import cli

        command_names = list(cli.commands.keys())
        assert "auth" in command_names
        assert "channels" in command_names
        assert "parse" in command_names
        assert "search" in command_names
        assert "web" in command_names

    def test_cli_version(self):
        from click.testing import CliRunner

        import tg_harvest
        from tg_harvest.cli.app import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert tg_harvest.__version__ in result.output

    def test_cli_help(self):
        from click.testing import CliRunner

        from tg_harvest.cli.app import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Telegram" in result.output

    def test_parse_help(self):
        from click.testing import CliRunner

        from tg_harvest.cli.app import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["parse", "--help"])
        assert result.exit_code == 0
        assert "--format" in result.output
        assert "--fields" in result.output
        assert "--incremental" in result.output

    def test_search_help(self):
        from click.testing import CliRunner

        from tg_harvest.cli.app import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["search", "--help"])
        assert result.exit_code == 0

    def test_channels_list_help(self):
        from click.testing import CliRunner

        from tg_harvest.cli.app import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["channels", "list", "--help"])
        assert result.exit_code == 0
        assert "--limit" in result.output


class TestConstantsConsistency:
    """Verify constants are consistent with actual usage."""

    def test_supported_formats(self):
        from tg_harvest.config.constants import SUPPORTED_FORMATS

        assert "json" in SUPPORTED_FORMATS
        assert "csv" in SUPPORTED_FORMATS
        assert "xlsx" in SUPPORTED_FORMATS
        assert "all" in SUPPORTED_FORMATS

    def test_all_export_fields_match_build_row(self):
        """ALL_EXPORT_FIELDS must match the keys produced by build_row()."""
        from tg_harvest.config.constants import ALL_EXPORT_FIELDS
        from tg_harvest.exporters.base import build_row
        from tg_harvest.models.message import ParsedMessage

        msg = ParsedMessage(
            id=1,
            channel_id=123,
            date="2024-01-01T00:00:00+00:00",
            text="test",
        )
        row_keys = set(build_row(msg).keys())
        assert row_keys == set(ALL_EXPORT_FIELDS), (
            f"Mismatch: build_row keys={row_keys}, ALL_EXPORT_FIELDS={set(ALL_EXPORT_FIELDS)}"
        )

    def test_default_web_port(self):
        from tg_harvest.config.constants import DEFAULT_WEB_PORT

        assert DEFAULT_WEB_PORT == 8777
