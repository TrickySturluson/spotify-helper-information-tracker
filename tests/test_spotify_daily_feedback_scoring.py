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



class DailyManualRemovalFeedbackTests(unittest.TestCase):
    def test_manual_removal_is_saved_once(self):
        import json
        import tempfile
        from pathlib import Path
        import spotify_daily_feedback as feedback

        with tempfile.TemporaryDirectory() as directory:
            original = feedback.DATA
            feedback.DATA = Path(directory) / "daily_feedback.json"
            try:
                rows = [{
                    "uri": "spotify:track:removed",
                    "name": "Removed Track",
                    "artists": ["Removed Artist"],
                    "detected_at": "2026-11-06T12:00:00+00:00",
                    "last_present_cycle": "2026-11-05T23:00:00+00:00",
                }]
                self.assertEqual(feedback.record_manual_removals(rows), 1)
                self.assertEqual(feedback.record_manual_removals(rows), 0)
                saved = json.loads(feedback.DATA.read_text(encoding="utf-8"))
                event = saved["tracks"]["spotify:track:removed"]["removal_events"][0]
                self.assertEqual(event["reason"], "user_removed")
                self.assertEqual(event["source"], "daily_snapshot_reconciliation")
            finally:
                feedback.DATA = original


    def test_removal_after_measured_exposure_is_negative_evidence(self):
        track = {
            "name": "Removed After Listening",
            "artists": [{"name": "Artist"}],
            "uri": "spotify:track:heard-then-removed",
        }
        base = {
            "negative_keys": {"artist|removed after listening"},
            "negative_uris": {"spotify:track:heard-then-removed"},
            "negative_artists": {}, "positive_artists": {},
        }
        unexposed = {
            **base,
            "daily_evidence": {
                "spotify:track:heard-then-removed": {
                    "removal_count": 1, "measured_plays": None, "lastfm_plays": None,
                }
            },
        }
        exposed = {
            **base,
            "daily_evidence": {
                "spotify:track:heard-then-removed": {
                    "removal_count": 1, "measured_plays": 12, "lastfm_plays": 4,
                }
            },
        }
        neutral_score = discovery.candidate_score(
            track, 0.8, {}, set(), date(2026, 11, 6), unexposed
        )[0]
        rejected_score = discovery.candidate_score(
            track, 0.8, {}, set(), date(2026, 11, 6), exposed
        )[0]
        self.assertLess(rejected_score, neutral_score)

    def test_unheard_manual_removal_does_not_create_exposure_penalty(self):
        track = {
            "name": "Removed Without Exposure",
            "artists": [{"name": "Artist"}],
            "uri": "spotify:track:unheard-removed",
        }
        base = {
            "negative_keys": {"artist|removed without exposure"},
            "negative_uris": {"spotify:track:unheard-removed"},
            "negative_artists": {}, "positive_artists": {},
        }
        feedback = {
            **base,
            "daily_evidence": {
                "spotify:track:unheard-removed": {
                    "removal_count": 1, "measured_plays": None, "lastfm_plays": None,
                }
            },
        }
        plain = discovery.candidate_score(
            track, 0.8, {}, set(), date(2026, 11, 6), {}
        )[0]
        neutral = discovery.candidate_score(
            track, 0.8, {}, set(), date(2026, 11, 6), feedback
        )[0]
        self.assertEqual(neutral, plain)

if __name__ == "__main__":
    unittest.main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Protect Tricky Daily's distinction between tracks already liked and tracks liked after exposure.
# Scope: A post-add save is positive conversion evidence, while a pre-existing like retains its
#        separate familiarity/liked penalty; these states must not be conflated.
# Run: python -m unittest tests.test_spotify_daily_feedback_scoring -v
# Related: scripts/spotify/spotify_discovery.py; scripts/spotify/spotify_daily_feedback.py;
#          docs/TRICKY_DAILY_CYCLE.md.
# -----------------------------------------------------------------------------
