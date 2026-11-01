import json
import subprocess
import sys
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
        self.assertEqual(report["songs"], 100)
        self.assertEqual(report["artists"], 47)
        self.assertEqual(report["albums"], 1)  # Ceres & Calypso is the first committed album example

    def test_committed_batch_loads_through_playlist_sequencer(self):
        index = json.loads((ROOT / "library_index.json").read_text(encoding="utf-8"))
        items = [
            {"name": entry["track"], "artists": [entry["artist"]], "album": ""}
            for entry in index["songs"].values()
        ]
        loaded = sequencer.load_library_profiles(items, root=ROOT)
        self.assertIsNotNone(loaded)
        artists, tracks, audio, albums = loaded
        self.assertEqual(len(tracks), 100)
        self.assertEqual(len(artists), 45)
        self.assertEqual(albums, {})
        self.assertTrue(any(profile.get("lastfm_tags") or profile.get("musicbrainz_tags")
                            for profile in tracks.values()))


    def test_second_batch_source_id_and_recording_mbid_are_retrievable(self):
        index = json.loads((ROOT / "library_index.json").read_text(encoding="utf-8"))
        library = MusicLibrary(ROOT)

        source_entry = next(
            (key, value) for key, value in index["songs"].items()
            if key.startswith("source:")
        )
        source_song = library.get_song(
            artist=source_entry[1]["artist"], track=source_entry[1]["track"]
        )
        self.assertIsNotNone(source_song)
        self.assertEqual(source_song["song"]["id"], source_entry[0])

        mbid_entry = next(
            (key, value) for key, value in index["songs"].items()
            if key.startswith("mbid:") and value["path"].startswith("songs/")
            and (ROOT / value["path"]).exists()
        )
        mbid_song = library.get_song(recording_mbid=mbid_entry[0])
        self.assertIsNotNone(mbid_song)
        self.assertEqual(mbid_song["song"]["id"], mbid_entry[0])

    def test_ceres_album_tracklist_crosslinks_only_verified_recordings(self):
        index = json.loads((ROOT / "library_index.json").read_text(encoding="utf-8"))
        self.assertEqual(len(index["albums"]), 1)
        album_id, album_entry = next(iter(index["albums"].items()))
        album = json.loads((ROOT / album_entry["path"]).read_text(encoding="utf-8"))
        self.assertEqual(album["album"], "Ceres & Calypso in the Deep Time")

        tracklist = album["evidence"]["lastfm_tracklist"]
        self.assertEqual([track["position"] for track in tracklist], list(range(1, 13)))
        linked = [track for track in tracklist if track.get("linked_song_id")]
        self.assertEqual(len(linked), 4)
        self.assertEqual({track["linked_song_id"] for track in linked}, set(album["song_ids"]))

        library = MusicLibrary(ROOT)
        for track in linked:
            song_id = track["linked_song_id"]
            self.assertEqual(track["linked_recording_mbid"], song_id.removeprefix("mbid:"))
            self.assertEqual(track["link_verification"]["confidence"], "high")
            entry = index["songs"][song_id]
            self.assertEqual(entry["album_id"], album_id)
            self.assertEqual(entry["track_number"], track["position"])
            self.assertTrue((ROOT / entry["path"]).exists())
            result = library.get_song(recording_mbid=song_id)
            self.assertIsNotNone(result)
            self.assertEqual(result["album"]["album"], album["album"])

        # The source tracklist did not provide MBIDs; cross-links are recorded
        # separately so they do not falsely appear to originate from Last.fm.
        self.assertTrue(all(track.get("mbid") is None for track in tracklist))
        self.assertEqual(sum(bool(track.get("linked_song_id")) for track in tracklist), 4)

    def test_committed_batch_preserves_recent_listening_context(self):
        index = json.loads((ROOT / "library_index.json").read_text(encoding="utf-8"))
        entry = next(iter(index["songs"].values()))
        song = json.loads((ROOT / entry["path"]).read_text(encoding="utf-8"))
        context = song.get("listening_context") or {}
        self.assertEqual(context.get("source"), "Last.fm scrobble archive")
        self.assertIsInstance(context.get("recent_plays"), int)
        self.assertIsInstance(context.get("all_time_plays"), int)



    def test_compat_recent_batch_dry_run_is_local_and_selects_50(self):
        result = subprocess.run(
            [sys.executable, "compat/migrate_music_library.py", "--recent-limit", "50", "--dry-run"],
            cwd=ROOT.parents[2],
            check=True, capture_output=True, text=True,
        )
        summary = json.loads(result.stdout)
        self.assertEqual(summary["track_profiles_selected"], 50)
        self.assertEqual(summary["selection"]["selected"], 50)
        self.assertEqual(summary["provider_requests"], 0)
        self.assertEqual(summary["writes"], 0)

if __name__ == "__main__":
    unittest.main()


# FILE OVERVIEW
# - Exercises both committed 50-song batches (100 songs total), not just synthetic fixtures.
# - Audits every song/artist path and verifies the playlist sequencer can load all 100 songs.
# - Checks that recent listening counts remain separate from track-level evidence.
