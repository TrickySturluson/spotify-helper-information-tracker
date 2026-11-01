import tempfile
import unittest
from music_library import MusicLibrary


class MusicEvidenceIntegrationTests(unittest.TestCase):
    def test_isrc_lookup_is_indexed_and_explained(self):
        with tempfile.TemporaryDirectory() as temp:
            library = MusicLibrary(temp)
            library.put_catalogue({"one": {
                "artist": "Artist", "track": "Song", "isrc": "US-ABC-26-12345",
                "track_mbid": "recording-id",
                "lastfm_tags": [{"tag": "dark"}], "musicbrainz_tags": [{"tag": "dark"}],
            }})
            result = library.lookup_song(isrc="USABC2612345")
            self.assertEqual(result["status"], "matched")
            self.assertEqual(result["matched_by"], "isrc")
            self.assertEqual(result["confidence"], "high")
            self.assertEqual(result["metadata_confidence"]["track_tags"]["dark"]["confidence"], "high")
            self.assertEqual(library.get_song(isrc="USABC2612345")["lookup_audit"]["matched_by"], "isrc")

    def test_release_position_lookup_requires_unique_release_disc_and_track(self):
        with tempfile.TemporaryDirectory() as temp:
            library = MusicLibrary(temp)
            library.put_catalogue({
                "one": {"artist": "Artist", "track": "One", "release_mbid": "release-id",
                        "track_number": 1, "disc_number": 1, "track_mbid": "recording-one"},
                "two": {"artist": "Artist", "track": "Two", "release_mbid": "release-id",
                        "track_number": 2, "disc_number": 1, "track_mbid": "recording-two"},
            })
            result = library.lookup_song(release_mbid="release-id", track_number=2, disc_number=1)
            self.assertEqual(result["status"], "matched")
            self.assertEqual(result["matched_by"], "verified_release_track_position")
            self.assertEqual(result["confidence"], "high")
            self.assertEqual(result["song_id"], "mbid:recording-two")

    def test_ambiguous_exact_name_lookup_reports_all_candidates(self):
        with tempfile.TemporaryDirectory() as temp:
            library = MusicLibrary(temp)
            library.put_catalogue({
                "a": {"artist": "Artist", "track": "Song", "album": "Original"},
                "b": {"artist": "Artist", "track": "Song", "album": "Remaster"},
            })
            result = library.lookup_song(artist="Artist", track="Song")
            self.assertEqual(result["status"], "ambiguous")
            self.assertEqual(len(result["candidate_ids"]), 2)
            self.assertEqual(result["confidence"], "unknown")

    def test_exact_album_profile_evidence_is_attached_to_release_record(self):
        with tempfile.TemporaryDirectory() as temp:
            library = MusicLibrary(temp)
            albums = {"profile": {
                "artist": "Artist", "album": "Record", "identity_verified": True,
                "lastfm_tracklist": [{"position": 1, "title": "Song"}],
                "lastfm_summary": "Short attributed summary.",
                "lastfm_url": "https://www.last.fm/music/Artist/Record",
            }}
            library.put_catalogue({"one": {
                "artist": "Artist", "track": "Song", "album": "Record",
            }}, album_rows=albums)
            result = library.get_album(artist="Artist", album="Record")
            self.assertEqual(result["evidence"]["lastfm_tracklist"][0]["title"], "Song")
            self.assertIn("Short attributed summary", result["evidence"]["lastfm_summary"])
            self.assertEqual(result["confidence"]["summary"]["confidence"], "low")


if __name__ == "__main__":
    unittest.main()


# FILE OVERVIEW
# Purpose: Integration tests for ISRC/release-position lookup audits and album metadata persistence.
# Coverage: Stable ID resolution, ambiguity reporting, confidence labels, and verified album evidence.
# Run: python -m unittest tests.test_music_evidence_integration -v.
# Related: scripts/music/music_library.py; scripts/music/music_evidence.py; tests/test_music_library.py.
