import unittest

from scripts.spotify.spotify_daily_report import build_report


class DailyReportTests(unittest.TestCase):
    def test_report_keeps_listening_sources_separate_and_unknowns_unknown(self):
        report = build_report({
            "tracks": {
                "spotify:track:a": {
                    "additions": [{"at": "2026-11-01T00:00:00+00:00", "liked_at_add": False}],
                    "liked_observations": [{"at": "2026-11-02T00:00:00+00:00", "liked": True}],
                    "playback_observations": [{"plays": 2, "played_ms": 300000}],
                    "lastfm_post_add_scrobbles": 3,
                    "removal_events": [{"reason": "curator_rotation"}],
                },
                "spotify:track:b": {
                    "additions": [{"at": "2026-11-02T00:00:00+00:00", "liked_at_add": False}],
                    "liked_observations": [{"at": "2026-11-03T00:00:00+00:00", "liked": False}],
                    "playback_observations": [{"plays": 0, "played_ms": 0}],
                    "lastfm_post_add_scrobbles": 0,
                    "removal_events": [{"reason": "user_removed"}],
                },
                "spotify:track:c": {
                    "additions": [{"at": "2026-11-03"}],
                    "liked_observations": [],
                    "playback_observations": [],
                },
            },
            "coverage": {
                "liked_songs": "observed",
                "playback_tracker": "available",
                "lastfm": "available",
            },
        })
        self.assertEqual(report["track_count"], 3)
        self.assertEqual(report["liked"]["observed_tracks"], 2)
        self.assertEqual(report["liked"]["positive_rate_among_observed"], 0.5)
        self.assertEqual(report["liked_after_add"]["observed_tracks"], 2)
        self.assertEqual(report["liked_after_add"]["tracks_saved_after_add"], 1)
        self.assertEqual(report["liked_after_add"]["save_rate_among_tracks_with_unliked_baseline"], 0.5)
        self.assertEqual(report["spotify_playback_tracker"]["total_sessions"], 2)
        self.assertEqual(report["lastfm_scrobbles"]["post_add_scrobbles"], 3)
        self.assertEqual(report["removals"]["neutral_curator_rotations"], 1)
        self.assertEqual(report["removals"]["other_removals"], 1)
        self.assertEqual(report["spotify_playback_tracker"]["coverage"], "available")
        self.assertIn("separately", report["interpretation"]["listening_sources"])

    def test_report_summarizes_daily_mix_by_tier_without_cross_playlist_leakage(self):
        feedback = {"tracks": {"spotify:track:a": {"additions": []}}, "coverage": {}}
        candidates = [
            {"spotify_uri": "spotify:track:a", "discovery_evidence": [
                {"context": {"playlist_id": "4yUVHSMQySfWeEowfIMcx7"},
                 "recommendation": {"daily_mix_bucket": "discovery"}}]},
            {"spotify_uri": "spotify:track:b", "discovery_evidence": [
                {"context": {"playlist_id": "4yUVHSMQySfWeEowfIMcx7"},
                 "recommendation": {"daily_mix_bucket": "rediscovery"}}]},
            {"spotify_uri": "spotify:track:c", "discovery_evidence": [
                {"context": {"playlist_id": "4diIlnF8BlgoJrwUfejf49"},
                 "recommendation": {"daily_mix_bucket": "familiar"}}]},
        ]
        report = build_report(feedback, candidates)
        self.assertEqual(report["discovery_mix"]["surfaced_tracks"], 2)
        self.assertEqual(report["discovery_mix"]["by_tier"]["discovery"]["tracks_with_feedback"], 1)
        self.assertEqual(report["discovery_mix"]["by_tier"]["rediscovery"]["unique_tracks"], 1)
        self.assertNotIn("familiar", report["discovery_mix"]["by_tier"])

    def test_empty_report_has_null_rates_not_zero_rates(self):
        report = build_report({"tracks": {}, "coverage": {}})
        self.assertEqual(report["track_count"], 0)
        self.assertIsNone(report["liked"]["positive_rate_among_observed"])
        self.assertIsNone(report["spotify_playback_tracker"]["positive_rate_among_observed"])
        self.assertEqual(report["lastfm_scrobbles"]["coverage"], "unknown")

    def test_malformed_feedback_is_rejected(self):
        with self.assertRaises(ValueError):
            build_report({"tracks": []})


if __name__ == "__main__":
    unittest.main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Regression tests for the read-only Tricky Daily quality report.
# Run: python -m unittest tests.test_spotify_daily_report -v.
# -----------------------------------------------------------------------------
