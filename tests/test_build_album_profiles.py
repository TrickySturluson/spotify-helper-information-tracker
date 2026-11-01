import unittest
from unittest.mock import patch

from scripts.music import build_album_profiles as albums


class AlbumProfileTests(unittest.TestCase):
    def test_catalogue_deduplicates_album_requests_and_prioritizes_playlists(self):
        rows = [
            {"artist": "Artist", "album": "Record", "track": "One", "timestamp": 1900000000},
            {"artist": "Artist", "album": "Record", "track": "Two", "timestamp": 1900000000},
            {"artist": "Other", "album": "Other Record", "track": "Three", "timestamp": 1},
        ]
        with patch.object(albums, "read", return_value={
            "id": "priority", "items_accessible": True,
            "items": [
                {"type": "track", "artists": ["Artist"], "album": "Record", "name": "One"},
                {"type": "track", "artists": ["Artist"], "album": "Record", "name": "Two"},
            ],
        }):
            result = albums.build_catalogue(rows, ["priority"], "unused")
        artist_record = result[albums.album_id("Artist", "Record")]
        self.assertEqual(len(result), 2)
        self.assertEqual(artist_record["priority_playlist_ids"], ["priority"])
        self.assertEqual(artist_record["track_count"], 2)

    def test_catalogue_ignores_inaccessible_or_wrong_playlist_snapshots(self):
        rows = []
        with patch.object(albums, "read", return_value={"id": "other", "items_accessible": False, "items": []}):
            result = albums.build_catalogue(rows, ["priority"], "unused")
        self.assertEqual(result, {})

    def test_album_response_requires_exact_artist_and_album_identity(self):
        payload = {"toptags": {"@attr": {"artist": "Artist", "album": "Record"},
                              "tag": [{"name": "dark", "count": "12"}]}}
        with patch.object(albums, "urlopen") as opened:
            response = opened.return_value.__enter__.return_value
            response.read.return_value = __import__("json").dumps(payload).encode()
            tags, status = albums.fetch_album_tags("Artist", "Record")
        self.assertEqual(status, "matched")
        self.assertEqual(tags[0]["tag"], "dark")
        self.assertEqual(tags[0]["count"], 12)

    def test_album_response_rejects_identity_mismatch(self):
        payload = {"toptags": {"@attr": {"artist": "Wrong", "album": "Record"},
                              "tag": [{"name": "dark", "count": "12"}]}}
        with patch.object(albums, "urlopen") as opened:
            response = opened.return_value.__enter__.return_value
            response.read.return_value = __import__("json").dumps(payload).encode()
            tags, status = albums.fetch_album_tags("Artist", "Record")
        self.assertEqual(tags, [])
        self.assertEqual(status, "identity_mismatch")



    def test_album_info_parses_ordered_tracklist_and_short_summary(self):
        payload = {"album": {"name": "Record", "artist": "Artist", "mbid": "release-id",
            "url": "https://www.last.fm/music/Artist/Record",
            "tracks": {"track": [
                {"name": "Opening", "duration": "91", "mbid": "rec-one", "@attr": {"rank": "1"}},
                {"name": "Finale", "duration": "122", "@attr": {"rank": "2"}},
            ]},
            "wiki": {"summary": "A <a href=x>short</a> album summary.", "content": "long content"},
            "image": [{"size": "large", "#text": "https://example.invalid/cover.jpg"}],
            "tags": {"tag": [{"name": "dark"}]}}}
        info, status = albums.parse_album_info(payload, "Artist", "Record")
        self.assertEqual(status, "matched")
        self.assertEqual([row["position"] for row in info["lastfm_tracklist"]], [1, 2])
        self.assertEqual(info["lastfm_tracklist"][0]["duration_seconds"], 91)
        self.assertIn("short", info["lastfm_summary"])
        self.assertNotIn("long content", str(info))
        self.assertTrue(info["lastfm_info_identity_verified"])

    def test_album_info_rejects_wrong_release_identity(self):
        info, status = albums.parse_album_info(
            {"album": {"name": "Different", "artist": "Artist"}}, "Artist", "Record")
        self.assertEqual(info, {})
        self.assertEqual(status, "identity_mismatch")


    def test_album_info_refreshes_legacy_tag_cache_once(self):
        old = {"status": "matched", "lastfm_tags": [{"tag": "rock"}], "retry_after": 0}
        self.assertTrue(albums.album_info_due(old, now=1000))
        new = {"status": "matched", "lastfm_info_status": "matched", "lastfm_info_retry_after": 0}
        self.assertFalse(albums.album_info_due(new, now=1000))

    def test_album_info_negative_cache_obeys_retry_after(self):
        old = {"lastfm_info_status": "identity_mismatch", "lastfm_info_retry_after": 2000}
        self.assertFalse(albums.album_info_due(old, now=1000))
        self.assertTrue(albums.album_info_due(old, now=2000))


    def test_album_info_merge_preserves_existing_top_tag_counts(self):
        previous = {"status": "matched", "identity_verified": True,
                    "lastfm_tags": [{"tag": "rock", "count": 42}]}
        info = {"lastfm_tracklist": [{"position": 1, "title": "Song"}],
                "lastfm_info_tags": [{"tag": "rock"}]}
        merged = albums.merge_album_info_profile(previous, {"artist": "Artist", "album": "Record"},
                                                 info, "matched", "checked", now=100)
        self.assertEqual(merged["lastfm_tags"][0]["count"], 42)
        self.assertEqual(merged["lastfm_tracklist"][0]["title"], "Song")
        self.assertEqual(merged["status"], "matched")
        self.assertEqual(merged["lastfm_info_status"], "matched")

    def test_album_info_merge_upgrades_old_no_tags_profile(self):
        previous = {"status": "no_tags", "lastfm_tags": [], "retry_after": 0}
        info = {"lastfm_info_tags": [{"tag": "dark"}]}
        merged = albums.merge_album_info_profile(previous, {}, info, "matched", "checked", now=100)
        self.assertEqual(merged["status"], "matched")
        self.assertEqual(merged["lastfm_tags"][0]["tag"], "dark")

    def test_album_info_merge_preserves_old_evidence_on_mismatch(self):
        previous = {"status": "matched", "identity_verified": True,
                    "lastfm_tags": [{"tag": "rock", "count": 42}]}
        merged = albums.merge_album_info_profile(previous, {}, {}, "identity_mismatch", "checked", now=100)
        self.assertEqual(merged["lastfm_tags"][0]["count"], 42)
        self.assertTrue(merged["identity_verified"])
        self.assertEqual(merged["lastfm_info_status"], "identity_mismatch")
        self.assertGreater(merged["lastfm_info_retry_after"], 100)

if __name__ == "__main__":
    unittest.main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Regression tests for incremental Last.fm album profile enrichment.
# Coverage: Album lookup deduplication, priority-playlist selection, inaccessible
#           snapshot handling, exact provider identity verification and parsing.
# Run: python -m unittest tests.test_build_album_profiles -v
# Related: scripts/music/build_album_profiles.py; docs/AUTOMATED_AUDIO_METADATA.md.
# -----------------------------------------------------------------------------
