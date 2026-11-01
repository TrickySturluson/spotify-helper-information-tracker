import json
import tempfile
import unittest
from pathlib import Path

import playlist_feedback_calibration as calibration


class PlaylistFeedbackCalibrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "feedback.json"

    def tearDown(self):
        self.temp.cleanup()

    def prediction(self, score=85, confidence="medium", version="fit-v1"):
        return calibration.record_prediction(
            "playlist-1", "spotify:track:abc", score, confidence,
            {"genre": ["shoegaze"], "sound_similarity": 90},
            playlist_name="Example", track_name="Track", artist="Artist",
            model_version=version, liked_before_prediction=True,
            path=self.path, predicted_at="2026-11-01T00:00:00Z",
        )

    def test_prediction_is_immutable_and_idempotent(self):
        first = self.prediction()
        second = self.prediction(score=20)
        self.assertEqual(first, second)
        self.assertEqual(first["fit_score"], 85)

    def test_explicit_outcome_is_joined_to_original_prediction(self):
        row = self.prediction()
        event = calibration.record_feedback(
            row["prediction_id"], "rejected", "explicit_blacklist",
            reason="Wrong playlist energy", path=self.path,
        )
        self.assertEqual(event["weight"], 1.0)
        report = calibration.calibration_report(self.path)
        self.assertEqual(report["labelled_predictions"], 1)

    def test_liked_observation_never_creates_fit_label(self):
        row = self.prediction()
        calibration.record_liked_observation(row["prediction_id"], False, path=self.path)
        report = calibration.calibration_report(self.path)
        self.assertEqual(report["labelled_predictions"], 0)

    def test_uncertain_and_unlabelled_predictions_are_excluded(self):
        row = self.prediction()
        calibration.record_feedback(row["prediction_id"], "uncertain", "retained_after_review", path=self.path)
        self.assertEqual(calibration.calibration_report(self.path)["labelled_predictions"], 0)

    def test_conflicting_feedback_keeps_history_and_uses_latest_event(self):
        row = self.prediction()
        calibration.record_feedback(row["prediction_id"], "rejected", "explicit_blacklist", path=self.path)
        calibration.record_feedback(row["prediction_id"], "accepted", "explicit_whitelist", path=self.path)
        payload = json.loads(self.path.read_text())
        self.assertEqual(len(payload["feedback_events"]), 2)
        report = calibration.calibration_report(self.path)
        self.assertEqual(report["labelled_predictions"], 1)

    def test_feedback_source_cannot_create_opposite_outcome(self):
        row = self.prediction()
        with self.assertRaises(ValueError):
            calibration.record_feedback(row["prediction_id"], "accepted", "explicit_blacklist", path=self.path)

    def test_duplicate_manual_feedback_is_idempotent(self):
        row = self.prediction()
        first = calibration.record_feedback(row["prediction_id"], "rejected", "manual_removal",
                                            reason="Imported removal", path=self.path)
        second = calibration.record_feedback(row["prediction_id"], "rejected", "manual_removal",
                                             reason="Imported removal", path=self.path)
        self.assertEqual(first, second)
        payload = json.loads(self.path.read_text())
        self.assertEqual(len(payload["feedback_events"]), 1)

    def test_daily_like_is_not_implicitly_imported_as_a_playlist_outcome(self):
        row = self.prediction()
        calibration.record_liked_observation(row["prediction_id"], True, path=self.path)
        self.assertEqual(calibration.calibration_report(self.path)["labelled_predictions"], 0)

    def test_unknown_prediction_and_invalid_score_fail_closed(self):
        with self.assertRaises(ValueError):
            calibration.record_prediction("p", "u", 101, "high", path=self.path)
        with self.assertRaises(KeyError):
            calibration.record_feedback("missing", "accepted", "explicit_whitelist", path=self.path)

    def test_report_has_independent_holdout_and_no_automatic_weight_updates(self):
        row = self.prediction()
        calibration.record_feedback(row["prediction_id"], "accepted", "explicit_whitelist", path=self.path)
        report = calibration.calibration_report(self.path)
        self.assertIn(report["calibration_status"], {"provisional", "reviewable_not_automatically_applied"})
        self.assertTrue(any("No scoring weights are changed automatically." in x for x in report["guardrails"]))


if __name__ == "__main__":
    unittest.main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Regression tests for immutable predictions, playlist-scoped outcomes,
#          liked-state separation, uncertain labels, holdout reporting and guards.
# Run: python -m unittest tests.test_playlist_feedback_calibration -v
# Related: scripts/spotify/playlist_feedback_calibration.py
# -----------------------------------------------------------------------------
