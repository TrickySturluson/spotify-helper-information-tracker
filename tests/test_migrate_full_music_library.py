import json
import tempfile
import unittest
from pathlib import Path

from scripts.music.migrate_full_music_library import legacy_archive_coverage


class MigrationCoverageTests(unittest.TestCase):
    def test_legacy_track_ids_and_artist_names_are_checked_against_canonical_index(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "indexes").mkdir()
            (root / "indexes" / "tracks.json").write_text(json.dumps({
                "mbid:recording-1": {},
                "track:source-1": {},
                "track:missing": {},
            }), encoding="utf-8")
            (root / "indexes" / "artists.json").write_text(json.dumps({
                "artist-id-1": {"artist": "Artist One"},
                "artist-id-2": {"artist": "Artist Two"},
                "artist-id-3": {"artist": "Not Present"},
            }), encoding="utf-8")
            index = {
                "songs": {"song-mbid": {}, "song-source": {}},
                "recording_mbids": {"recording-1": "song-mbid"},
                "source_track_ids": {"track:source-1": "song-source"},
                "artists": {
                    "artist-id-1": {"name": "Artist One"},
                    "different-id": {"name": "Artist Two"},
                },
            }
            report = legacy_archive_coverage(root, index)
            self.assertEqual(report["source_track_index_total"], 3)
            self.assertEqual(report["source_track_index_resolved"], 2)
            self.assertEqual(report["source_track_index_unresolved"], 1)
            self.assertEqual(report["track_resolution_methods"], {
                "source_track_id": 1, "recording_mbid": 1,
            })
            self.assertEqual(report["source_artist_index_total"], 3)
            self.assertEqual(report["source_artist_index_represented"], 2)
            self.assertEqual(report["source_artist_index_unrepresented"], 1)
            self.assertEqual(report["unrepresented_artist_examples"][0]["id"], "artist-id-3")


if __name__ == "__main__":
    unittest.main()


# FILE OVERVIEW
# Purpose: Regression tests for legacy-to-canonical source-index coverage reporting.
# Scope: MBID aliases, source-track aliases, artist ID/name equivalence, and unresolved examples.
# Run: python -m unittest tests.test_migrate_full_music_library -v
