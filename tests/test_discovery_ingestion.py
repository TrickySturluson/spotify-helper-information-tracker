import json
import tempfile
import unittest
from pathlib import Path

from scripts.music.discovery_ingestion import append_candidates


class DiscoveryIngestionTests(unittest.TestCase):
    def test_retry_is_idempotent_but_new_daily_context_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "candidates.json"
            row = {"uri": "spotify:track:abc123", "artist": "Artist", "name": "Song", "album": "Release"}
            first = append_candidates([row], source="tricky_daily_recommendations",
                context={"cycle_date_eastern": "2026-11-01"}, observed_at="2026-11-01T04:00:00Z", path=path)
            retry = append_candidates([row], source="tricky_daily_recommendations",
                context={"cycle_date_eastern": "2026-11-01"}, observed_at="2026-11-01T04:05:00Z", path=path)
            next_day = append_candidates([row], source="tricky_daily_recommendations",
                context={"cycle_date_eastern": "2026-11-02"}, observed_at="2026-11-02T04:00:00Z", path=path)
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(first["new_candidates"], 1)
            self.assertEqual(retry["new_candidates"], 0)
            self.assertEqual(next_day["new_candidates"], 0)
            self.assertEqual(len(saved), 1)
            self.assertEqual(len(saved[0]["discovery_evidence"]), 2)

    def test_discovery_does_not_infer_listening_or_preference(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "candidates.json"
            append_candidates([{"spotify_id": "abc", "artist": "Artist", "track": "Song"}], path=path)
            saved = json.loads(path.read_text(encoding="utf-8"))[0]
            self.assertEqual(saved["listening_evidence"], {"plays": None, "scrobbles": None, "saved": None})
            self.assertEqual(len(saved["discovery_evidence"]), 1)

    def test_invalid_candidates_are_skipped_and_existing_metadata_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "candidates.json"
            append_candidates([{"spotify_id": "abc", "artist": "Verified Artist", "track": "Verified Song",
                "track_mbid": "mbid-1"}], path=path)
            result = append_candidates([None, {"spotify_id": "missing-title", "artist": "Artist"},
                {"spotify_id": "abc", "artist": "Other Artist", "track": "Other Song"}], path=path)
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(result["input_rows"], 3)
            self.assertEqual(len(saved), 1)
            self.assertEqual(saved[0]["artist"], "Verified Artist")
            self.assertEqual(saved[0]["track"], "Verified Song")
            self.assertEqual(saved[0]["track_mbid"], "mbid-1")


if __name__ == "__main__":
    unittest.main()


# FILE OVERVIEW
# Purpose: Regression coverage for recommendation/discovery candidate persistence.
# Coverage: Retry idempotence, distinct daily evidence, neutral listening boundaries,
#           invalid-row handling, and preservation of existing metadata.
# Run: python -m unittest tests.test_discovery_ingestion -v
# Related: scripts/music/discovery_ingestion.py; scripts/spotify/spotify_daily_cycle.py.
