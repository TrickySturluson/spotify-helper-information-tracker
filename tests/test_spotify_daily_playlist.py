import unittest
import urllib.parse
from datetime import date
from unittest.mock import Mock

import spotify_daily_playlist as daily


class DailyCuratorTests(unittest.TestCase):
    def test_repository_archive_produces_a_diverse_daily_set(self):
        from pathlib import Path
        features = Path("assistant_data/recommendations/track_features.json")
        if not features.is_file():
            self.skipTest("generated recommendation archive is not present")
        import json
        tracks = json.loads(features.read_text(encoding="utf-8"))
        ranked = daily.rank_candidates(tracks, today=date(2026, 10, 30), limit=30)
        self.assertEqual(len(ranked), 30)
        counts = {}
        for row in ranked:
            counts[row["artist"]] = counts.get(row["artist"], 0) + 1
        self.assertLessEqual(max(counts.values()), 2)

    def test_recent_tracks_are_excluded(self):
        tracks = [
            {"track_id": "a", "artist": "A", "track": "Fresh", "plays": 100, "last_scrobble": "2026-10-25T00:00:00+00:00"},
            {"track_id": "b", "artist": "B", "track": "Old", "plays": 1, "last_scrobble": "2026-01-01T00:00:00+00:00"},
        ]
        ranked = daily.rank_candidates(tracks, today=date(2026, 10, 30), limit=10)
        self.assertEqual([x["track"] for x in ranked], ["Old"])

    def test_artist_cap_preserves_variety(self):
        tracks = []
        for i in range(8):
            tracks.append({"track_id": str(i), "artist": "Same Artist", "track": f"Track {i}", "plays": 1, "last_scrobble": "2025-01-01T00:00:00+00:00"})
        tracks.append({"track_id": "other", "artist": "Other Artist", "track": "Different", "plays": 1, "last_scrobble": "2025-01-01T00:00:00+00:00"})
        ranked = daily.rank_candidates(tracks, today=date(2026, 10, 30), limit=5)
        self.assertEqual(sum(x["artist"] == "Same Artist" for x in ranked), 2)
        self.assertIn("Other Artist", [x["artist"] for x in ranked])

    def test_repeat_listening_is_a_stronger_signal_than_a_single_scrobble(self):
        favorite = {"plays": 12, "last_scrobble": "2026-01-01T00:00:00+00:00"}
        one_off = {"plays": 1, "last_scrobble": "2026-01-01T00:00:00+00:00"}
        self.assertGreater(daily.score_track(favorite, date(2026, 10, 30)), daily.score_track(one_off, date(2026, 10, 30)))

    def test_daily_mix_balances_favorites_rediscoveries_and_deep_cuts(self):
        tracks = []
        for i in range(10):
            tracks.append({"track_id": f"f{i}", "artist": f"Favorite Artist {i}", "track": f"Favorite {i}", "plays": 8, "last_scrobble": "2025-01-01T00:00:00+00:00"})
            tracks.append({"track_id": f"r{i}", "artist": f"Rediscovery Artist {i}", "track": f"Rediscovery {i}", "plays": 3, "last_scrobble": "2025-01-01T00:00:00+00:00"})
            tracks.append({"track_id": f"d{i}", "artist": f"Deep Cut Artist {i}", "track": f"Deep Cut {i}", "plays": 1, "last_scrobble": "2025-01-01T00:00:00+00:00"})
        ranked = daily.rank_candidates(tracks, today=date(2026, 10, 30), limit=10)
        counts = {}
        for row in ranked:
            counts[row["_tier"]] = counts.get(row["_tier"], 0) + 1
        self.assertEqual(counts, {"favorite": 4, "rediscovery": 4, "deep_cut": 2})

    def test_candidate_order_interleaves_tiers_before_resolution(self):
        tracks = []
        for i in range(10):
            tracks.append({"track_id": f"f{i}", "artist": f"Favorite {i}", "track": f"F{i}", "plays": 8, "last_scrobble": "2025-01-01T00:00:00+00:00"})
            tracks.append({"track_id": f"r{i}", "artist": f"Rediscovery {i}", "track": f"R{i}", "plays": 3, "last_scrobble": "2025-01-01T00:00:00+00:00"})
            tracks.append({"track_id": f"d{i}", "artist": f"Deep {i}", "track": f"D{i}", "plays": 1, "last_scrobble": "2025-01-01T00:00:00+00:00"})
        ranked = daily.rank_candidates(tracks, today=date(2026, 10, 30), limit=10)
        self.assertEqual([row["_tier"] for row in ranked[:5]], [
            "favorite", "rediscovery", "favorite", "rediscovery", "deep_cut"
        ])

    def test_tier_shortage_is_filled_from_remaining_candidates(self):
        tracks = [
            {"track_id": str(i), "artist": f"Artist {i}", "track": f"Track {i}", "plays": 8, "last_scrobble": "2025-01-01T00:00:00+00:00"}
            for i in range(3)
        ]
        tracks += [
            {"track_id": f"d{i}", "artist": f"Deep {i}", "track": f"Cut {i}", "plays": 1, "last_scrobble": "2025-01-01T00:00:00+00:00"}
            for i in range(5)
        ]
        ranked = daily.rank_candidates(tracks, today=date(2026, 10, 30), limit=6)
        self.assertEqual(len(ranked), 6)

    def test_scoring_rewards_a_longer_gap(self):
        recent = {"plays": 20, "last_scrobble": "2026-10-01T00:00:00+00:00"}
        old = {"plays": 20, "last_scrobble": "2025-01-01T00:00:00+00:00"}
        self.assertGreater(daily.score_track(old, date(2026, 10, 30)), daily.score_track(recent, date(2026, 10, 30)))

    def test_only_exact_title_and_primary_artist_match_is_accepted(self):
        sp = Mock()
        sp.call.return_value = {"tracks": {"items": [
            {"name": "Track", "artists": [{"name": "Wrong Artist"}], "uri": "spotify:track:wrong"},
            {"name": "Track (Remaster)", "artists": [{"name": "Artist"}], "uri": "spotify:track:remaster"},
            {"name": "Track", "artists": [{"name": "Artist"}], "uri": "spotify:track:exact"},
        ]}}
        resolved, skipped = daily.resolve_exact_tracks(sp, [
            {"artist": "Artist", "track": "Track", "plays": 3, "last_scrobble": "2025-01-01T00:00:00+00:00"}
        ])
        self.assertEqual([x["uri"] for x in resolved], ["spotify:track:exact"])
        self.assertEqual(skipped, [])

    def test_matching_normalizes_internal_whitespace(self):
        self.assertEqual(daily.norm("  Artist   Name  "), "artist name")

    def test_spotify_resolution_preserves_tier_quotas(self):
        candidates = []
        for tier, plays, prefix in (("favorite", 8, "f"), ("rediscovery", 3, "r"), ("deep_cut", 1, "d")):
            for i in range(8):
                candidates.append({
                    "track_id": f"{prefix}{i}", "artist": f"{prefix} artist {i}",
                    "track": f"{prefix} track {i}", "plays": plays, "_tier": tier,
                    "_score": 0.5, "last_scrobble": "2025-01-01T00:00:00+00:00"
                })
        sp = Mock()
        def exact_match(method, endpoint):
            query = urllib.parse.parse_qs(urllib.parse.urlparse(endpoint).query)["q"][0]
            candidate = next(row for row in candidates if query == f'track:"{row["track"]}" artist:"{row["artist"]}"')
            return {"tracks": {"items": [{
                "name": candidate["track"],
                "artists": [{"name": candidate["artist"]}],
                "uri": f"spotify:track:{candidate['track_id']}"
            }]}}
        sp.call.side_effect = exact_match
        resolved, skipped = daily.resolve_exact_tracks(sp, candidates, limit=10)
        counts = {}
        for row in resolved:
            counts[row["tier"]] = counts.get(row["tier"], 0) + 1
        self.assertEqual(len(resolved), 10)
        self.assertEqual(counts, {"favorite": 4, "rediscovery": 4, "deep_cut": 2})
        self.assertEqual([row["tier"] for row in resolved[:5]], [
            "favorite", "rediscovery", "favorite", "rediscovery", "deep_cut"
        ])
        self.assertEqual(skipped, [])

    def test_existing_playlist_uri_is_not_added_again(self):
        sp = Mock()
        sp.call.return_value = {"tracks": {"items": [
            {"name": "Track", "artists": [{"name": "Artist"}], "uri": "spotify:track:exact"}
        ]}}
        resolved, skipped = daily.resolve_exact_tracks(sp, [
            {"artist": "Artist", "track": "Track"}
        ], existing_uris={"spotify:track:exact"})
        self.assertEqual(resolved, [])
        self.assertEqual(skipped[0]["reason"], "already in Tricky Daily")


if __name__ == "__main__":
    unittest.main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Regression test module.
# Scope: Regression checks for the behavior named by this test module.
# Run: python -m unittest tests.test_spotify_daily_playlist -v (from the repository root).
# Related: Implementation lives under scripts/; longer behavior notes live in docs/.
# -----------------------------------------------------------------------------
