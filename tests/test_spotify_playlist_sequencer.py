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
