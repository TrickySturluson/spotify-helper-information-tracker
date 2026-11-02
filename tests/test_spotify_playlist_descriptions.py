import unittest

import spotify_playlist_descriptions as descriptions


class PlaylistDescriptionTests(unittest.TestCase):
    def test_builds_description_from_mood_genre_and_theme_evidence(self):
        profile = {
            "moods": [{"tag": "dark", "count": 8}],
            "genres": [{"tag": "synthwave", "count": 7}],
            "themes": [{"tag": "night driving", "count": 5}],
            "track_metadata": {"moods": [{"tag": "energetic", "track_count": 4}], "lyric_themes": [{"tag": "escape", "track_count": 3}]},
            "sound_tags": {"families": []},
        }
        result = descriptions.build_description("Night Mix", [{"uri": "spotify:track:a"}] * 12, profile)
        self.assertIn("Mood: energetic", result)
        self.assertIn("Sounds: synthwave", result)
        self.assertIn("Themes: escape", result)
        self.assertIn("12 tracks", result)
        self.assertLessEqual(len(result), 300)

    def test_sparse_metadata_uses_neutral_fallback(self):
        result = descriptions.build_description("Untitled", [], {})
        self.assertIn("changing collection", result)
        self.assertLessEqual(len(result), 300)

    def test_preserves_nonempty_manual_description(self):
        playlist = {"id": "p1", "name": "Manual", "description": "Written by me"}
        plan = descriptions.plan_description(playlist, [], {}, {"playlists": {}})
        self.assertEqual(plan["status"], "manual_description_preserved")
        self.assertEqual(plan["current"], "Written by me")

    def test_updates_blank_description(self):
        playlist = {"id": "p1", "name": "Auto", "description": ""}
        plan = descriptions.plan_description(playlist, [], {}, {"playlists": {}})
        self.assertEqual(plan["status"], "update")
        self.assertTrue(plan["description"])

    def test_refreshes_its_own_previous_description(self):
        items = [{"uri": "spotify:track:a"}]
        first = descriptions.build_description("Auto", items, {})
        playlist = {"id": "p1", "name": "Auto", "description": first}
        state = {"playlists": {"p1": {"generated_description": first, "profile_signature": "old"}}}
        plan = descriptions.plan_description(playlist, items, {"genres": [{"tag": "rock"}]}, state)
        self.assertEqual(plan["status"], "update")
        self.assertIn("rock", plan["description"])

    def test_rejects_overlong_output(self):
        profile = {"genres": [{"tag": "genre-" + str(i) + "x" * 80} for i in range(10)]}
        result = descriptions.build_description("Long", [], profile)
        self.assertLessEqual(len(result), 300)


if __name__ == "__main__":
    unittest.main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Regression tests for metadata-driven playlist descriptions.
# Run: python -m unittest tests.test_spotify_playlist_descriptions -v
# -----------------------------------------------------------------------------
