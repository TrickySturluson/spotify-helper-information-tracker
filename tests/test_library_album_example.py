"""Regression tests for the staged Ceres & Calypso album-library example."""
import unittest

from music_library import MusicLibrary


class LibraryAlbumExampleTests(unittest.TestCase):
    """Ensure album metadata is indexed and recallable through the public API."""

    def setUp(self):
        self.library = MusicLibrary()
        self.artist = "Candy Claws"
        self.album_title = "Ceres & Calypso in the Deep Time"

    def test_album_is_retrievable_with_ordered_tracklist(self):
        album = self.library.get_album(artist=self.artist, album=self.album_title)
        self.assertIsNotNone(album)
        self.assertEqual(album["identity"]["spotify_album_id"], "5KkGAZrad4N4rc5FriwgzU")
        tracks = album["evidence"]["lastfm_tracklist"]
        self.assertEqual(len(tracks), 12)
        self.assertEqual([row["position"] for row in tracks], list(range(1, 13)))
        self.assertEqual(album["evidence"]["release_metadata"]["release_date"], "2013-06-25")

    def test_song_lookup_returns_linked_album_context(self):
        audit = self.library.lookup_song(
            recording_mbid="d6e2c73d-7d12-4b48-8cf4-85063c45e4df"
        )
        self.assertEqual(audit["status"], "matched")
        self.assertEqual(audit["matched_by"], "musicbrainz_recording_mbid")
        bundle = self.library.get_song(
            recording_mbid="d6e2c73d-7d12-4b48-8cf4-85063c45e4df"
        )
        self.assertEqual(bundle["song"]["identity"]["album"], self.album_title)
        self.assertEqual(bundle["album"]["id"], "album:01632cb9b68c6acda89d")
        self.assertEqual(bundle["album"]["identity"]["spotify_album_id"], "5KkGAZrad4N4rc5FriwgzU")
        self.assertEqual(bundle["album"]["song_ids"], [
            "mbid:4346d7c9-c6da-4610-b81e-9e2e892b7fde",
            "mbid:a55df03b-b6de-4240-a816-e9392fc7e270",
            "mbid:d6e2c73d-7d12-4b48-8cf4-85063c45e4df",
            "mbid:15a01c36-59b4-4bb1-9c94-92d14773f573",
        ])

    def test_album_context_does_not_claim_all_track_identities(self):
        album = self.library.get_album(artist=self.artist, album=self.album_title)
        tracklist = album["evidence"]["lastfm_tracklist"]
        self.assertEqual(len(tracklist), 12)
        self.assertEqual(len(album["song_ids"]), 4)
        self.assertTrue(all(row["recording_identity_verified"] is False for row in tracklist))

    def test_album_key_uses_canonical_artist_album_identity(self):
        album = self.library.get_album(artist=self.artist, album=self.album_title)
        self.assertEqual(album["id"], "album:01632cb9b68c6acda89d")
        self.assertEqual(self.library.index["albums"][album["id"]]["path"],
                         "albums/al/album-01632cb9b68c6acda89d/album.json")


if __name__ == "__main__":
    unittest.main()


# FILE OVERVIEW
# - Verifies exact artist/title album recall and ordered release tracklist integrity.
# - Exercises MusicLibrary song lookup and the joined song/artist/album response.
# - Protects the boundary between album tracklists and verified song identities.
# - Confirms the album record uses the canonical normalized artist/album key.
