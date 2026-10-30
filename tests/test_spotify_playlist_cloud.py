import json
import os
import tempfile
import unittest
from unittest.mock import Mock, patch

import spotify_playlist_cloud as cloud
import spotify_playlist_manager as manager


class CloudExecutorTests(unittest.TestCase):
    def test_locked_playlist_blocks_cloud_execution(self):
        operation = [{"action": "add", "uris": ["spotify:track:abc"]}]
        with patch.object(manager, "unlocked", return_value=False):
            with self.assertRaises(manager.ManagerError):
                cloud.execute(None, "playlist123", operation)

    def test_add_operation_uses_manager_batch_helper(self):
        operation = [{"action": "add", "uris": ["spotify:track:abc"]}]
        with patch.object(manager, "unlocked", return_value=True), patch.object(
            manager, "add"
        ) as add:
            cloud.execute(object(), "playlist123", operation)
        add.assert_called_once_with(unittest.mock.ANY, "playlist123", ["spotify:track:abc"])

    def test_restore_replaces_first_page_and_appends_remaining_items(self):
        uris = ["spotify:track:" + str(i) for i in range(205)]
        sp = Mock()
        with patch.object(manager, "unlocked", return_value=True):
            cloud.replace_playlist(sp, "playlist123", uris)
        sp.call.assert_any_call("PUT", "/playlists/playlist123/items", {"uris": uris[:100]})
        sp.call.assert_any_call("POST", "/playlists/playlist123/items", {"uris": uris[100:200]})
        sp.call.assert_any_call("POST", "/playlists/playlist123/items", {"uris": uris[200:]})

    def test_restore_empty_snapshot_removes_existing_items(self):
        sp = Mock()
        with patch.object(manager, "unlocked", return_value=True), patch.object(
            manager, "tracks", return_value=[{"uri": "spotify:track:a"}]
        ), patch.object(manager, "find", return_value={"id": "playlist123"}), patch.object(
            manager, "remove"
        ) as remove:
            cloud.replace_playlist(sp, "playlist123", [])
        remove.assert_called_once_with(sp, "playlist123", ["spotify:track:a"])

    def test_remove_operation_uses_manager_batch_helper(self):
        operation = [{"action": "remove", "uris": ["spotify:track:abc"]}]
        with patch.object(manager, "unlocked", return_value=True), patch.object(
            manager, "remove"
        ) as remove:
            cloud.execute(object(), "playlist123", operation)
        remove.assert_called_once_with(unittest.mock.ANY, "playlist123", ["spotify:track:abc"])


    def test_interrupted_confirm_keeps_recovery_pointer(self):
        with tempfile.TemporaryDirectory() as directory:
            root = __import__("pathlib").Path(directory)
            state_path = root / "state.json"
            token_path = root / "token.json"
            event_path = root / "event.json"
            audit_path = root / "audit.jsonl"
            event_path.write_text(json.dumps({
                "sender": {"login": "TrickySturluson"},
                "issue": {
                    "title": "Spotify Playlist Manager Control",
                    "state": "open",
                    "body": json.dumps({
                        "command": "confirm",
                        "confirmation": "one-time-code",
                    }),
                },
            }), encoding="utf-8")
            state_path.write_text(json.dumps({
                "version": 1,
                "playlists": {"playlist123": {"state": "unlocked"}},
                "pending": {
                    "kind": "edit",
                    "playlist_id": "playlist123",
                    "operations": [{"action": "add", "uris": ["spotify:track:a"]}],
                    "snapshot_id": "before",
                    "confirmation": "one-time-code",
                },
            }), encoding="utf-8")
            playlist_before = {"id": "playlist123", "name": "Tricky Daily", "snapshot_id": "before"}
            playlist_after = {"id": "playlist123", "name": "Tricky Daily", "snapshot_id": "partial"}
            sp = Mock()
            sp.playlists.return_value = [{"id": "playlist123", "owner": {"id": "user123"}}]
            sp.me.return_value = {"id": "user123"}

            with patch.dict(os.environ, {
                "GITHUB_EVENT_PATH": str(event_path),
                "SPOTIFY_CLIENT_ID": "client-id",
                "SPOTIFY_REFRESH_TOKEN": "refresh-token",
                "GITHUB_RUN_ID": "12345",
            }), patch.object(cloud, "STATE", state_path), patch.object(
                manager, "CONFIG", state_path
            ), patch.object(manager, "TOKEN", token_path), patch.object(
                manager, "AUDIT", audit_path
            ), patch.object(manager, "Spotify", return_value=sp), patch.object(
                manager, "unlocked", return_value=True
            ), patch.object(
                cloud, "owned_playlist", side_effect=[playlist_before, playlist_after]
            ), patch.object(
                manager, "snapshot", return_value={"playlist": {"id": "playlist123"}, "items": []}
            ), patch.object(
                manager, "save_snapshot", return_value="playlist_backups/before.json"
            ), patch.object(
                manager, "audit"
            ), patch.object(
                cloud, "execute", side_effect=manager.ManagerError("simulated partial API failure")
            ):
                with self.assertRaisesRegex(manager.ManagerError, "simulated partial API failure"):
                    cloud.main()

            saved = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["last_completed"]["kind"], "partial")
            self.assertEqual(saved["last_completed"]["backup"], "playlist_backups/before.json")
            self.assertEqual(saved["last_completed"]["after_snapshot_id"], "partial")
            self.assertNotIn("pending", saved)


if __name__ == "__main__":
    unittest.main()
