"""Shared helpers for web UI pages."""


def truncate(text: str | None, limit: int = 100) -> str:
    """Truncate text to *limit* characters, appending ellipsis if needed."""
    if not text:
        return ""
    return (text[:limit] + "...") if len(text) > limit else text
