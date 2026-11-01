"""Guard the responsibility-based script layout and compatibility entry points."""
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GROUPS = {
    "analytics": (
        "audit_project.py",
        "build_advanced_analytics.py",
        "build_assistant_data.py",
        "build_listening_time_summary.py",
        "build_music_analytics.py",
        "build_playback_analytics.py",
        "build_stats.py",
    ),
    "music": (
        "audio_analysis.py",
        "build_music_metadata.py",
        "build_music_profiles.py",
        "build_track_profiles.py",
        "enrich_acousticbrainz.py",
        "enrich_getsongbpm.py",
        "enrich_musicbrainz_durations.py",
        "enrich_musicbrainz_recording_ids.py",
        "enrich_recommendation_lyrics.py",
        "lyrics_library.py",
        "mood_inference.py",
    ),
    "spotify": (
        "playlist_intelligence.py",
        "playlist_metadata.py",
        "spotify_daily_feedback.py",
        "spotify_daily_playlist.py",
        "spotify_discovery.py",
        "spotify_playback_tracker.py",
        "spotify_playlist_cloud.py",
        "spotify_playlist_manager.py",
        "spotify_playlist_sequencer.py",
        "spotify_reference_library.py",
        "track_playlist_removals.py",
    ),
    "lastfm": ("update_lastfm.py",),
}


class ScriptLayoutTests(unittest.TestCase):
    def test_every_implementation_has_a_root_compatibility_entry_point(self):
        for group, filenames in GROUPS.items():
            for filename in filenames:
                with self.subTest(group=group, filename=filename):
                    implementation = ROOT / "scripts" / group / filename
                    shim = ROOT / filename
                    self.assertTrue(implementation.is_file())
                    self.assertTrue(shim.is_file())
                    source = shim.read_text(encoding="utf-8")
                    self.assertIn(f'"scripts" / "{group}" / "{filename}"', source)

    def test_each_script_group_is_a_python_package(self):
        for group in GROUPS:
            with self.subTest(group=group):
                self.assertTrue((ROOT / "scripts" / group / "__init__.py").is_file())


if __name__ == "__main__":
    unittest.main()
