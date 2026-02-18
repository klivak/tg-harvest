"""Tests for settings."""

from pathlib import Path

from tg_harvest.config.settings import Settings


class TestSettings:
    def test_settings_from_env(self, monkeypatch):
        monkeypatch.setenv("TG_API_ID", "12345")
        monkeypatch.setenv("TG_API_HASH", "abc123hash")
        monkeypatch.setenv("TG_PHONE", "+380123456789")

        settings = Settings()
        assert settings.api_id == 12345
        assert settings.api_hash == "abc123hash"
        assert settings.phone == "+380123456789"

    def test_default_values(self, monkeypatch):
        monkeypatch.setenv("TG_API_ID", "1")
        monkeypatch.setenv("TG_API_HASH", "hash")
        monkeypatch.setenv("TG_PHONE", "+1")

        settings = Settings()
        assert settings.session_name == "tg_harvest"
        assert settings.flood_sleep_threshold == 60
        assert settings.request_delay == 1.0
        assert settings.output_dir == Path("./output")

    def test_custom_values(self, monkeypatch):
        monkeypatch.setenv("TG_API_ID", "1")
        monkeypatch.setenv("TG_API_HASH", "hash")
        monkeypatch.setenv("TG_PHONE", "+1")
        monkeypatch.setenv("TG_SESSION_NAME", "my_session")
        monkeypatch.setenv("TG_FLOOD_SLEEP_THRESHOLD", "30")
        monkeypatch.setenv("TG_REQUEST_DELAY", "2.5")
        monkeypatch.setenv("TG_OUTPUT_DIR", "./custom_output")

        settings = Settings()
        assert settings.session_name == "my_session"
        assert settings.flood_sleep_threshold == 30
        assert settings.request_delay == 2.5
        assert settings.output_dir == Path("./custom_output")

    def test_session_path(self, monkeypatch):
        monkeypatch.setenv("TG_API_ID", "1")
        monkeypatch.setenv("TG_API_HASH", "hash")
        monkeypatch.setenv("TG_PHONE", "+1")
        monkeypatch.setenv("TG_SESSION_NAME", "test_sess")

        settings = Settings()
        assert settings.session_path == Path("./sessions/test_sess")

    def test_missing_fields_default_to_none(self, monkeypatch):
        monkeypatch.delenv("TG_API_ID", raising=False)
        monkeypatch.delenv("TG_API_HASH", raising=False)
        monkeypatch.delenv("TG_PHONE", raising=False)

        settings = Settings(_env_file=None)
        assert settings.api_id is None
        assert settings.api_hash is None
        assert settings.phone is None
