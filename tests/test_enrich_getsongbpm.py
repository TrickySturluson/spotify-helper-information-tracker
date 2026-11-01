import unittest

from enrich_getsongbpm import exact_match, norm, track_key


class GetSongBPMTests(unittest.TestCase):
    def test_exact_match_requires_artist_and_title(self):
        rows = [
            {"title": "Zombie", "artist": {"name": "The Cranberries"}, "tempo": "84"},
            {"title": "Zombie", "artist": {"name": "Bad Wolves"}, "tempo": "95"},
        ]
        self.assertEqual(exact_match(rows, "The Cranberries", "Zombie")["tempo"], "84")
        self.assertIsNone(exact_match(rows, "The Cranberries", "Zombie (Live)"))

    def test_ambiguous_exact_matches_are_rejected(self):
        rows = [
            {"title": "Song", "artist": {"name": "Artist"}},
            {"title": "Song", "artist": {"name": "Artist"}},
        ]
        self.assertIsNone(exact_match(rows, "Artist", "Song"))

    def test_normalization_is_conservative(self):
        self.assertEqual(norm("  THE   SONG "), "the song")
        self.assertNotEqual(norm("Song (Live)"), norm("Song"))

    def test_cache_key_is_stable(self):
        self.assertEqual(track_key("Artist", "Song"), track_key(" artist ", "SONG"))


if __name__ == "__main__":
    unittest.main()
