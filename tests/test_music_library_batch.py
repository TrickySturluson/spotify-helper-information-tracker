import json
import unittest
from pathlib import Path

from music_library import MusicLibrary
import spotify_playlist_sequencer as sequencer


ROOT = Path(__file__).resolve().parents[1] / "assistant_data" / "music" / "library"


class LibraryBatchIntegrationTests(unittest.TestCase):
    def test_committed_batch_has_valid_index_and_related_records(self):
        self.assertTrue((ROOT / "library_index.json").exists(), "staged Library batch is missing")
        library = MusicLibrary(ROOT)
        report = library.audit()
        self.assertTrue(report["ok"], report["errors"])
        self.assertEqual(report["songs"], 50)
        self.assertEqual(report["artists"], 22)
        self.assertEqual(report["albums"], 0)

    def test_committed_batch_loads_through_playlist_sequencer(self):
        index = json.loads((ROOT / "library_index.json").read_text(encoding="utf-8"))
        items = [
            {"name": entry["track"], "artists": [entry["artist"]], "album": ""}
            for entry in index["songs"].values()
        ]
        loaded = sequencer.load_library_profiles(items, root=ROOT)
        self.assertIsNotNone(loaded)
        artists, tracks, audio, albums = loaded
        self.assertEqual(len(tracks), 50)
        self.assertEqual(len(artists), 22)
        self.assertEqual(albums, {})
        self.assertTrue(any(profile.get("lastfm_tags") or profile.get("musicbrainz_tags")
                            for profile in tracks.values()))

    def test_committed_batch_preserves_recent_listening_context(self):
        index = json.loads((ROOT / "library_index.json").read_text(encoding="utf-8"))
        entry = next(iter(index["songs"].values()))
        song = json.loads((ROOT / entry["path"]).read_text(encoding="utf-8"))
        context = song.get("listening_context") or {}
        self.assertEqual(context.get("source"), "Last.fm scrobble archive")
        self.assertIsInstance(context.get("recent_plays"), int)
        self.assertIsInstance(context.get("all_time_plays"), int)


if __name__ == "__main__":
    unittest.main()


# FILE OVERVIEW
# - Exercises the committed 50-song staged Library dataset, not just synthetic fixtures.
# - Audits every song/artist path and verifies the playlist sequencer can load the batch.
# - Checks that recent listening counts remain separate from track-level evidence.
