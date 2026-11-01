import unittest
from scripts.music.music_evidence import identity_confidence, metadata_confidence

class MusicEvidenceTests(unittest.TestCase):
    def test_exact_stable_ids_are_high_confidence(self):
        for method in ("spotify_track_id", "musicbrainz_recording_mbid", "isrc", "verified_release_track_position"):
            with self.subTest(method=method): self.assertEqual(identity_confidence(method), "high")

    def test_name_matches_are_not_high_confidence(self):
        self.assertEqual(identity_confidence("unique_exact_artist_title"), "medium")
        self.assertEqual(identity_confidence("source_track_id"), "low")

    def test_independent_matching_field_sources_corroborate(self):
        result = metadata_confidence([
            {"source_family": "musicbrainz", "value": "1999-01-01"},
            {"source_family": "discogs", "value": "1999-01-01"},
        ])
        self.assertEqual(result["confidence"], "high")

    def test_duplicate_same_family_does_not_raise_confidence(self):
        result = metadata_confidence([
            {"source_family": "lastfm_community", "value": "dark"},
            {"source_family": "lastfm_community", "value": "dark"},
        ])
        self.assertEqual(result["confidence"], "low")

    def test_conflicts_lower_confidence(self):
        result = metadata_confidence([
            {"source_family": "musicbrainz", "value": "1999"},
            {"source_family": "discogs", "value": "2000"},
        ])
        self.assertEqual(result["confidence"], "low")
        self.assertIn("disagree", result["reason"])

if __name__ == "__main__": unittest.main()

# FILE OVERVIEW
# Purpose: Regression tests for conservative identity and field-level confidence.
# Coverage: Strong identifiers, weaker name matches, independent source families, duplicate sources, and conflicts.
# Run: python -m unittest tests.test_music_evidence -v.
# Related: scripts/music/music_evidence.py; docs/ALBUM_METADATA_AND_LOOKUP_CONFIDENCE.md.
