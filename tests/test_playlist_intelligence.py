import tempfile
import unittest
from pathlib import Path

import playlist_intelligence as intelligence


class PlaylistIntelligenceTests(unittest.TestCase):
    def test_profile_uses_playlist_membership_and_artist_metadata(self):
        items = [
            {"name": "One", "artists": ["The Example"], "uri": "spotify:track:1"},
            {"name": "Two", "artists": ["The Example"], "uri": "spotify:track:2"},
            {"name": "Three", "artists": ["Other"], "uri": "spotify:track:3"},
        ]
        profile = intelligence.build_playlist_profile(
            items,
            {"positive_artists": {"the example": 2}, "removed_count": 1, "whitelisted_count": 1},
            {"the example": {"genres": ["punk"], "moods": ["dark"], "themes": ["horror"]}},
        )
        self.assertEqual(profile["artist_count"], 2)
        self.assertEqual(profile["top_artists"][0]["artist"], "The Example")
        self.assertEqual(profile["genres"][0]["tag"], "punk")
        self.assertEqual(profile["negative_track_evidence"], 1)
        self.assertEqual(profile["whitelisted_tracks"], 1)

    def test_health_report_detects_surplus_duplicates_and_artist_concentration(self):
        items = [
            {"uri": "spotify:track:a", "artists": ["A"]},
            {"uri": "spotify:track:a", "artists": ["A"]},
            {"uri": "spotify:track:b", "artists": ["B"]},
            {"artists": ["A"]},
        ]
        health = intelligence.playlist_health(items, artist_profiles={"a": {}, "b": {}})
        self.assertEqual(health["surplus_duplicates"], 1)
        self.assertEqual(health["missing_uri_items"], 1)
        self.assertEqual(health["unique_primary_artists"], 2)
        self.assertEqual(health["top_artist_share"], 0.75)

    def test_confidence_tiers_are_distinct(self):
        self.assertEqual(intelligence.recommendation_confidence(0.9, 4), "strong fit")
        self.assertEqual(intelligence.recommendation_confidence(0.7, 2), "promising")
        self.assertEqual(intelligence.recommendation_confidence(0.4, 1), "wildcard")

    def test_scoring_config_merges_user_weights_over_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "weights.json"
            path.write_text('{"version": 3, "weights": {"similarity": 0.7}}', encoding="utf-8")
            config = intelligence.scoring_config(path)
            self.assertEqual(config["version"], 3)
            self.assertEqual(config["weights"]["similarity"], 0.7)
            self.assertEqual(config["weights"]["familiarity"], 0.30)


if __name__ == "__main__":
    unittest.main()
