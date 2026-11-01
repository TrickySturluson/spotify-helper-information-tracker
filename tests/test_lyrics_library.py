import tempfile
import unittest
from pathlib import Path

from lyrics_library import LyricsLibrary, analyze_lyrics, phrase_fingerprints


class LyricsLibraryTests(unittest.TestCase):
    def test_horror_themes_are_detected(self):
        result = analyze_lyrics("The vampire stalks the graveyard, the zombie wants blood.")
        self.assertIn("vampire", result["themes"])
        self.assertIn("zombie_undead", result["themes"])

    def test_lyrics_are_not_stored_but_phrase_fingerprint_is_searchable(self):
        with tempfile.TemporaryDirectory() as temp:
            db = Path(temp) / "lyrics.sqlite3"
            library = LyricsLibrary(db)
            lyrics = "The vampire stalks the graveyard while the midnight shadows rise."
            library.save("Night Song", "Example Artist", results=[{
                "provider": "test", "url": "https://example.test/song", "lyrics": lyrics
            }])
            matches = library.lookup(phrase="vampire stalks the graveyard while the midnight")
            self.assertEqual(len(matches), 1)
            self.assertEqual(matches[0]["title"], "Night Song")
            stored = " ".join(str(row[0]) for row in library.db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"))
            self.assertNotIn("lyrics_text", stored)
            library.close()

    def test_short_phrase_is_not_indexed(self):
        self.assertEqual(phrase_fingerprints("blood and thunder"), [])


if __name__ == "__main__":
    unittest.main()
