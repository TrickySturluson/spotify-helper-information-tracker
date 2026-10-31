import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import spotify_daily_feedback as feedback
import spotify_playlist_manager as manager
import spotify_reference_library as library


class PlaylistPermissionTests(unittest.TestCase):
    def test_only_approved_exception_or_registered_created_playlist_is_mutable(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "managed_playlists.json"
            path.write_text(json.dumps({
                "version": 1,
                "managed": {"assistant-made": {"provenance": "created_by_shit"}},
                "approved_exceptions": {"4yUVHSMQySfWeEowfIMcx7": {"name": "Tricky Daily"}},
            }))
            with patch.object(manager, "Path", Path), patch(
                "spotify_playlist_manager.Path", Path
            ):
                # Redirect the registry's relative path without changing the production default.
                import os
                old = os.getcwd()
                os.chdir(directory)
                try:
                    (Path("assistant_data/spotify")).mkdir(parents=True)
                    (Path("assistant_data/spotify/managed_playlists.json")).write_text(path.read_text())
                    manager.assert_managed("assistant-made")
                    manager.assert_managed("4yUVHSMQySfWeEowfIMcx7")
                    with self.assertRaises(manager.ManagerError):
                        manager.assert_managed("personal-playlist")
                finally:
                    os.chdir(old)


class DailyFeedbackTests(unittest.TestCase):
    def test_no_observation_is_unknown_not_negative(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(feedback, "DATA", Path(directory) / "daily.json"):
                feedback.record_additions([{"uri": "spotify:track:abc"}], "2026-10-31T10:00:00+00:00")
                result = feedback.feedback_for("spotify:track:abc")
                self.assertEqual(result["status"], "unknown")
                self.assertTrue(result["no_listening_is_neutral"])
                self.assertIsNone(result["liked"])
                self.assertIsNone(result["post_add_measured_plays"])

    def test_liked_song_observation_is_retained(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(feedback, "DATA", Path(directory) / "daily.json"):
                feedback.record_additions([{"uri": "spotify:track:abc"}], "2026-10-31T10:00:00+00:00")
                sp = Mock()
                sp.call.return_value = [True]
                feedback.observe_liked_songs(sp, ["spotify:track:abc"])
                self.assertTrue(feedback.feedback_for("spotify:track:abc")["liked"])

    def test_lastfm_scrobbles_are_counted_after_addition(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(feedback, "DATA", root / "daily.json"):
                feedback.record_additions([{
                    "uri": "spotify:track:abc", "artist": "Artist", "track": "Song"
                }], "2026-10-31T10:00:00+00:00")
                archive = root / "scrobbles.json"
                archive.write_text(json.dumps([
                    {"artist": "Artist", "track": "Song", "timestamp": 1793440000},
                    {"artist": "Artist", "track": "Song", "timestamp": 1793443600},
                ]))
                feedback.observe_lastfm_scrobbles(archive)
                result = feedback.feedback_for("spotify:track:abc")
                self.assertEqual(result["post_add_lastfm_scrobbles"], 2)

    def test_post_add_playback_ignores_pre_add_intervals(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / "daily.json"
            segments = root / "segments.jsonl"
            with patch.object(feedback, "DATA", data):
                feedback.record_additions([{"uri": "spotify:track:abc"}], "2026-10-31T10:00:00+00:00")
                segments.write_text(
                    json.dumps({"spotify_uri": "spotify:track:abc", "started_at": "2026-10-31T09:00:00+00:00", "played_ms": 30000}) + "\n" +
                    json.dumps({"spotify_uri": "spotify:track:abc", "started_at": "2026-10-31T11:00:00+00:00", "played_ms": 45000}) + "\n"
                )
                feedback.observe_playback_segments(segments)
                result = feedback.feedback_for("spotify:track:abc")
                self.assertEqual(result["post_add_measured_plays"], 1)
                self.assertEqual(result["post_add_playback_ms"], 45000)


if __name__ == "__main__":
    unittest.main()
