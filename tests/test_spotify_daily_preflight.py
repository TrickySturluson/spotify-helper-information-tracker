import unittest
from unittest.mock import patch

from scripts.spotify import spotify_daily_preflight as preflight


class FakeSpotify:
    def __init__(self, user_id="user-1", playlist_id=None, name="Tricky Daily", owner_id="user-1"):
        self.user_id = user_id
        self.playlist_id = playlist_id or preflight.DAILY_ID
        self.name = name
        self.owner_id = owner_id
        self.calls = []

    def me(self):
        self.calls.append(("GET", "/me"))
        return {"id": self.user_id}

    def call(self, method, path, body=None):
        self.calls.append((method, path))
        return {
            "id": self.playlist_id,
            "name": self.name,
            "owner": {"id": self.owner_id},
        }

    def items(self, playlist_id):
        self.calls.append(("GET", f"/playlists/{playlist_id}/items"))
        return [{"item": {"uri": "spotify:track:test"}}] * 7


class TrickyDailyLivePreflightTests(unittest.TestCase):
    def test_valid_live_playlist_passes_using_get_only(self):
        sp = FakeSpotify()
        with patch.object(preflight.manager, "assert_managed"), patch.object(
            preflight.manager, "unlocked", return_value=True
        ):
            report = preflight.validate_live_playlist(sp)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["mode"], "read_only_live_preflight")
        self.assertEqual(report["playlist_items_read"], 7)
        self.assertFalse(report["playlist_mutation"])
        self.assertTrue(all(method == "GET" for method, _ in sp.calls))

    def test_wrong_playlist_id_is_rejected(self):
        sp = FakeSpotify(playlist_id="wrong")
        with patch.object(preflight.manager, "assert_managed"), patch.object(
            preflight.manager, "unlocked", return_value=True
        ):
            with self.assertRaises(preflight.manager.ManagerError):
                preflight.validate_live_playlist(sp)

    def test_wrong_owner_is_rejected(self):
        sp = FakeSpotify(owner_id="someone-else")
        with patch.object(preflight.manager, "assert_managed"), patch.object(
            preflight.manager, "unlocked", return_value=True
        ):
            with self.assertRaises(preflight.manager.ManagerError):
                preflight.validate_live_playlist(sp)

    def test_wrong_name_is_rejected(self):
        sp = FakeSpotify(name="Not Tricky Daily")
        with patch.object(preflight.manager, "assert_managed"), patch.object(
            preflight.manager, "unlocked", return_value=True
        ):
            with self.assertRaises(preflight.manager.ManagerError):
                preflight.validate_live_playlist(sp)

    def test_locked_playlist_is_rejected(self):
        sp = FakeSpotify()
        with patch.object(preflight.manager, "assert_managed"), patch.object(
            preflight.manager, "unlocked", return_value=False
        ):
            with self.assertRaises(preflight.manager.ManagerError):
                preflight.validate_live_playlist(sp)


if __name__ == "__main__":
    unittest.main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Unit tests for the live Tricky Daily preflight.
# Coverage: Exact ID/name/owner checks, managed/unlocked permission, and GET-only behavior.
# Run: python -m unittest tests.test_spotify_daily_preflight -v
# Related: scripts/spotify/spotify_daily_preflight.py.
# -----------------------------------------------------------------------------
