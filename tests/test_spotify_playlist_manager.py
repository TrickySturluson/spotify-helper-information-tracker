import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import spotify_playlist_manager as manager


class PlaylistManagerTests(unittest.TestCase):
    def test_unknown_playlists_are_locked_by_default(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "permissions.json"
            with patch.object(manager, "CONFIG", config_path):
                self.assertFalse(manager.unlocked("not-listed"))

    def test_only_explicit_unlocked_entry_is_editable(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "permissions.json"
            with patch.object(manager, "CONFIG", config_path):
                manager.write(config_path, {
                    "version": 1,
                    "playlists": {"allowed": {"state": "unlocked"}}
                })
                self.assertTrue(manager.unlocked("allowed"))
                self.assertFalse(manager.unlocked("other"))

    def test_valid_add_plan(self):
        playlist_id, operations = manager.validate({
            "playlist_id": "playlist123",
            "operations": [{
                "action": "add",
                "uris": ["spotify:track:track123"]
            }]
        })
        self.assertEqual(playlist_id, "playlist123")
        self.assertEqual(operations[0]["action"], "add")

    def test_rejects_non_track_uris(self):
        with self.assertRaises(manager.ManagerError):
            manager.validate({
                "playlist_id": "playlist123",
                "operations": [{
                    "action": "add",
                    "uris": ["https://open.spotify.com/track/track123"]
                }]
            })

    def test_rejects_empty_plan(self):
        with self.assertRaises(manager.ManagerError):
            manager.validate({"playlist_id": "playlist123", "operations": []})


if __name__ == "__main__":
    unittest.main()
