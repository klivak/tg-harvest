"""Tests that verify project structure, configuration, and organization."""

from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent
SRC = ROOT / "src" / "tg_harvest"


class TestProjectFiles:
    """Verify all required project files exist."""

    @pytest.mark.parametrize(
        "filepath",
        [
            "pyproject.toml",
            "README.md",
            "CHANGELOG.md",
            "CLAUDE.md",
            "LICENSE",
            ".gitignore",
            ".env.example",
            ".pre-commit-config.yaml",
            ".github/workflows/ci.yml",
        ],
    )
    def test_root_file_exists(self, filepath):
        assert (ROOT / filepath).exists(), f"Missing: {filepath}"

    @pytest.mark.parametrize(
        "directory",
        [
            "config",
            "models",
            "client",
            "parsers",
            "exporters",
            "storage",
            "search",
            "analytics",
            "cli",
            "cli/commands",
            "web",
            "web/views",
            "utils",
        ],
    )
    def test_package_has_init(self, directory):
        init_file = SRC / directory / "__init__.py"
        assert init_file.exists(), f"Missing __init__.py in {directory}"

    def test_output_dir_has_gitkeep(self):
        assert (ROOT / "output" / ".gitkeep").exists()

    def test_sessions_dir_has_gitkeep(self):
        assert (ROOT / "sessions" / ".gitkeep").exists()


class TestPyprojectToml:
    """Verify pyproject.toml is properly configured."""

    @pytest.fixture
    def pyproject_text(self):
        return (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    def test_has_name(self, pyproject_text):
        assert 'name = "tg-harvest"' in pyproject_text

    def test_has_version(self, pyproject_text):
        assert "version =" in pyproject_text

    def test_requires_python_311(self, pyproject_text):
        assert ">=3.11" in pyproject_text

    def test_has_cli_script(self, pyproject_text):
        assert 'tg-harvest = "tg_harvest.cli.app:cli"' in pyproject_text

    def test_has_web_script(self, pyproject_text):
        assert 'tg-harvest-web = "tg_harvest.web.app:main"' in pyproject_text

    def test_has_src_layout(self, pyproject_text):
        assert 'where = ["src"]' in pyproject_text

    @pytest.mark.parametrize(
        "dep",
        [
            "telethon",
            "pydantic",
            "pydantic-settings",
            "click",
            "rich",
            "aiofiles",
            "streamlit",
            "plotly",
            "openpyxl",
        ],
    )
    def test_has_dependency(self, pyproject_text, dep):
        assert dep in pyproject_text, f"Missing dependency: {dep}"

    @pytest.mark.parametrize("dep", ["pytest", "pytest-asyncio", "ruff"])
    def test_has_dev_dependency(self, pyproject_text, dep):
        assert dep in pyproject_text, f"Missing dev dependency: {dep}"

    def test_ruff_config(self, pyproject_text):
        assert "[tool.ruff]" in pyproject_text
        assert 'target-version = "py311"' in pyproject_text

    def test_pytest_config(self, pyproject_text):
        assert "[tool.pytest.ini_options]" in pyproject_text
        assert 'asyncio_mode = "auto"' in pyproject_text


class TestVersionConsistency:
    """Verify version is consistent across project."""

    def test_pyproject_and_init_version_match(self):
        import tg_harvest

        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        # Extract version from pyproject.toml
        for line in pyproject.splitlines():
            if line.startswith("version ="):
                pyproject_version = line.split('"')[1]
                break
        else:
            pytest.fail("No version in pyproject.toml")

        assert tg_harvest.__version__ == pyproject_version

    def test_changelog_has_current_version(self):
        import tg_harvest

        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        assert f"[{tg_harvest.__version__}]" in changelog


class TestGitignore:
    """Verify .gitignore covers necessary patterns."""

    @pytest.fixture
    def gitignore(self):
        return (ROOT / ".gitignore").read_text(encoding="utf-8")

    @pytest.mark.parametrize(
        "pattern",
        [
            "__pycache__/",
            "*.py[cod]",
            ".venv/",
            ".env",
            "*.session",
            "output/*",
            ".egg-info/",
        ],
    )
    def test_has_pattern(self, gitignore, pattern):
        assert pattern in gitignore, f"Missing .gitignore pattern: {pattern}"

    def test_env_example_not_ignored(self, gitignore):
        # .env is ignored but .env.example should NOT be
        assert ".env.example" not in gitignore


class TestEnvExample:
    """Verify .env.example has all required variables."""

    @pytest.fixture
    def env_example(self):
        return (ROOT / ".env.example").read_text(encoding="utf-8")

    @pytest.mark.parametrize(
        "var",
        ["TG_API_ID", "TG_API_HASH", "TG_PHONE"],
    )
    def test_has_required_var(self, env_example, var):
        assert var in env_example, f"Missing required var: {var}"

    @pytest.mark.parametrize(
        "var",
        [
            "TG_SESSION_NAME",
            "TG_FLOOD_SLEEP_THRESHOLD",
            "TG_REQUEST_DELAY",
            "TG_OUTPUT_DIR",
            "TG_WEB_PORT",
        ],
    )
    def test_has_optional_var(self, env_example, var):
        assert var in env_example, f"Missing optional var: {var}"


class TestCIConfig:
    """Verify GitHub Actions CI is properly configured."""

    @pytest.fixture
    def ci_yaml(self):
        return (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    def test_triggers_on_push_main(self, ci_yaml):
        assert "push:" in ci_yaml
        assert "main" in ci_yaml

    def test_triggers_on_pr(self, ci_yaml):
        assert "pull_request:" in ci_yaml

    def test_uses_python_311(self, ci_yaml):
        assert "3.11" in ci_yaml

    def test_runs_ruff_check(self, ci_yaml):
        assert "ruff check" in ci_yaml

    def test_runs_ruff_format_check(self, ci_yaml):
        assert "ruff format --check" in ci_yaml

    def test_runs_pytest(self, ci_yaml):
        assert "pytest" in ci_yaml

    def test_installs_dev_deps(self, ci_yaml):
        assert '".[dev]"' in ci_yaml


class TestPreCommitConfig:
    """Verify pre-commit hooks are properly configured."""

    @pytest.fixture
    def precommit_yaml(self):
        return (ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")

    def test_has_ruff_hook(self, precommit_yaml):
        assert "ruff" in precommit_yaml

    def test_has_ruff_format_hook(self, precommit_yaml):
        assert "ruff-format" in precommit_yaml

    def test_has_trailing_whitespace(self, precommit_yaml):
        assert "trailing-whitespace" in precommit_yaml

    def test_has_end_of_file_fixer(self, precommit_yaml):
        assert "end-of-file-fixer" in precommit_yaml


class TestLicense:
    """Verify LICENSE file."""

    @pytest.fixture
    def license_text(self):
        return (ROOT / "LICENSE").read_text(encoding="utf-8")

    def test_is_mit(self, license_text):
        assert "MIT License" in license_text

    def test_has_permission_clause(self, license_text):
        assert "free of charge" in license_text

    def test_has_warranty_disclaimer(self, license_text):
        assert "WITHOUT WARRANTY" in license_text
