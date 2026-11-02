import json
import tempfile
import unittest
from pathlib import Path

from scripts.spotify.playlist_fit_preview import (
    build_preview, load_candidate_identities, profile_for_record, spotify_uri,
)


def library_record(uri, title="Track"):
    return {
        "id": uri,
        "identity": {
            "spotify_id": uri, "recording_mbid": None, "source_track_id": None,
            "artist": "Example Artist", "title": title,
        },
        "confidence": {"identity": "high"},
        "evidence": {
            "track_metadata": {
                "musicbrainz_genres": [{"tag": "dream pop", "provider": "musicbrainz"}],
                "discogs_styles": [{"tag": "shoegaze", "provider": "discogs"}],
            },
            "audio": {"energy": 0.4, "sound_descriptors": ["hazy"]},
            "lyrics": {"themes": ["longing"]},
        },
        "mood": {"recording_level": {"moods": ["wistful"]}},
    }


class PlaylistFitPreviewTests(unittest.TestCase):
    def test_spotify_uri_normalization_is_strict(self):
        self.assertEqual(spotify_uri("AbCdEf0123456789AbCdEf"), "spotify:track:AbCdEf0123456789AbCdEf")
        self.assertEqual(spotify_uri("https://open.spotify.com/track/AbCdEf0123456789AbCdEf?si=x"),
                         "spotify:track:AbCdEf0123456789AbCdEf")
        self.assertIsNone(spotify_uri("Artist - Track"))

    def test_candidate_loader_extracts_only_identity_and_deduplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidates.json"
            path.write_text(json.dumps({"tracks": [
                {"uri": "spotify:track:1234567890123456789012", "title": "One", "human_score": 99},
                {"spotify_id": "1234567890123456789012", "title": "Duplicate"},
                {"name": "No stable ID", "artist": "Unknown"},
            ]}), encoding="utf-8")
            candidates = load_candidate_identities(path)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(set(candidates[0]), {"uri", "title", "artist"})
        self.assertNotIn("human_score", candidates[0])

    def test_track_cache_requires_exact_recording_id(self):
        record = library_record("spotify:track:1234567890123456789012")
        record["identity"]["recording_mbid"] = "recording-1"
        cache = {
            "mbid:other": {"track_id": "mbid:other", "musicbrainz_genres": [{"tag": "country"}]},
            "mbid:recording-1": {"track_id": "mbid:recording-1", "musicbrainz_genres": [{"tag": "shoegaze"}]},
        }
        row = profile_for_record(record, cache)
        self.assertEqual(row["track_id"], "mbid:recording-1")

    def test_preview_excludes_whole_candidate_batch_and_never_claims_writes(self):
        references = []
        for i in range(12):
            uri = f"spotify:track:{i:022d}"
            references.append({
                "uri": uri, "title": f"Reference {i}", "artist": "Example",
                "dimensions": {
                    "genre": [{"value": "dream pop", "source_family": "musicbrainz",
                               "scope": "recording", "identity_confidence": "high"}],
                    "sound": [{"value": "hazy", "source_family": "discogs",
                               "scope": "recording", "identity_confidence": "high"}],
                    "energy": [{"value": 40, "source_family": "audio", "scope": "audio",
                                "identity_confidence": "high"}],
                    "mood": [{"value": "wistful", "source_family": "lastfm",
                              "scope": "recording", "identity_confidence": "high"}],
                    "theme": [{"value": "longing", "source_family": "lyrics",
                               "scope": "lyrics", "identity_confidence": "high"}],
                },
            })
        candidate_uri = "spotify:track:9999999999999999999999"
        targets = {
            f"target-{i}": {"name": f"Target {i}", "snapshot_id": f"snap-{i}",
                            "captured_at": "2026-11-02", "items": [{"uri": row["uri"]} for row in references]}
            for i in range(5)
        }
        records = {row["uri"]: library_record(row["uri"], row["title"]) for row in references}
        records[candidate_uri] = library_record(candidate_uri, "Candidate")
        result = build_preview([{"uri": candidate_uri, "title": "Candidate", "artist": "Example"}],
                               targets, records, {})
        self.assertTrue(result["heldout_batch_excluded_from_all_profiles"])
        self.assertEqual(result["targets"]["target-0"]["profile_track_count"], 12)
        self.assertFalse(result["human_ratings_read"])
        self.assertEqual(result["spotify_api_calls"], 0)
        self.assertEqual(result["playlist_writes"], 0)
        self.assertFalse(result["results"][0]["scores_by_target"]["Target 0"]["human_ratings_used"])


if __name__ == "__main__":
    unittest.main()

# FILE OVERVIEW
# Purpose: Synthetic integration tests for the read-only five-target playlist-fit preview.
# Scope: Strict Spotify identity parsing, exact cache joins, identity-only candidates and batch exclusion.
# Run: python -m unittest tests.test_playlist_fit_preview -v (from repository root).
