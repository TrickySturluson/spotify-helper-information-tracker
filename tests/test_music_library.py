import json
import tempfile
import unittest
from pathlib import Path
from music_library import MusicLibrary
import spotify_playlist_sequencer as sequencer

class MusicLibraryTests(unittest.TestCase):
    def test_id_lookup_and_related_context(self):
        with tempfile.TemporaryDirectory() as temp:
            lib = MusicLibrary(temp)
            result = lib.put_catalogue({"r": {"artist": "A", "track": "T", "album": "L", "track_mbid": "rec-1", "spotify_id": "spotify:track:sid", "lastfm_tags": [{"tag": "dark"}]}})
            self.assertEqual(result["recordings"], 1)
            found = lib.get_recording(spotify_id="sid")
            self.assertEqual(found["recording"]["evidence"]["track_metadata"]["lastfm_tags"][0]["tag"], "dark")
            self.assertEqual(found["artist"]["artist"], "A")
            self.assertEqual(found["album"]["album"], "L")
    def test_same_title_different_albums_remains_ambiguous(self):
        with tempfile.TemporaryDirectory() as temp:
            lib = MusicLibrary(temp)
            rows = {"a": {"artist": "A", "track": "T", "album": "Original"}, "b": {"artist": "A", "track": "T", "album": "Remaster"}}
            result = lib.put_catalogue(rows)
            self.assertEqual(result["recordings"], 2)
            self.assertEqual(result["ambiguous_name_aliases"], 1)
            self.assertIsNone(lib.get_recording(artist="A", track="T"))
            self.assertEqual(lib.get_recording(artist="A", track="T", album="Remaster")["recording"]["identity"]["album"], "Remaster")
    def test_scopes_remain_separate(self):
        with tempfile.TemporaryDirectory() as temp:
            lib = MusicLibrary(temp)
            lib.put_catalogue({"a": {"artist": "A", "track": "T", "album": "L", "lastfm_tags": [{"tag": "dreamy"}]}})
            found = lib.get_recording(artist="A", track="T")
            self.assertIn("lastfm_tags", found["recording"]["evidence"]["track_metadata"])
            self.assertEqual(found["recording"]["identity"]["identity_quality"], "fallback_release_context")
    def test_sequencer_loads_playlist_records_by_spotify_id(self):
        with tempfile.TemporaryDirectory() as temp:
            lib = MusicLibrary(temp)
            lib.put_catalogue({"r": {"artist": "Artist", "track": "Song", "album": "Release",
                "spotify_id": "spotify:track:abc", "lastfm_tags": [{"tag": "aggressive"}]}})
            loaded = sequencer.load_library_profiles([
                {"uri": "spotify:track:abc", "name": "Song", "artists": ["Artist"], "album": "Release"}
            ], root=temp)
            self.assertIsNotNone(loaded)
            artists, tracks, audio, albums = loaded
            self.assertIn(("artist", "song"), tracks)
            self.assertEqual(tracks[("artist", "song")]["lastfm_tags"][0]["tag"], "aggressive")
            self.assertIn(("artist", "release"), albums)

    def test_index_and_record_are_separate_files(self):
        with tempfile.TemporaryDirectory() as temp:
            lib = MusicLibrary(temp); lib.put_catalogue({"a": {"artist": "A", "track": "T", "album": "L"}})
            index = json.loads((Path(temp) / "library_index.json").read_text())
            key = next(iter(index["recordings"]))
            self.assertTrue((Path(temp) / index["recordings"][key]["path"]).exists())

if __name__ == "__main__": unittest.main()

# File overview
# - Covers lazy ID resolution, release collisions, evidence separation, and on-disk layout.
