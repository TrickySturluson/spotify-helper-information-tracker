"""Regression tests for owner-confirmed Tricky Daily production-stage recovery."""

import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "spotify"))
import spotify_daily_cycle as daily_cycle
import daily_stage_recovery


class DailyStageRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.stage_dir = root / "assistant_data" / "spotify" / "staging" / "tricky_daily"
        self.backup_dir = root / "playlist_backups"
        self.github_dir = root / ".github"
        self.stage_dir.mkdir(parents=True)
        self.backup_dir.mkdir(parents=True)
        self.github_dir.mkdir(parents=True)
        self.state_path = self.github_dir / "state.json"
        self.audit_path = self.github_dir / "audit.jsonl"

        self._patchers = [
            patch.object(daily_cycle, "DAILY_STAGE_DIR", self.stage_dir),
            patch.object(daily_cycle.manager, "BACKUPS", self.backup_dir),
            patch.object(daily_cycle.manager, "CONFIG", self.state_path),
            patch.object(daily_cycle.manager, "AUDIT", self.audit_path),
        ]
        for patcher in self._patchers:
            patcher.start()
            self.addCleanup(patcher.stop)

        self.before_uri = "spotify:track:before"
        self.before_items = [{
            "uri": self.before_uri,
            "name": "Before Track",
            "artists": ["Before Artist"],
            "album": "Before Album",
        }]
        self.target_uris = [f"spotify:track:target-{index}" for index in range(60)]
        self.target_items = [
            {
                "uri": uri,
                "name": f"Target Track {index}",
                "artists": [f"Target Artist {index}"],
                "album": "Target Album",
            }
            for index, uri in enumerate(self.target_uris)
        ]
        self.stage_path = self.stage_dir / "2026-11-21-run-1.json"
        self.backup_path = self.backup_dir / "before.json"
        self.backup = {
            "created_at": "2026-11-21T11:59:00Z",
            "playlist": {
                "id": daily_cycle.DAILY_ID,
                "name": "Tricky Daily",
                "description": "Old Daily description",
                "snapshot_id": "before-snapshot",
            },
            "items": self.before_items,
        }
        self.stage = {
            "schema_version": 1,
            "playlist_id": daily_cycle.DAILY_ID,
            "playlist_name": "Tricky Daily",
            "cycle_date_eastern": "2026-11-21",
            "run_id": "run-1",
            "created_at": "2026-11-21T11:59:01Z",
            "prewrite_snapshot_id": "before-snapshot",
            "prewrite_uris": [self.before_uri],
            "target_uris": list(self.target_uris),
            "candidate_tracks": [
                {"artist": f"Target Artist {index}", "track": f"Target Track {index}", "uri": uri}
                for index, uri in enumerate(self.target_uris)
            ],
            "target_description": "New Daily description",
            "backup_path": str(self.backup_path),
            "status": "staged_before_spotify_write",
            "stage_mode": "production",
        }
        self._write_fixture()
        self.initial_state = {
            "version": 1,
            "playlists": {},
            "pending": {"kind": "poker", "playlist_id": "unrelated-playlist"},
        }
        self._write_state(self.initial_state)

        self.before_playlist = {
            "id": daily_cycle.DAILY_ID,
            "name": "Tricky Daily",
            "owner": {"id": "owner"},
            "description": "Old Daily description",
            "snapshot_id": "before-snapshot",
            "items": {"total": 1},
        }
        self.before_snapshot = {
            "created_at": "2026-11-21T11:59:00Z",
            "playlist": {
                "id": daily_cycle.DAILY_ID,
                "name": "Tricky Daily",
                "description": "Old Daily description",
                "snapshot_id": "before-snapshot",
            },
            "items": self.before_items,
        }
        self.target_playlist = {
            "id": daily_cycle.DAILY_ID,
            "name": "Tricky Daily",
            "owner": {"id": "owner"},
            "description": "New Daily description",
            "snapshot_id": "target-snapshot",
            "items": {"total": 60},
        }
        self.target_snapshot = {
            "created_at": "2026-11-21T12:05:00Z",
            "playlist": {
                "id": daily_cycle.DAILY_ID,
                "name": "Tricky Daily",
                "description": "New Daily description",
                "snapshot_id": "target-snapshot",
            },
            "items": self.target_items,
        }

    def _write_fixture(self):
        self.backup_path.write_text(json.dumps(self.backup, indent=2) + "\n", encoding="utf-8")
        payload = dict(self.stage)
        payload.pop("payload_sha256", None)
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        self.stage["payload_sha256"] = digest
        self.stage_path.write_text(json.dumps(self.stage, indent=2) + "\n", encoding="utf-8")

    def _write_state(self, state):
        self.state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

    @property
    def stage_key(self):
        return self.stage_path.as_posix()

    def test_loader_verifies_production_stage_hash_and_exact_backup(self):
        stage, backup, path = daily_stage_recovery.load_verified_daily_stage(
            daily_cycle, str(self.stage_path)
        )
        self.assertEqual(path, self.stage_path)
        self.assertEqual(stage["payload_sha256"], self.stage["payload_sha256"])
        self.assertEqual(backup["items"], self.before_items)

    def test_loader_rejects_hash_mutation(self):
        payload = json.loads(self.stage_path.read_text(encoding="utf-8"))
        payload["target_description"] = "Tampered"
        self.stage_path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(daily_cycle.manager.ManagerError, "hash"):
            daily_stage_recovery.load_verified_daily_stage(daily_cycle, str(self.stage_path))

    def test_loader_rejects_backup_that_does_not_match_prewrite_order(self):
        backup = json.loads(self.backup_path.read_text(encoding="utf-8"))
        backup["items"][0]["uri"] = "spotify:track:someone-else"
        self.backup_path.write_text(json.dumps(backup), encoding="utf-8")
        with self.assertRaisesRegex(daily_cycle.manager.ManagerError, "ordered URIs"):
            daily_stage_recovery.load_verified_daily_stage(daily_cycle, str(self.stage_path))

    def test_loader_rejects_test_only_stage_and_path_traversal(self):
        payload = json.loads(self.stage_path.read_text(encoding="utf-8"))
        payload["stage_mode"] = "test_only"
        self.stage_path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(daily_cycle.manager.ManagerError, "production stage"):
            daily_stage_recovery.load_verified_daily_stage(daily_cycle, str(self.stage_path))
        with self.assertRaisesRegex(daily_cycle.manager.ManagerError, "path is invalid"):
            daily_stage_recovery.load_verified_daily_stage(daily_cycle, "../outside.json")

    def test_live_state_classification_accepts_only_exact_known_states(self):
        stage, backup, _ = daily_stage_recovery.load_verified_daily_stage(
            daily_cycle, str(self.stage_path)
        )
        self.assertEqual(
            daily_stage_recovery.classify_live_state(
                daily_cycle, self.before_playlist, self.before_snapshot, stage, backup
            ),
            "prewrite",
        )
        self.assertEqual(
            daily_stage_recovery.classify_live_state(
                daily_cycle, self.target_playlist, self.target_snapshot, stage, backup
            ),
            "target",
        )
        partial = dict(self.target_snapshot)
        partial["items"] = self.target_items[:-1]
        partial_playlist = dict(self.target_playlist)
        partial_playlist["items"] = {"total": 59}
        with self.assertRaisesRegex(daily_cycle.manager.ManagerError, "neither the exact"):
            daily_stage_recovery.classify_live_state(
                daily_cycle, partial_playlist, partial, stage, backup
            )
        conflict = dict(self.before_playlist)
        conflict["description"] = "User changed this"
        with self.assertRaisesRegex(daily_cycle.manager.ManagerError, "neither the exact"):
            daily_stage_recovery.classify_live_state(
                daily_cycle, conflict, self.before_snapshot, stage, backup
            )

    def test_unresolved_stage_blocks_and_resolved_stage_requires_matching_hash(self):
        with self.assertRaisesRegex(daily_cycle.manager.ManagerError, "Automatic retry is blocked"):
            daily_cycle.assert_no_pending_daily_stage("2026-11-21", self.initial_state)

        resolved = {
            "daily_recovery": {
                self.stage_key: {
                    "status": "completed",
                    "payload_sha256": self.stage["payload_sha256"],
                }
            }
        }
        daily_cycle.assert_no_pending_daily_stage("2026-11-21", resolved)

        resolved["daily_recovery"][self.stage_key]["payload_sha256"] = "0" * 64
        with self.assertRaisesRegex(daily_cycle.manager.ManagerError, "Automatic retry is blocked"):
            daily_cycle.assert_no_pending_daily_stage("2026-11-21", resolved)

    def test_completed_stage_is_rejected_before_spotify_read(self):
        self._write_state({
            **self.initial_state,
            "daily_cycle": {
                "last_cycle_date_eastern": "2026-11-21",
                "status": "completed",
                "stage_path": self.stage_key,
            },
            "last_completed": {"kind": "daily", "stage_path": self.stage_key},
        })
        spotify = Mock()
        with self.assertRaisesRegex(daily_cycle.manager.ManagerError, "already has a terminal"):
            daily_stage_recovery.run_daily_stage_recovery(
                daily_cycle, spotify, self.stage_key, "resume", "owner"
            )
        spotify.call.assert_not_called()

    def test_discard_requires_exact_prewrite_and_preserves_unrelated_pending_state(self):
        spotify = Mock()
        spotify.call.return_value = self.before_playlist
        with patch.object(daily_cycle.manager, "assert_managed"), \
             patch.object(daily_cycle.manager, "snapshot", return_value=self.before_snapshot), \
             patch.object(daily_cycle, "set_action_output"), \
             patch.object(daily_cycle.manager, "unlocked") as unlocked, \
             patch.object(daily_cycle.cloud, "replace_playlist") as replace, \
             patch.object(daily_cycle.discovery, "write_daily_removal_baseline") as baseline:
            self.assertEqual(
                daily_stage_recovery.run_daily_stage_recovery(
                    daily_cycle, spotify, self.stage_key, "discard", "owner"
                ),
                0,
            )
        spotify.call.assert_called_once_with("GET", f"/playlists/{daily_cycle.DAILY_ID}")
        unlocked.assert_not_called()
        replace.assert_not_called()
        baseline.assert_not_called()
        state = daily_cycle.manager.config()
        self.assertEqual(state["pending"], self.initial_state["pending"])
        self.assertEqual(state["daily_cycle"]["status"], "recovery_discarded")
        self.assertEqual(state["daily_recovery"][self.stage_key]["status"], "discarded")
        daily_cycle.assert_no_pending_daily_stage("2026-11-21", state)

    def test_resume_when_target_is_already_live_does_not_repeat_playlist_write(self):
        spotify = Mock()
        spotify.call.return_value = self.target_playlist
        with patch.object(daily_cycle.manager, "assert_managed"), \
             patch.object(daily_cycle.manager, "snapshot", return_value=self.target_snapshot), \
             patch.object(daily_cycle, "capture_and_persist_after_snapshot", return_value=(
                 self.target_playlist, self.target_snapshot, "playlist_backups/after.json"
             )) as capture, \
             patch.object(daily_cycle.discovery, "load_playlist_feedback", return_value={}), \
             patch.object(daily_cycle.discovery, "is_playlist_candidate_blocked", return_value=False), \
             patch.object(daily_cycle.discovery, "write_daily_removal_baseline") as baseline, \
             patch.object(daily_cycle.manager, "unlocked") as unlocked, \
             patch.object(daily_cycle, "set_action_output"), \
             patch.object(daily_cycle.manager, "audit"), \
             patch.object(daily_cycle.cloud, "replace_playlist") as replace, \
             patch.object(daily_cycle, "update_description_and_capture_after_snapshot") as update_description:
            self.assertEqual(
                daily_stage_recovery.run_daily_stage_recovery(
                    daily_cycle, spotify, self.stage_key, "resume", "owner"
                ),
                0,
            )
        replace.assert_not_called()
        update_description.assert_not_called()
        unlocked.assert_not_called()
        capture.assert_called_once()
        baseline.assert_called_once()
        state = daily_cycle.manager.config()
        self.assertEqual(state["daily_cycle"]["status"], "completed")
        self.assertEqual(state["daily_recovery"][self.stage_key]["status"], "completed")

    def test_resume_rechecks_current_blacklist_before_any_write_or_state_change(self):
        spotify = Mock()
        spotify.call.return_value = self.before_playlist
        with patch.object(daily_cycle.manager, "assert_managed"), \
             patch.object(daily_cycle.manager, "snapshot", return_value=self.before_snapshot), \
             patch.object(daily_cycle.discovery, "load_playlist_feedback", return_value={}), \
             patch.object(daily_cycle.discovery, "is_playlist_candidate_blocked", return_value=True), \
             patch.object(daily_cycle, "set_action_output") as output, \
             patch.object(daily_cycle.cloud, "replace_playlist") as replace:
            with self.assertRaisesRegex(daily_cycle.manager.ManagerError, "blacklisted tracks"):
                daily_stage_recovery.run_daily_stage_recovery(
                    daily_cycle, spotify, self.stage_key, "resume", "owner"
                )
        replace.assert_not_called()
        output.assert_not_called()
        self.assertNotIn("daily_recovery", daily_cycle.manager.config())

    def test_rollback_rechecks_backup_blacklist_before_any_write_or_state_change(self):
        spotify = Mock()
        spotify.call.return_value = self.target_playlist
        with patch.object(daily_cycle.manager, "assert_managed"), \
             patch.object(daily_cycle.manager, "snapshot", return_value=self.target_snapshot), \
             patch.object(daily_cycle.discovery, "load_playlist_feedback", return_value={}), \
             patch.object(daily_cycle.discovery, "is_playlist_candidate_blocked", return_value=True), \
             patch.object(daily_cycle, "set_action_output") as output, \
             patch.object(daily_cycle.cloud, "replace_playlist") as replace:
            with self.assertRaisesRegex(daily_cycle.manager.ManagerError, "blacklisted tracks"):
                daily_stage_recovery.run_daily_stage_recovery(
                    daily_cycle, spotify, self.stage_key, "rollback", "owner"
                )
        replace.assert_not_called()
        output.assert_not_called()
        self.assertNotIn("daily_recovery", daily_cycle.manager.config())

    def test_track_recovery_commits_before_snapshot_before_write_and_captures_after(self):
        stage, _backup, _path = daily_stage_recovery.load_verified_daily_stage(
            daily_cycle, str(self.stage_path)
        )
        events = []
        with patch.object(daily_cycle.manager, "save_snapshot", return_value="playlist_backups/before-recovery.json"), \
             patch.object(daily_cycle.manager, "audit"), \
             patch.object(daily_cycle, "persist_daily_snapshot", side_effect=lambda *args: events.append("before_commit") or "commit"), \
             patch.object(daily_cycle, "assert_repository_head_unchanged"), \
             patch.object(daily_cycle, "assert_live_snapshot_unchanged", return_value=(self.before_playlist, self.before_snapshot)), \
             patch.object(daily_cycle.discovery, "load_playlist_feedback", return_value={}), \
             patch.object(daily_cycle.discovery, "is_playlist_candidate_blocked", return_value=False), \
             patch.object(daily_cycle.manager, "unlocked", return_value=True), \
             patch.object(daily_cycle.cloud, "replace_playlist", side_effect=lambda *args, **kwargs: events.append("write")), \
             patch.object(daily_cycle, "capture_and_persist_after_snapshot", side_effect=lambda *args: (
                 events.append("after_capture") or (self.target_playlist, self.target_snapshot, "playlist_backups/after-recovery.json")
             )):
            result = daily_stage_recovery._replace_tracks(
                daily_cycle, Mock(), self.before_snapshot, self.target_uris,
                stage["candidate_tracks"], self.stage_key, stage, "resume", "owner"
            )
        self.assertEqual(events, ["before_commit", "write", "after_capture"])
        self.assertEqual(result[2], "playlist_backups/before-recovery.json")
        self.assertEqual(result[3], "playlist_backups/after-recovery.json")

    def test_recovery_cli_is_manual_owner_only_and_broker_only(self):
        argv = [
            "spotify_daily_cycle.py",
            "--recover-stage", self.stage_key,
            "--recovery-action", "discard",
            "--recovery-confirmation", daily_stage_recovery.DAILY_RECOVERY_CONFIRMATION,
        ]
        with patch.object(daily_cycle.sys, "argv", argv), \
             patch.dict(os.environ, {
                 "GITHUB_EVENT_NAME": "workflow_dispatch",
                 "GITHUB_ACTOR": "not-the-owner",
                 "GITHUB_REPOSITORY": "TrickySturluson/spotify-helper-information-tracker",
                 "SHIT_AUTH_MODE": "broker",
             }, clear=True), \
             patch.object(daily_cycle, "configure") as configure:
            with self.assertRaisesRegex(daily_cycle.manager.ManagerError, "repository owner"):
                daily_cycle.main()
        configure.assert_not_called()

        with patch.object(daily_cycle.sys, "argv", argv), \
             patch.dict(os.environ, {
                 "GITHUB_EVENT_NAME": "workflow_dispatch",
                 "GITHUB_ACTOR": "TrickySturluson",
                 "GITHUB_REPOSITORY": "TrickySturluson/spotify-helper-information-tracker",
                 "SHIT_AUTH_MODE": "legacy",
             }, clear=True), \
             patch.object(daily_cycle, "configure") as configure:
            with self.assertRaisesRegex(daily_cycle.manager.ManagerError, "central SHIT auth broker"):
                daily_cycle.main()
        configure.assert_not_called()

    def test_workflow_recovery_requires_owner_confirmation_and_persists_state(self):
        workflow = (
            ROOT / ".github" / "workflows" / "spotify-daily-midnight-cycle.yml"
        ).read_text(encoding="utf-8")
        self.assertIn('options: ["none", "resume", "rollback", "discard"]', workflow)
        self.assertIn('test "$GITHUB_ACTOR" = "TrickySturluson"', workflow)
        self.assertIn('test "$RECOVERY_CONFIRMATION" = "RECOVER TRICKY DAILY"', workflow)
        self.assertIn("--recover-stage", workflow)
        self.assertIn("steps.daily-cycle.outputs.recovery_started == 'true'", workflow)
        self.assertIn("github.event_name == 'workflow_dispatch' && inputs.recovery_action != 'none'", workflow)


# FILE OVERVIEW
# Purpose: Regression-test Tricky Daily production-stage recovery.
# Scope: Mocked Spotify reads/writes and temporary stage/backup/state files; no live provider calls.
# Coverage: Committed stage/hash/backup integrity, exact live-state classification, owner/broker gates,
#           blacklist checks, safe discard, idempotent resume, snapshot ordering, and state isolation.
# Run: python -m unittest tests.test_spotify_daily_stage_recovery -v
# Related: scripts/spotify/daily_stage_recovery.py, scripts/spotify/spotify_daily_cycle.py,
#          .github/workflows/spotify-daily-midnight-cycle.yml, docs/TRICKY_DAILY_CYCLE.md.


if __name__ == "__main__":
    unittest.main()
