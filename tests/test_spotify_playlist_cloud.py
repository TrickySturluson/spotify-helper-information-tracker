import unittest
from unittest.mock import patch

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

    def test_remove_operation_uses_manager_batch_helper(self):
        operation = [{"action": "remove", "uris": ["spotify:track:abc"]}]
        with patch.object(manager, "unlocked", return_value=True), patch.object(
            manager, "remove"
        ) as remove:
            cloud.execute(object(), "playlist123", operation)
        remove.assert_called_once_with(unittest.mock.ANY, "playlist123", ["spotify:track:abc"])


if __name__ == "__main__":
    unittest.main()
