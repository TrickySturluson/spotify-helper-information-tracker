import json
import unittest
from pathlib import Path


class BoozeFitCandidateSnapshotTests(unittest.TestCase):
    def test_booze_candidates_are_identity_only_and_match_saved_playlist_snapshot(self):
        root = Path(__file__).resolve().parents[1]
        snapshot = json.loads((root / "assistant_data/spotify/playlists/4diIlnF8BlgoJrwUfejf49.json").read_text(encoding="utf-8"))
        candidates = json.loads((root / "assistant_data/spotify/playlist_fit_booze_candidates_20261102.json").read_text(encoding="utf-8"))
        self.assertEqual(candidates["source_playlist_id"], snapshot["id"])
        self.assertEqual(candidates["source_snapshot_id"], snapshot["snapshot_id"])
        snapshot_uris = [row["uri"] for row in snapshot["items"] if row.get("type") == "track" and row.get("uri")]
        candidate_uris = [row["uri"] for row in candidates["tracks"]]
        self.assertEqual(candidate_uris, snapshot_uris)
        self.assertEqual(len(candidate_uris), len(set(candidate_uris)))
        self.assertEqual(len(candidate_uris), 64)
        for row in candidates["tracks"]:
            self.assertTrue(row["uri"].startswith("spotify:track:"))
            self.assertNotIn("score", row)
            self.assertNotIn("human_rating", row)
            self.assertNotIn("confidence", row)


if __name__ == "__main__":
    unittest.main()

# FILE OVERVIEW
# Purpose: Ensure the Booze cross-reference audit candidates are identity-only and stay aligned with the saved Spotify playlist snapshot.
# Safety: No Spotify API calls or playlist writes; fails closed if the source snapshot changes without regenerating the candidate file.
