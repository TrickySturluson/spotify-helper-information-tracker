import unittest

import spotify_playlist_sequencer as sequencer


class PlaylistSequencerTests(unittest.TestCase):
    def test_audio_energy_dominates_order(self):
        rows = [
            {"uri": "spotify:track:high", "name": "Loud", "artists": ["Artist"],
             "audio_features": {"energy": 0.95, "tempo": 170, "loudness": -4}},
            {"uri": "spotify:track:low", "name": "Quiet", "artists": ["Artist"],
             "audio_features": {"energy": 0.08, "tempo": 65, "loudness": -29}},
        ]
        result = sequencer.sequence_tracks(rows)
        self.assertEqual([r["item"]["name"] for r in result], ["Quiet", "Loud"])
        self.assertGreater(result[1]["score"], result[0]["score"])
        self.assertEqual(result[0]["confidence"], "high")

    def test_track_tags_are_preferred_to_artist_mood(self):
        item = {"uri": "spotify:track:1", "name": "Track", "artists": ["Artist"]}
        artists = {"artist": {"tags": [{"tag": "calm"}]}}
        tracks = {("artist", "track"): {"lastfm_tags": [{"tag": "aggressive"}]}}
        result = sequencer.score_track(item, artists, tracks)
        self.assertIn("aggressive", " ".join(result["evidence"]))
        self.assertNotIn("artist-level mood fallback", " ".join(result["evidence"]))

    def test_missing_metadata_is_explicitly_unknown(self):
        result = sequencer.score_track({"uri": "spotify:track:1", "name": "Unknown", "artists": ["No Profile"]})
        self.assertEqual(result["confidence"], "unknown")
        self.assertEqual(result["score"], 50.0)


    def test_theme_grouping_is_available_without_replacing_energy_scores(self):
        rows = [
            {"uri": "spotify:track:b", "name": "B", "artists": ["Artist B"],
             "audio_features": {"energy": 0.51}},
            {"uri": "spotify:track:a", "name": "A", "artists": ["Artist A"],
             "audio_features": {"energy": 0.52}},
        ]
        artists = {
            "artist a": {"themes": ["dreamlike"]},
            "artist b": {"themes": ["nocturnal"]},
        }
        result = sequencer.sequence_tracks(rows, artist_profiles=artists, group_by="theme")
        self.assertEqual(result[0]["sequence_group"], "dreamlike")
        self.assertEqual(result[1]["sequence_group"], "nocturnal")
        self.assertLessEqual(abs(result[1]["score"] - result[0]["score"]), 10)

    def test_confidence_summary_counts_unknown_metadata(self):
        rows = [
            {"confidence": "high"},
            {"confidence": "low"},
            {"confidence": "unknown"},
            {"confidence": "unknown"},
        ]
        self.assertEqual(
            sequencer.confidence_summary(rows),
            {"high": 1, "medium": 0, "low": 1, "unknown": 2},
        )

    def test_sort_modes_include_atmosphere_style_narrative_and_discovery(self):
        rows = [
            {"uri": "spotify:track:1", "name": "Soft", "artists": ["Rare"]},
            {"uri": "spotify:track:2", "name": "Loud", "artists": ["Popular"]},
            {"uri": "spotify:track:3", "name": "Dark", "artists": ["Dark Artist"]},
        ]
        artists = {
            "rare": {"play_count": 12, "lastfm_tags": [{"tag": "dreamy"}], "genres": ["dream pop"], "themes": ["dreamlike"]},
            "popular": {"play_count": 900, "lastfm_tags": [{"tag": "energetic"}], "genres": ["punk"], "themes": ["rebellious"]},
            "dark artist": {"play_count": 80, "lastfm_tags": [{"tag": "dark"}], "genres": ["darkwave"], "themes": ["nocturnal"]},
        }
        atmosphere = sequencer.sequence_tracks(rows, artists, mode="atmosphere")
        self.assertEqual(atmosphere[0]["sequence_group"], "dreamy")
        style = sequencer.sequence_tracks(rows, artists, mode="style")
        self.assertEqual({row["sequence_group"] for row in style}, {"dream pop", "punk", "darkwave"})
        narrative = sequencer.sequence_tracks(rows, artists, mode="narrative")
        self.assertEqual(narrative[0]["sequence_group"], "act-1")
        discovery = sequencer.sequence_tracks(rows, artists, mode="discovery")
        self.assertEqual(discovery[0]["artist"], "Rare")

    def test_hybrid_keeps_broad_energy_bands_in_order(self):
        rows = [
            {"uri": "spotify:track:high", "name": "High", "artists": ["A"],
             "audio_features": {"energy": 0.91}},
            {"uri": "spotify:track:low", "name": "Low", "artists": ["B"],
             "audio_features": {"energy": 0.12}},
        ]
        result = sequencer.sequence_tracks(rows, mode="hybrid")
        self.assertEqual([row["item"]["name"] for row in result], ["Low", "High"])

    def test_reorder_plan_preserves_duplicates_and_transforms_order(self):
        current = ["a", "b", "a", "c"]
        desired = ["a", "a", "c", "b"]
        operations = sequencer.build_reorder_operations(current, desired)
        working = list(current)
        for op in operations:
            moved = working.pop(op["range_start"])
            working.insert(op["insert_before"], moved)
        self.assertEqual(working, desired)

    def test_reorder_rejects_changed_playlist_membership(self):
        with self.assertRaises(ValueError):
            sequencer.build_reorder_operations(["a", "b"], ["a", "c"])


if __name__ == "__main__":
    unittest.main()
