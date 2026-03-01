"""User info cache for sender enrichment."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class UserCache:
    """Cache resolved Telegram user info to avoid repeated API calls."""

    def __init__(self, cache_path: Path):
        self._path = cache_path
        self._cache: dict[str, dict[str, Any]] = {}
        self.load()

    def load(self) -> None:
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                if not isinstance(data, dict):
                    raise ValueError("Cache file is not a JSON object")
                self._cache = data
            except (json.JSONDecodeError, OSError, ValueError):
                logger.warning(
                    "Failed to load user cache from %s, starting fresh",
                    self._path,
                )
                self._cache = {}

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(self._cache, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def get(self, user_id: int) -> dict[str, Any] | None:
        return self._cache.get(str(user_id))

    def put(self, user_id: int, info: dict[str, Any]) -> None:
        info["cached_at"] = datetime.now(timezone.utc).isoformat()
        self._cache[str(user_id)] = info

    def get_missing(self, user_ids: set[int]) -> set[int]:
        """Return user IDs not in cache."""
        return {uid for uid in user_ids if str(uid) not in self._cache}
