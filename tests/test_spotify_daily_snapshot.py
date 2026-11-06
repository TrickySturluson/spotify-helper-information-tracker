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

daily_id = spotify_daily_snapshot.DAILY_ID
catalog = {
    "version": 1,
    "playlists": [
        {"id": daily_id, "name": "Tricky Daily", "snapshot_id": "old", "item_count": 2},
        {"id": "other-playlist", "name": "Other", "snapshot_id": "other", "item_count": 1},
    ],
}
index = {
    "track_playlists": {
        "spotify:track:old": [daily_id, "other-playlist"],
        "spotify:track:new": ["other-playlist"],
    },
    "artist_playlists": {
        "old artist": [daily_id],
        "shared artist": [daily_id, "other-playlist"],
        "new artist": ["other-playlist"],
    },
}
previous = {
    "snapshot_id": "old",
    "items": [
        {"uri": "spotify:track:old", "artists": ["Old Artist", "Shared Artist"]},
    ],
}
record = {
    "id": daily_id,
    "name": "Tricky Daily",
    "owner": {"id": "owner"},
    "public": False,
    "collaborative": False,
    "snapshot_id": "new",
    "item_count_fetched": 2,
    "items_accessible": True,
    "last_items_accessible_at": "2026-11-06T17:31:19Z",
    "captured_at": "2026-11-06T17:31:19Z",
    "items": [
        {"uri": "spotify:track:new-daily", "artists": ["Shared Artist", "New Artist"]},
        {"uri": "spotify:track:second-daily", "artists": ["New Artist"]},
    ],
}
updated_catalog, updated_index = spotify_daily_snapshot.build_daily_reference_updates(
    catalog, index, previous, record
)
daily_row = next(row for row in updated_catalog["playlists"] if row["id"] == daily_id)
assert daily_row["snapshot_id"] == "new" and daily_row["item_count"] == 2
assert updated_index["track_playlists"]["spotify:track:old"] == ["other-playlist"]
assert daily_id in updated_index["track_playlists"]["spotify:track:new-daily"]
assert "old artist" not in updated_index["artist_playlists"]
assert updated_index["artist_playlists"]["shared artist"] == [daily_id, "other-playlist"]
assert daily_id in updated_index["artist_playlists"]["new artist"]
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
# Purpose: Regression-test Daily snapshot imports and reference-index reconciliation.
# Tests: Verify maintained module imports and that Daily-only track/artist index
#        updates preserve other playlist memberships while removing stale Daily links.
# Safety: No Spotify credentials, provider requests, repository writes, or playlist
#         mutations are used by this test.
# Related: scripts/spotify/spotify_daily_snapshot.py and docs/TRICKY_DAILY_CYCLE.md.
