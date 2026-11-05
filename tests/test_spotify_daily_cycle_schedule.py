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

    def test_cycle_date_guard_rejects_malformed_state(self):
        with self.assertRaises(daily_cycle.manager.ManagerError):
            daily_cycle.cycle_already_completed({"daily_cycle": []}, "2026-11-05")

    def test_action_output_is_written_as_a_real_newline_delimited_value(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "github-output"
            with patch.dict(os.environ, {"GITHUB_OUTPUT": str(output)}):
                daily_cycle.set_action_output("cycled", "true")
            self.assertEqual(output.read_text(encoding="utf-8"), "cycled=true\n")


if __name__ == "__main__":
    unittest.main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Regression tests for Tricky Daily scheduled-run timing and outputs.
# Coverage: Delayed catch-up, EST cron boundary, manual dispatch gating, force,
#           date idempotency, malformed state, and Actions step outputs.
# Run: python -m unittest tests.test_spotify_daily_cycle_schedule -v
# Related: scripts/spotify/spotify_daily_cycle.py and the midnight-cycle workflow.
# -----------------------------------------------------------------------------
