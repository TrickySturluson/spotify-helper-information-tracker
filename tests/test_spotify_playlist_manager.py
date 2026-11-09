import tempfile
import io
import urllib.error
import unittest
from pathlib import Path
from unittest.mock import patch

import spotify_playlist_manager as manager


class PlaylistManagerTests(unittest.TestCase):
    def test_cloud_refresh_persists_rotated_token_to_repository_secret(self):
        with patch.dict("os.environ", {"SHIT_PERSIST_ROTATED_SPOTIFY_TOKEN": "1", "GH_TOKEN": "short-lived-app-token", "GITHUB_REPOSITORY": "TrickySturluson/spotify-helper-information-tracker"}, clear=True), patch.object(manager.subprocess, "run") as run:
            manager.persist_refresh_token("rotated-refresh-token")
        self.assertEqual(run.call_args.args[0], ["gh", "secret", "set", "SPOTIFY_REFRESH_TOKEN", "--repo", "TrickySturluson/spotify-helper-information-tracker"])
        self.assertEqual(run.call_args.kwargs["input"], "rotated-refresh-token")
        self.assertNotIn("rotated-refresh-token", repr(run.call_args.args[0]))

    def test_cloud_refresh_fails_closed_before_spotify_request_without_secret_writer(self):
        spotify = manager.Spotify.__new__(manager.Spotify)
        spotify.t = {"refresh_token": "existing", "obtained_at": 0, "expires_in": 0}
        with patch.dict("os.environ", {"SHIT_PERSIST_ROTATED_SPOTIFY_TOKEN": "1"}, clear=True), patch.object(manager, "token_post") as token_post:
            with self.assertRaisesRegex(manager.ManagerError, "blocked before contacting Spotify"):
                spotify.bearer()
        token_post.assert_not_called()

    def test_broker_access_token_is_used_without_loading_or_refreshing_a_refresh_token(self):
        with patch.dict("os.environ", {
            "SHIT_BROKER_ACCESS_TOKEN": "short-lived-broker-access-token",
            "SHIT_BROKER_ACCESS_TOKEN_EXPIRES_IN": "3600",
        }, clear=True), patch.object(manager, "check_spotify_cooldown"), patch.object(
            manager, "read", side_effect=AssertionError("broker mode must not read the legacy token file")
        ), patch.object(manager, "token_post") as token_post:
            spotify = manager.Spotify()
            self.assertTrue(spotify.broker_managed)
            self.assertNotIn("refresh_token", spotify.t)
            self.assertEqual(spotify.bearer(), "short-lived-broker-access-token")
            token_post.assert_not_called()

    def test_broker_required_mode_never_falls_back_to_legacy_token_file(self):
        with patch.dict("os.environ", {"SHIT_AUTH_MODE": "broker"}, clear=True), patch.object(
            manager, "check_spotify_cooldown"
        ), patch.object(manager, "read", side_effect=AssertionError("legacy token file must not be read")):
            with self.assertRaisesRegex(manager.ManagerError, "requires a broker-issued"):
                manager.Spotify()

    def test_broker_mode_forbids_refresh_token_secret_persistence(self):
        with patch.dict("os.environ", {
            "SHIT_AUTH_MODE": "broker",
            "SHIT_PERSIST_ROTATED_SPOTIFY_TOKEN": "1",
            "GH_TOKEN": "must-not-be-used",
            "GITHUB_REPOSITORY": "TrickySturluson/spotify-helper-information-tracker",
        }, clear=True), patch.object(manager.subprocess, "run") as run:
            with self.assertRaisesRegex(manager.ManagerError, "must never persist refresh tokens"):
                manager.persist_refresh_token("sensitive-refresh-token")
        run.assert_not_called()

    def test_expired_broker_access_token_renews_only_through_the_central_broker(self):
        spotify = manager.Spotify.__new__(manager.Spotify)
        spotify.broker_managed = True
        spotify.t = {"access_token": "expired-broker-access-token", "obtained_at": 0, "expires_in": 60}
        with patch("scripts.spotify.broker_access_token.request_broker_access_token", side_effect=manager_error := RuntimeError("temporary broker failure")), patch.object(
            manager.time, "time", return_value=1000
        ), patch.object(manager, "token_post") as token_post:
            with self.assertRaisesRegex(manager.ManagerError, "central broker could not renew"):
                spotify.bearer()
            token_post.assert_not_called()

    def test_expired_broker_access_token_can_be_renewed_without_direct_refresh(self):
        spotify = manager.Spotify.__new__(manager.Spotify)
        spotify.broker_managed = True
        spotify.t = {"access_token": "expired-broker-access-token", "obtained_at": 0, "expires_in": 60}
        with patch("scripts.spotify.broker_access_token.request_broker_access_token", return_value=("renewed-broker-access-token", 3600)) as broker, patch.object(
            manager.time, "time", return_value=1000
        ), patch.dict("os.environ", {"GITHUB_ACTIONS": "true"}, clear=True), patch("builtins.print") as output, patch.object(manager, "token_post") as token_post:
            self.assertEqual(spotify.bearer(), "renewed-broker-access-token")
            self.assertEqual(spotify.t["expires_in"], 3600)
            self.assertEqual(os.environ["SHIT_BROKER_ACCESS_TOKEN"], "renewed-broker-access-token")
            broker.assert_called_once_with()
            output.assert_called_once_with("::add-mask::renewed-broker-access-token")
            token_post.assert_not_called()

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
        spotify.items.return_value = []
        with patch.object(manager, "register_created") as register, patch.object(
            manager, "CONFIG", Path(tempfile.gettempdir()) / "shit-manager-test-config.json"
        ), patch.object(manager, "audit"), patch.object(manager, "write"):
            manager.create(spotify, "SHIT Test", "", False)
        register.assert_called_once_with("new-playlist", "SHIT Test")

    def test_snapshot_preserves_description_for_prewrite_guards(self):
        spotify = __import__("unittest").mock.Mock()
        spotify.items.return_value = []
        playlist = {
            "id": "playlist123", "name": "Tricky Daily",
            "description": "Could be worse. Could be quiet.",
            "snapshot_id": "snapshot123",
        }
        result = manager.snapshot(spotify, playlist)
        self.assertEqual(
            result["playlist"]["description"],
            "Could be worse. Could be quiet.",
        )

    def test_mutation_snapshots_use_exact_playlist_lookup_not_account_scan(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spotify = __import__("unittest").mock.Mock()
            spotify.call.side_effect = lambda method, path, body=None: (
                {"id": "playlist123", "name": "Test", "snapshot_id": "before"}
                if method == "GET" else {"snapshot_id": "after"}
            )
            spotify.items.return_value = []
            with patch.object(manager, "BACKUPS", root / "backups"), patch.object(
                manager, "AUDIT", root / "audit.jsonl"
            ):
                manager.mutate_with_snapshots(
                    spotify, "playlist123",
                    lambda: spotify.call("PUT", "/playlists/playlist123/items", {"uris": []}),
                    event="test_mutation",
                )
            spotify.playlists.assert_not_called()
            self.assertEqual(
                [call.args[:2] for call in spotify.call.call_args_list],
                [("GET", "/playlists/playlist123"), ("PUT", "/playlists/playlist123/items"),
                 ("GET", "/playlists/playlist123")],
            )

    def test_request_metrics_count_endpoint_status_and_latency(self):
        spotify = manager.Spotify.__new__(manager.Spotify)
        spotify.request_metrics = {
            "total_requests": 0, "by_endpoint": {}, "by_status": {}, "elapsed_ms": 0
        }
        spotify.record_request("GET", "/playlists/ABCDEFGHIJKLMNOPQRSTUV/items?limit=50", 200, 12.5)
        spotify.record_request("GET", "/playlists/ABCDEFGHIJKLMNOPQRSTUV/items?offset=50", 429, 8.0)
        metrics = spotify.request_metrics
        self.assertEqual(metrics["total_requests"], 2)
        self.assertEqual(metrics["by_endpoint"]["GET /playlists/{id}/items"]["count"], 2)
        self.assertEqual(metrics["by_status"], {"200": 1, "429": 1})
        self.assertEqual(metrics["elapsed_ms"], 20.5)
        self.assertNotIn("ABCDEFGHIJKLMNOPQRSTUV", str(metrics))
        self.assertNotIn("limit=50", str(metrics))

    def test_metric_endpoint_removes_query_and_redacts_spotify_ids(self):
        endpoint = manager.Spotify.metric_endpoint(
            "/playlists/ABCDEFGHIJKLMNOPQRSTUV/items?limit=50&additional_types=track"
        )
        self.assertEqual(endpoint, "/playlists/{id}/items")

    def test_single_track_lookup_supports_explicit_market(self):
        spotify = manager.Spotify.__new__(manager.Spotify)
        seen = []
        spotify.call = lambda method, url: (seen.append((method, url)) or {"id": "1234567890123456789012"})
        result = spotify.track("1234567890123456789012", market="from_token")
        self.assertEqual(result["id"], "1234567890123456789012")
        self.assertEqual(seen, [("GET", "/tracks/1234567890123456789012?market=from_token")])
        with self.assertRaises(manager.ManagerError):
            spotify.track("not-a-track-id", market="from_token")

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
        seen.clear()
        self.assertEqual(spotify.items("playlist123", market="from_token"), [])
        self.assertEqual(seen, [("GET", "/playlists/playlist123/items?limit=50&additional_types=track,episode&market=from_token")])
        with self.assertRaises(manager.ManagerError):
            spotify.items("playlist123", market="not-a-market")

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
            with self.assertRaisesRegex(manager.ManagerError, "invalid_grant"):
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


    def test_spotify_429_reports_quota_cooldown_and_no_retry(self):
        spotify = manager.Spotify.__new__(manager.Spotify)
        spotify.bearer = lambda: "test-token"
        spotify.request_metrics = {"total_requests": 0, "by_endpoint": {}, "by_status": {}, "elapsed_ms": 0}
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
                r"quota/rate limit reached.*QUOTA_EXCEEDED.*3h 37m.*No playlist changes were attempted",
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

    def test_spotify_429_parses_http_date_retry_after(self):
        spotify = manager.Spotify.__new__(manager.Spotify)
        spotify.bearer = lambda: "test-token"
        spotify.request_metrics = {"total_requests": 0, "by_endpoint": {}, "by_status": {}, "elapsed_ms": 0}
        error = urllib.error.HTTPError(
            url="https://api.spotify.com/v1/me/playlists",
            code=429,
            msg="Too Many Requests",
            hdrs={"Retry-After": "Wed, 02 Jan 2030 03:04:05 GMT"},
            fp=io.BytesIO(b'{"error":{"status":429,"message":"Too many requests","reason":"QUOTA_EXCEEDED"}}'),
        )
        with tempfile.TemporaryDirectory() as directory, patch.object(
            manager, "SPOTIFY_COOLDOWN", Path(directory) / "cooldown.json"
        ), patch.object(manager.urllib.request, "urlopen", side_effect=error) as request:
            with self.assertRaisesRegex(manager.ManagerError, "No playlist changes were attempted"):
                spotify.call("GET", "/me/playlists")
            saved = manager.read(manager.SPOTIFY_COOLDOWN, {})
            self.assertEqual(saved["cooldown_until"], "2030-01-02T03:04:05+00:00")
            self.assertGreater(saved["retry_after_seconds"], 0)
            self.assertFalse(saved.get("manual_clear_required", False))
        request.assert_called_once()

    def test_spotify_429_without_usable_retry_after_fails_closed(self):
        spotify = manager.Spotify.__new__(manager.Spotify)
        spotify.bearer = lambda: "test-token"
        spotify.request_metrics = {"total_requests": 0, "by_endpoint": {}, "by_status": {}, "elapsed_ms": 0}
        error = urllib.error.HTTPError(
            url="https://api.spotify.com/v1/me/playlists",
            code=429,
            msg="Too Many Requests",
            hdrs={},
            fp=io.BytesIO(b'{"error":{"status":429,"message":"Too many requests","reason":"QUOTA_EXCEEDED"}}'),
        )
        with tempfile.TemporaryDirectory() as directory, patch.object(
            manager, "SPOTIFY_COOLDOWN", Path(directory) / "cooldown.json"
        ), patch.object(manager.urllib.request, "urlopen", side_effect=error) as request:
            with self.assertRaisesRegex(manager.ManagerError, "manual clearance"):
                spotify.call("GET", "/me/playlists")
            saved = manager.read(manager.SPOTIFY_COOLDOWN, {})
            self.assertTrue(saved["manual_clear_required"])
            self.assertIsNone(saved["cooldown_until"])
            with self.assertRaisesRegex(manager.ManagerError, "requires manual clearance"):
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


if __name__ == "__main__":
    unittest.main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Verify the shared Spotify playlist manager's authorization and write-safety invariants.
# Scope: Deny-by-default managed-playlist policy, lock checks, plan validation, backups, metrics,
#        refresh-token rotation/secret persistence, exact lookup behavior and Retry-After cooldowns.
# Run: python -m unittest tests.test_spotify_playlist_manager -v
# Related: scripts/spotify/spotify_playlist_manager.py; docs/SPOTIFY_API_OPERATIONS.md;
#          docs/WORKFLOWS.md.
# -----------------------------------------------------------------------------
