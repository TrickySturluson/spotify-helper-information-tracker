import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from scripts.spotify import spotify_discover_weekly_feedback as weekly


class DiscoverWeeklyFeedbackTests(unittest.TestCase):
    def _fixture(self, root, items, snapshot_id):
        catalog = root / "playlists.json"
        playlist_dir = root / "playlists"
        playlist_dir.mkdir(exist_ok=True)
        catalog.write_text(json.dumps({"playlists": [{"id": "weekly-id", "name": "Discover Weekly"}]}))
        snapshot = {
            "id": "weekly-id", "name": "Discover Weekly", "snapshot_id": snapshot_id,
            "items_snapshot_id": snapshot_id, "captured_at": "2026-11-02T10:00:00+00:00",
            "items_accessible": True, "total_items_reported": len(items),
            "item_count_fetched": len(items), "items": items,
        }
        (playlist_dir / "weekly-id.json").write_text(json.dumps(snapshot))
        return catalog, playlist_dir

    def test_first_snapshot_records_exposure_and_initial_liked_state(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            catalog, playlists = self._fixture(root, [{
                "uri": "spotify:track:abc", "id": "abc", "name": "Song",
                "artists": ["Artist"], "album": "Record",
            }], "s1")
            sp = Mock()
            sp.call.return_value = [True]
            result = weekly.observe(sp, catalog_path=catalog, playlist_dir=playlists,
                data_path=root / "feedback.json", scrobbles_path=root / "missing.json",
                observed_at="2026-11-02T11:00:00+00:00")
            saved = json.loads((root / "feedback.json").read_text())
            track = saved["tracks"]["spotify:track:abc"]
            self.assertEqual(result["newly_appeared"], 1)
            self.assertTrue(track["appearances"][0]["liked_at_appearance"])
            self.assertEqual(track["liked_observations"][0]["liked"], True)
            self.assertEqual(saved["coverage"]["explicit_hidden_events"], "unsupported_by_spotify_web_api")

    def test_changed_snapshot_records_disappearance_without_claiming_hidden(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            catalog, playlists = self._fixture(root, [{
                "uri": "spotify:track:new", "id": "new", "name": "New",
                "artists": ["Artist"], "album": "Record",
            }], "s2")
            data_path = root / "feedback.json"
            data_path.write_text(json.dumps({
                "version": 1, "playlist_id": "weekly-id", "tracks": {
                    "spotify:track:old": {"uri": "spotify:track:old", "appearances": [{"at": "2026-10-26T00:00:00+00:00"}], "liked_observations": []}
                }, "last_snapshot": {"snapshot_id": "s1", "uris": ["spotify:track:old"]},
                "snapshots": [], "coverage": {},
            }))
            sp = Mock()
            sp.call.return_value = [False, True]
            result = weekly.observe(sp, catalog_path=catalog, playlist_dir=playlists,
                data_path=data_path, scrobbles_path=root / "missing.json",
                observed_at="2026-11-02T11:00:00+00:00")
            saved = json.loads(data_path.read_text())
            event = saved["tracks"]["spotify:track:old"]["disappearance_events"][0]
            self.assertEqual(result["disappeared_since_previous_snapshot"], 1)
            self.assertIsNone(event["explicitly_hidden"])
            self.assertEqual(event["reason"], "absent_from_later_playlist_snapshot")

    def test_inaccessible_or_incomplete_snapshot_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            catalog, playlists = self._fixture(root, [], "s1")
            path = playlists / "weekly-id.json"
            snapshot = json.loads(path.read_text())
            snapshot["items_accessible"] = False
            path.write_text(json.dumps(snapshot))
            with self.assertRaises(RuntimeError):
                weekly.observe(Mock(), catalog_path=catalog, playlist_dir=playlists,
                    data_path=root / "feedback.json", scrobbles_path=root / "missing.json")

    def test_missing_or_ambiguous_playlist_does_not_guess(self):
        with self.assertRaises(RuntimeError):
            weekly.find_playlist({"playlists": []})
        with self.assertRaises(RuntimeError):
            weekly.find_playlist({"playlists": [
                {"id": "1", "name": "Discover Weekly"}, {"id": "2", "name": "Discover Weekly"}
            ]})


if __name__ == "__main__":
    unittest.main()


# FILE OVERVIEW
# Purpose: Regression tests for Discover Weekly exposure and feedback tracking.
# Coverage: First exposure, liked-at-appearance baseline, disappearance semantics,
#           inaccessible/incomplete snapshot fail-closed behavior, and playlist resolution.
# Run: python -m unittest tests.test_spotify_discover_weekly_feedback -v
# Related: scripts/spotify/spotify_discover_weekly_feedback.py.
