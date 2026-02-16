"""Tests for StateManager."""

import json

from tg_harvest.storage.state import StateManager


class TestStateManager:
    def test_get_last_id_empty(self, tmp_path):
        state = StateManager(tmp_path / "state.json")
        assert state.get_last_id(12345) is None

    def test_set_and_get(self, tmp_path):
        state = StateManager(tmp_path / "state.json")
        state.set_last_id(12345, 999)
        assert state.get_last_id(12345) == 999

    def test_persists_to_file(self, tmp_path):
        path = tmp_path / "state.json"
        state = StateManager(path)
        state.set_last_id(111, 500)

        # Create new instance from same file
        state2 = StateManager(path)
        assert state2.get_last_id(111) == 500

    def test_multiple_channels(self, tmp_path):
        state = StateManager(tmp_path / "state.json")
        state.set_last_id(111, 100)
        state.set_last_id(222, 200)
        state.set_last_id(333, 300)

        assert state.get_last_id(111) == 100
        assert state.get_last_id(222) == 200
        assert state.get_last_id(333) == 300

    def test_update_existing(self, tmp_path):
        state = StateManager(tmp_path / "state.json")
        state.set_last_id(111, 100)
        state.set_last_id(111, 200)
        assert state.get_last_id(111) == 200

    def test_handles_corrupt_file(self, tmp_path):
        path = tmp_path / "state.json"
        path.write_text("not valid json", encoding="utf-8")
        state = StateManager(path)
        assert state.get_last_id(111) is None

    def test_creates_parent_dirs(self, tmp_path):
        path = tmp_path / "deep" / "nested" / "state.json"
        state = StateManager(path)
        state.set_last_id(111, 100)
        assert path.exists()

    def test_file_format(self, tmp_path):
        path = tmp_path / "state.json"
        state = StateManager(path)
        state.set_last_id(12345, 999)

        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["12345"] == 999
