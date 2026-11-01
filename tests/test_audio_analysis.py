import unittest
from pathlib import Path

from audio_analysis import dbfs, parse_filename


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


if __name__ == "__main__":
    unittest.main()
