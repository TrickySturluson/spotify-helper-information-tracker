import json
from datetime import datetime, timezone
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
    def test_changed_snapshot_preserves_previous_complete_snapshot_in_history(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "assistant_data" / "spotify"
            playlists = root / "playlists"
            playlists.mkdir(parents=True)
            old = {
                "schema_version": 1, "captured_at": "2026-11-01T12:00:00+00:00",
                "id": "p1", "name": "Playlist", "snapshot_id": "old-snapshot",
                "total_items_reported": 1, "item_count_fetched": 1,
                "items_accessible": True,
                "items": [{"uri": "spotify:track:old", "name": "Old",
                           "artists": ["Artist"], "type": "track"}],
            }
            (playlists / "p1.json").write_text(json.dumps(old), encoding="utf-8")
            sp = Mock()
            sp.playlists.return_value = [{
                "id": "p1", "name": "Playlist", "owner": {"id": "owner"},
                "snapshot_id": "new-snapshot", "items": {"total": 1},
                "public": True, "collaborative": False,
            }]
            sp.items.return_value = [{
                "item": {"id": "new", "uri": "spotify:track:new", "name": "New",
                         "artists": [{"name": "Artist", "id": "artist"}],
                         "album": {"name": "Album"}, "duration_ms": 1000},
                "added_at": None,
            }]
            with patch.object(library, "ROOT", root), \
                 patch.object(library, "CATALOG", root / "playlists.json"), \
                 patch.object(library, "PLAYLIST_DIR", playlists), \
                 patch.object(library, "HISTORY_DIR", root / "history"), \
                 patch.object(library, "INDEX", root / "reference_index.json"), \
                 patch.object(library, "MusicLibrary") as music_library:
                music_library.return_value.put_catalogue.return_value = {
                    "songs": 1, "artists": 1, "albums": 1,
                }
                library.sync(sp)
            history = list((root / "history" / "p1").glob("*.json"))
            records = [json.loads(path.read_text(encoding="utf-8")) for path in history]
            self.assertTrue(any(row.get("snapshot_id") == "old-snapshot" for row in records))
            self.assertTrue(any(row.get("snapshot_id") == "new-snapshot" for row in records))
            current = json.loads((playlists / "p1.json").read_text(encoding="utf-8"))
            self.assertEqual(current["snapshot_id"], "new-snapshot")

    def test_playability_refresh_plan_is_bounded_and_skips_recent_market_observations(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            lib = library.MusicLibrary(root / "library")
            ids = ["1234567890123456789012", "2345678901234567890123", "3456789012345678901234"]
            lib.put_catalogue([{
                "track_id": "spotify:track:" + spotify_id, "spotify_id": spotify_id,
                "artist": "Artist", "track": "Song " + str(i),
            } for i, spotify_id in enumerate(ids)])
            lib.add_spotify_playability_observation(ids[0], {
                "status": "playable", "is_playable": True, "market": "from_token",
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "requested_spotify_id": ids[0],
            })
            plan = library.refresh_playability_from_spotify(
                library_root=root / "library", limit=2, stale_days=90, execute=False,
            )
            self.assertEqual(plan["provider_requests"], 0)
            self.assertEqual(plan["selected_count"], 2)
            self.assertNotIn(ids[0], [row["spotify_id"] for row in plan["selected"]])

    def test_playability_refresh_records_relink_result_on_requested_song(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = "1234567890123456789012"
            replacement = "2345678901234567890123"
            lib = library.MusicLibrary(root / "library")
            lib.put_catalogue([{
                "track_id": "spotify:track:" + original, "spotify_id": original,
                "artist": "Artist", "track": "Song",
            }])

            class FakeSpotify:
                def __init__(self):
                    self.calls = []
                def track(self, spotify_id, market=None):
                    self.calls.append((spotify_id, market))
                    return {
                        "id": replacement, "is_playable": True,
                        "linked_from": {"id": original, "uri": "spotify:track:" + original},
                        "restrictions": {},
                    }

            fake = FakeSpotify()
            result = library.refresh_playability_from_spotify(
                library_root=root / "library", limit=1, stale_days=90,
                market="from_token", sp=fake, execute=True, sleep_seconds=0,
            )
            self.assertEqual(fake.calls, [(original, "from_token")])
            self.assertEqual(result["provider_requests"], 1)
            self.assertEqual(result["updated"], 1)
            self.assertTrue(Path(result["backup_path"]).is_dir())
            song = library.MusicLibrary(root / "library").get_song(spotify_id=original)["song"]
            observation = song["evidence"]["spotify_playability"]["observations"][0]
            self.assertEqual(observation["requested_spotify_id"], original)
            self.assertEqual(observation["returned_spotify_id"], replacement)
            self.assertEqual(observation["status"], "playable")

    def test_playability_refresh_records_404_as_unknown_not_false(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spotify_id = "1234567890123456789012"
            lib = library.MusicLibrary(root / "library")
            lib.put_catalogue([{
                "track_id": "spotify:track:" + spotify_id, "spotify_id": spotify_id,
                "artist": "Artist", "track": "Song",
            }])

            class MissingSpotify:
                def track(self, requested_id, market=None):
                    raise library.manager.ManagerError("Spotify API request failed: HTTP 404")

            result = library.refresh_playability_from_spotify(
                library_root=root / "library", limit=1, stale_days=90,
                sp=MissingSpotify(), execute=True, sleep_seconds=0,
            )
            self.assertEqual(result["not_found_or_unavailable"], 1)
            song = library.MusicLibrary(root / "library").get_song(spotify_id=spotify_id)["song"]
            observation = song["evidence"]["spotify_playability"]["observations"][0]
            self.assertEqual(observation["status"], "unknown")
            self.assertIsNone(observation["is_playable"])
            self.assertEqual(observation["response_status"], 404)

    def test_backfill_playability_from_saved_snapshots_is_offline_and_backup_protected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            library_root = root / "music" / "library"
            playlist_dir = root / "playlists"
            playlist_dir.mkdir()
            music_library = library.MusicLibrary(library_root)
            music_library.put_catalogue([{
                "track_id": "spotify:track:abc", "spotify_id": "abc",
                "artist": "Artist", "track": "Song",
            }])
            snapshot = {
                "id": "playlist-1", "snapshot_id": "snapshot-1",
                "items_accessible": True,
                "last_items_accessible_at": "2026-11-02T10:00:00+00:00",
                "items": [{
                    "type": "track", "id": "abc", "name": "Song",
                    "artists": ["Artist"], "is_playable": False,
                    "restrictions": {"reason": "market"},
                }],
            }
            (playlist_dir / "playlist-1.json").write_text(json.dumps(snapshot), encoding="utf-8")
            result = library.backfill_playability_from_snapshots(playlist_dir, library_root)
            self.assertEqual(result["provider_requests"], 0)
            self.assertEqual(result["spotify_playlist_writes"], 0)
            self.assertEqual(result["updated"], 1)
            self.assertTrue(Path(result["backup_path"]).is_dir())
            song = library.MusicLibrary(library_root).get_song(spotify_id="abc")["song"]
            observation = song["evidence"]["spotify_playability"]["observations"][0]
            self.assertEqual(observation["market"], "from_token")
            self.assertEqual(observation["status"], "restricted")
            self.assertEqual(observation["checked_at"], "2026-11-02T10:00:00+00:00")

    def test_relinked_playability_uses_original_requested_id(self):
        observation = library.playability_observation({
            "id": "replacement", "linked_from": "spotify:track:original",
            "is_playable": True, "is_playable_present": True,
            "playability_market": "from_token",
        }, "playlist", "snapshot", "2026-11-02T10:00:00+00:00")
        self.assertEqual(observation["requested_spotify_id"], "original")
        self.assertEqual(observation["returned_spotify_id"], "replacement")
        self.assertEqual(observation["linked_from_spotify_id"], "original")
        self.assertEqual(observation["market"], "from_token")

    def test_playability_observation_distinguishes_unplayable_and_restricted(self):
        unplayable = library.playability_observation({
            "id": "requested", "is_playable": False,
            "is_playable_present": True, "playability_checked_at": "2026-11-02T10:00:00+00:00",
        }, "playlist", "snapshot")
        restricted = library.playability_observation({
            "id": "requested", "is_playable": False,
            "is_playable_present": True, "restrictions": {"reason": "market"},
            "linked_from": "spotify:track:original",
            "playability_checked_at": "2026-11-02T11:00:00+00:00",
        }, "playlist", "snapshot")
        self.assertEqual(unplayable["status"], "unplayable")
        self.assertEqual(restricted["status"], "restricted")
        self.assertEqual(restricted["market"], "unknown")
        self.assertEqual(restricted["linked_from_spotify_id"], "original")
        self.assertEqual(restricted["restrictions_reason"], "market")

    def test_playability_observation_ignores_missing_field_and_keeps_unknown_market(self):
        self.assertIsNone(library.playability_observation({
            "id": "requested", "is_playable": None, "is_playable_present": False,
        }, "playlist", "snapshot"))
        observation = library.playability_observation({
            "id": "requested", "is_playable": None, "is_playable_present": True,
        }, "playlist", "snapshot", "2026-11-02T12:00:00+00:00")
        self.assertEqual(observation["status"], "unknown")
        self.assertEqual(observation["market"], "unknown")
        self.assertEqual(observation["checked_at"], "2026-11-02T12:00:00+00:00")

    def test_item_record_preserves_explicit_unplayable_state_and_restriction(self):
        row = library.item_record({
            "item": {
                "id": "spotify-id", "uri": "spotify:track:spotify-id",
                "type": "track", "name": "Unavailable Song",
                "artists": [{"id": "artist-id", "name": "Artist"}],
                "is_playable": False,
                "restrictions": {"reason": "market"},
                "linked_from": {"uri": "spotify:track:original-id"},
            }
        }, 0)
        self.assertFalse(row["is_playable"])
        self.assertTrue(row["is_playable_present"])
        self.assertEqual(row["restrictions"]["reason"], "market")
        self.assertEqual(row["linked_from"], "spotify:track:original-id")
        self.assertIsNotNone(row["playability_checked_at"])

    def test_item_record_does_not_turn_missing_playability_into_false(self):
        row = library.item_record({
            "item": {
                "id": "spotify-id", "type": "track", "name": "Unknown Song",
                "artists": [{"name": "Artist"}],
            }
        }, 0)
        self.assertIsNone(row["is_playable"])
        self.assertFalse(row["is_playable_present"])
        self.assertIsNone(row["playability_checked_at"])

    def test_unchanged_snapshot_reuses_cached_items_without_spotify_item_request(self):
        cached = {
            "id": "playlist123", "name": "Cached",
            "snapshot_id": "same-snapshot",
            "items_snapshot_id": "same-snapshot",
            "items_accessible": True,
            "item_count_fetched": 1,
            "items": [{"uri": "spotify:track:cached", "name": "Cached Track", "artists": ["Artist"]}],
        }
        playlist = {
            "id": "playlist123", "name": "Cached",
            "owner": {"id": "owner"}, "snapshot_id": "same-snapshot",
            "items": {"total": 1}, "public": True, "collaborative": False,
        }
        sp = Mock()
        record = library.playlist_record(sp, playlist, cached)
        sp.items.assert_not_called()
        self.assertEqual(record["items"], cached["items"])
        self.assertEqual(record["items_snapshot_id"], "same-snapshot")
        self.assertTrue(record["items_accessible"])
        self.assertEqual(record["playability_market"], "from_token")

    def test_item_endpoint_404_is_recorded_as_inaccessible(self):
        sp = Mock()
        sp.items.side_effect = manager.ManagerError(
            "Spotify API GET /playlists/restricted/items: HTTP 404"
        )
        record = library.playlist_record(sp, {
            "id": "restricted", "name": "Restricted",
            "snapshot_id": "snapshot-1", "items": {"total": 3},
        })
        self.assertFalse(record["items_accessible"])
        self.assertEqual(record["items"], [])
        self.assertIn("HTTP 404", record["items_error"])
        self.assertIsNone(record["items_snapshot_id"])
        sp.items.assert_called_once_with("restricted", market="from_token")

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

    def test_malformed_jsonl_rows_and_durations_do_not_crash_observation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / "daily.json"
            segments = root / "segments.jsonl"
            with patch.object(feedback, "DATA", data):
                feedback.record_additions([{"uri": "spotify:track:abc"}], "2026-10-31T00:00:00+00:00")
                segments.write_text(
                    json.dumps(["not", "an", "object"]) + "\n" +
                    json.dumps({"spotify_uri": ["not", "a", "uri"], "started_at": "2026-10-31T01:00:00+00:00"}) + "\n" +
                    json.dumps({"spotify_uri": "spotify:track:abc", "started_at": "2026-10-31T01:00:00+00:00", "played_ms": "bad"}) + "\n" +
                    json.dumps({"spotify_uri": "spotify:track:abc", "started_at": "2026-10-31T01:00:10+00:00", "played_ms": -100}) + "\n",
                    encoding="utf-8",
                )
                feedback.observe_playback_segments(segments)
                result = feedback.feedback_for("spotify:track:abc")
                self.assertEqual(result["post_add_measured_plays"], 1)
                self.assertEqual(result["post_add_playback_ms"], 0)
                self.assertEqual(feedback.read()["coverage"]["playback_tracker_detail"]["segment_count"], 2)

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


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Regression test module.
# Scope: Regression checks for the behavior named by this test module.
# Run: python -m unittest tests.test_spotify_reference_library -v (from the repository root).
# Related: Implementation lives under scripts/; longer behavior notes live in docs/.
# -----------------------------------------------------------------------------
