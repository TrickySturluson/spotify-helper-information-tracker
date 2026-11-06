"""Regression coverage for the read-only Tricky Daily snapshot refresher."""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DailySnapshotImportTests(unittest.TestCase):
    def test_snapshot_imports_maintained_modules_ahead_of_compat_shims(self):
        probe = r"""
import sys
from pathlib import Path
root = Path.cwd()
sys.path.insert(0, str(root / "scripts" / "spotify"))
import spotify_daily_snapshot  # noqa: F401
import spotify_playlist_manager
import spotify_discovery
import spotify_reference_library
import spotify_listening_trends
expected = {
    "spotify_playlist_manager": root / "scripts" / "spotify" / "spotify_playlist_manager.py",
    "spotify_discovery": root / "scripts" / "spotify" / "spotify_discovery.py",
    "spotify_reference_library": root / "scripts" / "spotify" / "spotify_reference_library.py",
    "spotify_listening_trends": root / "scripts" / "spotify" / "spotify_listening_trends.py",
}
actual = {
    "spotify_playlist_manager": spotify_playlist_manager,
    "spotify_discovery": spotify_discovery,
    "spotify_reference_library": spotify_reference_library,
    "spotify_listening_trends": spotify_listening_trends,
}
for name, module in actual.items():
    assert Path(module.__file__).resolve() == expected[name].resolve(), (
        name, module.__file__, expected[name]
    )
"""
        result = subprocess.run(
            [sys.executable, "-c", probe],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()

# FILE OVERVIEW
# Purpose: Regression-test the Daily snapshot refresher's import precedence.
# Tests: Launch an isolated interpreter and verify all imported Spotify modules
#        resolve to maintained scripts/ implementations rather than compat shims.
# Safety: No Spotify credentials, provider requests, repository writes, or playlist
#         mutations are used by this test.
# Related: scripts/spotify/spotify_daily_snapshot.py and docs/TRICKY_DAILY_CYCLE.md.
