import tempfile
import unittest
from pathlib import Path

from lyrics_library import LyricsLibrary, analyze_lyrics, phrase_fingerprints


class LyricsLibraryTests(unittest.TestCase):
    def test_horror_themes_are_detected(self):
        result = analyze_lyrics("The vampire stalks the graveyard, the zombie wants blood.")
        self.assertIn("vampire", result["themes"])
        self.assertIn("zombie_undead", result["themes"])
        self.assertEqual(result["schema_version"], 3)

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
            import json
            analysis = library.db.execute("SELECT themes_json FROM analyses").fetchone()
            decoded = json.loads(analysis["themes_json"])
            self.assertIn("vampire", decoded["themes"])
            self.assertEqual(decoded["source_count"], 1)
            stored = " ".join(str(row[0]) for row in library.db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"))
            self.assertNotIn("lyrics_text", stored)
            library.close()

    def test_short_phrase_is_not_indexed(self):
        self.assertEqual(phrase_fingerprints("blood and thunder"), [])


    def test_multiple_sources_are_merged(self):
        with tempfile.TemporaryDirectory() as temp:
            library = LyricsLibrary(Path(temp) / "lyrics.sqlite3")
            library.save("Monster Song", "Example Artist", results=[
                {"provider": "source_a", "lyrics": "The vampire rises from the coffin."},
                {"provider": "source_b", "lyrics": "A zombie crawls from the graveyard."},
            ])
            import json
            row = library.db.execute("SELECT themes_json FROM analyses").fetchone()
            data = json.loads(row["themes_json"])
            self.assertIn("vampire", data["themes"])
            self.assertIn("zombie_undead", data["themes"])
            self.assertEqual(data["source_count"], 2)
            library.close()

    def test_general_themes_are_detected_without_inflating_horror_score(self):
        result = analyze_lyrics("We party and celebrate in the nightclub, dancing with friends together tonight.")
        self.assertIn("nightlife_clubbing", result["themes"])
        self.assertIn("party_celebration", result["themes"])
        self.assertIn("friendship_togetherness", result["themes"])
        self.assertEqual(result["horror_relevance"], 0.0)

    def test_recommendation_theme_sets_are_multi_source_and_versioned(self):
        with tempfile.TemporaryDirectory() as temp:
            library = LyricsLibrary(Path(temp) / "lyrics.sqlite3")
            song_id = library.save("Monster Song", "Example Artist", results=[
                {"provider": "source_a", "lyrics": "The vampire rises from the coffin."},
                {"provider": "source_b", "lyrics": "A zombie crawls from the graveyard."},
            ])
            import json
            row = library.db.execute("SELECT themes_json FROM analyses WHERE song_id=?", (song_id,)).fetchone()
            data = json.loads(row["themes_json"])
            self.assertEqual(data["schema_version"], 3)
            self.assertEqual(data["source_count"], 2)
            self.assertEqual(data["themes"]["vampire"]["source_count"], 1)
            self.assertEqual(data["themes"]["zombie_undead"]["source_count"], 1)
            library.close()


if __name__ == "__main__":
    unittest.main()
