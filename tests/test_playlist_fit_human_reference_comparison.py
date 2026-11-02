import unittest

from scripts.spotify.compare_playlist_fit_human_reference import compare


class PlaylistFitHumanReferenceComparisonTests(unittest.TestCase):
    def test_comparison_is_post_hoc_and_keeps_unknown_scores_missing(self):
        preview = {
            "model_version": "five-axis-fit-v0.3",
            "status": "read_only_preview_not_for_sorting",
            "targets": {"target-1": {"name": "To 11"}},
            "results": [
                {"uri": "spotify:track:0000000000000000000001", "title": "Track A", "artist": "Artist A",
                 "scores_by_target": {"To 11": {"fit_score": 80, "confidence": "low",
                                                "supported_dimensions": 1, "directly_supported_dimensions": 0}}},
                {"uri": "spotify:track:0000000000000000000002", "title": "Track B", "artist": "Artist B",
                 "scores_by_target": {"To 11": {"fit_score": None, "confidence": "unknown"}}},
            ],
        }
        ratings = {"ratings": [
            {"track": {"uri": "spotify:track:0000000000000000000001", "name": "Track A", "artist": "Artist A"},
             "human_fit_ratings": [{"playlist_id": "target-1", "score": 100}]},
            {"track": {"name": "Track B", "artist": "Artist B"},
             "human_fit_ratings": [{"playlist_id": "target-1", "score": 40}]},
        ]}
        result = compare(preview, ratings)
        self.assertEqual(result["status"], "diagnostic_reference_comparison_only")
        self.assertFalse(result["human_ratings_used_by_model_scorer"])
        self.assertFalse(result["human_ratings_used_for_training"])
        self.assertEqual(result["match_methods"]["spotify_uri"], 1)
        self.assertEqual(result["match_methods"]["unique_exact_title_artist_display_join"], 1)
        self.assertEqual(result["unknown_model_score_pairs"], 1)
        self.assertEqual(result["overall"]["n"], 1)
        self.assertEqual(result["overall"]["mae"], 20.0)
        self.assertEqual(result["overall"]["mean_bias_model_minus_human"], -20.0)
        self.assertEqual(result["targets"]["To 11"]["human_rating_pairs"], 2)
        self.assertEqual(result["targets"]["To 11"]["score_coverage"], 0.5)

    def test_ambiguous_display_join_is_rejected(self):
        preview = {
            "targets": {"target-1": {"name": "To 11"}},
            "results": [
                {"uri": "spotify:track:0000000000000000000001", "title": "Same", "artist": "Artist",
                 "scores_by_target": {"To 11": {"fit_score": 80, "confidence": "low"}}},
                {"uri": "spotify:track:0000000000000000000002", "title": "Same", "artist": "Artist",
                 "scores_by_target": {"To 11": {"fit_score": 20, "confidence": "low"}}},
            ],
        }
        ratings = {"ratings": [
            {"track": {"name": "Same", "artist": "Artist"},
             "human_fit_ratings": [{"playlist_id": "target-1", "score": 50}]},
        ]}
        result = compare(preview, ratings)
        self.assertEqual(result["ambiguous_human_rating_tracks"], 1)
        self.assertEqual(result["overall"]["n"], 0)


if __name__ == "__main__":
    unittest.main()

# FILE OVERVIEW
# Purpose: Verify post-hoc human reference comparison, unknown-score handling and ambiguity rejection.
# Boundary: The comparison tool is not imported by model scoring and does not write to Spotify.
