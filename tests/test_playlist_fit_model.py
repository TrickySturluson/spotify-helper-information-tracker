import unittest

from scripts.spotify.playlist_fit_model import (
    DIMENSIONS, build_reference_profile, score_track,
)


def evidence(value, family="musicbrainz", scope="recording", identity="high"):
    return {"value": value, "source_family": family, "scope": scope,
            "identity_confidence": identity}


def make_track(i, uri=None):
    return {
        "uri": uri or f"spotify:track:reference{i:02d}",
        "artist": f"Artist {i}", "title": f"Song {i}",
        "dimensions": {
            "genre": [evidence("dream pop", "musicbrainz"), evidence("indie", "lastfm")],
            "sound": [evidence("hazy", "review_source"), evidence("shimmering guitars", "musicbrainz")],
            "energy": [evidence(35 + (i % 3), "essentia", "audio")],
            "mood": [evidence("wistful", "lastfm"), evidence("dreamy", "musicbrainz")],
            "theme": [evidence("introspection", "lyrics", "lyrics")],
        },
    }


class PlaylistFitModelTests(unittest.TestCase):
    def setUp(self):
        self.references = [make_track(i) for i in range(24)]
        self.candidate = make_track(100, "spotify:track:candidate")

    def test_candidate_is_excluded_from_its_own_profile(self):
        profile = build_reference_profile(
            self.references + [self.candidate],
            candidate_uri=self.candidate["uri"],
        )
        self.assertEqual(profile["track_count"], 24)
        self.assertEqual(profile["excluded_candidate_and_holdout_count"], 1)

    def test_heldout_batch_is_excluded(self):
        heldout = {self.references[0]["uri"], self.references[1]["uri"]}
        profile = build_reference_profile(self.references, heldout_uris=heldout)
        self.assertEqual(profile["track_count"], 22)
        self.assertEqual(profile["excluded_candidate_and_holdout_count"], 2)

    def test_complete_independent_evidence_can_reach_high_confidence(self):
        profile = build_reference_profile(self.references)
        result = score_track(self.candidate, profile)
        self.assertIsNotNone(result["fit_score"])
        self.assertEqual(result["confidence_tier"], "high")
        self.assertEqual(result["supported_dimensions"], 5)
        self.assertFalse(result["human_ratings_used"])

    def test_missing_dimension_is_unknown_not_zero(self):
        profile = build_reference_profile(self.references)
        sparse = make_track(101, "spotify:track:sparse")
        sparse["dimensions"]["theme"] = []
        result = score_track(sparse, profile)
        self.assertIsNone(result["dimension_scores"]["theme"]["score"])
        self.assertEqual(result["supported_dimensions"], 4)
        self.assertLess(result["evidence_coverage"], 1.0)
        self.assertNotEqual(result["confidence_tier"], "high")

    def test_artist_only_context_cannot_promote_confidence(self):
        profile = build_reference_profile(self.references)
        artist_context = make_track(102, "spotify:track:artist-context")
        artist_context["dimensions"] = {
            dim: [evidence("dream pop", "lastfm_artist", "artist", "medium")]
            for dim in ("genre", "sound", "mood", "theme")
        }
        artist_context["dimensions"]["energy"] = []
        result = score_track(artist_context, profile)
        self.assertEqual(result["confidence_tier"], "low")
        self.assertTrue(any("identity" in reason or "source families" in reason
                            for reason in result["confidence_reasons"]))

    def test_single_source_family_is_not_independent_corroboration(self):
        profile = build_reference_profile(self.references)
        single = make_track(103, "spotify:track:single-source")
        for dim in DIMENSIONS:
            single["dimensions"][dim] = [evidence("dream pop", "lastfm") for _ in range(5)]
        result = score_track(single, profile)
        self.assertNotEqual(result["confidence_tier"], "high")
        self.assertIn("fewer than two independent source families",
                      result["confidence_reasons"])

    def test_unresolved_identity_returns_unknown(self):
        profile = build_reference_profile(self.references)
        unknown = make_track(104, "spotify:track:unknown-id")
        for dim in DIMENSIONS:
            unknown["dimensions"][dim] = [evidence("dream pop", "lastfm", "recording", "unknown")]
        result = score_track(unknown, profile)
        self.assertEqual(result["confidence_tier"], "unknown")
        self.assertEqual(result["decision"], "insufficient_evidence")

    def test_scores_are_per_target_and_not_forced_to_sum_to_100(self):
        profile = build_reference_profile(self.references)
        result = score_track(self.candidate, profile)
        self.assertIsInstance(result["fit_score"], float)
        self.assertNotIn("normalized_target_distribution", result)

    def test_no_evidence_produces_no_fit_score(self):
        profile = build_reference_profile(self.references)
        empty = {"uri": "spotify:track:empty", "artist": "Unknown",
                 "title": "Unknown", "dimensions": {}}
        result = score_track(empty, profile)
        self.assertIsNone(result["fit_score"])
        self.assertEqual(result["confidence_tier"], "unknown")


if __name__ == "__main__":
    unittest.main()
