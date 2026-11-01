import unittest
from enrich_musicbrainz_recording_ids import norm


class RecordingIdResolutionTests(unittest.TestCase):
    def test_normalization(self):
        self.assertEqual(norm("  The  Song  "), "the song")

    def test_punctuation_and_case_are_not_fuzzy_erased(self):
        self.assertNotEqual(norm("Song (Live)"), norm("Song"))


if __name__ == "__main__":
    unittest.main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Regression test module.
# Scope: Regression checks for the behavior named by this test module.
# Run: python -m unittest tests.test_musicbrainz_recording_ids -v (from the repository root).
# Related: Implementation lives under scripts/; longer behavior notes live in docs/.
# -----------------------------------------------------------------------------
