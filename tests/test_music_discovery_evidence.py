import tempfile
import unittest
from pathlib import Path

from scripts.music.music_library import MusicLibrary, read_json


class MusicDiscoveryEvidenceTests(unittest.TestCase):
    def test_recommendation_provenance_does_not_become_listening_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            library = MusicLibrary(root)
            row = {
                "artist": "Example Artist",
                "track": "Suggested Song",
                "track_id": "discovery:spotify_id:abc123",
                "spotify_id": "abc123",
                "discovery_context": {
                    "kind": "recommendation_or_discovery",
                    "discovery_sources": [{"source": "SHIT recommendation", "context": "seed: Example Artist"}],
                    "observed_user_action": "unknown",
                    "listening_evidence": "not_inferred_from_discovery",
                },
            }
            result = library.put_catalogue([row])
            self.assertGreaterEqual(result.get("songs", 0), 1)
            index = read_json(root / "library_index.json")
            song_id = index["spotify_ids"]["abc123"]
            entry = index["songs"][song_id]
            song = read_json(root / entry["path"])
            self.assertEqual(song["discovery_context"]["kind"], "recommendation_or_discovery")
            self.assertEqual(song["discovery_context"]["listening_evidence"], "not_inferred_from_discovery")
            self.assertNotIn("listening_context", song)
            self.assertNotIn("discovery_context", song["evidence"]["track_metadata"])

    def test_existing_listening_context_is_preserved_when_discovery_is_added(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            library = MusicLibrary(root)
            row = {
                "artist": "Example Artist",
                "track": "Known Scrobbled Song",
                "track_id": "track:existing",
                "listening_context": {
                    "source": "Last.fm scrobble archive",
                    "recent_plays": 4,
                    "all_time_plays": 12,
                },
                "discovery_context": {
                    "kind": "recommendation_or_discovery",
                    "discovery_sources": [{"source": "related-track discovery"}],
                    "observed_user_action": "accepted",
                    "listening_evidence": "not_inferred_from_discovery",
                },
            }
            library.put_catalogue([row])
            index = read_json(root / "library_index.json")
            entry = next(iter(index["songs"].values()))
            song = read_json(root / entry["path"])
            self.assertEqual(song["listening_context"]["all_time_plays"], 12)
            self.assertEqual(song["discovery_context"]["observed_user_action"], "accepted")
            self.assertEqual(song["discovery_context"]["listening_evidence"], "not_inferred_from_discovery")


if __name__ == "__main__":
    unittest.main()


# FILE OVERVIEW
# Purpose: Guard the distinction between recommendation/discovery provenance and listening facts.
# Tests: Discovery evidence is stored independently, does not fabricate scrobbles, and preserves
#        existing Last.fm listening context when a discovered song is already known.
# Related: scripts/music/record_discovery.py; scripts/music/music_library.py.
