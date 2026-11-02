import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import subprocess

from scripts.music.backfill_duration_observations import build_plan, apply_plan


class DurationObservationBackfillTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.library = self.root / "library"
        self.music = self.root / "music"
        self.song_id = "mbid:14c4ff34-27e4-491d-8c65-c1773a1bea46"
        self.song_rel = Path("songs/mb/test/song.json")
        self.song_path = self.library / self.song_rel
        self.song_path.parent.mkdir(parents=True, exist_ok=True)
        self.library.mkdir(parents=True, exist_ok=True)
        self.music.joinpath("artists").mkdir(parents=True, exist_ok=True)
        self.song = {
            "id": self.song_id,
            "identity": {"artist": "At the Gates", "title": "Slaughter of the Soul",
                         "source_track_id": self.song_id},
            "evidence": {"track_metadata": {
                "duration_ms": 183000,
                "duration_source": "Last.fm track.getInfo",
            }},
        }
        self.write_json(self.song_path, self.song)
        self.write_json(self.library / "library_index.json", {
            "songs": {self.song_id: {"path": str(self.song_rel)}},
            "source_track_ids": {self.song_id.casefold(): self.song_id},
            "recording_mbids": {},
        })
        self.legacy_track = {
            "track_id": self.song_id,
            "track_mbid": self.song_id.removeprefix("mbid:"),
            "duration_ms": 183000,
            "duration_source": "Last.fm track.getInfo",
            "metadata_checked_at": 1793324246,
            "metadata_status": "matched",
            "retry_after": 0,
            "confidence": "low",
            "match_type": "recording_mbid",
        }
        self.write_legacy([self.legacy_track])

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def write_json(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2), encoding="utf-8")

    def write_legacy(self, tracks):
        self.write_json(self.music / "artists" / "shard-00.json", {
            "artists": {
                "at-the-gates": {
                    "artist": "At the Gates",
                    "tracks": {str(i): row for i, row in enumerate(tracks)},
                }
            }
        })

    def plan(self):
        return build_plan(self.library, self.music)

    def test_exact_id_duration_source_and_timestamp_are_planned(self):
        report, changes = self.plan()
        self.assertTrue(report["safe_to_apply"])
        self.assertEqual(report["counts"]["candidate_observations"], 1)
        self.assertEqual(report["songs_to_update"], 1)
        updated = next(iter(changes.values()))
        observation = updated["evidence"]["track_metadata"]["duration_observations"][0]
        self.assertEqual(observation["provider"], "lastfm")
        self.assertEqual(observation["duration_ms"], 183000)
        self.assertEqual(observation["status"], "matched")
        self.assertTrue(observation["checked_at"].startswith("2026-10-30T"))
        self.assertEqual(observation["provenance"], "legacy_music_metadata_shard")

    def test_preview_does_not_write_or_create_backup(self):
        before = self.song_path.read_text(encoding="utf-8")
        report, changes = self.plan()
        self.assertEqual(self.song_path.read_text(encoding="utf-8"), before)
        self.assertEqual(list(self.music.glob("library.backup-duration-observations-*")), [])
        self.assertEqual(report["writes"], 0)
        self.assertEqual(report["provider_requests"], 0)
        self.assertTrue(changes)

    def test_duration_mismatch_is_skipped_without_overwriting(self):
        self.song["evidence"]["track_metadata"]["duration_ms"] = 184000
        self.write_json(self.song_path, self.song)
        report, changes = self.plan()
        self.assertEqual(report["counts"]["duration_mismatch"], 1)
        self.assertEqual(report["songs_to_update"], 0)
        self.assertFalse(changes)

    def test_source_mismatch_is_skipped(self):
        self.song["evidence"]["track_metadata"]["duration_source"] = "Spotify catalog"
        self.write_json(self.song_path, self.song)
        report, changes = self.plan()
        self.assertEqual(report["counts"]["source_mismatch"], 1)
        self.assertFalse(changes)

    def test_non_matched_legacy_status_is_not_used_as_successful_value_evidence(self):
        self.legacy_track["metadata_status"] = "not_found"
        self.write_legacy([self.legacy_track])
        report, changes = self.plan()
        self.assertEqual(report["counts"]["not_matched_status"], 1)
        self.assertFalse(changes)

    def test_existing_newer_matching_observation_is_preserved(self):
        self.song["evidence"]["track_metadata"]["duration_observations"] = [{
            "provider": "lastfm",
            "checked_at": "2026-10-31T00:00:00+00:00",
            "status": "matched",
            "duration_ms": 183000,
            "source": "Last.fm track.getInfo",
        }]
        self.write_json(self.song_path, self.song)
        report, changes = self.plan()
        self.assertEqual(report["counts"]["already_present"], 1)
        self.assertFalse(changes)

    def test_newer_observation_for_different_value_does_not_hide_matching_legacy_evidence(self):
        self.song["evidence"]["track_metadata"]["duration_observations"] = [{
            "provider": "lastfm",
            "checked_at": "2026-10-31T00:00:00+00:00",
            "status": "matched",
            "duration_ms": 184000,
            "source": "Last.fm track.getInfo",
        }]
        self.write_json(self.song_path, self.song)
        report, changes = self.plan()
        self.assertEqual(report["counts"]["candidate_observations"], 1)
        self.assertTrue(changes)

    def test_conflicting_duplicate_legacy_ids_fail_closed(self):
        second = dict(self.legacy_track, duration_ms=184000)
        self.write_legacy([self.legacy_track, second])
        report, changes = self.plan()
        self.assertEqual(report["counts"]["duplicate_legacy_rows"], 1)
        self.assertFalse(report["safe_to_apply"])

    def test_malformed_timestamp_is_skipped(self):
        self.legacy_track["metadata_checked_at"] = "not-an-epoch"
        self.write_legacy([self.legacy_track])
        report, changes = self.plan()
        self.assertEqual(report["counts"]["invalid_timestamp"], 1)
        self.assertFalse(changes)

    def test_apply_creates_backup_and_appends_observation(self):
        report, changes = self.plan()
        result = apply_plan(changes, self.library, self.music, health_check=False)
        updated = json.loads(self.song_path.read_text(encoding="utf-8"))
        self.assertEqual(len(updated["evidence"]["track_metadata"]["duration_observations"]), 1)
        self.assertEqual(result["changed_files"], 1)
        backup = Path(result["backup_root"])
        self.assertTrue((backup / self.song_rel).is_file())
        self.assertTrue((backup / "manifest.json").is_file())

    def test_post_write_health_failure_rolls_back(self):
        report, changes = self.plan()
        before = self.song_path.read_text(encoding="utf-8")
        failed = subprocess.CompletedProcess(args=["health"], returncode=2, stdout='{"ok": false}', stderr="failed")
        with patch("scripts.music.backfill_duration_observations.subprocess.run", return_value=failed):
            with self.assertRaises(RuntimeError):
                apply_plan(changes, self.library, self.music, health_check=True)
        self.assertEqual(self.song_path.read_text(encoding="utf-8"), before)


if __name__ == "__main__":
    unittest.main()


# FILE OVERVIEW
# Purpose: Regression tests for exact, non-destructive duration provenance backfill.
# Coverage: ID matching, value/source checks, timestamp validity, duplicate rows,
#           existing observations, preview no-write, backup, and rollback.
# Run: python -m unittest tests.test_backfill_duration_observations -v
