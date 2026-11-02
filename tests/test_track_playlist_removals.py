import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import track_playlist_removals as removals


class RemovalBaselineTests(unittest.TestCase):
    def test_targeted_refresh_fails_when_playlist_cannot_be_read(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(removals, "BASELINE", root / "baseline.json"), patch.object(
                removals, "BLACKLIST", root / "blacklist.json"
            ), patch.object(sys, "argv", ["track_playlist_removals.py", "playlist"]), patch.object(
                removals.manager, "Spotify", return_value=object()
            ), patch.object(
                removals.manager, "fetch_playlist", return_value={"id": "playlist", "name": "Booze"}
            ), patch.object(
                removals, "process_playlist", side_effect=removals.manager.ManagerError("temporary API failure")
            ):
                with self.assertRaisesRegex(SystemExit, "Could not refresh removal history for Booze"):
                    removals.main()

    def test_seed_uses_only_complete_accessible_reference_snapshots(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spotify = root / "assistant_data" / "spotify"
            (spotify / "playlists").mkdir(parents=True)
            (spotify / "playlists.json").write_text(json.dumps({
                "playlists": [
                    {"id": "complete", "name": "Complete"},
                    {"id": "incomplete", "name": "Incomplete"},
                ]
            }))
            (spotify / "playlists" / "complete.json").write_text(json.dumps({
                "name": "Complete", "items_accessible": True,
                "total_items_reported": 1, "item_count_fetched": 1,
                "items": [{"uri": "spotify:track:one", "name": "One",
                           "artists": ["Artist"], "album": "Album"}],
            }))
            (spotify / "playlists" / "incomplete.json").write_text(json.dumps({
                "name": "Incomplete", "items_accessible": False,
                "total_items_reported": 2, "item_count_fetched": 0, "items": [],
            }))
            baseline_path = root / "baseline.json"
            blacklist_path = root / "blacklist.json"
            with patch.object(removals, "BASELINE", baseline_path), patch.object(
                removals, "BLACKLIST", blacklist_path
            ), patch("track_playlist_removals.Path", Path):
                old = Path.cwd()
                import os
                os.chdir(root)
                try:
                    baseline = {"version": 1, "playlists": {}}
                    seeded, skipped = removals.seed_from_reference_library(baseline)
                finally:
                    os.chdir(old)
            self.assertEqual((seeded, skipped), (1, 1))
            saved = json.loads(baseline_path.read_text())
            self.assertEqual(saved["playlists"]["complete"][0]["uri"], "spotify:track:one")
            self.assertNotIn("incomplete", saved["playlists"])

    def test_removal_comparison_adds_playlist_local_sticky_feedback(self):
        baseline = {"version": 1, "playlists": {
            "booze": [{"uri": "spotify:track:gone", "name": "Gone",
                       "artists": ["Artist"], "album": "Album"},
                      {"uri": "spotify:track:stay", "name": "Stay",
                       "artists": ["Artist"], "album": "Album"}]
        }}
        blacklist = {"version": 1, "playlists": {"booze": {"name": "Booze", "removed": []}}}
        removals.process_removal_rows(
            "booze", "Booze",
            [{"uri": "spotify:track:stay", "name": "Stay", "artists": ["Artist"], "album": "Album"}],
            baseline, blacklist,
        )
        self.assertEqual([row["uri"] for row in blacklist["playlists"]["booze"]["removed"]],
                         ["spotify:track:gone"])
        self.assertEqual([row["uri"] for row in baseline["playlists"]["booze"]],
                         ["spotify:track:stay"])


if __name__ == "__main__":
    unittest.main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Verify safe baseline seeding and playlist-local manual-removal feedback.
# Coverage: Complete-snapshot filtering, no false empty-list baselines, and sticky
#           URI-based removal records after a playlist changes.
# Related: scripts/spotify/track_playlist_removals.py and the Spotify reference
#          library workflow.
# -----------------------------------------------------------------------------
