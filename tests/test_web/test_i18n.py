"""Tests for i18n locale file consistency."""

import json
from pathlib import Path

LOCALES_DIR = (
    Path(__file__).resolve().parent.parent.parent / "src" / "tg_harvest" / "web" / "locales"
)


class TestLocaleConsistency:
    def _load(self, lang: str) -> dict:
        path = LOCALES_DIR / f"{lang}.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def test_en_and_uk_have_same_keys(self):
        en = self._load("en")
        uk = self._load("uk")
        en_keys = set(en.keys())
        uk_keys = set(uk.keys())

        missing_in_uk = en_keys - uk_keys
        missing_in_en = uk_keys - en_keys

        assert not missing_in_uk, f"Keys in EN but missing in UK: {missing_in_uk}"
        assert not missing_in_en, f"Keys in UK but missing in EN: {missing_in_en}"

    def test_no_empty_values_in_en(self):
        en = self._load("en")
        empty = [k for k, v in en.items() if not v.strip()]
        assert not empty, f"Empty values in EN: {empty}"

    def test_no_empty_values_in_uk(self):
        uk = self._load("uk")
        empty = [k for k, v in uk.items() if not v.strip()]
        assert not empty, f"Empty values in UK: {empty}"

    def test_valid_json_format(self):
        """Both files should be valid JSON."""
        for lang in ("en", "uk"):
            path = LOCALES_DIR / f"{lang}.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            assert isinstance(data, dict)
            assert len(data) > 0
