import json
import tempfile
import unittest
from pathlib import Path

from scripts.music.library_maintenance import maintain, plan_maintenance
from tests.test_library_health import write_record


class LibraryMaintenanceTests(unittest.TestCase):
    def build_library(self, root):
        artist_id, song_id = "artist-id", "song-id"
        artist_path = write_record(root, "artists", artist_id, "artist.json", {
            "schema_version": 1, "id": artist_id, "artist": "Artist", "album_ids": [],
        })
        song_path = write_record(root, "songs", song_id, "song.json", {
            "schema_version": 1, "id": song_id,
            "identity": {
                "artist": "Artist", "title": "Song", "artist_id": artist_id,
                "spotify_id": "spotify:track:abcdefghijklmnopqrstuv",
            },
            "relations": {"artist_path": artist_path},
        })
        index = {
            "schema_version": 1,
            "songs": {song_id: {"path": song_path}},
            "artists": {artist_id: {"path": artist_path}},
            "albums": {},
            "spotify_ids": {"abcdefghijklmnopqrstuv": song_id},
            "recording_mbids": {}, "isrcs": {}, "source_track_ids": {},
            "name_candidates": {"artist\u0000song": [song_id]},
        }
        (root / "library_index.json").write_text(json.dumps(index), encoding="utf-8")

    def test_preview_is_read_only_and_detects_unindexed_record(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "library"
            root.mkdir()
            self.build_library(root)
            extra_id = "song-extra"
            artist_path = next(root.glob("artists/**/artist.json")).relative_to(root).as_posix()
            write_record(root, "songs", extra_id, "song.json", {
                "schema_version": 1, "id": extra_id,
                "identity": {"artist": "Artist", "title": "Extra", "artist_id": "artist-id"},
                "relations": {"artist_path": artist_path},
            })
            before = (root / "library_index.json").read_bytes()
            report = plan_maintenance(root)
            after = (root / "library_index.json").read_bytes()
            self.assertTrue(report["safe_to_rebuild"], report)
            self.assertTrue(report["repair_needed"])
            self.assertEqual(report["proposed_counts"]["songs"], 2)
            self.assertEqual(before, after)
            self.assertFalse(list(base.glob("library.backup-maintenance-*")))

    def test_apply_requires_explicit_repair_and_creates_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.build_library(root)
            artist_path = next(root.glob("artists/**/artist.json")).relative_to(root).as_posix()
            write_record(root, "songs", "song-extra", "song.json", {
                "schema_version": 1, "id": "song-extra",
                "identity": {"artist": "Artist", "title": "Extra", "artist_id": "artist-id"},
                "relations": {"artist_path": artist_path},
            })
            preview = maintain(root, apply=True, repair_index=False)
            self.assertIn("requires explicit", preview["error"])
            result = maintain(root, apply=True, repair_index=True)
            self.assertTrue(result["changed"], result)
            self.assertTrue(result["post_repair_health_ok"])
            self.assertTrue(Path(result["backup_path"]).is_file())
            self.assertEqual(result["post_repair_counts"]["songs"], 2)

    def test_rebuild_refuses_to_drop_existing_aliases(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.build_library(root)
            index_path = root / "library_index.json"
            index = json.loads(index_path.read_text(encoding="utf-8"))
            index["spotify_ids"]["unreconstructable"] = "song-id"
            index_path.write_text(json.dumps(index), encoding="utf-8")
            report = plan_maintenance(root)
            self.assertFalse(report["safe_to_rebuild"])
            self.assertIn("spotify_ids", report["aliases_or_records_that_would_be_lost"])
            result = maintain(root, apply=True, repair_index=True)
            self.assertFalse(result["changed"])
            self.assertIn("refused", result["error"])


if __name__ == "__main__":
    unittest.main()


# FILE OVERVIEW
# Purpose: Fixture tests for preview-only and backup-protected Library index maintenance.
# Scope: No-write preview, explicit apply, backup creation, health verification and alias-loss refusal.
# Run: python -m unittest tests.test_library_maintenance -v
