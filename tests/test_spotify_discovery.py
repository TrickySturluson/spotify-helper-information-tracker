import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch

import spotify_discovery as discovery


class DiscoveryScoringTests(unittest.TestCase):
    def test_artist_diversity_selector_keeps_only_one_track_per_artist(self):
        candidates = [
            {"artist": "Artist A", "track": "Lower score", "score": 0.7},
            {"artist": "Artist B", "track": "Track B", "score": 0.8},
            {"artist": " artist   a ", "track": "Higher score", "score": 0.9},
            {"artist": "Artist C", "track": "Track C", "score": 0.6},
        ]
        selected = discovery.select_unique_artist_candidates(candidates, target_size=3)
        self.assertEqual(len(selected), 3)
        self.assertEqual(selected[0]["track"], "Higher score")
        self.assertEqual(len({discovery.norm(row["artist"]) for row in selected}), 3)

    def test_two_per_artist_is_only_a_fallback_selection_ceiling(self):
        candidates = [
            {"artist": "Artist A", "track": "A1", "score": 1.0},
            {"artist": "Artist A", "track": "A2", "score": 0.9},
            {"artist": "Artist A", "track": "A3", "score": 0.8},
            {"artist": "Artist B", "track": "B1", "score": 0.7},
            {"artist": "Artist B", "track": "B2", "score": 0.6},
            {"artist": "Artist C", "track": "C1", "score": 0.5},
        ]
        strict = discovery.select_unique_artist_candidates(candidates, target_size=6)
        fallback = discovery.select_unique_artist_candidates(candidates, target_size=6, max_per_artist=2)
        self.assertEqual(len(strict), 3)
        self.assertEqual(len(fallback), 5)
        counts = {}
        for row in fallback:
            key = discovery.norm(row["artist"])
            counts[key] = counts.get(key, 0) + 1
        self.assertLessEqual(max(counts.values()), 2)
        self.assertEqual(fallback[0]["track"], "A1")

    def test_spotify_artist_search_supports_alternate_result_page(self):
        sp = Mock()
        sp.call.return_value = {"tracks": {"items": []}}
        discovery.spotify_artist_tracks(sp, "Artist", offset=10)
        self.assertIn("offset=10", sp.call.call_args.args[1])

    def test_general_discovery_defaults_remain_unchanged_and_artist_pool_is_expanded(self):
        self.assertEqual(discovery.TARGET_SIZE, 30)
        self.assertEqual(discovery.MIN_MATCHES, 20)
        self.assertGreaterEqual(discovery.DISCOVERY_ARTISTS, 60)

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


if __name__ == "__main__":
    unittest.main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Regression test module.
# Scope: Regression checks for the behavior named by this test module.
# Run: python -m unittest tests.test_spotify_discovery -v (from the repository root).
# Related: Implementation lives under scripts/; longer behavior notes live in docs/.
# -----------------------------------------------------------------------------
