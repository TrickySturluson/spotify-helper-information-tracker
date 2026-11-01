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

    def test_tricky_daily_is_excluded_from_fit_calibration(self):
        with self.assertRaises(ValueError):
            calibration.record_prediction("4yUVHSMQySfWeEowfIMcx7", "spotify:track:daily", 80, "high", path=self.path)

    def test_daily_like_is_not_implicitly_imported_as_a_playlist_outcome(self):
        row = self.prediction()
        calibration.record_liked_observation(row["prediction_id"], True, path=self.path)
        self.assertEqual(calibration.calibration_report(self.path)["labelled_predictions"], 0)

    def test_unknown_prediction_and_invalid_score_fail_closed(self):
        with self.assertRaises(ValueError):
            calibration.record_prediction("p", "u", 101, "high", path=self.path)
        with self.assertRaises(KeyError):
            calibration.record_feedback("missing", "accepted", "explicit_whitelist", path=self.path)

    def test_exposure_is_context_only_and_does_not_label_prediction(self):
        row = self.prediction()
        calibration.record_exposure_observation(
            row["prediction_id"], spotify_plays=4, lastfm_scrobbles=2, path=self.path
        )
        report = calibration.calibration_report(self.path)
        self.assertEqual(report["labelled_predictions"], 0)
        payload = json.loads(self.path.read_text())
        self.assertEqual(payload["predictions"][row["prediction_id"]]["exposure_observations"][0]["spotify_plays"], 4)

    def test_removal_weight_reflects_exposure_without_changing_outcome(self):
        row = self.prediction()
        payload = json.loads(self.path.read_text())
        prediction = payload["predictions"][row["prediction_id"]]
        self.assertEqual(calibration._removal_feedback_weight(prediction), 0.65)
        prediction["exposure_observations"] = [{"spotify_plays": 0, "lastfm_scrobbles": None}]
        self.assertEqual(calibration._removal_feedback_weight(prediction), 0.45)
        prediction["exposure_observations"] = [{"spotify_plays": 5, "lastfm_scrobbles": None}]
        self.assertEqual(calibration._removal_feedback_weight(prediction), 0.90)

    def test_report_keeps_playlist_and_model_summaries_separate(self):
        first = self.prediction(version="fit-v1")
        calibration.record_feedback(first["prediction_id"], "accepted", "explicit_whitelist", path=self.path)
        second = calibration.record_prediction(
            "playlist-2", "spotify:track:def", 25, "low", model_version="fit-v2",
            path=self.path, predicted_at="2026-11-01T00:00:01Z",
        )
        calibration.record_feedback(second["prediction_id"], "rejected", "explicit_blacklist", path=self.path)
        report = calibration.calibration_report(self.path)
        self.assertEqual({row["playlist_id"] for row in report["by_playlist"]}, {"playlist-1", "playlist-2"})
        self.assertEqual({row["model_version"] for row in report["by_model_version"]}, {"fit-v1", "fit-v2"})

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
