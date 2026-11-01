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


if __name__ == "__main__":
    unittest.main()
