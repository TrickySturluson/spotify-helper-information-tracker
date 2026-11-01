import json
import tempfile
import unittest
from pathlib import Path
from enrich_musicbrainz_recording_ids import norm, recent_priority


class RecordingIdResolutionTests(unittest.TestCase):
    def test_normalization(self):
        self.assertEqual(norm("  The  Song  "), "the song")

    def test_punctuation_and_case_are_not_fuzzy_erased(self):
        self.assertNotEqual(norm("Song (Live)"), norm("Song"))

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
