import tempfile
import unittest
from pathlib import Path

import playlist_intelligence as intelligence
import mood_inference


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

    def test_metadata_coverage_distinguishes_tagged_partial_and_missing(self):
        items = [
            {"artists": ["Tagged"]},
            {"artists": ["Empty"]},
            {"artists": ["Absent"]},
        ]
        coverage = intelligence.artist_metadata_coverage(items, {
            "tagged": {"status": "matched", "tags": [{"tag": "punk"}]},
            "empty": {"status": "no_tags", "tags": []},
        })
        self.assertEqual(coverage["tagged"], 1)
        self.assertEqual(coverage["profile_without_tags"], 1)
        self.assertEqual(coverage["missing_profile"], 1)
        self.assertEqual(coverage["tagged_item_coverage"], 0.3333)

    def test_playlist_track_moods_use_track_tags_not_artist_moods(self):
        items = [
            {"name": "Dream Song", "artists": ["Same Artist"]},
            {"name": "Aggressive Song", "artists": ["Same Artist"]},
        ]
        track_profiles = {
            ("same artist", "dream song"): {
                "lastfm_tags": [{"tag": "dreamy", "count": 10}],
                "musicbrainz_tags": [],
                "musicbrainz_genres": [],
            }
        }
        profile = intelligence.build_playlist_profile(
            items,
            artist_profiles={"same artist": {"tags": [{"tag": "aggressive"}], "moods": ["aggressive"]}},
            track_profiles=track_profiles,
        )
        self.assertEqual(profile["track_metadata"]["matched_tracks"], 1)
        self.assertEqual(profile["track_moods"], [{"tag": "dreamy", "track_count": 1}])
        self.assertEqual(profile["artist_moods"][0]["tag"], "aggressive")

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

    def test_mood_inference_uses_independent_artist_evidence(self):
        items = [
            {"artists": ["One"]}, {"artists": ["One"]},
            {"artists": ["Two"]}, {"artists": ["Three"]},
        ]
        profiles = {
            "one": {"tags": [{"tag": "haunting", "count": 100}, {"tag": "surf rock", "count": 90}]},
            "two": {"tags": [{"tag": "eerie", "count": 60}]},
            "three": {"tags": [{"tag": "dreamy", "count": 80}]},
        }
        result = mood_inference.infer_mood_profile(items, profiles)
        moods = {row["mood"]: row for row in result["moods"]}
        self.assertEqual(moods["eerie"]["artist_support"], 2)
        self.assertGreater(moods["eerie"]["confidence"], 0.4)
        self.assertIn("dreamy", moods)
        self.assertNotIn("rock", moods)

    def test_expanded_moods_and_sound_tags_are_separate(self):
        self.assertIn("nocturnal", mood_inference._tag_moods("nocturnal"))
        self.assertIn("chaotic", mood_inference._tag_moods("chaotic"))
        self.assertIn("groovy", mood_inference._tag_moods("groovy"))
        self.assertNotIn("shoegaze", mood_inference._tag_moods("shoegaze"))
        items = [{"artists": ["One"]}, {"artists": ["Two"]}]
        profiles = {
            "one": {"genres": ["dream pop", "shoegaze"], "themes": ["surreal"],
                    "tags": [{"tag": "dreamy"}, {"tag": "shoegaze"}]},
            "two": {"genres": ["punk", "surf rock"], "themes": ["horror"],
                    "tags": [{"tag": "chaotic"}, {"tag": "surf rock"}]},
        }
        tags = mood_inference.infer_sound_tag_profile(items, profiles)
        families = {row["tag"] for row in tags["families"]}
        self.assertIn("dream pop & shoegaze", families)
        self.assertIn("punk & noise", families)
        self.assertIn("surf & rockabilly", families)
        profile = intelligence.build_playlist_profile(items, artist_profiles=profiles)
        self.assertIn("sound_tags", profile)
        self.assertTrue(profile["sound_tags"]["genres"])

    def test_playlist_profile_exposes_mood_evidence(self):
        items = [{"artists": ["One"]}, {"artists": ["Two"]}]
        profiles = {
            "one": {"genres": ["rock"], "tags": [{"tag": "dark", "count": 100}]},
            "two": {"genres": ["pop"], "tags": [{"tag": "gloomy", "count": 80}]},
        }
        profile = intelligence.build_playlist_profile(items, artist_profiles=profiles)
        self.assertEqual(profile["moods"][0]["tag"], "dark")
        self.assertEqual(profile["mood_inference"]["artists_with_tag_evidence"], 2)
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
