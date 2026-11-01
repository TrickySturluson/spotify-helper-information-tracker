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

    def test_create_rejects_invalid_name_before_spotify_call(self):
        spotify = __import__("unittest").mock.Mock()
        for name in ("", "   ", "x" * 101):
            with self.subTest(name_length=len(name)):
                with self.assertRaises(manager.ManagerError):
                    manager.create(spotify, name, "", False)
        spotify.me.assert_not_called()
        spotify.call.assert_not_called()

    def test_create_rejects_oversized_description_before_spotify_call(self):
        spotify = __import__("unittest").mock.Mock()
        with self.assertRaisesRegex(manager.ManagerError, "description"):
            manager.create(spotify, "Valid name", "x" * 301, False)
        spotify.me.assert_not_called()
        spotify.call.assert_not_called()

    def test_create_registers_managed_provenance(self):
        spotify = __import__("unittest").mock.Mock()
        spotify.me.return_value = {"id": "user123"}
        spotify.call.return_value = {"id": "new-playlist", "name": "SHIT Test"}
        with patch.object(manager, "register_created") as register, patch.object(
            manager, "CONFIG", Path(tempfile.gettempdir()) / "shit-manager-test-config.json"
        ), patch.object(manager, "audit"), patch.object(manager, "write"):
            manager.create(spotify, "SHIT Test", "", False)
        register.assert_called_once_with("new-playlist", "SHIT Test")

    def test_request_metrics_count_endpoint_status_and_latency(self):
        spotify = manager.Spotify.__new__(manager.Spotify)
        spotify.request_metrics = {
            "total_requests": 0, "by_endpoint": {}, "by_status": {}, "elapsed_ms": 0
        }
        spotify.record_request("GET", "/playlists/ABCDEFGHIJKLMNOPQRSTUVWX/items?limit=50", 200, 12.5)
        spotify.record_request("GET", "/playlists/ABCDEFGHIJKLMNOPQRSTUVWX/items?offset=50", 429, 8.0)
        metrics = spotify.request_metrics
        self.assertEqual(metrics["total_requests"], 2)
        self.assertEqual(metrics["by_endpoint"]["GET /playlists/{id}/items"]["count"], 2)
        self.assertEqual(metrics["by_status"], {"200": 1, "429": 1})
        self.assertEqual(metrics["elapsed_ms"], 20.5)
        self.assertNotIn("ABCDEFGHIJKLMNOPQRSTUVWX", str(metrics))
        self.assertNotIn("limit=50", str(metrics))

    def test_metric_endpoint_removes_query_and_redacts_spotify_ids(self):
        endpoint = manager.Spotify.metric_endpoint(
            "/playlists/ABCDEFGHIJKLMNOPQRSTUVWX/items?limit=50&additional_types=track"
        )
        self.assertEqual(endpoint, "/playlists/{id}/items")

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

    def test_rejects_non_object_plan_operations(self):
        with self.assertRaisesRegex(manager.ManagerError, "operation must be an object"):
            manager.validate({"playlist_id": "playlist123", "operations": ["add"]})

    def test_rejects_empty_track_uri_identifier(self):
        with self.assertRaises(manager.ManagerError):
            manager.validate({
                "playlist_id": "playlist123",
                "operations": [{"action": "add", "uris": ["spotify:track:"]}],
            })

    def test_rejects_boolean_reorder_positions(self):
        with self.assertRaisesRegex(manager.ManagerError, "Invalid reorder range"):
            manager.validate({
                "playlist_id": "playlist123",
                "operations": [{
                    "action": "reorder",
                    "range_start": True,
                    "insert_before": 0,
                    "range_length": 1,
                }],
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

    def test_spotify_429_reports_quota_cooldown_and_no_retry(self):
        spotify = manager.Spotify.__new__(manager.Spotify)
        spotify.bearer = lambda: "test-token"
        error = urllib.error.HTTPError(
            url="https://api.spotify.com/v1/me/playlists",
            code=429,
            msg="Too Many Requests",
            hdrs={"Retry-After": "13060"},
            fp=io.BytesIO(b'{"error":{"status":429,"message":"Too many requests","reason":"QUOTA_EXCEEDED"}}'),
        )
        with tempfile.TemporaryDirectory() as directory, patch.object(
            manager, "SPOTIFY_COOLDOWN", Path(directory) / "cooldown.json"
        ), patch.object(manager.urllib.request, "urlopen", side_effect=error) as request:
            with self.assertRaisesRegex(
                manager.ManagerError,
                r"quota/rate limit reached.*QUOTA_EXCEEDED.*3h 38m.*No playlist changes were attempted",
            ):
                spotify.call("GET", "/me/playlists?limit=50")
            saved = manager.read(manager.SPOTIFY_COOLDOWN, {})
            self.assertEqual(saved["retry_after_seconds"], 13060)
            self.assertEqual(saved["reason"], "QUOTA_EXCEEDED")
            # A later request in the same process must be blocked before
            # urlopen, including best-effort recovery code after the 429.
            with self.assertRaisesRegex(manager.ManagerError, "Spotify API cooldown is active"):
                spotify.call("GET", "/me")
        request.assert_called_once()

    def test_active_spotify_cooldown_blocks_client_initialization(self):
        with tempfile.TemporaryDirectory() as directory:
            cooldown = Path(directory) / "cooldown.json"
            manager.write(cooldown, {
                "cooldown_until": "2999-01-01T00:00:00+00:00",
                "reason": "QUOTA_EXCEEDED",
            })
            with patch.object(manager, "SPOTIFY_COOLDOWN", cooldown):
                with self.assertRaisesRegex(manager.ManagerError, "Spotify API cooldown is active"):
                    manager.Spotify()

    def test_expired_spotify_cooldown_allows_client_initialization(self):
        with tempfile.TemporaryDirectory() as directory:
            cooldown = Path(directory) / "cooldown.json"
            manager.write(cooldown, {
                "cooldown_until": "2000-01-01T00:00:00+00:00",
                "reason": "QUOTA_EXCEEDED",
            })
            with patch.object(manager, "SPOTIFY_COOLDOWN", cooldown):
                manager.check_spotify_cooldown()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Regression test module.
# Scope: Regression checks for the behavior named by this test module.
# Run: python -m unittest tests.test_spotify_playlist_manager -v (from the repository root).
# Related: Implementation lives under scripts/; longer behavior notes live in docs/.
# -----------------------------------------------------------------------------
