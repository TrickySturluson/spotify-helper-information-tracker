import unittest
from enrich_acousticbrainz import aggregate_submissions, extract


class AcousticBrainzTests(unittest.TestCase):
    def test_extracts_tempo_and_acoustic_features(self):
        row = extract({
            "lowlevel": {
                "rhythm": {
                    "bpm": 128.4,
                    "bpm_histogram_first_peak_bpm": {"mean": 64.2},
                    "bpm_histogram_second_peak_bpm": {"mean": 128.4},
                    "danceability": 2.1,
                    "onset_rate": 3.2,
                    "beats_count": 245,
                },
                "average_loudness": 0.91,
                "dynamic_complexity": 1.7,
            },
            "metadata": {"audio_properties": {"replay_gain": -4.5}},
        }, "Artist", "Track", "00000000-0000-0000-0000-000000000000")
        self.assertEqual(row["tempo_bpm"], 128.4)
        self.assertEqual(row["average_loudness"], 0.91)
        self.assertEqual(row["dynamic_complexity"], 1.7)
        self.assertEqual(row["replay_gain_db"], -4.5)
        self.assertEqual(row["source_license"], "CC0")


    def test_aggregates_all_submissions_and_retains_tempo_disagreement(self):
        docs = [
            {"lowlevel": {"rhythm": {"bpm": 120.0}, "average_loudness": 0.8}},
            {"lowlevel": {"rhythm": {"bpm": 122.0}, "average_loudness": 0.9}},
            {"lowlevel": {"rhythm": {"bpm": 160.0}, "average_loudness": 1.0}},
        ]
        row = aggregate_submissions(
            docs, "Artist", "Track", "00000000-0000-0000-0000-000000000000"
        )
        self.assertEqual(row["submission_count"], 3)
        self.assertEqual(row["tempo_bpm"], 122.0)
        self.assertEqual(row["tempo_spread_bpm"], 40.0)
        self.assertEqual(row["tempo_confidence"], "low")
        self.assertEqual(row["average_loudness"], 0.9)
        self.assertEqual(row["tempo_submission_values_bpm"], [120.0, 122.0, 160.0])

    def test_empty_submission_set_is_a_cacheable_miss(self):
        self.assertIsNone(aggregate_submissions([], "Artist", "Track", "id"))

    def test_missing_fields_are_none(self):
        row = extract({}, "Artist", "Track", "id")
        self.assertIsNone(row["tempo_bpm"])
        self.assertIsNone(row["average_loudness"])


if __name__ == "__main__":
    unittest.main()

# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Verify extraction and normalization of sourced AcousticBrainz features.
# Coverage: Tempo, loudness, dynamic complexity, replay gain, license metadata,
#           and safe handling of missing feature fields.
# Run: python -m unittest tests.test_enrich_acousticbrainz -v (from the repository root).
# Related: scripts/music/enrich_acousticbrainz.py and docs/AUTOMATED_AUDIO_METADATA.md.
# -----------------------------------------------------------------------------
