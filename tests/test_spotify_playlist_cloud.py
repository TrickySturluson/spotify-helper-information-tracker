import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import spotify_playlist_cloud as cloud
import spotify_playlist_manager as manager


class CloudExecutorTests(unittest.TestCase):
    def test_non_string_cloud_command_is_rejected_before_spotify_access(self):
        with tempfile.TemporaryDirectory() as directory:
            event_path = Path(directory) / "event.json"
            event_path.write_text(json.dumps({
                "sender": {"login": "TrickySturluson"},
                "issue": {
                    "title": "SHIT — Playlist Control",
                    "state": "open",
                    "body": json.dumps({"command": []}),
                },
            }), encoding="utf-8")
            with patch.dict(os.environ, {"GITHUB_EVENT_PATH": str(event_path)}), patch.object(
                manager, "Spotify"
            ) as spotify:
                with self.assertRaises(SystemExit):
                    cloud.main()
            spotify.assert_not_called()

    def test_locked_playlist_blocks_cloud_execution(self):
        operation = [{"action": "add", "uris": ["spotify:track:abc"]}]
        with patch.object(manager, "assert_managed"), patch.object(manager, "unlocked", return_value=False):
            with self.assertRaises(manager.ManagerError):
                cloud.execute(None, "playlist123", operation)

    def test_add_operation_uses_manager_batch_helper(self):
        operation = [{"action": "add", "uris": ["spotify:track:abc"]}]
        sp = Mock()
        sp.playlists.return_value = [{"id": "playlist123", "name": "Test"}]
        sp.call.side_effect = lambda method, path, body=None: (
            {"id": "playlist123", "name": "Test", "snapshot_id": "snapshot"}
            if method == "GET" else {"snapshot_id": "after"}
        )
        sp.items.return_value = []
        with patch.object(manager, "assert_managed"), patch.object(manager, "unlocked", return_value=True), patch.object(
            manager, "add"
        ) as add:
            cloud.execute(sp, "playlist123", operation)
        add.assert_called_once_with(unittest.mock.ANY, "playlist123", ["spotify:track:abc"])

    def test_restore_replaces_first_page_and_appends_remaining_items(self):
        uris = ["spotify:track:" + str(i) for i in range(205)]
        sp = Mock()
        sp.playlists.return_value = [{"id": "playlist123", "name": "Test"}]
        sp.call.side_effect = lambda method, path, body=None: (
            {"id": "playlist123", "name": "Test", "snapshot_id": "snapshot"}
            if method == "GET" else {"snapshot_id": "after"}
        )
        sp.items.return_value = []
        with patch.object(manager, "assert_managed"), patch.object(manager, "unlocked", return_value=True):
            cloud.replace_playlist(sp, "playlist123", uris)
        sp.call.assert_any_call("PUT", "/playlists/playlist123/items", {"uris": uris[:100]})
        sp.call.assert_any_call("POST", "/playlists/playlist123/items", {"uris": uris[100:200]})
        sp.call.assert_any_call("POST", "/playlists/playlist123/items", {"uris": uris[200:]})

    def test_restore_empty_snapshot_removes_existing_items(self):
        sp = Mock()
        with patch.object(manager, "assert_managed"), patch.object(manager, "unlocked", return_value=True), patch.object(
            manager, "tracks", return_value=[{"uri": "spotify:track:a"}]
        ), patch.object(manager, "find", return_value={"id": "playlist123"}), patch.object(
            manager, "fetch_playlist", return_value={"id": "playlist123", "name": "Test", "snapshot_id": "snapshot"}
        ), patch.object(manager, "remove") as remove:
            cloud.replace_playlist(sp, "playlist123", [])
        remove.assert_called_once_with(sp, "playlist123", ["spotify:track:a"])

    def test_remove_operation_uses_manager_batch_helper(self):
        operation = [{"action": "remove", "uris": ["spotify:track:abc"]}]
        sp = Mock()
        sp.playlists.return_value = [{"id": "playlist123", "name": "Test"}]
        sp.call.side_effect = lambda method, path, body=None: (
            {"id": "playlist123", "name": "Test", "snapshot_id": "snapshot"}
            if method == "GET" else {"snapshot_id": "after"}
        )
        sp.items.return_value = []
        with patch.object(manager, "assert_managed"), patch.object(manager, "unlocked", return_value=True), patch.object(
            manager, "remove"
        ) as remove:
            cloud.execute(sp, "playlist123", operation)
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
                    "title": "SHIT — Playlist Control",
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
                manager, "assert_managed"
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


class UndoSnapshotValidationTests(unittest.TestCase):
    def test_pending_recommendation_confirmation_rechecks_removal_history(self):
        pending = {
            "kind": "booze10",
            "candidate_tracks": [{
                "artist": "Misfits", "title": "Where Eagles Dare",
                "uri": "spotify:track:5LgiqEgpK54OfXC6947wbU",
            }],
        }
        feedback = {
            "negative_keys": {"misfits|where eagles dare"},
            "negative_uris": {"spotify:track:5LgiqEgpK54OfXC6947wbU"},
        }
        self.assertEqual(
            cloud.pending_removal_conflicts(pending, feedback),
            ["Misfits — Where Eagles Dare [spotify:track:5LgiqEgpK54OfXC6947wbU]"],
        )

    def test_legacy_pending_recommendation_without_metadata_fails_closed(self):
        self.assertEqual(
            cloud.pending_removal_conflicts({"kind": "booze10"}, {}),
            ["pending preview has no candidate metadata; stage it again"],
        )

    def test_workflow_refreshes_removal_history_before_preview_or_confirmation(self):
        workflow = (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "spotify-playlist-manager.yml").read_text(encoding="utf-8")
        refresh = workflow.index("Refresh playlist removal history before protected staging or confirmation")
        execute = workflow.index("Execute owner command")
        self.assertLess(refresh, execute)
        self.assertIn("steps.parse-command.outputs.command == 'booze10_preview'", workflow)
        self.assertIn("steps.parse-command.outputs.command == 'daily_preview'", workflow)
        self.assertIn('"daily"', workflow[refresh:execute])
        self.assertIn("steps.parse-command.outputs.command == 'confirm'", workflow[refresh:execute])

    def test_undo_accepts_same_ordered_items_even_if_snapshot_id_differs(self):
        pending = {
            "kind": "undo",
            "snapshot_id": "snapshot-from-preview",
            "expected_uris": ["spotify:track:a", "spotify:track:b"],
        }
        current = {
            "playlist": {"id": "playlist123", "snapshot_id": "different-snapshot"},
            "items": [{"uri": "spotify:track:a"}, {"uri": "spotify:track:b"}],
        }
        self.assertTrue(
            cloud.pending_state_matches(
                {"snapshot_id": "different-snapshot"}, pending, current
            )
        )

    def test_undo_rejects_changed_order_or_content(self):
        pending = {
            "kind": "undo",
            "expected_uris": ["spotify:track:a", "spotify:track:b"],
        }
        changed = {
            "playlist": {"id": "playlist123"},
            "items": [{"uri": "spotify:track:b"}, {"uri": "spotify:track:a"}],
        }
        self.assertFalse(
            cloud.pending_state_matches({"snapshot_id": "anything"}, pending, changed)
        )

    def test_regular_edit_uses_ordered_contents_not_snapshot_id(self):
        pending = {
            "kind": "edit",
            "snapshot_id": "stale-snapshot",
            "expected_uris": ["spotify:track:a", "spotify:track:b"],
        }
        current = {
            "items": [{"uri": "spotify:track:a"}, {"uri": "spotify:track:b"}],
        }
        self.assertTrue(
            cloud.pending_state_matches(
                {"snapshot_id": "different-live-snapshot"}, pending, current
            )
        )

    def test_regular_edit_rejects_changed_playlist_contents(self):
        pending = {"kind": "edit", "expected_uris": ["spotify:track:a"]}
        current = {"items": [{"uri": "spotify:track:changed"}]}
        self.assertFalse(
            cloud.pending_state_matches({"snapshot_id": "anything"}, pending, current)
        )


    def test_completed_undo_validation_uses_saved_ordered_contents(self):
        completed = {
            "after_snapshot_id": "stale-snapshot",
            "after_uris": ["spotify:track:a", "spotify:track:b"],
        }
        current = {
            "items": [{"uri": "spotify:track:a"}, {"uri": "spotify:track:b"}],
        }
        self.assertTrue(
            cloud.completed_state_matches(
                {"snapshot_id": "new-live-snapshot"}, completed, current
            )
        )

    def test_completed_undo_validation_rejects_changed_contents(self):
        completed = {"after_uris": ["spotify:track:a", "spotify:track:b"]}
        current = {
            "items": [{"uri": "spotify:track:a"}, {"uri": "spotify:track:c"}],
        }
        self.assertFalse(
            cloud.completed_state_matches(
                {"snapshot_id": "same-snapshot"}, completed, current
            )
        )

    def test_legacy_undo_pointer_falls_back_to_snapshot_id(self):
        completed = {"after_snapshot_id": "expected"}
        current = {"items": []}
        self.assertTrue(
            cloud.completed_state_matches(
                {"snapshot_id": "expected"}, completed, current
            )
        )
        self.assertFalse(
            cloud.completed_state_matches(
                {"snapshot_id": "different"}, completed, current
            )
        )


class OwnedPlaylistTests(unittest.TestCase):
    def test_uses_direct_playlist_resource_for_fresh_snapshot(self):
        spotify = Mock()
        live = {
            "id": "playlist123",
            "name": "Tricky Daily",
            "owner": {"id": "user123"},
            "snapshot_id": "fresh-snapshot",
        }
        spotify.call.return_value = live
        spotify.playlists.side_effect = AssertionError(
            "Do not use the potentially stale /me/playlists collection"
        )

        result = cloud.owned_playlist(spotify, "playlist123", {"id": "user123"})

        self.assertIs(result, live)
        spotify.call.assert_called_once_with("GET", "/playlists/playlist123")
        spotify.playlists.assert_not_called()
        self.assertEqual(result["snapshot_id"], "fresh-snapshot")

    def test_exact_lookup_failure_does_not_scan_entire_playlist_collection(self):
        spotify = Mock()
        spotify.call.side_effect = manager.ManagerError(
            "Spotify API GET /playlists/playlist123: HTTP 404"
        )

        with self.assertRaises(SystemExit):
            cloud.owned_playlist(spotify, "playlist123", {"id": "user123"})

        spotify.call.assert_called_once_with("GET", "/playlists/playlist123")
        spotify.playlists.assert_not_called()

    def test_rejects_playlist_not_owned_by_current_account(self):
        spotify = Mock()
        spotify.call.return_value = {
            "id": "playlist123",
            "owner": {"id": "another-user"},
        }
        with self.assertRaises(SystemExit):
            cloud.owned_playlist(spotify, "playlist123", {"id": "user123"})

    def test_rejects_mismatched_playlist_id(self):
        spotify = Mock()
        spotify.call.return_value = {
            "id": "different-id",
            "owner": {"id": "user123"},
        }
        spotify.playlists.return_value = []
        with self.assertRaises(SystemExit):
            cloud.owned_playlist(spotify, "playlist123", {"id": "user123"})

    def test_rejects_inaccessible_playlist(self):
        spotify = Mock()
        spotify.call.side_effect = manager.ManagerError("not found")
        spotify.playlists.return_value = []
        with self.assertRaises(SystemExit):
            cloud.owned_playlist(spotify, "playlist123", {"id": "user123"})


if __name__ == "__main__":
    unittest.main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Regression test module.
# Scope: Regression checks for the behavior named by this test module.
# Run: python -m unittest tests.test_spotify_playlist_cloud -v (from the repository root).
# Related: Implementation lives under scripts/; longer behavior notes live in docs/.
# -----------------------------------------------------------------------------
