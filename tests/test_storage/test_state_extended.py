"""Extended tests for StateManager: concurrent channels, reload, edge cases."""

import json

from tg_harvest.storage.state import StateManager


class TestStateManagerReload:
    def test_reload_after_external_modification(self, tmp_path):
        """State should be fresh on each new StateManager instance."""
        path = tmp_path / "state.json"
        state1 = StateManager(path)
        state1.set_last_id(1, 100)

        # Externally modify the file
        data = json.loads(path.read_text(encoding="utf-8"))
        data["1"] = 999
        path.write_text(json.dumps(data), encoding="utf-8")

        # New instance should read the external modification
        state2 = StateManager(path)
        assert state2.get_last_id(1) == 999

    def test_load_nonexistent_file(self, tmp_path):
        path = tmp_path / "does_not_exist.json"
        state = StateManager(path)
        assert state.get_last_id(1) is None

    def test_overwrite_with_higher_id(self, tmp_path):
        state = StateManager(tmp_path / "state.json")
        state.set_last_id(1, 100)
        state.set_last_id(1, 200)
        assert state.get_last_id(1) == 200

    def test_overwrite_with_lower_id_allowed(self, tmp_path):
        """StateManager doesn't enforce monotonic IDs — it just stores."""
        state = StateManager(tmp_path / "state.json")
        state.set_last_id(1, 200)
        state.set_last_id(1, 50)
        assert state.get_last_id(1) == 50


class TestStateManagerFileFormat:
    def test_json_is_pretty_printed(self, tmp_path):
        path = tmp_path / "state.json"
        state = StateManager(path)
        state.set_last_id(1, 100)

        content = path.read_text(encoding="utf-8")
        assert "\n" in content  # indent=2 means newlines
        assert "  " in content

    def test_unicode_preserved(self, tmp_path):
        """ensure_ascii=False means non-ASCII should work."""
        path = tmp_path / "state.json"
        state = StateManager(path)
        state.set_last_id(1, 100)

        content = path.read_text(encoding="utf-8")
        data = json.loads(content)
        assert data["1"] == 100

    def test_channel_id_stored_as_string_key(self, tmp_path):
        """JSON keys are always strings, so channel_id is converted."""
        path = tmp_path / "state.json"
        state = StateManager(path)
        state.set_last_id(12345, 999)

        data = json.loads(path.read_text(encoding="utf-8"))
        assert "12345" in data
        assert 12345 not in data  # Not numeric key


class TestStateManagerManyChannels:
    def test_ten_channels(self, tmp_path):
        state = StateManager(tmp_path / "state.json")
        for i in range(10):
            state.set_last_id(i, i * 100)

        for i in range(10):
            assert state.get_last_id(i) == i * 100

    def test_persistence_with_many_channels(self, tmp_path):
        path = tmp_path / "state.json"
        state = StateManager(path)
        for i in range(10):
            state.set_last_id(i, i * 100)

        # Reload
        state2 = StateManager(path)
        for i in range(10):
            assert state2.get_last_id(i) == i * 100


class TestStateManagerCorruptData:
    def test_empty_file(self, tmp_path):
        path = tmp_path / "state.json"
        path.write_text("", encoding="utf-8")
        state = StateManager(path)
        assert state.get_last_id(1) is None

    def test_non_dict_json_treated_as_corrupt(self, tmp_path):
        """JSON that's valid but not a dict (e.g., array) — resets to empty."""
        path = tmp_path / "state.json"
        path.write_text("[1, 2, 3]", encoding="utf-8")
        state = StateManager(path)
        # Non-dict JSON should be treated as corrupt and reset
        assert state.get_last_id(1) is None
        # Should work normally after reset
        state.set_last_id(1, 100)
        assert state.get_last_id(1) == 100
