import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch

import spotify_discovery as discovery


class DiscoveryScoringTests(unittest.TestCase):
    def test_similar_artists_rank_consensus_above_alphabetical_ties(self):
        profiles = {
            "a": {"artist": "Seed A", "plays": 100, "status": "matched", "genres": ["rock"]},
            "b": {"artist": "Seed B", "plays": 80, "status": "matched", "genres": ["pop"]},
            "c": {"artist": "Seed C", "plays": 60, "status": "matched", "genres": ["indie"]},
        }
        responses = {
            "Seed A": [{"name": "Zulu Artist", "match": "1.0"}, {"name": "Alpha Artist", "match": "1.0"}],
            "Seed B": [{"name": "Zulu Artist", "match": "1.0"}],
            "Seed C": [{"name": "Zulu Artist", "match": "1.0"}],
        }
        with patch.object(discovery, "_lastfm_similar", side_effect=lambda seed, key: responses[seed["artist"]]):
            with patch.object(discovery.time, "sleep"):
                rows = discovery.discover_similar_artists(profiles, "test-key", today=date(2026, 10, 30), seed_limit=3)
        self.assertEqual(rows[0]["artist"], "Zulu Artist")
        self.assertEqual(rows[0]["supporting_seeds"], 3)
        self.assertGreater(rows[0]["similarity"], rows[1]["similarity"])

    def test_normalization_collapses_whitespace(self):
        self.assertEqual(discovery.norm("  Two   Words  "), "two words")

    def test_unheard_tracks_have_no_familiarity_penalty(self):
        self.assertEqual(discovery.familiarity_penalty(0, None, date(2026, 10, 30)), 0)

    def test_repeated_and_recent_plays_are_penalized_more(self):
        today = date(2026, 10, 30)
        one_play = discovery.familiarity_penalty(1, "2024-01-01", today)
        many_recent = discovery.familiarity_penalty(30, "2026-10-20", today)
        self.assertGreater(many_recent, one_play)

    def test_one_or_two_plays_remain_eligible(self):
        today = date(2026, 10, 30)
        penalty = discovery.familiarity_penalty(2, "2026-10-25", today)
        self.assertLess(penalty, 0.9)

    def test_missing_spotify_popularity_does_not_change_score(self):
        today = date(2026, 10, 30)
        base = {"name": "Track", "artists": [{"name": "Artist"}], "uri": "spotify:track:1"}
        without_field, *_ = discovery.candidate_score(base, 0.8, {}, set(), today)
        with_zero, *_ = discovery.candidate_score({**base, "popularity": 0}, 0.8, {}, set(), today)
        with_hundred, *_ = discovery.candidate_score({**base, "popularity": 100}, 0.8, {}, set(), today)
        self.assertEqual(without_field, with_zero)
        self.assertEqual(without_field, with_hundred)

    def test_liked_tracks_are_deprioritized_not_excluded(self):
        track = {"name": "Known", "artists": [{"name": "Artist"}], "uri": "spotify:track:1", "popularity": 50}
        normal, *_ = discovery.candidate_score(track, 0.8, {}, set(), date(2026, 10, 30))
        liked, *_ = discovery.candidate_score(track, 0.8, {}, {"artist|known"}, date(2026, 10, 30))
        self.assertLess(liked, normal)

    def test_liked_library_paginates(self):
        sp = Mock()
        sp.call.side_effect = [
            {"items": [{"track": {"name": "A", "artists": [{"name": "X"}], "uri": "spotify:track:a"}}],
             "next": "https://api.spotify.com/v1/me/tracks?limit=50&offset=50"},
            {"items": [{"track": {"name": "B", "artists": [{"name": "Y"}], "uri": "spotify:track:b"}}],
             "next": None},
        ]
        liked = discovery.liked_track_keys(sp)
        self.assertIn("x|a", liked)
        self.assertIn("spotify:track:b", liked)
        self.assertEqual(sp.call.call_count, 2)

    def test_playlist_removed_track_is_blocked_but_artist_removal_is_soft(self):
        feedback = {
            "negative_keys": {"artist|removed song"},
            "negative_uris": {"spotify:track:removed"},
            "negative_artists": {"artist": 1},
        }
        self.assertTrue(discovery.is_playlist_candidate_blocked(
            "Artist", "Removed Song", "spotify:track:other", feedback
        ))
        self.assertTrue(discovery.is_playlist_candidate_blocked(
            "Artist", "Different Song", "spotify:track:removed", feedback
        ))
        self.assertFalse(discovery.is_playlist_candidate_blocked(
            "Artist", "Different Song", "spotify:track:other", feedback
        ))

    def test_readded_removed_track_remains_blocked_without_explicit_whitelist(self):
        with tempfile.TemporaryDirectory() as directory:
            history = Path(directory) / "removed.json"
            history.write_text(
                '{"playlists":{"playlist":{"removed":[{"artist":"Artist","name":"Song","uri":"spotify:track:song"}]}}}',
                encoding="utf-8",
            )
            feedback = discovery.load_playlist_feedback(
                [{"name": "Song", "artists": [{"name": "Artist"}], "uri": "spotify:track:song"}],
                "playlist",
                history,
            )
        self.assertEqual(feedback["whitelisted_count"], 0)
        self.assertEqual(feedback["removed_count"], 1)
        self.assertTrue(discovery.is_playlist_candidate_blocked(
            "Artist", "Song", "spotify:track:song", feedback
        ))

    def test_new_booze_removals_are_loaded_as_permanent_playlist_local_blocks(self):
        feedback = discovery.load_playlist_feedback([], "4diIlnF8BlgoJrwUfejf49")
        self.assertGreaterEqual(feedback["removed_count"], 8)
        self.assertTrue(discovery.is_playlist_candidate_blocked(
            "Creature Feature", "The Greatest Show Unearthed",
            "spotify:track:5YEkxfNMTHkfoYlh4d1Y7b", feedback
        ))
        self.assertTrue(discovery.is_playlist_candidate_blocked(
            "Creature Feature", "The Netherworld",
            "spotify:track:62EKjHgJEMoBkL2uhCVHKr", feedback
        ))

    def test_where_eagles_dare_is_loaded_from_booze_removal_history(self):
        feedback = discovery.load_playlist_feedback([], "4diIlnF8BlgoJrwUfejf49")
        self.assertTrue(discovery.is_playlist_candidate_blocked(
            "Misfits", "Where Eagles Dare",
            "spotify:track:5LgiqEgpK54OfXC6947wbU", feedback
        ))

    def test_explicit_playlist_whitelist_overrides_removal(self):
        with tempfile.TemporaryDirectory() as directory:
            history = Path(directory) / "removed.json"
            history.write_text(
                '{"playlists":{"playlist":{"removed":[{"artist":"Artist","name":"Song","uri":"spotify:track:song"}],'
                '"whitelisted":[{"artist":"Artist","name":"Song","uri":"spotify:track:song"}]}}}',
                encoding="utf-8",
            )
            feedback = discovery.load_playlist_feedback([], "playlist", history)
        self.assertEqual(feedback["whitelisted_count"], 1)
        self.assertEqual(feedback["removed_count"], 0)
        self.assertFalse(discovery.is_playlist_candidate_blocked(
            "Artist", "Song", "spotify:track:song", feedback
        ))

    def test_removed_track_stays_blocked_when_not_in_current_playlist(self):
        with tempfile.TemporaryDirectory() as directory:
            history = Path(directory) / "removed.json"
            history.write_text(
                '{"playlists":{"playlist":{"removed":[{"artist":"Artist","name":"Song","uri":"spotify:track:song"}]}}}',
                encoding="utf-8",
            )
            feedback = discovery.load_playlist_feedback([], "playlist", history)
        self.assertEqual(feedback["removed_count"], 1)
        self.assertTrue(discovery.is_playlist_candidate_blocked(
            "Artist", "Song", "spotify:track:song", feedback
        ))

    def test_lyric_theme_affinity_rewards_playlist_theme_overlap(self):
        playlist_themes = {"vampire": 3, "murder_slasher": 2, "nightlife_clubbing": 1}
        aligned = {"themes": {"vampire": {"count": 1}, "nightlife_clubbing": {"count": 2}}}
        unrelated = {"themes": {"love_romance": {"count": 4}}}
        self.assertAlmostEqual(discovery.lyric_theme_affinity(aligned, playlist_themes), 4 / 6, places=3)
        self.assertEqual(discovery.lyric_theme_affinity(unrelated, playlist_themes), 0.0)
        self.assertEqual(discovery.lyric_theme_affinity({}, playlist_themes), 0.0)

    def test_explicit_whitelist_is_positive_track_level_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            history = Path(directory) / "removed.json"
            history.write_text(
                '{"playlists":{"playlist":{"removed":[{"artist":"Artist","name":"Song","uri":"spotify:track:song"}],'
                '"whitelisted":[{"artist":"Artist","name":"Song","uri":"spotify:track:song"}]}}}',
                encoding="utf-8",
            )
            feedback = discovery.load_playlist_feedback([], "playlist", history)
        track = {"name": "Song", "artists": [{"name": "Artist"}], "uri": "spotify:track:song"}
        plain, *_ = discovery.candidate_score(track, 0.8, {}, set(), date(2026, 10, 30), {})
        approved, *_ = discovery.candidate_score(track, 0.8, {}, set(), date(2026, 10, 30), feedback)
        self.assertIn("artist|song", feedback["positive_keys"])
        self.assertIn("spotify:track:song", feedback["positive_uris"])
        self.assertGreater(approved, plain)

    def test_corrupt_removal_feedback_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            history = Path(directory) / "removed.json"
            history.write_text("{not valid json", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "recommendation generation stopped"):
                discovery.load_playlist_feedback([], "playlist", history)

    def test_general_discovery_never_recommends_exactly_removed_track(self):
        import json
        with tempfile.TemporaryDirectory() as directory:
            profiles = Path(directory) / "profiles.json"
            features = Path(directory) / "features.json"
            profiles.write_text(json.dumps({"seed": {"artist": "Seed", "status": "matched", "genres": ["rock"]}}), encoding="utf-8")
            features.write_text("[]", encoding="utf-8")
            blocked_feedback = {
                "negative_keys": {"candidate artist|rejected song"},
                "negative_uris": {"spotify:track:rejected"},
                "negative_artists": {},
                "positive_artists": {},
                "positive_keys": set(),
                "positive_uris": set(),
                "daily_evidence": {},
            }
            track = {"name": "Rejected Song", "uri": "spotify:track:rejected",
                     "artists": [{"name": "Candidate Artist"}]}
            with patch.object(discovery, "load_playlist_feedback", return_value=blocked_feedback), \
                 patch.object(discovery, "spotify_artist_tracks", return_value=[track]), \
                 patch.object(discovery.intelligence, "track_metadata_index", return_value={}), \
                 patch.object(discovery.intelligence, "playlist_track_metadata", return_value={"lyric_themes": []}):
                with self.assertRaisesRegex(RuntimeError, "Only 0 discovery candidates"):
                    discovery.build_discovery_recommendations(
                        Mock(), [], profiles_path=profiles, features_path=features,
                        similar_artist_rows=[{"artist": "Candidate Artist", "similarity": 1.0, "supporting_seeds": 5}],
                        liked_keys=set(), playlist_id="playlist", target_size=1,
                    )


    def test_daily_exposure_history_is_playlist_scoped_and_decays(self):
        with tempfile.TemporaryDirectory() as directory:
            history = Path(directory) / "candidates.json"
            history.write_text(
                '[{"spotify_id":"daily1","spotify_uri":"spotify:track:daily1",'
                '"discovery_evidence":['
                '{"source":"tricky_daily_recommendations","observed_at":"2026-11-04T05:00:00+00:00",'
                '"context":{"playlist_id":"4yUVHSMQySfWeEowfIMcx7","cycle_date_eastern":"2026-11-04"}},'
                '{"source":"booze_recommendation","observed_at":"2026-11-05T05:00:00+00:00",'
                '"context":{"playlist_id":"4diIlnF8BlgoJrwUfejf49"}}]},'
                '{"spotify_id":"booze1","spotify_uri":"spotify:track:booze1",'
                '"discovery_evidence":[{"observed_at":"2026-11-05T05:00:00+00:00",'
                '"context":{"playlist_id":"4diIlnF8BlgoJrwUfejf49"}}]}]',
                encoding="utf-8",
            )
            recent = discovery.load_daily_discovery_exposure(date(2026, 11, 5), history)
            older = discovery.load_daily_discovery_exposure(date(2026, 11, 20), history)
        self.assertIn("spotify:track:daily1", recent)
        self.assertEqual(recent["spotify:track:daily1"]["events_30d"], 1)
        self.assertNotIn("spotify:track:booze1", recent)
        self.assertLess(
            older["spotify:track:daily1"]["penalty"],
            recent["spotify:track:daily1"]["penalty"],
        )

    def test_daily_exposure_uses_eastern_cycle_date_over_utc_timestamp(self):
        with tempfile.TemporaryDirectory() as directory:
            history = Path(directory) / "candidates.json"
            history.write_text(
                '[{"spotify_id":"daily1","spotify_uri":"spotify:track:daily1",'
                '"discovery_evidence":[{"observed_at":"2026-11-06T04:30:00+00:00",'
                '"context":{"playlist_id":"4yUVHSMQySfWeEowfIMcx7",'
                '"cycle_date_eastern":"2026-11-05"}}]}]',
                encoding="utf-8",
            )
            exposure = discovery.load_daily_discovery_exposure(date(2026, 11, 6), history)
        self.assertEqual(exposure["spotify:track:daily1"]["latest_days_ago"], 1)

    def test_daily_exposure_penalty_is_soft_and_positive_outcomes_override(self):
        track = {"name": "Track", "artists": [{"name": "Artist"}], "uri": "spotify:track:daily1"}
        exposure = {"discovery_exposure": {"spotify:track:daily1": {"penalty": 0.10}}}
        plain, *_ = discovery.candidate_score(track, 0.8, {}, set(), date(2026, 11, 5), {})
        exposed, *_ = discovery.candidate_score(track, 0.8, {}, set(), date(2026, 11, 5), exposure)
        saved_feedback = {
            **exposure,
            "daily_evidence": {"spotify:track:daily1": {"liked": True, "liked_at_add": False}},
        }
        saved, *_ = discovery.candidate_score(track, 0.8, {}, set(), date(2026, 11, 5), saved_feedback)
        self.assertLess(exposed, plain)
        self.assertAlmostEqual(saved, plain + 0.06, places=5)

    def test_measured_listening_reduces_daily_exposure_penalty(self):
        track = {"name": "Track", "artists": [{"name": "Artist"}], "uri": "spotify:track:daily1"}
        exposure = {"discovery_exposure": {"spotify:track:daily1": {"penalty": 0.10}}}
        unobserved, *_ = discovery.candidate_score(
            track, 0.8, {}, set(), date(2026, 11, 5), exposure
        )
        played_feedback = {
            **exposure,
            "daily_evidence": {
                "spotify:track:daily1": {
                    "measured_plays": 2,
                    "lastfm_plays": 0,
                    "liked": False,
                    "liked_at_add": False,
                }
            },
        }
        played, *_ = discovery.candidate_score(
            track, 0.8, {}, set(), date(2026, 11, 5), played_feedback
        )
        self.assertGreater(played, unobserved)

    def test_non_daily_feedback_does_not_apply_discovery_exposure(self):
        track = {"name": "Track", "artists": [{"name": "Artist"}], "uri": "spotify:track:daily1"}
        plain, *_ = discovery.candidate_score(track, 0.8, {}, set(), date(2026, 11, 5), {})
        other_playlist = {"discovery_exposure": {}}
        unchanged, *_ = discovery.candidate_score(track, 0.8, {}, set(), date(2026, 11, 5), other_playlist)
        self.assertEqual(unchanged, plain)


    def test_daily_mix_uses_freshness_quotas_and_artist_cap(self):
        ranked = []
        for tier, count in (("familiar", 20), ("rediscovery", 20), ("discovery", 20)):
            for index in range(count):
                ranked.append({
                    "uri": f"spotify:track:{tier}{index}",
                    "artist": f"{tier} artist {index // 2}",
                    "track": f"{tier} track {index}",
                    "tier": tier,
                    "score": 1.0 - index / 1000,
                })
        selected = discovery.select_daily_mix(ranked, target_size=20, per_artist=2)
        counts = {}
        for row in selected:
            counts[row["tier"]] = counts.get(row["tier"], 0) + 1
        self.assertEqual(len(selected), 20)
        self.assertEqual(counts, {"discovery": 9, "rediscovery": 6, "familiar": 5})
        self.assertLessEqual(max(
            sum(1 for row in selected if row["artist"] == artist)
            for artist in {row["artist"] for row in selected}
        ), 2)

    def test_daily_mix_backfills_short_tiers_by_global_rank(self):
        ranked = [
            {"uri": "spotify:track:d1", "artist": "D1", "tier": "discovery", "score": 0.9},
            {"uri": "spotify:track:r1", "artist": "R1", "tier": "rediscovery", "score": 0.8},
            {"uri": "spotify:track:f1", "artist": "F1", "tier": "familiar", "score": 0.7},
            {"uri": "spotify:track:f2", "artist": "F2", "tier": "familiar", "score": 0.6},
            {"uri": "spotify:track:f3", "artist": "F3", "tier": "familiar", "score": 0.5},
        ]
        selected = discovery.select_daily_mix(ranked, target_size=5, per_artist=2)
        self.assertEqual(len(selected), 5)
        self.assertEqual({row["uri"] for row in selected}, {row["uri"] for row in ranked})

    def test_daily_mix_is_deterministic_and_does_not_mutate_candidates(self):
        ranked = [
            {"uri": f"spotify:track:{tier}", "artist": tier, "tier": tier, "score": 1.0}
            for tier in ("discovery", "rediscovery", "familiar")
        ]
        before = [dict(row) for row in ranked]
        first = discovery.select_daily_mix(ranked, target_size=3)
        second = discovery.select_daily_mix(ranked, target_size=3)
        self.assertEqual(first, second)
        self.assertEqual(ranked, before)


if __name__ == "__main__":
    unittest.main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Regression test module.
# Scope: Regression checks for the behavior named by this test module.
# Run: python -m unittest tests.test_spotify_discovery -v (from the repository root).
# Related: Implementation lives under scripts/; longer behavior notes live in docs/.
# -----------------------------------------------------------------------------
