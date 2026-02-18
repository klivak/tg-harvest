"""Internationalization helper for TG Harvest web UI."""

import json
from pathlib import Path
from typing import Any

import streamlit as st

LANGUAGES: dict[str, str] = {
    "English": "en",
    "Українська": "uk",
}

_cache: dict[str, dict[str, str]] = {}


def _load(lang: str) -> dict[str, str]:
    """Load and cache locale JSON for a given language code."""
    if lang not in _cache:
        path = Path(__file__).parent / "locales" / f"{lang}.json"
        _cache[lang] = json.loads(path.read_text(encoding="utf-8"))
    return _cache[lang]


def get_lang() -> str:
    """Return the active language code ('en' or 'uk')."""
    return st.session_state.get("lang", "en")


def t(key: str, **kwargs: Any) -> str:
    """Translate a key into the active language.

    Falls back to English, then to the raw key if neither has it.
    Supports keyword-argument interpolation via str.format().

    Example:
        t("auth.success", name="Alice")
        t("parser.error_flood", seconds=30)
    """
    lang = get_lang()
    text = _load(lang).get(key) or _load("en").get(key) or key
    return text.format(**kwargs) if kwargs else text
