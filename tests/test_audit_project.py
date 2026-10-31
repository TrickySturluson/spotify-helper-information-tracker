import json
import tempfile
import unittest
from pathlib import Path

import audit_project


class SpotifyReferenceAuditTests(unittest.TestCase):
    def write_library(self, root, accessible=True):
        base = root / "assistant_data" / "spotify"
        (base / "playlists").mkdir(parents=True)
        (base / "playlists" / "p1.json").write_text(json.dumps({
            "id": "p1",
            "items_accessible": accessible,
            "items": [{"uri": "spotify:track:a"}] if accessible else [],
        }), encoding="utf-8")
        (base / "playlists.json").write_text(json.dumps({
            "playlist_count": 1,
            "playlists": [{
                "id": "p1", "items_accessible": accessible,
                "record_path": "assistant_data/spotify/playlists/p1.json",
            }],
        }), encoding="utf-8")
        (base / "reference_index.json").write_text(json.dumps({
            "track_playlists": {"spotify:track:a": ["p1"]} if accessible else {},
            "artist_playlists": {},
        }), encoding="utf-8")
        return base

    def test_valid_reference_library_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_library(root)
            errors, warnings = audit_project.audit_spotify_reference(root)
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])

    def test_catalog_record_summary_drift_is_an_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = self.write_library(root)
            catalog_path = base / "playlists.json"
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            catalog["playlists"][0]["item_count"] = 9
            catalog["playlists"][0]["snapshot_id"] = "newer-snapshot"
            catalog["playlists"][0]["items_accessible"] = False
            catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
            errors, _ = audit_project.audit_spotify_reference(root)
            self.assertTrue(any("fetched-item count mismatch" in error for error in errors))
            self.assertTrue(any("snapshot mismatch" in error for error in errors))
            self.assertTrue(any("accessibility mismatch" in error for error in errors))

    def test_record_fetched_count_must_match_accessible_items(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = self.write_library(root)
            record_path = base / "playlists" / "p1.json"
            record = json.loads(record_path.read_text(encoding="utf-8"))
            record["item_count_fetched"] = 2
            record_path.write_text(json.dumps(record), encoding="utf-8")
            errors, _ = audit_project.audit_spotify_reference(root)
            self.assertTrue(any("item_count_fetched does not match its items list" in error for error in errors))

    def test_inaccessible_items_are_warning_not_empty_library_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_library(root, accessible=False)
            errors, warnings = audit_project.audit_spotify_reference(root)
            self.assertEqual(errors, [])
            self.assertTrue(any("inaccessible" in warning for warning in warnings))

    def test_dangling_index_playlist_id_is_an_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = self.write_library(root)
            (base / "reference_index.json").write_text(json.dumps({
                "track_playlists": {"spotify:track:a": ["missing-playlist"]},
                "artist_playlists": {},
            }), encoding="utf-8")
            errors, _ = audit_project.audit_spotify_reference(root)
            self.assertTrue(any("unknown playlist ID" in error for error in errors))

    def test_duplicate_playlist_reference_in_index_is_an_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = self.write_library(root)
            (base / "reference_index.json").write_text(json.dumps({
                "track_playlists": {"spotify:track:a": ["p1", "p1"]},
                "artist_playlists": {},
            }), encoding="utf-8")
            errors, _ = audit_project.audit_spotify_reference(root)
            self.assertTrue(any("duplicate playlist references" in error for error in errors))

    def test_malformed_index_reference_list_is_an_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = self.write_library(root)
            (base / "reference_index.json").write_text(json.dumps({
                "track_playlists": {"spotify:track:a": "p1"},
                "artist_playlists": {},
            }), encoding="utf-8")
            errors, _ = audit_project.audit_spotify_reference(root)
            self.assertTrue(any("malformed playlist-reference list" in error for error in errors))

    def test_missing_catalog_is_reported_as_not_synced_yet(self):
        with tempfile.TemporaryDirectory() as directory:
            errors, warnings = audit_project.audit_spotify_reference(Path(directory))
            self.assertEqual(errors, [])
            self.assertTrue(any("not been synced yet" in warning for warning in warnings))


if __name__ == "__main__":
    unittest.main()
