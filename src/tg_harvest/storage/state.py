"""Incremental parsing state management."""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class StateManager:
    """Tracks the last parsed message ID per channel for incremental parsing."""

    def __init__(self, state_path: Path):
        self._path = state_path
        self._state: dict[str, int] = {}
        self.load()

    def load(self) -> None:
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                if not isinstance(data, dict):
                    raise ValueError("State file is not a JSON object")
                self._state = data
            except (json.JSONDecodeError, OSError, ValueError):
                logger.warning("Failed to load parse state from %s, starting fresh", self._path)
                self._state = {}

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(self._state, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def get_last_id(self, channel_id: int) -> int | None:
        return self._state.get(str(channel_id))

    def set_last_id(self, channel_id: int, message_id: int) -> None:
        self._state[str(channel_id)] = message_id
        self.save()
