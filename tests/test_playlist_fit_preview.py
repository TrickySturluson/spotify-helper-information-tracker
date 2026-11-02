import json
import tempfile
import unittest
from pathlib import Path

from scripts.spotify.playlist_fit_preview import (
    build_preview, index_profiles_by_song, load_candidate_identities, profile_for_record, spotify_uri,
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

    def test_track_cache_joins_through_exact_library_aliases(self):
        canonical_id = "spotify:6v0a3jkb9ntudo0kmcj1xd"
        cache = {
            "track:source-1": {
                "track_id": "track:source-1", "lastfm_checked_at": "2026-10-01T00:00:00Z",
                "lastfm_tags": [{"tag": "rock"}],
            },
            "mbid:recording-1": {
                "track_id": "mbid:recording-1", "track_mbid": "recording-1",
                "lastfm_checked_at": "2026-10-02T00:00:00Z",
                "musicbrainz_genres": [{"tag": "shoegaze"}],
            },
            "track:unrelated": {
                "track_id": "track:unrelated", "artist": "Same Artist",
                "track": "Same Title", "lastfm_tags": [{"tag": "country"}],
            },
        }
        library_index = {
            "source_track_ids": {"track:source-1": canonical_id, "track:unrelated": "source:other"},
            "recording_mbids": {"recording-1": canonical_id},
            "spotify_ids": {},
        }
        indexed = index_profiles_by_song(cache, library_index)
        record = {"id": canonical_id, "identity": {"artist": "Same Artist", "title": "Same Title"}}
        row = profile_for_record(record, indexed)
        self.assertEqual(row["track_id"], "mbid:recording-1")
        self.assertIsNone(profile_for_record({"id": "source:other-2", "identity": record["identity"]}, indexed))


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
        self.assertEqual(result["status"], "read_only_preview_not_for_sorting")
        self.assertGreater(result["usable_target_profile_count"], 0)
        self.assertEqual(result["targets"]["target-0"]["profile_track_count"], 12)
        self.assertFalse(result["human_ratings_read"])
        self.assertEqual(result["spotify_api_calls"], 0)
        self.assertEqual(result["playlist_writes"], 0)
        self.assertFalse(result["results"][0]["scores_by_target"]["Target 0"]["human_ratings_used"])


    def test_zero_evidence_profiles_block_all_candidate_scores(self):
        candidates = [{"uri": "spotify:track:9999999999999999999999", "title": "Candidate", "artist": "Example"}]
        targets = {
            f"target-{i}": {"name": f"Target {i}", "snapshot_id": f"snap-{i}",
                            "captured_at": "2026-11-02",
                            "items": [{"uri": f"spotify:track:{j:022d}"} for j in range(8)]}
            for i in range(5)
        }
        records = {
            f"spotify:track:{j:022d}": {
                "id": f"spotify:{j:022d}",
                "identity": {"spotify_id": f"{j:022d}", "artist": "Example", "title": f"Reference {j}"},
                "confidence": {"identity": "high"}, "evidence": {}, "mood": {},
            }
            for j in range(8)
        }
        records[candidates[0]["uri"]] = {
            "id": candidates[0]["uri"],
            "identity": {"spotify_id": candidates[0]["uri"], "artist": "Example", "title": "Candidate"},
            "confidence": {"identity": "high"}, "evidence": {}, "mood": {},
        }
        result = build_preview(candidates, targets, records, {})
        self.assertEqual(result["status"], "blocked_insufficient_reference_evidence")
        self.assertEqual(result["usable_target_profile_count"], 0)
        self.assertTrue(result["block_reasons"])
        for score in result["results"][0]["scores_by_target"].values():
            self.assertIsNone(score["fit_score"])
            self.assertEqual(score["confidence"], "unknown")


if __name__ == "__main__":
    unittest.main()

# FILE OVERVIEW
# Purpose: Synthetic integration tests for the read-only five-target playlist-fit preview.
# Scope: Strict Spotify identity parsing, exact cache joins, identity-only candidates and batch exclusion.
# Run: python -m unittest tests.test_playlist_fit_preview -v (from repository root).
