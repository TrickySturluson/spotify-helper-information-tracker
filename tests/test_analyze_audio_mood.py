import json
import tempfile
import unittest
from pathlib import Path

from scripts.music import analyze_audio_mood as mood


class AudioMoodModelTests(unittest.TestCase):
    def test_aggregate_predictions_reports_axes_and_segment_variability(self):
        result = mood.aggregate_predictions([
            [5.0, 3.0],
            [7.0, 5.0],
        ])
        self.assertEqual(result["valence_mean"], 6.0)
        self.assertEqual(result["arousal_mean"], 4.0)
        self.assertEqual(result["segment_count"], 2)
        self.assertEqual(result["valence_std"], 1.0)
        self.assertEqual(result["arousal_std"], 1.0)
        self.assertEqual(result["scale"], {"min": 1.0, "max": 9.0})

    def test_aggregate_predictions_rejects_bad_shape(self):
        with self.assertRaises(ValueError):
            mood.aggregate_predictions([[1.0, 2.0, 3.0]])

    def test_aggregate_predictions_rejects_out_of_range_values(self):
        with self.assertRaises(ValueError):
            mood.aggregate_predictions([[0.0, 5.0]])

    def test_model_files_require_expected_name_classes_and_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / mood.EMBEDDING_MODEL).write_bytes(b"embedding")
            (root / mood.MOOD_MODEL).write_bytes(b"model")
            (root / mood.MODEL_METADATA).write_text(json.dumps({
                "name": "arousal_valence",
                "version": "2",
                "classes": ["valence", "arousal"],
                "dataset": {"name": "DEAM"},
            }), encoding="utf-8")
            embedding, model, metadata = mood.validate_model_files(root)
            self.assertEqual(embedding.name, mood.EMBEDDING_MODEL)
            self.assertEqual(model.name, mood.MOOD_MODEL)
            self.assertEqual(metadata["dataset"]["name"], "DEAM")

    def test_model_files_reject_wrong_output_class_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in (mood.EMBEDDING_MODEL, mood.MOOD_MODEL):
                (root / name).write_bytes(b"model")
            (root / mood.MODEL_METADATA).write_text(json.dumps({
                "name": "arousal_valence",
                "version": "2",
                "classes": ["arousal", "valence"],
            }), encoding="utf-8")
            with self.assertRaises(ValueError):
                mood.validate_model_files(root)


if __name__ == "__main__":
    unittest.main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Regression tests for optional Essentia DEAM valence/arousal inference.
# Coverage: Segment aggregation, output scale validation, required local model files,
#           and metadata class/version identity checks.
# Run: python -m unittest tests.test_analyze_audio_mood -v
# Related: scripts/music/analyze_audio_mood.py; docs/AUDIO_MOOD_MODELS.md.
# -----------------------------------------------------------------------------
