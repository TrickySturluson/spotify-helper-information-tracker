"""Regression tests for Tricky Daily's DST-aware scheduled-run gate."""

import unittest
from datetime import datetime
from zoneinfo import ZoneInfo
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts' / 'spotify'))
import spotify_daily_cycle as cycle

class DailyScheduleGateTests(unittest.TestCase):
    def test_est_offset(self):
        now = datetime(2026, 11, 5, 0, 0, tzinfo=ZoneInfo('America/New_York'))
        self.assertTrue(cycle.should_run_cycle(now, event_name='schedule', schedule_cron='0 5 * * *'))
        self.assertFalse(cycle.should_run_cycle(now, event_name='schedule', schedule_cron='0 4 * * *'))

    def test_edt_offset(self):
        now = datetime(2026, 7, 1, 0, 0, tzinfo=ZoneInfo('America/New_York'))
        self.assertTrue(cycle.should_run_cycle(now, event_name='schedule', schedule_cron='0 4 * * *'))
        self.assertFalse(cycle.should_run_cycle(now, event_name='schedule', schedule_cron='0 5 * * *'))

if __name__ == '__main__':
    unittest.main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Verify Tricky Daily only accepts the scheduled UTC cron matching
#          the current America/New_York daylight/standard-time offset.
# Coverage: EDT and EST acceptance plus rejection of the stale counterpart.
# Related: scripts/spotify/spotify_daily_cycle.py
# -----------------------------------------------------------------------------
