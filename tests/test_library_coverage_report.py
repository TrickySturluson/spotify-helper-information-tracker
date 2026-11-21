import json
import tempfile
import unittest
from pathlib import Path

from scripts.music.library_coverage_report import build_report


class LibraryCoverageReportTests(unittest.TestCase):
    def test_report_is_read_only_and_prioritizes_from_listening_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            song_dir = root / "songs" / "aa"
            song_dir.mkdir(parents=True)
            record = {
                "id": "song-a",
                "identity": {"artist": "Artist", "title": "Track", "spotify_id": None,
                    "recording_mbid": None, "isrc": None},
                "evidence": {"track_metadata": {"duration_ms": 180000,
                    "lastfm_status": "http_503", "retry_after": 123}},
                "listening_context": {"all_time_plays": 20, "recent_plays": 4},
                "mood": {"recording_level": {"moods": []}},
                "relations": {},
            }
            path = song_dir / "song.json"
            path.write_text(json.dumps(record), encoding="utf-8")
            report = build_report(root, limit=10)
            self.assertEqual(report["mode"], "read_only_no_provider_calls")
            self.assertEqual(report["counts"]["songs_seen"], 1)
            self.assertEqual(report["counts"]["missing_recording_mbid"], 1)
            self.assertEqual(report["counts"]["missing_duration"], 0)
            self.assertEqual(report["provider_outcomes"]["lastfm_transient_or_error"], 1)
            self.assertEqual(report["priority_queue"][0]["priority_score"], 32)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), record)

    def test_negative_provider_result_is_not_counted_as_transient_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "songs" / "aa" / "song.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({
                "id": "song-b", "identity": {"artist": "A", "title": "B"},
                "evidence": {"track_metadata": {"lastfm_status": "no_tags"}},
                "relations": {},
            }), encoding="utf-8")
            report = build_report(root)
            self.assertEqual(report["provider_outcomes"]["lastfm_negative_cached"], 1)
            self.assertNotIn("lastfm_transient_or_error", report["provider_outcomes"])

    def test_invalid_json_is_reported_without_crashing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "songs" / "aa" / "song.json"
            path.parent.mkdir(parents=True)
            path.write_text("{broken", encoding="utf-8")
            report = build_report(root)
            self.assertEqual(report["counts"]["invalid_song_records"], 1)
            self.assertEqual(report["errors"][0]["issue"], "invalid_or_unreadable_json")


if __name__ == "__main__":
    unittest.main()


# FILE OVERVIEW
# Purpose: Validate the read-only metadata coverage and provider-outcome planner.
# Coverage: Gap classification, transient-vs-negative provider outcomes, deterministic
#           listening-based priority, malformed record handling, and no file mutation.
# Run: python -m unittest tests.test_library_coverage_report -v
# Related: scripts/music/library_coverage_report.py; scripts/music/music_library.py.
