import unittest
from datetime import date
from unittest.mock import Mock

import spotify_daily_playlist as daily


class DailyCuratorTests(unittest.TestCase):
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
