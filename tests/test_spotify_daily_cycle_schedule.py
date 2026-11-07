"""Regression tests for Tricky Daily scheduled-run timing and outputs."""
import os
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "spotify"))
import spotify_daily_cycle as daily_cycle

EASTERN = ZoneInfo("America/New_York")


class DailyCycleScheduleTests(unittest.TestCase):
    def test_delayed_scheduled_run_catches_up_during_same_eastern_day(self):
        delayed = datetime(2026, 11, 5, 6, 47, tzinfo=EASTERN)
        self.assertTrue(daily_cycle.should_run_cycle(delayed, event_name="schedule"))

    def test_scheduled_run_catches_up_after_one_am(self):
        delayed = datetime(2026, 11, 5, 1, 5, tzinfo=EASTERN)
        self.assertTrue(daily_cycle.should_run_cycle(delayed, event_name="schedule"))

    def test_scheduled_run_can_catch_up_late_in_same_eastern_day(self):
        delayed = datetime(2026, 11, 5, 22, 45, tzinfo=EASTERN)
        self.assertTrue(daily_cycle.should_run_cycle(delayed, event_name="schedule"))

    def test_standard_time_early_cron_before_midnight_is_ignored(self):
        early_cron = datetime(2026, 11, 4, 23, 0, tzinfo=EASTERN)
        self.assertFalse(daily_cycle.should_run_cycle(early_cron, event_name="schedule"))

    def test_late_standard_time_cron_occurrence_is_also_ignored(self):
        late_early_cron = datetime(2026, 11, 4, 23, 59, tzinfo=EASTERN)
        self.assertFalse(daily_cycle.should_run_cycle(late_early_cron, event_name="schedule"))

    def test_manual_dispatch_remains_midnight_gated_without_force(self):
        daytime = datetime(2026, 11, 5, 6, 47, tzinfo=EASTERN)
        self.assertFalse(daily_cycle.should_run_cycle(daytime, event_name="workflow_dispatch"))

    def test_manual_dispatch_can_run_in_midnight_window(self):
        midnight = datetime(2026, 11, 5, 0, 10, tzinfo=EASTERN)
        self.assertTrue(daily_cycle.should_run_cycle(midnight, event_name="workflow_dispatch"))

    def test_force_overrides_time_and_event_gate(self):
        daytime = datetime(2026, 11, 5, 14, 0, tzinfo=EASTERN)
        self.assertTrue(daily_cycle.should_run_cycle(daytime, force=True, event_name="workflow_dispatch"))

    def test_cycle_date_guard_skips_already_completed_eastern_date(self):
        config = {"daily_cycle": {"last_cycle_date_eastern": "2026-11-05"}}
        self.assertTrue(daily_cycle.cycle_already_completed(config, "2026-11-05"))
        self.assertFalse(daily_cycle.cycle_already_completed(config, "2026-11-06"))
        self.assertTrue(daily_cycle.cycle_already_completed(config, "2026-11-05"))
        source = (ROOT / "scripts" / "spotify" / "spotify_daily_cycle.py").read_text(encoding="utf-8")
        self.assertGreaterEqual(source.count("cycle_already_completed(config, cycle_date)"), 2)

    def test_duplicate_forced_dispatch_exits_before_spotify_api(self):
        class FrozenDateTime:
            @staticmethod
            def now(tz):
                return datetime(2026, 11, 5, 14, 0, tzinfo=tz)

        completed = {"daily_cycle": {"last_cycle_date_eastern": "2026-11-05"}}
        with patch.object(daily_cycle, "datetime", FrozenDateTime), \
             patch.object(daily_cycle, "configure"), \
             patch.object(daily_cycle.manager, "config", return_value=completed), \
             patch.object(daily_cycle.manager, "Spotify") as spotify, \
             patch.object(daily_cycle, "set_action_output"), \
             patch.dict(os.environ, {"GITHUB_EVENT_NAME": "workflow_dispatch"}), \
             patch.object(sys, "argv", ["spotify_daily_cycle.py", "--force"]):
            self.assertEqual(daily_cycle.main(), 0)
        spotify.assert_not_called()

    def test_verify_only_runs_after_same_day_cycle_without_any_playlist_mutation(self):
        class FrozenDateTime:
            @staticmethod
            def now(tz):
                return datetime(2026, 11, 6, 14, 0, tzinfo=tz)

        completed = {
            "daily_cycle": {
                "last_cycle_date_eastern": "2026-11-06",
                "description": "Current Daily description",
            }
        }
        playlist = {
            "id": daily_cycle.DAILY_ID,
            "name": "Tricky Daily",
            "owner": {"id": "owner"},
            "description": "Current Daily description",
            "snapshot_id": "snapshot-60",
        }
        items = [
            {"uri": f"spotify:track:{i:022d}", "name": f"Track {i}", "artists": [f"Artist {i}"]}
            for i in range(60)
        ]
        spotify = __import__("unittest").mock.Mock()
        spotify.me.return_value = {"id": "owner"}
        spotify.call.return_value = playlist
        with patch.object(daily_cycle, "datetime", FrozenDateTime), \
             patch.object(daily_cycle, "configure"), \
             patch.object(daily_cycle.manager, "config", return_value=completed), \
             patch.object(daily_cycle.manager, "check_spotify_cooldown"), \
             patch.object(daily_cycle.manager, "Spotify", return_value=spotify), \
             patch.object(daily_cycle.manager, "assert_managed"), \
             patch.object(daily_cycle.manager, "unlocked", return_value=True), \
             patch.object(daily_cycle.manager, "snapshot", return_value={"items": items}), \
             patch.object(daily_cycle.discovery, "load_playlist_feedback", return_value={"negative_keys": set(), "negative_uris": set()}), \
             patch.object(daily_cycle, "set_action_output"), \
             patch.dict(os.environ, {"GITHUB_EVENT_NAME": "workflow_dispatch"}), \
             patch.object(sys, "argv", ["spotify_daily_cycle.py", "--force", "--verify-only"]):
            self.assertEqual(daily_cycle.main(), 0)
        spotify.call.assert_called_once_with("GET", f"/playlists/{daily_cycle.DAILY_ID}")
        self.assertEqual(spotify.method_calls, [unittest.mock.call.me(), unittest.mock.call.call("GET", f"/playlists/{daily_cycle.DAILY_ID}")])

    def test_cycle_date_guard_rejects_malformed_state(self):
        with self.assertRaises(daily_cycle.manager.ManagerError):
            daily_cycle.cycle_already_completed({"daily_cycle": []}, "2026-11-05")

    def test_duplicate_schedule_delivery_exits_before_spotify_api(self):
        class FrozenDateTime:
            @staticmethod
            def now(tz):
                return datetime(2026, 11, 5, 6, 47, tzinfo=tz)

        completed = {"daily_cycle": {"last_cycle_date_eastern": "2026-11-05"}}
        with patch.object(daily_cycle, "datetime", FrozenDateTime), \
             patch.object(daily_cycle, "configure"), \
             patch.object(daily_cycle.manager, "config", return_value=completed), \
             patch.object(daily_cycle.manager, "Spotify") as spotify, \
             patch.object(daily_cycle, "set_action_output"), \
             patch.dict(os.environ, {"GITHUB_EVENT_NAME": "schedule"}), \
             patch.object(sys, "argv", ["spotify_daily_cycle.py"]):
            self.assertEqual(daily_cycle.main(), 0)
        spotify.assert_not_called()


    def test_daily_verifies_sixty_tracks_after_spotify_readback_without_artist_ceiling(self):
        source = (ROOT / "scripts" / "spotify" / "spotify_daily_cycle.py").read_text(encoding="utf-8")
        self.assertIn('verified_items = updated_snapshot["items"]', source)
        self.assertIn("validate_daily_post_write(", source)
        self.assertIn("actual_uris != expected_uris", source)
        self.assertIn("len(set(actual_uris)) != len(actual_uris)", source)
        self.assertIn("is_playlist_candidate_blocked", source)
        self.assertNotIn("count > 2 for count in verified_artist_counts.values()", source)
        self.assertIn('event="daily_post_change_validation_failed"', source)


    def test_prewrite_guard_aborts_if_live_daily_changed_during_discovery(self):
        from unittest.mock import Mock
        before = {
            "playlist": {"id": daily_cycle.DAILY_ID, "name": "Tricky Daily", "description": "Daily line", "snapshot_id": "before"},
            "items": [{"uri": "spotify:track:before"}],
        }
        live = {
            "id": daily_cycle.DAILY_ID, "name": "Tricky Daily", "owner": {"id": "owner"},
            "description": "Daily line", "snapshot_id": "after", "tracks": {"total": 1},
        }
        sp = Mock()
        sp.call.return_value = live
        with patch.object(daily_cycle.manager, 'unlocked', return_value=True), patch.object(
            daily_cycle.manager, 'snapshot',
            return_value={"playlist": live, "items": [{"uri": "spotify:track:changed"}]},
        ), patch.object(daily_cycle.manager, 'audit'):
            with self.assertRaisesRegex(daily_cycle.manager.ManagerError, "changed after candidate generation"):
                daily_cycle.assert_live_snapshot_unchanged(sp, before, "owner")
        sp.call.assert_called_once_with("GET", f"/playlists/{daily_cycle.DAILY_ID}")

    def test_prewrite_guard_aborts_if_description_changed_during_discovery(self):
        from unittest.mock import Mock
        before = {
            "playlist": {
                "id": daily_cycle.DAILY_ID, "name": "Tricky Daily",
                "description": "Original line", "snapshot_id": "same",
            },
            "items": [{"uri": "spotify:track:a"}],
        }
        live = {
            "id": daily_cycle.DAILY_ID, "name": "Tricky Daily",
            "description": "User edited line", "owner": {"id": "owner"},
            "snapshot_id": "same", "tracks": {"total": 1},
        }
        sp = Mock()
        sp.call.return_value = live
        with patch.object(daily_cycle.manager, "unlocked", return_value=True):
            with self.assertRaisesRegex(daily_cycle.manager.ManagerError, "changed Daily description"):
                daily_cycle.assert_live_snapshot_unchanged(sp, before, "owner")
        sp.call.assert_called_once_with("GET", f"/playlists/{daily_cycle.DAILY_ID}")


    def test_prewrite_guard_accepts_only_complete_unchanged_snapshot(self):
        from unittest.mock import Mock
        before = {
            "playlist": {"id": daily_cycle.DAILY_ID, "name": "Tricky Daily", "description": "Daily line", "snapshot_id": "same"},
            "items": [{"uri": "spotify:track:a"}],
        }
        live = {
            "id": daily_cycle.DAILY_ID, "name": "Tricky Daily", "owner": {"id": "owner"},
            "description": "Daily line", "snapshot_id": "same", "tracks": {"total": 1},
        }
        live_snapshot = {"playlist": live, "items": [{"uri": "spotify:track:a"}]}
        sp = Mock()
        sp.call.return_value = live
        with patch.object(daily_cycle.manager, 'unlocked', return_value=True), patch.object(
            daily_cycle.manager, 'snapshot', return_value=live_snapshot
        ):
            result, snapshot = daily_cycle.assert_live_snapshot_unchanged(sp, before, "owner")
        self.assertIs(result, live)
        self.assertIs(snapshot, live_snapshot)

    def test_postwrite_guard_rejects_order_mismatch_and_blacklist(self):
        uris = ["spotify:track:" + str(i) for i in range(daily_cycle.DAILY_TARGET_SIZE)]
        items = [{"uri": uri, "name": "Track " + str(i), "artists": ["Artist " + str(i)]} for i, uri in enumerate(uris)]
        updated = {"tracks": {"total": daily_cycle.DAILY_TARGET_SIZE}}
        snapshot = {"items": items}
        with patch.object(daily_cycle.discovery, 'is_playlist_candidate_blocked', return_value=False):
            self.assertEqual(
                len(daily_cycle.validate_daily_post_write(updated, snapshot, uris, {})),
                daily_cycle.DAILY_TARGET_SIZE,
            )
            reordered = dict(snapshot)
            reordered['items'] = [items[1], items[0], *items[2:]]
            with self.assertRaisesRegex(daily_cycle.manager.ManagerError, "ordered URI"):
                daily_cycle.validate_daily_post_write(updated, reordered, uris, {})
        with patch.object(daily_cycle.discovery, 'is_playlist_candidate_blocked', return_value=True):
            with self.assertRaisesRegex(daily_cycle.manager.ManagerError, "blacklisted tracks"):
                daily_cycle.validate_daily_post_write(updated, snapshot, uris, {})
    def test_stage_only_mode_returns_before_any_spotify_write(self):
        source = (ROOT / "scripts" / "spotify" / "spotify_daily_cycle.py").read_text(encoding="utf-8")
        stage_only_at = source.index("if args.stage_only:")
        write_at = source.index("cloud.replace_playlist(sp, DAILY_ID, uris, expected_before_uris=before_uris)")
        self.assertLess(stage_only_at, write_at)
        self.assertIn('set_action_output("cycled", "false")', source[stage_only_at:write_at])
        self.assertIn("args.stage_only", source[source.index("def create_daily_stage("):write_at])

    def test_test_only_stage_uses_separate_nonblocking_subdirectory(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        uris = ["spotify:track:" + str(i) for i in range(daily_cycle.DAILY_TARGET_SIZE)]
        recommendations = [{"artist": "Artist", "track": "Track", "uri": uri} for uri in uris]
        before = {"playlist": {"snapshot_id": "before"}, "items": []}
        with TemporaryDirectory() as directory, patch.object(
            daily_cycle, "DAILY_STAGE_DIR", Path(directory) / "stage"
        ), patch.object(daily_cycle.manager, "stamp", return_value="2026-11-06T18:00:00Z"), patch.object(
            daily_cycle.manager, "audit"
        ), patch.object(daily_cycle, "persist_daily_stage", return_value=False), patch.dict(
            os.environ, {"GITHUB_ACTIONS": "false", "GITHUB_RUN_ID": "stage-test-2"}
        ):
            stage_path, _, _ = daily_cycle.create_daily_stage(
                "2026-11-06", before, [], recommendations, uris,
                "playlist_backups/before.json", "Stage-only", test_mode=True
            )
            self.assertEqual(Path(stage_path).parent.name, "tests")
            daily_cycle.assert_no_pending_daily_stage("2026-11-06")
    def test_pending_durable_stage_blocks_same_date_retry(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        with TemporaryDirectory() as directory, patch.object(
            daily_cycle, "DAILY_STAGE_DIR", Path(directory)
        ):
            (Path(directory) / "2026-11-06-run-123.json").write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(daily_cycle.manager.ManagerError, "Automatic retry is blocked"):
                daily_cycle.assert_no_pending_daily_stage("2026-11-06")

    def test_no_pending_stage_is_a_noop_for_new_cycle_date(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        with TemporaryDirectory() as directory, patch.object(
            daily_cycle, "DAILY_STAGE_DIR", Path(directory)
        ):
            daily_cycle.assert_no_pending_daily_stage("2026-11-06")
    def test_daily_stage_preserves_exact_order_hash_and_prewrite_snapshot(self):
        import hashlib
        import json
        from tempfile import TemporaryDirectory
        from pathlib import Path
        uris = ["spotify:track:" + str(i) for i in range(daily_cycle.DAILY_TARGET_SIZE)]
        recommendations = [{"artist": "Artist " + str(i), "track": "Track " + str(i), "uri": uri} for i, uri in enumerate(uris)]
        before = {"playlist": {"snapshot_id": "before"}, "items": [{"uri": "spotify:track:old"}]}
        with TemporaryDirectory() as directory, patch.object(
            daily_cycle, "DAILY_STAGE_DIR", Path(directory) / "stage"
        ), patch.object(daily_cycle.manager, "stamp", return_value="2026-11-06T18:00:00Z"), patch.object(
            daily_cycle.manager, "audit"
        ), patch.object(daily_cycle, "persist_daily_stage", return_value=False), patch.dict(
            os.environ, {"GITHUB_ACTIONS": "false", "GITHUB_RUN_ID": "stage-test-1"}
        ):
            stage_path, digest, stage_commit_sha = daily_cycle.create_daily_stage(
                "2026-11-06", before, ["spotify:track:old"], recommendations,
                uris, "playlist_backups/before.json", "Today's detour starts here."
            )
            record = json.loads(Path(stage_path).read_text(encoding="utf-8"))
        self.assertEqual(record["target_uris"], uris)
        self.assertEqual(record["prewrite_uris"], ["spotify:track:old"])
        self.assertEqual(record["prewrite_snapshot_id"], "before")
        self.assertEqual(record["status"], "staged_before_spotify_write")
        self.assertEqual(record["payload_sha256"], digest)
        self.assertEqual(len(digest), 64)
        self.assertFalse(stage_commit_sha)

    def test_daily_stage_verification_rejects_mutated_payload(self):
        import hashlib
        import json
        from tempfile import TemporaryDirectory
        from pathlib import Path
        target = ["spotify:track:a", "spotify:track:b"]
        candidate_tracks = [
            {"artist": "A", "track": "One", "uri": target[0]},
            {"artist": "B", "track": "Two", "uri": target[1]},
        ]
        record = {
            "schema_version": 1,
            "playlist_id": daily_cycle.DAILY_ID,
            "playlist_name": "Tricky Daily",
            "cycle_date_eastern": "2026-11-06",
            "run_id": "test",
            "created_at": "2026-11-06T18:00:00Z",
            "prewrite_snapshot_id": "before",
            "prewrite_uris": ["spotify:track:before"],
            "target_uris": list(target),
            "candidate_tracks": candidate_tracks,
            "target_description": "Daily stage test",
            "backup_path": "playlist_backups/before.json",
            "status": "staged_before_spotify_write",
        }
        digest = hashlib.sha256(
            json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        record["payload_sha256"] = digest
        record["target_uris"][0] = "spotify:track:tampered"
        with TemporaryDirectory() as directory:
            stage_path = Path(directory) / "stage.json"
            daily_cycle.manager.write(stage_path, record)
            with patch.dict(os.environ, {"GITHUB_ACTIONS": "false"}):
                with self.assertRaisesRegex(daily_cycle.manager.ManagerError, "failed exact hash/order"):
                    daily_cycle.verify_daily_stage(
                        str(stage_path), digest, target, ["spotify:track:before"], "before"
                    )

    def test_repository_head_guard_accepts_unchanged_stage_commit(self):
        from unittest.mock import Mock
        results = [Mock(), Mock(stdout="abc123\n"), Mock(stdout="abc123\n")]
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}), patch.object(
            daily_cycle.subprocess, "run", side_effect=results
        ):
            daily_cycle.assert_repository_head_unchanged("abc123")

    def test_repository_head_guard_rejects_concurrent_main_commit(self):
        from unittest.mock import Mock
        results = [Mock(), Mock(stdout="abc123\n"), Mock(stdout="def456\n")]
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}), patch.object(
            daily_cycle.subprocess, "run", side_effect=results
        ):
            with self.assertRaisesRegex(daily_cycle.manager.ManagerError, "Repository main changed"):
                daily_cycle.assert_repository_head_unchanged("abc123")
    def test_persisted_stage_returns_commit_sha_after_successful_push(self):
        from unittest.mock import Mock
        import subprocess
        from tempfile import TemporaryDirectory
        from pathlib import Path
        with TemporaryDirectory() as directory:
            stage = Path(directory) / "stage.json"
            backup = Path(directory) / "backup.json"
            stage.write_text("{}", encoding="utf-8")
            backup.write_text("{}", encoding="utf-8")
            results = [Mock(), Mock(), Mock(), Mock(), Mock(), Mock(), Mock(stdout="abc123\n")]
            with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}), patch.object(
                daily_cycle.subprocess, "run", side_effect=results
            ):
                commit_sha = daily_cycle.persist_daily_stage(stage, backup, "2026-11-06")
        self.assertEqual(commit_sha, "abc123")

    def test_verify_daily_stage_reads_committed_git_version_in_actions(self):
        import hashlib
        import json
        from unittest.mock import Mock
        record = {
            "schema_version": 1,
            "playlist_id": daily_cycle.DAILY_ID,
            "cycle_date_eastern": "2026-11-06",
            "target_uris": ["spotify:track:a"],
            "candidate_tracks": [{"artist": "A", "track": "One", "uri": "spotify:track:a"}],
            "target_description": "Daily stage test",
            "prewrite_uris": ["spotify:track:before"],
            "prewrite_snapshot_id": "before",
            "backup_path": "playlist_backups/before.json",
            "status": "staged_before_spotify_write",
        }
        digest = hashlib.sha256(
            json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        record["payload_sha256"] = digest
        result = Mock(stdout=json.dumps(record))
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}), patch.object(
            daily_cycle.subprocess, "run", return_value=result
        ) as run:
            staged = daily_cycle.verify_daily_stage(
                "assistant_data/spotify/staging/tricky_daily/test.json",
                digest,
                ["spotify:track:a"],
                ["spotify:track:before"],
                "before",
            )
        self.assertEqual(staged["payload_sha256"], digest)
        run.assert_called_once_with(
            ["git", "show", "HEAD:assistant_data/spotify/staging/tricky_daily/test.json"],
            check=True, capture_output=True, text=True,
        )

    def test_github_daily_stage_requires_successful_git_push_before_write(self):
        import subprocess
        from tempfile import TemporaryDirectory
        from pathlib import Path
        with TemporaryDirectory() as directory:
            stage = Path(directory) / "stage.json"
            backup = Path(directory) / "backup.json"
            stage.write_text("{}", encoding="utf-8")
            backup.write_text("{}", encoding="utf-8")
            calls = [None, None, None, None, None, subprocess.CalledProcessError(1, ["git", "push"])]
            with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}), patch.object(
                daily_cycle.subprocess, "run", side_effect=calls
            ) as run:
                with self.assertRaises(subprocess.CalledProcessError):
                    daily_cycle.persist_daily_stage(stage, backup, "2026-11-06")
            commands = [call.args[0] for call in run.call_args_list]
            add_index = next(i for i, command in enumerate(commands) if command[:2] == ["git", "add"])
            commit_index = next(i for i, command in enumerate(commands) if command[:2] == ["git", "commit"])
            push_index = next(i for i, command in enumerate(commands) if command[:2] == ["git", "push"])
            self.assertLess(add_index, commit_index)
            self.assertLess(commit_index, push_index)

    def test_daily_stage_is_created_and_committed_before_playlist_replace(self):
        source = (ROOT / "scripts" / "spotify" / "spotify_daily_cycle.py").read_text(encoding="utf-8")
        prepare_at = source.index("stage_path, payload_sha256, stage_commit_sha = create_daily_stage(")
        replace_at = source.index("cloud.replace_playlist(sp, DAILY_ID, uris, expected_before_uris=before_uris)")
        stage_function = source[source.index("def create_daily_stage("):source.index("def assert_live_snapshot_unchanged(")]
        self.assertLess(prepare_at, replace_at)
        self.assertIn("persist_daily_stage(stage_path, backup, cycle_date)", stage_function)
        self.assertIn('subprocess.run(["git", "push", "origin", "HEAD:main"], check=True)', source)
    def test_daily_requires_sixty_tracks_and_valid_primary_artists(self):
        self.assertEqual(daily_cycle.DAILY_TARGET_SIZE, 60)
        self.assertEqual(daily_cycle.MINIMUM_RECOMMENDATIONS, 60)
        source = (ROOT / "scripts" / "spotify" / "spotify_daily_cycle.py").read_text(encoding="utf-8")
        self.assertIn("len(recommendations) != DAILY_TARGET_SIZE", source)
        self.assertIn("not artist for artist in artist_keys", source)
        self.assertIn("daily_artist_diversity_fallback_used", source)
        self.assertNotIn("count > 2 for count in artist_counts.values()", source)

    def test_daily_description_pool_keeps_all_originally_discussed_lines(self):
        expected = {
            "Could be worse. Could be quiet.",
            "At least the music's good.",
            "Familiar names. Unexpected detours",
            "Your daily dose of questionable taste.",
        }
        self.assertTrue(expected.issubset(set(daily_cycle.DAILY_DESCRIPTIONS)))
        self.assertEqual(len(daily_cycle.DAILY_DESCRIPTIONS), len(set(daily_cycle.DAILY_DESCRIPTIONS)))

    def test_daily_description_rotates_deterministically_and_never_repeats_current(self):
        current = daily_cycle.DAILY_DESCRIPTIONS[0]
        first = daily_cycle.choose_daily_description("2026-11-05", current)
        second = daily_cycle.choose_daily_description("2026-11-05", current)
        self.assertEqual(first, second)
        self.assertNotEqual(first, current)
        self.assertIn(first, daily_cycle.DAILY_DESCRIPTIONS)
        self.assertLessEqual(len(first), 300)

    def test_daily_description_selection_changes_for_next_cycle(self):
        first = daily_cycle.choose_daily_description("2026-11-05")
        second = daily_cycle.choose_daily_description("2026-11-06", first)
        self.assertNotEqual(first, second)

    def test_description_readback_normalizes_html_escaped_apostrophes(self):
        class FakeSpotify:
            def call(self, method, path, payload=None):
                if method == "PUT":
                    self.description = payload["description"]
                    return {}
                return {"description": "Today&#x27;s detour starts here."}

        with patch.object(daily_cycle.time, "sleep"):
            daily_cycle.update_description_and_verify(
                FakeSpotify(), "Today's detour starts here."
            )

    def test_description_update_precedes_readback_and_retries_spotify_lag(self):
        source = (ROOT / "scripts" / "spotify" / "spotify_daily_cycle.py").read_text(encoding="utf-8")
        replace_at = source.index("cloud.replace_playlist(sp, DAILY_ID, uris, expected_before_uris=before_uris)")
        description_at = source.index("update_description_and_verify(sp, next_description)", replace_at)
        verify_at = source.index('updated = sp.call("GET", f"/playlists/{DAILY_ID}")', description_at)
        self.assertLess(replace_at, description_at)
        self.assertLess(description_at, verify_at)
        self.assertIn("for attempt in range(5)", source)
        self.assertIn('sp.call("PUT", f"/playlists/{DAILY_ID}", {"description": description})', source)

    def test_description_only_mode_is_present_and_does_not_replace_tracks(self):
        source = (ROOT / "scripts" / "spotify" / "spotify_daily_cycle.py").read_text(encoding="utf-8")
        branch = source[source.index("if args.description_only:"):source.index("# Re-read immediately before planning/mutation")]
        self.assertIn("update_description_and_verify(sp, next_description)", branch)
        self.assertNotIn("cloud.replace_playlist", branch)
        self.assertIn('set_action_output("description_updated", "true")', branch)

    def test_replacement_state_is_persisted_before_post_change_read(self):
        source = (ROOT / "scripts" / "spotify" / "spotify_daily_cycle.py").read_text(encoding="utf-8")
        replace_at = source.index("cloud.replace_playlist(sp, DAILY_ID, uris, expected_before_uris=before_uris)")
        persist_at = source.index("manager.write(manager.CONFIG, config)", replace_at)
        output_at = source.index('set_action_output("cycled", "true")', persist_at)
        audit_at = source.index('event="daily_cycle_replacement_accepted"', output_at)
        verify_at = source.index('updated = sp.call("GET", f"/playlists/{DAILY_ID}")', audit_at)
        self.assertLess(replace_at, persist_at)
        self.assertLess(persist_at, output_at)
        self.assertLess(output_at, audit_at)
        self.assertLess(audit_at, verify_at)

    def test_workflow_persists_accepted_replacement_even_after_later_step_failure(self):
        workflow = (ROOT / ".github" / "workflows" / "spotify-daily-midnight-cycle.yml").read_text(encoding="utf-8")
        self.assertIn('- cron: "15 4,5 * * *"', workflow)
        self.assertIn("steps.daily-cycle.outputs.cycled == 'true' || steps.daily-cycle.outputs.description_updated == 'true'", workflow)

    def test_workflow_persists_spotify_cooldown_even_when_cycle_fails(self):
        workflow = (ROOT / ".github" / "workflows" / "spotify-daily-midnight-cycle.yml").read_text(encoding="utf-8")
        start = workflow.index("name: Preserve surfaced candidates and Spotify cooldown even if rotation fails")
        step = workflow[start:workflow.index("\n\n", start)]
        self.assertIn("hashFiles('.github/spotify_api_cooldown.json')", step)
        self.assertIn(".github/spotify_api_cooldown.json", step)
        self.assertIn("if: always()", step)


    def test_action_output_is_written_as_a_real_newline_delimited_value(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "github-output"
            with patch.dict(os.environ, {"GITHUB_OUTPUT": str(output)}):
                daily_cycle.set_action_output("cycled", "true")
            self.assertEqual(output.read_text(encoding="utf-8"), "cycled=true" + chr(10))


if __name__ == "__main__":
    unittest.main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Regression tests for Tricky Daily scheduled-run timing and outputs.
# Coverage: Delayed catch-up, EST cron boundary, manual dispatch, force, early
#           duplicate no-op, accepted-mutation persistence, and Actions outputs.
# Run: python -m unittest tests.test_spotify_daily_cycle_schedule -v
# Related: scripts/spotify/spotify_daily_cycle.py and the midnight-cycle workflow.
# -----------------------------------------------------------------------------

