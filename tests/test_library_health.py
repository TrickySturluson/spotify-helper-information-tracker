import json
import tempfile
import unittest
from pathlib import Path

from scripts.music.library_health import inspect_library, _safe_id


def write_record(root, kind, record_id, filename, payload):
    safe = _safe_id(record_id)
    path = root / kind / safe[:2] / safe / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path.relative_to(root).as_posix()


class LibraryHealthTests(unittest.TestCase):
    def build_valid_library(self, root):
        artist_id = "artist-id"
        song_id = "song-id"
        artist_path = write_record(root, "artists", artist_id, "artist.json", {
            "schema_version": 1, "id": artist_id, "artist": "Artist", "album_ids": [],
        })
        song_path = write_record(root, "songs", song_id, "song.json", {
            "schema_version": 1, "id": song_id,
            "identity": {"artist": "Artist", "title": "Song", "artist_id": artist_id},
            "relations": {"artist_path": artist_path},
        })
        index = {
            "schema_version": 1,
            "songs": {song_id: {"path": song_path}},
            "artists": {artist_id: {"path": artist_path}},
            "albums": {},
            "spotify_ids": {"abc": song_id},
            "recording_mbids": {}, "isrcs": {}, "source_track_ids": {},
            "name_candidates": {"artist\u0000song": [song_id]},
        }
        (root / "library_index.json").write_text(json.dumps(index), encoding="utf-8")

    def test_valid_library_passes_and_checker_does_not_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.build_valid_library(root)
            before = {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in root.rglob("*") if path.is_file()
            }
            report = inspect_library(root)
            after = {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in root.rglob("*") if path.is_file()
            }
            self.assertTrue(report["ok"], report["errors"])
            self.assertEqual(report["counts"], {"songs": 1, "artists": 1, "albums": 0})
            self.assertEqual(before, after)

    def test_missing_alias_target_and_dangling_relation_are_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.build_valid_library(root)
            index_path = root / "library_index.json"
            index = json.loads(index_path.read_text(encoding="utf-8"))
            index["spotify_ids"]["dangling"] = "missing-song"
            index_path.write_text(json.dumps(index), encoding="utf-8")
            song_entry = index["songs"]["song-id"]
            song_path = root / song_entry["path"]
            song = json.loads(song_path.read_text(encoding="utf-8"))
            song["relations"]["artist_path"] = "artists/missing/artist.json"
            song_path.write_text(json.dumps(song), encoding="utf-8")
            report = inspect_library(root)
            self.assertFalse(report["ok"])
            self.assertTrue(any("alias references missing song" in error for error in report["errors"]))
            self.assertTrue(any("related artist record is missing" in error for error in report["errors"]))

    def test_invalid_json_and_unindexed_record_are_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.build_valid_library(root)
            extra = root / "songs" / "zz" / "orphan" / "song.json"
            extra.parent.mkdir(parents=True)
            extra.write_text("{not-json", encoding="utf-8")
            report = inspect_library(root)
            self.assertFalse(report["ok"])
            self.assertTrue(any("unreadable" in error for error in report["errors"]))

    def test_index_path_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.build_valid_library(root)
            index_path = root / "library_index.json"
            index = json.loads(index_path.read_text(encoding="utf-8"))
            index["songs"]["song-id"]["path"] = "../../outside/song.json"
            index_path.write_text(json.dumps(index), encoding="utf-8")
            report = inspect_library(root)
            self.assertFalse(report["ok"])
            self.assertTrue(any("escapes Library root" in error for error in report["errors"]))


if __name__ == "__main__":
    unittest.main()


# FILE OVERVIEW
# Purpose: Fixture tests for the read-only canonical Library health checker.
# Scope: Valid structures, no-write behavior, dangling aliases/relations, malformed JSON and path traversal.
# Run: python -m unittest tests.test_library_health -v
