"""Tests for conservative MusicBrainz recording-ID resolution."""
import unittest
from enrich_musicbrainz_recording_ids import norm


class RecordingIdResolutionTests(unittest.TestCase):
    def test_normalization(self):
        self.assertEqual(norm("  The  Song  "), "the song")

    def test_punctuation_and_case_are_not_fuzzy_erased(self):
        self.assertNotEqual(norm("Song (Live)"), norm("Song"))


if __name__ == "__main__":
    unittest.main()
