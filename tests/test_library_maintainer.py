import json
import tempfile
import unittest
from pathlib import Path

from scripts.music.library_maintainer import apply_maintenance, main, plan_maintenance


def add_song(root, song_id, metadata, context=None, playlist_sources=None, confidence=None):
    safe = song_id.replace(":", "-")
    path = root / "songs" / safe[:2] / safe / "song.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "id": song_id,
        "identity": {"identity_quality": "verified_recording"},
        "evidence": {"track_metadata": metadata},
        "confidence": confidence or {"identity": "high", "metadata": {}},
        "listening_context": context or {},
        "playlist_sources": playlist_sources or [],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


class LibraryMaintainerTests(unittest.TestCase):
    def test_plan_only_proposes_explicit_spotify_provenance_and_missing_confidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "library"
            path = add_song(
                root, "spotify:track:one", {"duration_ms": 210000},
                {"source": "Spotify reference-library snapshot"}, ["playlist-1"],
            )
            before = path.read_bytes()
            report = plan_maintenance(root)
            self.assertTrue(report["ok"])
            self.assertEqual(report["counts"]["safe_spotify_provenance_repairs"], 1)
            self.assertEqual(report["counts"]["missing_duration_confidence"], 1)
            self.assertEqual(report["action_count"], 2)
            self.assertEqual(path.read_bytes(), before)

    def test_plan_fills_lastfm_confidence_but_does_not_guess_unknown_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "library"
            add_song(root, "mbid:lastfm", {
                "duration_ms": 200000, "duration_source": "lastfm_catalog",
            })
            add_song(root, "fallback:unknown", {"duration_ms": 190000})
            report = plan_maintenance(root)
            self.assertEqual(report["counts"]["missing_duration_confidence"], 1)
            self.assertEqual(report["counts"]["unresolved_duration_provenance"], 1)
            self.assertEqual(report["action_count"], 1)

    def test_existing_confidence_conflicts_are_reported_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "library"
            path = add_song(
                root, "mbid:conflict",
                {"duration_ms": 200000, "duration_source": "lastfm_catalog"},
                confidence={"identity": "high", "metadata": {
                    "duration": {"confidence": "high", "source_families": ["spotify"]}
                }},
            )
            before = path.read_bytes()
            report = plan_maintenance(root)
            self.assertEqual(report["counts"]["existing_duration_confidence_conflicts"], 1)
            self.assertEqual(report["action_count"], 0)
            self.assertEqual(path.read_bytes(), before)

    def test_apply_backups_records_and_journals_repairs_idempotently(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "library"
            music_root = Path(directory) / "music"
            spotify_path = add_song(
                root, "spotify:track:one", {"duration_ms": 210000},
                {"source": "Spotify reference-library snapshot"}, ["playlist-1"],
            )
            lastfm_path = add_song(root, "mbid:lastfm", {
                "duration_ms": 200000, "duration_source": "lastfm_catalog",
            })
            before_duration = json.loads(spotify_path.read_text())["evidence"]["track_metadata"]["duration_ms"]
            result = apply_maintenance(root, music_root)
            self.assertEqual(result["updated_records"], 2)
            self.assertEqual(result["actions_applied"], 3)
            self.assertTrue(Path(result["backup_path"]).is_dir())
            self.assertTrue(Path(result["journal_path"]).is_file())
            spotify = json.loads(spotify_path.read_text(encoding="utf-8"))
            lastfm = json.loads(lastfm_path.read_text(encoding="utf-8"))
            self.assertEqual(spotify["evidence"]["track_metadata"]["duration_ms"], before_duration)
            self.assertEqual(spotify["evidence"]["track_metadata"]["duration_source"], "spotify_reference_library_snapshot")
            self.assertEqual(spotify["evidence"]["track_metadata"]["duration_provider"], "spotify")
            self.assertEqual(spotify["confidence"]["metadata"]["duration"]["confidence"], "low")
            self.assertEqual(lastfm["confidence"]["metadata"]["duration"]["confidence"], "low")
            journal = Path(result["journal_path"]).read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(journal), 2)
            second = apply_maintenance(root, music_root)
            self.assertEqual(second["updated_records"], 0)
            self.assertEqual(second["remaining_action_count"], 0)

    def test_apply_requires_explicit_yes(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(SystemExit):
                main(["--root", str(Path(directory) / "library"), "--apply", "--json"])


if __name__ == "__main__":
    unittest.main()


# FILE OVERVIEW
# Purpose: Tests for the safe Library maintainer's plan/apply boundary.
# Scope: Explicit Spotify provenance, missing confidence, unresolved sources, conflict preservation, backups, journaling and idempotence.
# Run: python -m unittest tests.test_library_maintainer -v
