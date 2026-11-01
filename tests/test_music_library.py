import json
import tempfile
import unittest
from pathlib import Path
from music_library import MusicLibrary, select_recent_track_rows
import spotify_playlist_sequencer as sequencer

class MusicLibraryTests(unittest.TestCase):
    def test_id_lookup_and_related_context(self):
        with tempfile.TemporaryDirectory() as temp:
            lib = MusicLibrary(temp)
            result = lib.put_catalogue({"r": {"artist": "A", "track": "T", "album": "L", "track_mbid": "rec-1", "spotify_id": "spotify:track:sid", "lastfm_tags": [{"tag": "dark"}]}})
            self.assertEqual(result["songs"], 1)
            found = lib.get_song(spotify_id="sid")
            self.assertEqual(found["song"]["evidence"]["track_metadata"]["lastfm_tags"][0]["tag"], "dark")
            self.assertEqual(found["artist"]["artist"], "A")
            self.assertEqual(found["album"]["album"], "L")
    def test_same_title_different_albums_remains_ambiguous(self):
        with tempfile.TemporaryDirectory() as temp:
            lib = MusicLibrary(temp)
            rows = {"a": {"artist": "A", "track": "T", "album": "Original"}, "b": {"artist": "A", "track": "T", "album": "Remaster"}}
            result = lib.put_catalogue(rows)
            self.assertEqual(result["songs"], 2)
            self.assertEqual(result["ambiguous_name_aliases"], 1)
            self.assertIsNone(lib.get_song(artist="A", track="T"))
            self.assertEqual(lib.get_song(artist="A", track="T", album="Remaster")["song"]["identity"]["album"], "Remaster")
    def test_scopes_remain_separate(self):
        with tempfile.TemporaryDirectory() as temp:
            lib = MusicLibrary(temp)
            lib.put_catalogue({"a": {"artist": "A", "track": "T", "album": "L", "lastfm_tags": [{"tag": "dreamy"}]}})
            found = lib.get_song(artist="A", track="T")
            self.assertIn("lastfm_tags", found["song"]["evidence"]["track_metadata"])
            self.assertEqual(found["song"]["identity"]["identity_quality"], "fallback_release_context")
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
            key = next(iter(index["songs"]))
            self.assertTrue((Path(temp) / index["songs"][key]["path"]).exists())
            song = json.loads((Path(temp) / index["songs"][key]["path"]).read_text())
            self.assertEqual(song["mood"]["status"], "not_assessed")
            self.assertEqual(song["mood"]["recording_level"]["confidence"], "none")
            self.assertEqual(song["mood"]["album_context"]["moods"], [])
            self.assertEqual(song["mood"]["artist_context"]["moods"], [])


    def test_albumless_source_song_does_not_create_placeholder_album(self):
        with tempfile.TemporaryDirectory() as temp:
            lib = MusicLibrary(temp)
            mbid = "b8b46357-3cb3-4ed8-bcb0-2501a164c90d"
            artist_mbid = "303abdee-ffca-4685-a582-6aaaefd81b01"
            result = lib.put_catalogue({
                "mbid:" + mbid: {
                    "track_id": "mbid:" + mbid, "track_mbid": mbid,
                    "artist_id": "mbid:" + artist_mbid,
                    "artist": "Carpenter Brut", "track": "Le Perv",
                    "lastfm_tags": [{"tag": "dark synth"}],
                }
            })
            self.assertEqual(result["songs"], 1)
            self.assertEqual(result["albums"], 0)
            found = lib.get_song(recording_mbid=mbid)
            self.assertEqual(found["song"]["identity"]["identity_quality"], "verified_recording")
            self.assertEqual(found["artist"]["identity"]["artist_mbid"], "mbid:" + artist_mbid)
            self.assertEqual(found["album"], {})
            self.assertEqual(lib.index["albums"], {})

    def test_duplicate_mbid_rows_do_not_erase_successful_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            lib = MusicLibrary(temp)
            mbid = "caab5c9c-3cfc-4ec9-9c2b-c6650f9fdc5b"
            rows = {
                "mbid:" + mbid: {
                    "track_id": "mbid:" + mbid, "track_mbid": mbid,
                    "artist_id": "mbid:aa62b28e-b6d4-4086-91d4-e5fac1ed56f3",
                    "artist": "Royal Blood", "track": "Figure It Out",
                    "lastfm_tags": [{"tag": "indie rock"}], "lastfm_status": "matched",
                },
                "track:duplicate": {
                    "track_id": "track:duplicate", "track_mbid": mbid,
                    "artist": "Royal Blood", "track": "Figure It Out",
                    "lastfm_tags": [], "lastfm_status": "no_tags",
                },
            }
            result = lib.put_catalogue(rows)
            self.assertEqual(result["songs"], 1)
            found = lib.get_song(recording_mbid=mbid)["song"]
            self.assertEqual(found["evidence"]["track_metadata"]["lastfm_tags"][0]["tag"], "indie rock")
            self.assertEqual(found["sources"]["lastfm_status"]["status"], "matched")
            self.assertEqual(result["artists"], 1)

    def test_unknown_release_source_ids_keep_same_title_versions_distinct(self):
        with tempfile.TemporaryDirectory() as temp:
            lib = MusicLibrary(temp)
            rows = {
                "track:version-one": {"track_id": "track:version-one", "artist": "Artist", "track": "Song"},
                "track:version-two": {"track_id": "track:version-two", "artist": "Artist", "track": "Song"},
            }
            result = lib.put_catalogue(rows)
            self.assertEqual(result["songs"], 2)
            self.assertEqual(result["ambiguous_name_aliases"], 1)
            self.assertIsNone(lib.get_song(artist="Artist", track="Song"))


    def test_recent_batch_selection_is_bounded_and_preserves_listening_context(self):
        profiles = {
            "mbid:recording-one": {
                "track_id": "mbid:recording-one", "track_mbid": "recording-one",
                "artist": "A", "track": "One", "lastfm_tags": [{"tag": "dark"}],
            },
            "mbid:recording-two": {
                "track_id": "mbid:recording-two", "track_mbid": "recording-two",
                "artist": "B", "track": "Two",
            },
        }
        recent = [
            {"track_id": "mbid:recording-one", "track_mbid": "recording-one", "recent_plays": 9, "all_time_plays": 20},
            {"track_id": "mbid:recording-one", "track_mbid": "recording-one", "recent_plays": 8, "all_time_plays": 20},
            {"track_id": "mbid:recording-two", "track_mbid": "recording-two", "recent_plays": 7, "all_time_plays": 10},
        ]
        selected, report = select_recent_track_rows(profiles, recent, 2)
        self.assertEqual(len(selected), 2)
        self.assertEqual(report["selected"], 2)
        self.assertEqual(report["duplicates"], 1)
        first = selected["mbid:recording-one"]
        self.assertEqual(first["listening_context"]["recent_plays"], 9)
        self.assertEqual(first["lastfm_tags"][0]["tag"], "dark")


    def test_catalogue_refresh_preserves_unseen_existing_records_and_mood(self):
        with tempfile.TemporaryDirectory() as temp:
            lib = MusicLibrary(temp)
            lib.put_catalogue({
                "old": {"track_id": "track:old", "artist": "Old Artist", "track": "Old Song",
                        "lastfm_tags": [{"tag": "nocturnal"}]},
                "refresh": {"track_id": "track:refresh", "artist": "Artist", "track": "Song"},
            })
            old_key = next(key for key in lib.index["songs"] if key.startswith("source:old"))
            old_path = Path(temp) / lib.index["songs"][old_key]["path"]
            old_record = json.loads(old_path.read_text())
            old_record["mood"]["status"] = "assessed"
            old_record["mood"]["recording_level"] = {
                "moods": ["nocturnal"], "confidence": "high",
                "evidence_refs": ["lastfm:recording-tag"], "method": "curated",
            }
            old_record["listening_context"] = {"all_time_plays": 42}
            old_path.write_text(json.dumps(old_record))

            lib.put_catalogue({
                "new": {"track_id": "track:new", "artist": "New Artist", "track": "New Song"},
            })
            lib = MusicLibrary(temp)
            self.assertEqual(len(lib.index["songs"]), 3)
            preserved = lib.get_song(source_track_id="track:old")["song"]
            self.assertEqual(preserved["mood"]["status"], "assessed")
            self.assertEqual(preserved["mood"]["recording_level"]["moods"], ["nocturnal"])
            self.assertEqual(preserved["listening_context"]["all_time_plays"], 42)
            self.assertIn("lastfm_tags", preserved["evidence"]["track_metadata"])
            self.assertTrue(lib.audit()["ok"], lib.audit()["errors"])

    def test_catalogue_refresh_merges_new_evidence_without_erasing_existing_mood(self):
        with tempfile.TemporaryDirectory() as temp:
            lib = MusicLibrary(temp)
            lib.put_catalogue({
                "r": {"track_id": "track:r", "artist": "Artist", "track": "Song",
                      "lastfm_tags": [{"tag": "dark"}]},
            })
            key = next(iter(lib.index["songs"]))
            path = Path(temp) / lib.index["songs"][key]["path"]
            record = json.loads(path.read_text())
            record["mood"]["recording_level"] = {
                "moods": ["ominous"], "confidence": "medium",
                "evidence_refs": ["manual:review"], "method": "manual",
            }
            path.write_text(json.dumps(record))
            lib.put_catalogue({
                "r": {"track_id": "track:r", "artist": "Artist", "track": "Song",
                      "musicbrainz_tags": [{"tag": "industrial"}]},
            })
            refreshed = MusicLibrary(temp).get_song(source_track_id="track:r")["song"]
            self.assertEqual(refreshed["mood"]["recording_level"]["moods"], ["ominous"])
            tags = refreshed["evidence"]["track_metadata"]
            self.assertEqual(tags["lastfm_tags"][0]["tag"], "dark")
            self.assertEqual(tags["musicbrainz_tags"][0]["tag"], "industrial")

    def test_library_audit_accepts_consistent_song_artist_relations(self):
        with tempfile.TemporaryDirectory() as temp:
            lib = MusicLibrary(temp)
            lib.put_catalogue({
                "mbid:recording": {
                    "track_id": "mbid:recording", "track_mbid": "recording",
                    "artist_id": "mbid:artist", "artist": "Artist", "track": "Song",
                }
            })
            report = lib.audit()
            self.assertTrue(report["ok"], report["errors"])
            self.assertEqual(report["songs"], 1)
            self.assertEqual(report["artists"], 1)
            self.assertEqual(report["albums"], 0)

if __name__ == "__main__": unittest.main()

# FILE OVERVIEW
# - Covers lazy ID resolution, release collisions, evidence separation, and on-disk song layout.
