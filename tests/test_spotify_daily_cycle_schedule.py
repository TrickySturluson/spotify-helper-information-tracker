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
        self.assertEqual(source.count("cycle_already_completed(config, cycle_date)"), 2)

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
        self.assertIn("len(verified_items) != DAILY_TARGET_SIZE", source)
        self.assertIn("len(verified_items) != DAILY_TARGET_SIZE", source)
        self.assertNotIn("count > 2 for count in verified_artist_counts.values()", source)
        self.assertIn('event="daily_post_change_validation_failed"', source)

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

    def test_description_update_precedes_readback_and_retries_spotify_lag(self):
        source = (ROOT / "scripts" / "spotify" / "spotify_daily_cycle.py").read_text(encoding="utf-8")
        replace_at = source.index("cloud.replace_playlist(sp, DAILY_ID, uris)")
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
        replace_at = source.index("cloud.replace_playlist(sp, DAILY_ID, uris)")
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
