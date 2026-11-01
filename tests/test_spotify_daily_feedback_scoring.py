import unittest
from datetime import date

import spotify_discovery as discovery


class DailyPostAddSaveScoringTests(unittest.TestCase):
    def test_new_liked_song_conversion_is_positive_not_a_preliked_penalty(self):
        track = {
            "name": "Saved After Daily",
            "artists": [{"name": "Artist"}],
            "uri": "spotify:track:conversion",
        }
        liked = {"spotify:track:conversion"}
        base_feedback = {
            "negative_keys": set(), "negative_uris": set(),
            "negative_artists": {}, "positive_artists": {},
            "daily_evidence": {},
        }
        converted_feedback = {
            **base_feedback,
            "daily_evidence": {
                "spotify:track:conversion": {
                    "liked": True, "liked_at_add": False,
                    "removal_count": 1, "measured_plays": 3,
                }
            },
        }
        base = discovery.candidate_score(
            track, 0.8, {}, liked, date(2026, 10, 31), base_feedback
        )[0]
        converted = discovery.candidate_score(
            track, 0.8, {}, liked, date(2026, 10, 31), converted_feedback
        )[0]
        self.assertGreater(converted, base)

    def test_tracks_already_liked_at_addition_keep_the_preliked_penalty(self):
        track = {
            "name": "Already Liked",
            "artists": [{"name": "Artist"}],
            "uri": "spotify:track:already",
        }
        feedback = {
            "negative_keys": set(), "negative_uris": set(),
            "negative_artists": {}, "positive_artists": {},
            "daily_evidence": {
                "spotify:track:already": {
                    "liked": True, "liked_at_add": True,
                    "removal_count": 0, "measured_plays": 0,
                }
            },
        }
        liked_score = discovery.candidate_score(
            track, 0.8, {}, {"spotify:track:already"}, date(2026, 10, 31), feedback
        )[0]
        unliked_score = discovery.candidate_score(
            track, 0.8, {}, set(), date(2026, 10, 31), feedback
        )[0]
        self.assertLess(liked_score, unliked_score)


if __name__ == "__main__":
    unittest.main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Regression test module.
# Scope: Regression checks for the behavior named by this test module.
# Run: python -m unittest tests.test_spotify_daily_feedback_scoring -v (from the repository root).
# Related: Implementation lives under scripts/; longer behavior notes live in docs/.
# -----------------------------------------------------------------------------
