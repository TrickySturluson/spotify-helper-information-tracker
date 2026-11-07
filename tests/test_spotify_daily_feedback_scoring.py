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
                record = saved["tracks"]["spotify:track:removed"]
                self.assertEqual(record["artist"], "Removed Artist")
                self.assertEqual(record["track"], "Removed Track")
                self.assertEqual(len(record["removal_events"]), 1)
                self.assertEqual(record["removal_events"][0]["reason"], "user_removed")
                self.assertEqual(record["removal_events"][0]["last_present_cycle"], "2026-11-05T23:00:00+00:00")
                self.assertIsNone(record["first_added_at"])
            finally:
                feedback.DATA = original

    def test_removal_only_record_without_add_time_is_not_attributed_lastfm_plays(self):
        import json
        import tempfile
        from pathlib import Path
        import spotify_daily_feedback as feedback

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = feedback.DATA
            feedback.DATA = root / "daily_feedback.json"
            scrobbles = root / "scrobbles.json"
            try:
                feedback.record_manual_removals([{
                    "uri": "spotify:track:removed",
                    "name": "Removed Track",
                    "artists": ["Removed Artist"],
                    "detected_at": "2026-11-06T12:00:00+00:00",
                }])
                scrobbles.write_text(json.dumps([{
                    "artist": "Removed Artist",
                    "track": "Removed Track",
                    "timestamp": 1793966400,
                }]), encoding="utf-8")
                feedback.observe_lastfm_scrobbles(scrobbles)
                saved = json.loads(feedback.DATA.read_text(encoding="utf-8"))
                record = saved["tracks"]["spotify:track:removed"]
                self.assertIsNone(record["first_added_at"])
                self.assertEqual(record["lastfm_post_add_scrobbles"], 0)
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



    def test_unexposed_manual_removal_does_not_penalize_the_artist(self):
        import json
        import os
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "assistant_data/spotify").mkdir(parents=True)
            blacklist = root / "playlist_removed_tracks.json"
            blacklist.write_text(json.dumps({
                "playlists": {
                    "4yUVHSMQySfWeEowfIMcx7": {
                        "removed": [{
                            "uri": "spotify:track:removed",
                            "name": "Removed Track",
                            "artists": ["Artist"],
                        }],
                        "whitelisted": [],
                    }
                }
            }), encoding="utf-8")
            feedback_path = root / "assistant_data/spotify/daily_feedback.json"
            feedback_path.write_text(json.dumps({
                "tracks": {
                    "spotify:track:removed": {
                        "removal_events": [{"reason": "user_removed"}],
                        "playback_observations": [],
                        "lastfm_post_add_scrobbles": None,
                    }
                }
            }), encoding="utf-8")
            original = Path.cwd()
            try:
                os.chdir(root)
                feedback = discovery.load_playlist_feedback(
                    [], "4yUVHSMQySfWeEowfIMcx7", path=blacklist
                )
            finally:
                os.chdir(original)
        self.assertEqual(feedback["negative_artists"].get("artist", 0), 0)
        self.assertIn("spotify:track:removed", feedback["negative_uris"])
        self.assertTrue(discovery.is_playlist_candidate_blocked(
            "Artist", "Removed Track", "spotify:track:removed", feedback
        ))

    def test_exposed_manual_removal_can_inform_artist_level_negative_feedback(self):
        import json
        import os
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "assistant_data/spotify").mkdir(parents=True)
            blacklist = root / "playlist_removed_tracks.json"
            blacklist.write_text(json.dumps({
                "playlists": {
                    "4yUVHSMQySfWeEowfIMcx7": {
                        "removed": [{
                            "uri": "spotify:track:removed",
                            "name": "Removed Track",
                            "artists": ["Artist"],
                        }],
                        "whitelisted": [],
                    }
                }
            }), encoding="utf-8")
            feedback_path = root / "assistant_data/spotify/daily_feedback.json"
            feedback_path.write_text(json.dumps({
                "tracks": {
                    "spotify:track:removed": {
                        "removal_events": [{"reason": "user_removed"}],
                        "playback_observations": [{"plays": 3}],
                        "lastfm_post_add_scrobbles": 2,
                    }
                }
            }), encoding="utf-8")
            original = Path.cwd()
            try:
                os.chdir(root)
                feedback = discovery.load_playlist_feedback(
                    [], "4yUVHSMQySfWeEowfIMcx7", path=blacklist
                )
            finally:
                os.chdir(original)
        self.assertEqual(feedback["negative_artists"].get("artist", 0), 1)

class DailyLikedSongQueryTests(unittest.TestCase):
    def test_saved_item_queries_never_exceed_spotify_40_uri_limit(self):
        from unittest.mock import Mock
        import spotify_daily_feedback as feedback

        uris = [f"spotify:track:{index:022d}" for index in range(81)]
        spotify = Mock()
        spotify.call.side_effect = [[True] * 40, [False] * 40, [True]]

        liked = feedback.query_liked_status(spotify, uris)

        self.assertEqual(len(spotify.call.call_args_list), 3)
        expected_sizes = [40, 40, 1]
        for call, expected_size in zip(spotify.call.call_args_list, expected_sizes):
            method, path = call.args
            self.assertEqual(method, "GET")
            values = path.split("?uris=", 1)[1].split(",")
            self.assertEqual(len(values), expected_size)
            self.assertTrue(all(value.startswith("spotify:track:") for value in values))
        self.assertTrue(liked[uris[0]])
        self.assertFalse(liked[uris[40]])
        self.assertTrue(liked[uris[80]])

    def test_observe_liked_songs_records_60_tracks_in_40_and_20_batches(self):
        import json
        import tempfile
        from pathlib import Path
        from unittest.mock import Mock
        import spotify_daily_feedback as feedback

        original = feedback.DATA
        uris = [f"spotify:track:{index:022d}" for index in range(60)]
        items = [{"uri": uri, "artist": f"Artist {index}", "track": f"Track {index}"} for index, uri in enumerate(uris)]
        with tempfile.TemporaryDirectory() as directory:
            feedback.DATA = Path(directory) / "daily_feedback.json"
            try:
                feedback.record_additions(items, added_at="2026-11-06T12:00:00+00:00")
                spotify = Mock()
                spotify.call.side_effect = [[True] * 40, [False] * 20]
                result = feedback.observe_liked_songs(spotify, uris, observed_at="2026-11-06T12:01:00+00:00")
                saved = json.loads(feedback.DATA.read_text(encoding="utf-8"))
                self.assertEqual(len(result), 60)
                self.assertTrue(saved["tracks"][uris[0]]["liked_observations"][-1]["liked"])
                self.assertFalse(saved["tracks"][uris[59]]["liked_observations"][-1]["liked"])
                self.assertEqual(saved["coverage"]["liked_songs"], "observed")
                self.assertEqual([len(call.args[1].split("?uris=", 1)[1].split(",")) for call in spotify.call.call_args_list], [40, 20])
            finally:
                feedback.DATA = original


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
