import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch
from pathlib import Path

import audit_project


class SpotifyReferenceAuditTests(unittest.TestCase):
    def write_library(self, root, accessible=True):
        base = root / "assistant_data" / "spotify"
        (base / "playlists").mkdir(parents=True)
        (base / "playlists" / "p1.json").write_text(json.dumps({
            "id": "p1",
            "snapshot_id": "snapshot-p1",
            "items_accessible": accessible,
            "item_count_fetched": 1 if accessible else 0,
            "items": [{"uri": "spotify:track:a"}] if accessible else [],
        }), encoding="utf-8")
        (base / "playlists.json").write_text(json.dumps({
            "playlist_count": 1,
            "playlists": [{
                "id": "p1", "items_accessible": accessible,
                "snapshot_id": "snapshot-p1", "item_count": 1 if accessible else 0,
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

    def test_malformed_item_record_is_an_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = self.write_library(root)
            record_path = base / "playlists" / "p1.json"
            record = json.loads(record_path.read_text(encoding="utf-8"))
            record["items"].append("not-an-item-object")
            record["item_count_fetched"] = 2
            record_path.write_text(json.dumps(record), encoding="utf-8")
            errors, _ = audit_project.audit_spotify_reference(root)
            self.assertTrue(any("malformed item record" in error for error in errors))

    def test_non_numeric_fetched_count_is_an_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = self.write_library(root)
            record_path = base / "playlists" / "p1.json"
            record = json.loads(record_path.read_text(encoding="utf-8"))
            record["item_count_fetched"] = "1"
            record_path.write_text(json.dumps(record), encoding="utf-8")
            errors, _ = audit_project.audit_spotify_reference(root)
            self.assertTrue(any("invalid item_count_fetched" in error for error in errors))

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

    def test_index_membership_must_match_saved_playlist_records(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = self.write_library(root)
            index_path = base / "reference_index.json"
            index_path.write_text(json.dumps({
                "track_playlists": {"spotify:track:wrong": ["p1"]},
                "artist_playlists": {},
            }), encoding="utf-8")
            errors, _ = audit_project.audit_spotify_reference(root)
            self.assertTrue(any("track_playlists disagrees with saved playlist records" in error for error in errors))

    def test_index_detects_missing_artist_membership(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = self.write_library(root)
            record_path = base / "playlists" / "p1.json"
            record = json.loads(record_path.read_text(encoding="utf-8"))
            record["items"][0]["artists"] = ["Example Artist"]
            record_path.write_text(json.dumps(record), encoding="utf-8")
            errors, _ = audit_project.audit_spotify_reference(root)
            self.assertTrue(any("artist_playlists disagrees with saved playlist records" in error for error in errors))

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

    def test_unhashable_playlist_id_is_reported_without_crashing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = self.write_library(root)
            catalog_path = base / "playlists.json"
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            catalog["playlists"][0]["id"] = {"malformed": "id"}
            catalog["playlists"][0]["record_path"] = "assistant_data/spotify/playlists/p1.json"
            catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
            errors, _ = audit_project.audit_spotify_reference(root)
            self.assertTrue(any("malformed playlist records" in error for error in errors))
            self.assertTrue(any("identity mismatch" in error for error in errors))

    def test_missing_catalog_is_reported_as_not_synced_yet(self):
        with tempfile.TemporaryDirectory() as directory:
            errors, warnings = audit_project.audit_spotify_reference(Path(directory))
            self.assertEqual(errors, [])
            self.assertTrue(any("not been synced yet" in warning for warning in warnings))



class ProjectAuditMainTests(unittest.TestCase):
    def write_minimal_project(self, root):
        files = {
            "data/metadata.json": {"total_scrobbles": 0},
            "assistant_data/manifest.json": {},
            "assistant_data/advanced/manifest.json": {},
            "assistant_data/music/manifest.json": {},
            "assistant_data/recommendations/manifest.json": {},
            "assistant_data/playback/manifest.json": {"source_exists": True, "recorded_intervals": 0},
            "assistant_data/music/overview.json": {"unique_tracks": 0, "tracks_with_duration": 0},
            "assistant_data/music/track_profiles.json": {},
        }
        for relative, payload in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload), encoding="utf-8")

    def test_malformed_top_level_json_objects_report_errors_without_crashing(self):
        targets = (
            ("data/metadata.json", ["not", "an", "object"]),
            ("assistant_data/music/overview.json", ["not", "an", "object"]),
            ("assistant_data/music/track_profiles.json", ["not", "an", "object"]),
            ("assistant_data/playback/manifest.json", ["not", "an", "object"]),
        )
        for relative, malformed in targets:
            with self.subTest(path=relative), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.write_minimal_project(root)
                (root / relative).write_text(json.dumps(malformed), encoding="utf-8")
                output = io.StringIO()
                with patch.object(audit_project, "ROOT", root), redirect_stdout(output):
                    result = audit_project.main()
                self.assertEqual(result, 1)
                self.assertIn("must contain a JSON object", output.getvalue())

    def test_boolean_values_are_not_accepted_as_numeric_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_minimal_project(root)
            metadata = root / "data/metadata.json"
            metadata.write_text(json.dumps({"total_scrobbles": True}), encoding="utf-8")
            overview = root / "assistant_data/music/overview.json"
            overview.write_text(json.dumps({"unique_tracks": True, "tracks_with_duration": 0}), encoding="utf-8")
            output = io.StringIO()
            with patch.object(audit_project, "ROOT", root), redirect_stdout(output):
                result = audit_project.main()
            self.assertEqual(result, 1)
            self.assertIn("ERROR: Canonical scrobble count is valid.", output.getvalue())
            self.assertIn("ERROR: Music duration coverage counts are valid.", output.getvalue())

    def test_main_clears_previous_results_between_runs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_minimal_project(root)
            with patch.object(audit_project, "ROOT", root), redirect_stdout(io.StringIO()):
                first = audit_project.main()
                second = audit_project.main()
            self.assertEqual(first, 0)
            self.assertEqual(second, 0)


if __name__ == "__main__":
    unittest.main()

# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Regression tests for the cross-project generated-data integrity audit.
# Coverage: Spotify reference catalog/index consistency, malformed records,
#           manifest/count validation, and repeatable audit execution.
# Run: python -m unittest tests.test_audit_project -v (from the repository root).
# Related: scripts/analytics/audit_project.py and compat/audit_project.py.
# -----------------------------------------------------------------------------
