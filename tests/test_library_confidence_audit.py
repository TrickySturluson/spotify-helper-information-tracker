import json
import tempfile
import unittest
from pathlib import Path

from scripts.music.library_confidence_audit import inspect_confidence
from scripts.music.music_evidence import identity_confidence, track_metadata_confidence


def write_song(root, song_id, identity_quality, metadata=None, stored_identity=None, stored_metadata=None):
    safe = song_id.replace(":", "-")
    path = root / "songs" / safe[:2] / safe / "song.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    metadata = metadata or {}
    payload = {
        "id": song_id,
        "identity": {"identity_quality": identity_quality},
        "evidence": {"track_metadata": metadata, "audio": {}, "lyrics": None},
        "mood": {"recording_level": {"confidence": "none"}},
        "confidence": {
            "identity": stored_identity or identity_confidence(
                "musicbrainz_recording_mbid" if song_id.startswith("mbid:") else
                "source_track_id" if song_id.startswith("source:") else
                "fallback_identity",
                {"identity_quality": identity_quality},
            ),
            "metadata": stored_metadata if stored_metadata is not None else track_metadata_confidence(metadata),
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


class LibraryConfidenceAuditTests(unittest.TestCase):
    def test_confidence_audit_recomputes_tiers_and_legacy_coverage_without_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "library"
            music = Path(directory) / "music"
            (music / "indexes").mkdir(parents=True)
            write_song(root, "mbid:recording-1", "verified_recording", {
                "duration_ms": 2000, "duration_source": "lastfm",
                "lastfm_tags": [{"tag": "shoegaze"}],
            })
            write_song(root, "source:track-1", "source_track_id")
            write_song(root, "fallback:track-2", "fallback_artist_title")
            (root / "library_index.json").write_text(json.dumps({
                "artists": {"artist-1": {"name": "Artist"}},
                "recording_mbids": {"recording-1": "mbid:recording-1"},
                "source_track_ids": {"track:track-1": "source:track-1"},
                "name_candidates": {"ambiguous": ["source:track-1", "fallback:track-2"]},
            }), encoding="utf-8")
            (music / "indexes" / "tracks.json").write_text(json.dumps({
                "mbid:recording-1": {}, "track:track-1": {},
            }), encoding="utf-8")
            (music / "indexes" / "artists.json").write_text(json.dumps({
                "artist-1": {"artist": "Artist"},
            }), encoding="utf-8")
            before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
            report = inspect_confidence(root, music)
            after = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
            self.assertTrue(report["ok"])
            self.assertEqual(report["songs_scanned"], 3)
            self.assertEqual(report["identity_confidence_drift_count"], 0)
            self.assertEqual(report["legacy_source_coverage"]["track_index_resolved"], 2)
            self.assertEqual(report["legacy_source_coverage"]["artist_index_represented"], 1)
            self.assertEqual(report["ambiguous_name_aliases"], 1)
            self.assertEqual(report["field_coverage"]["duration"], 1)
            self.assertEqual(before, after)

    def test_missing_confidence_is_separated_from_incorrect_stored_confidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "library"
            music = Path(directory) / "music"
            (music / "indexes").mkdir(parents=True)
            metadata = {"duration_ms": 1800, "duration_source": "lastfm"}
            write_song(root, "source:missing", "source_track_id", metadata, stored_metadata={})
            write_song(root, "source:mismatch", "source_track_id", metadata,
                       stored_metadata={"duration": {"confidence": "high"}})
            (root / "library_index.json").write_text(json.dumps({
                "artists": {}, "name_candidates": {},
            }), encoding="utf-8")
            (music / "indexes" / "tracks.json").write_text("{}", encoding="utf-8")
            (music / "indexes" / "artists.json").write_text("{}", encoding="utf-8")
            report = inspect_confidence(root, music)
            self.assertEqual(report["metadata_confidence_drift_count"], 2)
            self.assertEqual(report["metadata_confidence_missing_count"], 1)
            self.assertEqual(report["metadata_confidence_missing_by_field"], {"duration": 1})
            self.assertEqual(report["metadata_confidence_mismatch_count"], 1)
            self.assertEqual(report["metadata_confidence_mismatch_by_field"], {"duration": 1})

    def test_confidence_drift_is_reported_not_rewritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "library"
            music = Path(directory) / "music"
            (music / "indexes").mkdir(parents=True)
            bad_metadata = {"duration_ms": 1800, "duration_source": "lastfm"}
            write_song(
                root, "fallback:wrong", "fallback_artist_title", bad_metadata,
                stored_identity="high",
                stored_metadata={"duration": {"confidence": "high"}},
            )
            (root / "library_index.json").write_text(json.dumps({"artists": {}, "name_candidates": {}}), encoding="utf-8")
            (music / "indexes" / "tracks.json").write_text("{}", encoding="utf-8")
            (music / "indexes" / "artists.json").write_text("{}", encoding="utf-8")
            path = next((root / "songs").rglob("song.json"))
            before = path.read_bytes()
            report = inspect_confidence(root, music)
            self.assertEqual(report["identity_confidence_drift_count"], 1)
            self.assertEqual(report["metadata_confidence_drift_count"], 1)
            self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()


# FILE OVERVIEW
# Purpose: Fixture tests for read-only identity and metadata confidence auditing.
# Scope: Confidence recomputation, source-index coverage, ambiguity, drift reporting, and no-write behavior.
# Run: python -m unittest tests.test_library_confidence_audit -v
