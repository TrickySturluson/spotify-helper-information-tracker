import unittest

from scripts.spotify.spotify_daily_report import build_report


class DailyReportTests(unittest.TestCase):
    def test_report_keeps_listening_sources_separate_and_unknowns_unknown(self):
        report = build_report({
            "tracks": {
                "spotify:track:a": {
                    "additions": [{"at": "2026-11-01"}],
                    "liked_observations": [{"liked": True}],
                    "playback_observations": [{"plays": 2, "played_ms": 300000}],
                    "lastfm_post_add_scrobbles": 3,
                    "removal_events": [{"reason": "curator_rotation"}],
                },
                "spotify:track:b": {
                    "additions": [{"at": "2026-11-02"}],
                    "liked_observations": [{"liked": False}],
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
        self.assertEqual(report["spotify_playback_tracker"]["total_sessions"], 2)
        self.assertEqual(report["lastfm_scrobbles"]["post_add_scrobbles"], 3)
        self.assertEqual(report["removals"]["neutral_curator_rotations"], 1)
        self.assertEqual(report["removals"]["other_removals"], 1)
        self.assertEqual(report["spotify_playback_tracker"]["coverage"], "available")
        self.assertIn("separately", report["interpretation"]["listening_sources"])

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
