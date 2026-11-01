"""Regression tests for local audio parsing, level conversion, and profile scoring."""
import unittest
from pathlib import Path

from audio_analysis import dbfs, parse_filename
from spotify_playlist_sequencer import score_track


class AudioAnalysisTests(unittest.TestCase):
    def test_filename_parser(self):
        self.assertEqual(
            parse_filename(Path("Messer Chups - Zombie Twist.flac")),
            ("Messer Chups", "Zombie Twist"),
        )

    def test_filename_requires_artist_separator(self):
        with self.assertRaises(ValueError):
            parse_filename(Path("unlabelled-track.mp3"))

    def test_dbfs_zero_is_finite_floor(self):
        self.assertEqual(dbfs(0), -240.0)

    def test_dbfs_full_scale(self):
        self.assertEqual(dbfs(1), 0.0)

    def test_measured_audio_profile_contributes_to_energy(self):
        row = score_track(
            {"name": "Night Drive", "artists": ["Test Artist"]},
            audio_profiles={("test artist", "night drive"): {
                "tempo_bpm": 150, "integrated_lufs": -8.5,
                "loudness_range_lu": 5.2, "dynamic_complexity": 0.4,
            }},
        )
        self.assertNotEqual(row["confidence"], "unknown")
        self.assertTrue(any("150.0 BPM" in item for item in row["evidence"]))
        self.assertTrue(any("LUFS" in item for item in row["evidence"]))


if __name__ == "__main__":
    unittest.main()
