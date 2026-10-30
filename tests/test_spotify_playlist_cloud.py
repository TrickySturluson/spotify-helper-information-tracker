import unittest
from unittest.mock import Mock, patch

import spotify_playlist_cloud as cloud
import spotify_playlist_manager as manager


class CloudExecutorTests(unittest.TestCase):
    def test_locked_playlist_blocks_cloud_execution(self):
        operation = [{"action": "add", "uris": ["spotify:track:abc"]}]
        with patch.object(manager, "unlocked", return_value=False):
            with self.assertRaises(manager.ManagerError):
                cloud.execute(None, "playlist123", operation)

    def test_add_operation_uses_manager_batch_helper(self):
        operation = [{"action": "add", "uris": ["spotify:track:abc"]}]
        with patch.object(manager, "unlocked", return_value=True), patch.object(
            manager, "add"
        ) as add:
            cloud.execute(object(), "playlist123", operation)
        add.assert_called_once_with(unittest.mock.ANY, "playlist123", ["spotify:track:abc"])

    def test_restore_replaces_first_page_and_appends_remaining_items(self):
        uris = ["spotify:track:" + str(i) for i in range(205)]
        sp = Mock()
        with patch.object(manager, "unlocked", return_value=True):
            cloud.replace_playlist(sp, "playlist123", uris)
        sp.call.assert_any_call("PUT", "/playlists/playlist123/items", {"uris": uris[:100]})
        sp.call.assert_any_call("POST", "/playlists/playlist123/items", {"uris": uris[100:200]})
        sp.call.assert_any_call("POST", "/playlists/playlist123/items", {"uris": uris[200:]})

    def test_restore_empty_snapshot_removes_existing_items(self):
        sp = Mock()
        with patch.object(manager, "unlocked", return_value=True), patch.object(
            manager, "tracks", return_value=[{"uri": "spotify:track:a"}]
        ), patch.object(manager, "find", return_value={"id": "playlist123"}), patch.object(
            manager, "remove"
        ) as remove:
            cloud.replace_playlist(sp, "playlist123", [])
        remove.assert_called_once_with(sp, "playlist123", ["spotify:track:a"])

    def test_remove_operation_uses_manager_batch_helper(self):
        operation = [{"action": "remove", "uris": ["spotify:track:abc"]}]
        with patch.object(manager, "unlocked", return_value=True), patch.object(
            manager, "remove"
        ) as remove:
            cloud.execute(object(), "playlist123", operation)
        remove.assert_called_once_with(unittest.mock.ANY, "playlist123", ["spotify:track:abc"])


if __name__ == "__main__":
    unittest.main()
