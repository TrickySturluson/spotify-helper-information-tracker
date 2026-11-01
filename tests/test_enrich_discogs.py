import unittest

from enrich_discogs import exact_release_track, lookup_track, unique_release_candidate


class DiscogsEnrichmentTests(unittest.TestCase):
    def test_exact_track_requires_exact_artist_and_title(self):
        release = {
            "artists": [{"name": "Example Artist"}],
            "tracklist": [{"title": "Example Song", "position": "A1"}],
        }
        self.assertEqual(exact_release_track(release, "Example Artist", "Example Song")["position"], "A1")
        self.assertIsNone(exact_release_track(release, "Other Artist", "Example Song"))
        self.assertIsNone(exact_release_track(release, "Example Artist", "Example Song (Live)"))

    def test_duplicate_track_titles_in_release_are_rejected(self):
        release = {
            "artists": [{"name": "Example Artist"}],
            "tracklist": [{"title": "Song"}, {"title": "Song"}],
        }
        self.assertIsNone(exact_release_track(release, "Example Artist", "Song"))

    def test_multiple_masters_are_ambiguous(self):
        candidate, status = unique_release_candidate([
            {"id": 1, "master_id": 10},
            {"id": 2, "master_id": 20},
        ])
        self.assertIsNone(candidate)
        self.assertEqual(status, "ambiguous_release")

    def test_unique_master_and_exact_track_produce_release_context(self):
        calls = []
        def fake_fetch(path, params=None):
            calls.append((path, params))
            if path == "/database/search":
                return {"results": [{"id": 123, "master_id": 456}]}, {}
            return {
                "id": 123, "master_id": 456, "title": "Example Album",
                "artists": [{"name": "Example Artist"}],
                "tracklist": [{"title": "Example Song", "position": "A1"}],
                "genres": ["Rock"], "styles": ["Deathrock"],
                "uri": "https://www.discogs.com/release/123",
            }, {}
        row, status = lookup_track("Example Artist", "Example Song", fake_fetch)
        self.assertEqual(status, "matched")
        self.assertEqual(row["discogs_styles"], ["Deathrock"])
        self.assertEqual(row["discogs_scope"], "release-level context; not track-specific acoustic evidence")
        self.assertEqual(calls[0][0], "/database/search")
        self.assertEqual(calls[1][0], "/releases/123")

    def test_release_with_wrong_track_is_rejected(self):
        def fake_fetch(path, params=None):
            if path == "/database/search":
                return {"results": [{"id": 123, "master_id": 456}]}, {}
            return {
                "artists": [{"name": "Example Artist"}],
                "tracklist": [{"title": "Different Song"}],
            }, {}
        row, status = lookup_track("Example Artist", "Example Song", fake_fetch)
        self.assertIsNone(row)
        self.assertEqual(status, "release_track_or_artist_mismatch")


if __name__ == "__main__":
    unittest.main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Verify conservative Discogs track-to-release identity matching.
# Coverage: Exact artist/title, ambiguous masters, duplicate track titles,
#           provenance, and rejection of release-level false positives.
# Run: python -m unittest tests.test_enrich_discogs -v.
# Related: scripts/music/enrich_discogs.py and docs/AUTOMATED_AUDIO_METADATA.md.
# -----------------------------------------------------------------------------
