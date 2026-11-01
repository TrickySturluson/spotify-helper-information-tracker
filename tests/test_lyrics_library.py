import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lyrics_library import LyricsLibrary, analyze_lyrics, phrase_fingerprints, search_and_analyze, export_analysis_features
import build_music_analytics


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

    def test_search_returns_merged_analysis_not_first_provider(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch("lyrics_library.lrclib_lookup", return_value={
                "provider": "lrclib", "url": "https://example.test/a",
                "lyrics": "The vampire rises from the coffin."
            }), patch("lyrics_library.musixmatch_lookup", return_value={
                "provider": "musixmatch", "url": "https://example.test/b",
                "lyrics": "A zombie crawls from the graveyard."
            }), patch("lyrics_library.lyrics_ovh_lookup", return_value=None), \
                 patch("lyrics_library.genius_search", return_value=None), \
                 patch("lyrics_library.time.sleep"):
                result = search_and_analyze("Monster Song", "Example Artist", db_path=Path(temp) / "lyrics.sqlite3")
            self.assertIn("vampire", result["analysis"]["themes"])
            self.assertIn("zombie_undead", result["analysis"]["themes"])
            self.assertEqual(result["analysis"]["source_count"], 2)

    def test_export_contains_derived_themes_but_not_lyrics_or_phrase_hashes(self):
        with tempfile.TemporaryDirectory() as temp:
            db_path = Path(temp) / "lyrics.sqlite3"
            export_path = Path(temp) / "lyric_features.json"
            library = LyricsLibrary(db_path)
            library.save("Night Song", "Example Artist", results=[{
                "provider": "test",
                "lyrics": "The vampire rises from the coffin beneath the midnight moon."
            }])
            library.close()
            self.assertEqual(export_analysis_features(db_path, export_path), 1)
            payload = export_path.read_text(encoding="utf-8")
            import json
            rows = json.loads(payload)
            self.assertIn("vampire", rows[0]["themes"])
            self.assertFalse(rows[0]["full_lyrics_stored"])
            self.assertNotIn("midnight moon", payload)
            self.assertNotIn("phrase_hash", payload)

    def test_recommendation_builder_loads_committed_lyric_export_without_local_db(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            (output / "lyric_features.json").write_text(
                '[{"artist":"Example Artist","track":"Night Song","schema_version":3,'
                '"themes":{"vampire":{"count":1}},"horror_relevance":0.3,'
                '"assessment":"clear","source_count":2,"sources":["lrclib","lyrics_ovh"]}]',
                encoding="utf-8",
            )
            with patch.object(build_music_analytics, "OUT", output), \
                 patch.object(build_music_analytics, "LYRICS_DB", output / "missing.sqlite3"):
                index = build_music_analytics.load_lyric_analyses()
            self.assertIn(("night song", "example artist"), index)
            self.assertIn("vampire", index[("night song", "example artist")]["themes"])


if __name__ == "__main__":
    unittest.main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Regression test module.
# Scope: Regression checks for the behavior named by this test module.
# Run: python -m unittest tests.test_lyrics_library -v (from the repository root).
# Related: Implementation lives under scripts/; longer behavior notes live in docs/.
# -----------------------------------------------------------------------------
