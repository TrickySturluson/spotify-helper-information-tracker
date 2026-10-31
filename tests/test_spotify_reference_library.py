import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import spotify_daily_feedback as feedback
import spotify_playlist_manager as manager
import spotify_reference_library as library


class PlaylistPermissionTests(unittest.TestCase):
    def test_only_approved_exception_or_registered_created_playlist_is_mutable(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "managed_playlists.json"
            path.write_text(json.dumps({
                "version": 1,
                "managed": {"assistant-made": {"provenance": "created_by_shit"}},
                "approved_exceptions": {"4yUVHSMQySfWeEowfIMcx7": {"name": "Tricky Daily"}},
            }))
            with patch.object(manager, "Path", Path), patch(
                "spotify_playlist_manager.Path", Path
            ):
                # Redirect the registry's relative path without changing the production default.
                import os
                old = os.getcwd()
                os.chdir(directory)
                try:
                    (Path("assistant_data/spotify")).mkdir(parents=True)
                    (Path("assistant_data/spotify/managed_playlists.json")).write_text(path.read_text())
                    manager.assert_managed("assistant-made")
                    manager.assert_managed("4yUVHSMQySfWeEowfIMcx7")
                    with self.assertRaises(manager.ManagerError):
                        manager.assert_managed("personal-playlist")
                finally:
                    os.chdir(old)


class DailyFeedbackObservationTests(unittest.TestCase):
    def test_observe_all_refreshes_likes_playback_and_lastfm_without_playlist_edits(self):
        with tempfile.TemporaryDirectory() as directory:
            data_path = Path(directory) / "daily.json"
            with patch.object(feedback, "DATA", data_path):
                feedback.record_additions([{"uri": "spotify:track:a"}], "2026-10-30T10:00:00+00:00")
                sp = Mock()
                with patch.object(feedback, "observe_liked_songs", return_value={"spotify:track:a": True}) as liked, patch.object(feedback, "observe_playback_segments") as playback, patch.object(feedback, "observe_lastfm_scrobbles") as lastfm:
                    result = feedback.observe_all(sp, Path(directory) / "segments.jsonl", Path(directory) / "scrobbles.json")
                liked.assert_called_once_with(sp, ["spotify:track:a"])
                playback.assert_called_once()
                lastfm.assert_called_once()
                self.assertEqual(result["tracks"], 1)
                self.assertEqual(result["liked_tracks_checked"], 1)


class ReferenceLibraryIntegrityTests(unittest.TestCase):
    def test_inaccessible_playlist_preserves_last_known_tracklist(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "assistant_data" / "spotify"
            playlists = root / "playlists"
            playlists.mkdir(parents=True)
            old = {
                "id": "restricted", "name": "Previously Indexed",
                "owner": {"id": "owner"}, "snapshot_id": "old-snapshot",
                "items_snapshot_id": "old-snapshot", "items_accessible": True,
                "item_count_fetched": 1, "total_items_reported": 1,
                "captured_at": "2026-10-01T00:00:00+00:00",
                "items": [{"uri": "spotify:track:known", "name": "Known Track", "artists": ["Artist"]}],
            }
            (playlists / "restricted.json").write_text(json.dumps(old))
            (root / "playlists.json").write_text(json.dumps({"version": 1, "playlists": [{"id": "restricted"}]}))
            sp = Mock()
            sp.playlists.return_value = [{
                "id": "restricted", "name": "Previously Indexed",
                "owner": {"id": "owner"}, "snapshot_id": "new-snapshot",
                "items": {"total": 1},
            }]
            sp.items.side_effect = manager.ManagerError("Spotify API GET /playlists/restricted/items: HTTP 403")
            with patch.object(library, "ROOT", root), patch.object(library, "CATALOG", root / "playlists.json"), patch.object(library, "PLAYLIST_DIR", playlists), patch.object(library, "HISTORY_DIR", root / "history"), patch.object(library, "INDEX", root / "reference_index.json"):
                library.sync(sp)
                saved = json.loads((playlists / "restricted.json").read_text())
                catalog = json.loads((root / "playlists.json").read_text())
                self.assertFalse(saved["items_accessible"])
                self.assertEqual(saved["items"][0]["uri"], "spotify:track:known")
                self.assertEqual(saved["item_count_fetched"], 1)
                self.assertEqual(catalog["playlists"][0]["item_count"], 1)
                self.assertFalse(catalog["playlists"][0]["changed"])
                report = json.loads((root / "health.json").read_text())
                self.assertEqual(report["playlists"]["inaccessible"], 1)
                self.assertEqual(report["index"]["unique_tracks"], 1)

    def test_health_report_flags_item_count_mismatch_and_missing_tracker(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "assistant_data" / "spotify"
            root.mkdir(parents=True)
            (root / "daily_feedback.json").write_text(json.dumps({
                "tracks": {"spotify:track:a": {}},
                "coverage": {"playback_tracker": "unknown", "lastfm": "available"},
            }))
            row = {"id": "p1", "name": "Playlist", "record_path": str(root / "p1.json"), "items_accessible": True, "item_count": 2}
            Path(row["record_path"]).write_text(json.dumps({"total_items_reported": 3, "item_count_fetched": 2}))
            with patch.object(library, "ROOT", root), patch.object(library, "CATALOG", root / "playlists.json"), patch.object(library, "PLAYLIST_DIR", root / "playlists"), patch.object(library, "INDEX", root / "reference_index.json"):
                report = library.build_health_report([row], {"a": ["p1"]}, {"artist": ["p1"]})
                self.assertEqual(report["overall_status"], "warning")
                self.assertEqual(report["playlists"]["incomplete"], 1)
                self.assertEqual(report["daily_feedback"]["playback_tracker_status"], "unknown")
                self.assertFalse(report["daily_feedback"]["segments_file_in_sync_environment"])

    def test_first_inaccessible_fetch_does_not_create_empty_history_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "assistant_data" / "spotify"
            playlists = root / "playlists"
            sp = Mock()
            sp.playlists.return_value = [{
                "id": "restricted-first-sync", "name": "Restricted",
                "owner": {"id": "owner"}, "snapshot_id": "snapshot-1",
                "items": {"total": 4}, "public": False, "collaborative": False,
            }]
            sp.items.side_effect = manager.ManagerError(
                "Spotify API GET /playlists/restricted-first-sync/items: HTTP 403"
            )
            with patch.object(library, "ROOT", root), \
                 patch.object(library, "CATALOG", root / "playlists.json"), \
                 patch.object(library, "PLAYLIST_DIR", playlists), \
                 patch.object(library, "HISTORY_DIR", root / "history"), \
                 patch.object(library, "INDEX", root / "reference_index.json"):
                library.sync(sp)
            saved = json.loads((playlists / "restricted-first-sync.json").read_text())
            self.assertFalse(saved["items_accessible"])
            self.assertEqual(saved["items"], [])
            self.assertFalse(list((root / "history" / "restricted-first-sync").glob("*.json")))

    def test_duplicate_playlist_ids_are_processed_once(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "assistant_data" / "spotify"
            playlists = root / "playlists"
            sp = Mock()
            duplicate = {
                "id": "same-id", "name": "Repeated page result",
                "owner": {"id": "owner", "display_name": "Owner"},
                "snapshot_id": "snapshot-1", "items": {"total": 1},
                "public": True, "collaborative": False,
            }
            sp.playlists.return_value = [duplicate, dict(duplicate)]
            sp.items.return_value = [{
                "item": {"id": "track-1", "uri": "spotify:track:track-1",
                         "name": "Track", "artists": [{"name": "Artist", "id": "artist-1"}]},
                "added_at": None,
            }]
            with patch.object(library, "ROOT", root), \
                 patch.object(library, "CATALOG", root / "playlists.json"), \
                 patch.object(library, "PLAYLIST_DIR", playlists), \
                 patch.object(library, "HISTORY_DIR", root / "history"), \
                 patch.object(library, "INDEX", root / "reference_index.json"):
                library.sync(sp)
            catalog = json.loads((root / "playlists.json").read_text())
            index = json.loads((root / "reference_index.json").read_text())
            self.assertEqual(catalog["playlist_count"], 1)
            self.assertEqual([row["id"] for row in catalog["playlists"]], ["same-id"])
            self.assertEqual(sp.items.call_count, 1)
            self.assertEqual(index["track_playlists"]["spotify:track:track-1"], ["same-id"])
            self.assertEqual(index["artist_playlists"]["artist"], ["same-id"])


class DailyFeedbackTests(unittest.TestCase):
    def test_no_observation_is_unknown_not_negative(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(feedback, "DATA", Path(directory) / "daily.json"):
                feedback.record_additions([{"uri": "spotify:track:abc"}], "2026-10-31T10:00:00+00:00")
                result = feedback.feedback_for("spotify:track:abc")
                self.assertEqual(result["status"], "unknown")
                self.assertTrue(result["no_listening_is_neutral"])
                self.assertIsNone(result["liked"])
                self.assertIsNone(result["post_add_measured_plays"])

    def test_liked_song_observation_is_retained(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(feedback, "DATA", Path(directory) / "daily.json"):
                feedback.record_additions([{"uri": "spotify:track:abc"}], "2026-10-31T10:00:00+00:00")
                sp = Mock()
                sp.call.return_value = [True]
                feedback.observe_liked_songs(sp, ["spotify:track:abc"])
                self.assertTrue(feedback.feedback_for("spotify:track:abc")["liked"])

    def test_lastfm_scrobbles_are_counted_after_addition(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(feedback, "DATA", root / "daily.json"):
                feedback.record_additions([{
                    "uri": "spotify:track:abc", "artist": "Artist", "track": "Song"
                }], "2026-10-31T10:00:00+00:00")
                archive = root / "scrobbles.json"
                archive.write_text(json.dumps([
                    {"artist": "Artist", "track": "Song", "timestamp": 1793441000},
                    {"artist": "Artist", "track": "Song", "timestamp": 1793444600},
                ]))
                feedback.observe_lastfm_scrobbles(archive)
                result = feedback.feedback_for("spotify:track:abc")
                self.assertEqual(result["post_add_lastfm_scrobbles"], 2)

    def test_repeated_additions_keep_each_liked_baseline(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(feedback, "DATA", Path(directory) / "daily.json"):
                feedback.record_additions([{"uri": "spotify:track:abc"}], "2026-10-30T10:00:00+00:00", {"spotify:track:abc": False})
                feedback.record_additions([{"uri": "spotify:track:abc"}], "2026-10-31T10:00:00+00:00", {"spotify:track:abc": True})
                result = feedback.feedback_for("spotify:track:abc")
                self.assertEqual(result["additions"], 2)
                self.assertEqual([x["liked_at_add"] for x in result["addition_history"]], [False, True])
                self.assertTrue(result["liked_before_or_at_add"])

    def test_lastfm_counts_are_cumulative_from_first_daily_addition(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(feedback, "DATA", root / "daily.json"):
                feedback.record_additions([{"uri": "spotify:track:abc", "artist": "Artist", "track": "Song"}], "2026-10-30T10:00:00+00:00")
                feedback.record_additions([{"uri": "spotify:track:abc", "artist": "Artist", "track": "Song"}], "2026-10-31T10:00:00+00:00")
                archive = root / "scrobbles.json"
                archive.write_text(json.dumps([
                    {"artist": "Artist", "track": "Song", "timestamp": 1793358000},
                    {"artist": "Artist", "track": "Song", "timestamp": 1793444600},
                ]))
                feedback.observe_lastfm_scrobbles(archive)
                self.assertEqual(feedback.feedback_for("spotify:track:abc")["post_add_lastfm_scrobbles"], 2)

    def test_malformed_playback_timestamps_do_not_count_as_coverage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / "daily.json"
            segments = root / "segments.jsonl"
            with patch.object(feedback, "DATA", data):
                feedback.record_additions([{"uri": "spotify:track:abc"}], "2026-10-31T10:00:00+00:00")
                segments.write_text(
                    json.dumps({"spotify_uri": "spotify:track:abc", "started_at": "not-a-timestamp", "played_ms": 30000}) + "\n" +
                    json.dumps({"spotify_uri": "spotify:track:abc", "started_at": 12345, "played_ms": 30000}) + "\n"
                )
                feedback.observe_playback_segments(segments)
                result = feedback.read()
                self.assertEqual(result["coverage"]["playback_tracker"], "unknown")
                self.assertEqual(result["coverage"]["playback_tracker_detail"]["segment_count"], 0)
                self.assertIsNone(result["coverage"]["playback_tracker_detail"]["latest_segment_at"])

    def test_latest_playback_timestamp_is_normalized_to_utc(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / "daily.json"
            segments = root / "segments.jsonl"
            with patch.object(feedback, "DATA", data):
                feedback.record_additions([{"uri": "spotify:track:abc"}], "2026-10-31T00:00:00+00:00")
                segments.write_text(
                    json.dumps({"spotify_uri": "spotify:track:abc", "started_at": "2026-10-31T01:00:00+02:00", "played_ms": 30000}) + "\n" +
                    json.dumps({"spotify_uri": "spotify:track:abc", "started_at": "2026-10-31T00:30:00+00:00", "played_ms": 30000}) + "\n"
                )
                feedback.observe_playback_segments(segments)
                detail = feedback.read()["coverage"]["playback_tracker_detail"]
                self.assertEqual(detail["latest_segment_at"], "2026-10-31T00:30:00+00:00")
                self.assertEqual(detail["segment_count"], 2)

    def test_post_add_playback_ignores_pre_add_intervals(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / "daily.json"
            segments = root / "segments.jsonl"
            with patch.object(feedback, "DATA", data):
                feedback.record_additions([{"uri": "spotify:track:abc"}], "2026-10-31T10:00:00+00:00")
                segments.write_text(
                    json.dumps({"spotify_uri": "spotify:track:abc", "started_at": "2026-10-31T09:00:00+00:00", "played_ms": 30000}) + "\n" +
                    json.dumps({"spotify_uri": "spotify:track:abc", "started_at": "2026-10-31T11:00:00+00:00", "played_ms": 45000}) + "\n"
                )
                feedback.observe_playback_segments(segments)
                result = feedback.feedback_for("spotify:track:abc")
                self.assertEqual(result["post_add_measured_plays"], 1)
                self.assertEqual(result["post_add_playback_ms"], 45000)


if __name__ == "__main__":
    unittest.main()
