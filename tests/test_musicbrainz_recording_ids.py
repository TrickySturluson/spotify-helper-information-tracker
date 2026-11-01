import json
import tempfile
import unittest
from pathlib import Path
from enrich_musicbrainz_recording_ids import norm, recent_priority, spotify_isrc_index, unique_exact_recording


class RecordingIdResolutionTests(unittest.TestCase):
    def test_normalization(self):
        self.assertEqual(norm("  The  Song  "), "the song")

    def test_punctuation_and_case_are_not_fuzzy_erased(self):
        self.assertNotEqual(norm("Song (Live)"), norm("Song"))


    def test_spotify_snapshot_isrc_index_uses_only_accessible_exact_tracks(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "good.json").write_text(json.dumps({
                "items_accessible": True,
                "items": [{
                    "type": "track", "name": "Song", "artists": ["Artist"],
                    "external_ids": {"isrc": "usabc2600001"},
                }],
            }), encoding="utf-8")
            (root / "partial.json").write_text(json.dumps({
                "items_accessible": False,
                "items": [{
                    "type": "track", "name": "Wrong", "artists": ["Artist"],
                    "external_ids": {"isrc": "USABC2600002"},
                }],
            }), encoding="utf-8")
            index = spotify_isrc_index(root)
        self.assertEqual(index[("artist", "song")], {"USABC2600001"})
        self.assertNotIn(("artist", "wrong"), index)

    def test_isrc_recording_match_still_requires_exact_artist_and_title(self):
        rows = [
            {"id": "one", "title": "Song", "artist-credit-phrase": "Artist"},
            {"id": "two", "title": "Song (Live)", "artist-credit-phrase": "Artist"},
        ]
        row, status = unique_exact_recording(rows, "Artist", "Song")
        self.assertEqual(row["id"], "one")
        self.assertEqual(status, "matched")
        row, status = unique_exact_recording(rows + [
            {"id": "three", "title": "Song", "artist-credit-phrase": "Artist"}
        ], "Artist", "Song")
        self.assertIsNone(row)
        self.assertEqual(status, "ambiguous")

    def test_recent_priority_preserves_rank_and_exact_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "recent.json"
            path.write_text(json.dumps({"tracks": [
                {"artist": "Artist A", "track": "Track A"},
                {"artist": "Artist B", "track": "Track B"},
            ]}), encoding="utf-8")
            priority = recent_priority(path)
        self.assertEqual(priority[("artist a", "track a")], 0)
        self.assertEqual(priority[("artist b", "track b")], 1)
        self.assertNotIn(("artist a", "track (live)"), priority)


if __name__ == "__main__":
    unittest.main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Regression test module.
# Scope: Regression checks for the behavior named by this test module.
# Run: python -m unittest tests.test_musicbrainz_recording_ids -v (from the repository root).
# Related: Implementation lives under scripts/; longer behavior notes live in docs/.
# -----------------------------------------------------------------------------
