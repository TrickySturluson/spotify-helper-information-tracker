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
                }]
                self.assertEqual(feedback.record_manual_removals(rows), 1)
                self.assertEqual(feedback.record_manual_removals(rows), 0)
                saved = json.loads(feedback.DATA.read_text(encoding="utf-8"))
                record = saved["tracks"]["spotify:track:removed"]
                self.assertEqual(record["artist"], "Removed Artist")
                self.assertEqual(record["track"], "Removed Track")
                self.assertEqual(len(record["removal_events"]), 1)
                self.assertEqual(record["removal_events"][0]["reason"], "user_removed")
                self.assertIsNone(record["first_added_at"])
            finally:
                feedback.DATA = original

    def test_exposed_removal_is_negative_but_unexposed_removal_is_neutral(self):
        track = {
            "name": "Removed Track",
            "artists": [{"name": "Artist"}],
            "uri": "spotify:track:removed",
        }
        base = {
            "negative_keys": {"artist|removed track"},
            "negative_uris": {"spotify:track:removed"},
            "negative_artists": {}, "positive_artists": {},
        }
        neutral_feedback = {
            **base,
            "daily_evidence": {
                "spotify:track:removed": {
                    "removal_count": 1, "measured_plays": None, "lastfm_plays": None,
                }
            },
        }
        exposed_feedback = {
            **base,
            "daily_evidence": {
                "spotify:track:removed": {
                    "removal_count": 1, "measured_plays": 12, "lastfm_plays": 4,
                }
            },
        }
        plain_score = discovery.candidate_score(
            track, 0.8, {}, set(), date(2026, 11, 6), {}
        )[0]
        neutral_score = discovery.candidate_score(
            track, 0.8, {}, set(), date(2026, 11, 6), neutral_feedback
        )[0]
        exposed_score = discovery.candidate_score(
            track, 0.8, {}, set(), date(2026, 11, 6), exposed_feedback
        )[0]
        self.assertEqual(neutral_score, plain_score)
        self.assertLess(exposed_score, neutral_score)


class DailyFeedbackWorkflowTests(unittest.TestCase):
    def test_observation_workflow_adds_compat_path_before_manager_import(self):
        from pathlib import Path
        workflow = Path(".github/workflows/spotify-daily-feedback-observation.yml").read_text(
            encoding="utf-8"
        )
        path_setup = workflow.index('sys.path.insert(0, "compat")')
        manager_import = workflow.index("import spotify_playlist_manager as manager")
        self.assertLess(path_setup, manager_import)
        self.assertIn("python compat/spotify_daily_feedback.py observe", workflow)


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
