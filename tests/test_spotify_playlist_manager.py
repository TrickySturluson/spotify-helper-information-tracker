import tempfile
import io
import urllib.error
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

    def test_direct_add_and_remove_require_managed_permission(self):
        for operation in (manager.add, manager.remove):
            with patch.object(manager, "assert_managed", side_effect=manager.ManagerError("protected")) as guard:
                with self.assertRaisesRegex(manager.ManagerError, "protected"):
                    operation(object(), "personal-playlist", ["spotify:track:a"])
                guard.assert_called_once_with("personal-playlist")

    def test_unlock_cannot_grant_managed_permission(self):
        with patch.object(manager, "assert_managed", side_effect=manager.ManagerError("protected")) as guard:
            with self.assertRaisesRegex(manager.ManagerError, "protected"):
                manager.set_lock(object(), "personal-playlist", "unlocked")
            guard.assert_called_once_with("personal-playlist")

    def test_apply_checks_managed_permission_before_lock_or_spotify_access(self):
        with tempfile.TemporaryDirectory() as directory:
            plan = Path(directory) / "plan.json"
            plan.write_text('{"playlist_id":"personal-playlist","operations":[{"action":"add","uris":["spotify:track:a"]}]}')
            with patch.object(manager, "assert_managed", side_effect=manager.ManagerError("protected")) as guard:
                with self.assertRaisesRegex(manager.ManagerError, "protected"):
                    manager.apply(object(), plan)
                guard.assert_called_once_with("personal-playlist")

    def test_create_registers_managed_provenance(self):
        spotify = __import__("unittest").mock.Mock()
        spotify.me.return_value = {"id": "user123"}
        spotify.call.return_value = {"id": "new-playlist", "name": "SHIT Test"}
        with patch.object(manager, "register_created") as register, patch.object(
            manager, "CONFIG", Path(tempfile.gettempdir()) / "shit-manager-test-config.json"
        ), patch.object(manager, "audit"), patch.object(manager, "write"):
            manager.create(spotify, "SHIT Test", "", False)
        register.assert_called_once_with("new-playlist", "SHIT Test")

    def test_playlist_items_use_current_api_page_limit(self):
        spotify = manager.Spotify.__new__(manager.Spotify)
        spotify.call = lambda method, path: {"items": [], "next": None, "requested": path}
        spotify.t = {}
        spotify.refresh_token_rotated = False
        seen = []
        def fake_call(method, path):
            seen.append((method, path))
            return {"items": [], "next": None}
        spotify.call = fake_call
        self.assertEqual(spotify.items("playlist123"), [])
        self.assertEqual(seen, [("GET", "/playlists/playlist123/items?limit=50&additional_types=track,episode")])

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

    def test_refresh_token_rotation_is_flagged_for_cloud_runner(self):
        initial = {
            "refresh_token": "old-refresh-token",
            "obtained_at": 0,
            "expires_in": 0,
        }
        replacement = {
            "access_token": "access-token",
            "refresh_token": "new-refresh-token",
            "expires_in": 3600,
        }
        with patch.object(manager, "read", return_value=initial.copy()), patch.object(
            manager, "token_post", return_value=replacement.copy()
        ), patch.object(manager, "write"), patch.object(manager.time, "time", return_value=1000):
            spotify = manager.Spotify()
            self.assertEqual(spotify.bearer(), "access-token")
            self.assertTrue(spotify.refresh_token_rotated)
            self.assertEqual(spotify.t["refresh_token"], "new-refresh-token")

    def test_expired_refresh_token_has_reauthorization_guidance(self):
        error = urllib.error.HTTPError(
            "https://accounts.spotify.com/api/token",
            400,
            "Bad Request",
            {},
            io.BytesIO(b'{"error":"invalid_grant"}'),
        )
        with patch("urllib.request.urlopen", side_effect=error):
            with self.assertRaisesRegex(manager.ManagerError, "six months"):
                manager.token_post({
                    "grant_type": "refresh_token",
                    "refresh_token": "not-a-real-token",
                })

    def test_rejects_empty_plan(self):
        with self.assertRaises(manager.ManagerError):
            manager.validate({"playlist_id": "playlist123", "operations": []})


    def test_backup_roundtrip_preserves_playlist_identity_and_ordered_items(self):
        snapshot = {
            "created_at": "2026-10-31T00:00:00+00:00",
            "playlist": {
                "id": "safe-test-playlist",
                "name": "Round-trip test",
                "snapshot_id": "snapshot-before-edit",
            },
            "items": [
                {"uri": "spotify:track:first", "name": "First", "artists": ["Artist A"], "album": "Album 1"},
                {"uri": None, "name": "[unavailable item]", "artists": [], "album": None},
                {"uri": "spotify:track:last", "name": "Last", "artists": ["Artist B"], "album": "Album 2"},
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(manager, "BACKUPS", Path(directory)):
                backup_path = Path(manager.save_snapshot(snapshot))
                restored = manager.read(backup_path, None)
        self.assertIsNotNone(restored)
        self.assertEqual(restored["playlist"], snapshot["playlist"])
        self.assertEqual(restored["created_at"], snapshot["created_at"])
        self.assertEqual(restored["items"], snapshot["items"])
        self.assertEqual([row["name"] for row in restored["items"]], ["First", "[unavailable item]", "Last"])


if __name__ == "__main__":
    unittest.main()
