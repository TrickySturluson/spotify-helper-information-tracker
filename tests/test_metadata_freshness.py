import json
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

from scripts.music.metadata_freshness import build_plan


class MetadataFreshnessTests(unittest.TestCase):
    def write_song(self, root, song_id, payload):
        path = root / "songs" / song_id[:2] / song_id / "song.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_market_scoped_playability_and_stale_field_observations_are_planned(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            now = datetime(2026, 11, 2, tzinfo=timezone.utc)
            self.write_song(root, "song-one", {
                "id": "song-one",
                "identity": {"artist": "Artist", "title": "Song", "spotify_id": "abcdefghijklmnopqrstuv"},
                "evidence": {"spotify_playability": {"latest_by_market": {
                    "US": {"checked_at": "2026-01-01T00:00:00Z", "status": "playable"},
                    "GB": {"checked_at": "2026-10-01T00:00:00Z", "status": "playable"},
                }}},
                "freshness": {"observations": {
                    "track_tags": {"provider": "lastfm", "observed_at": "2025-01-01T00:00:00Z"},
                    "album_profile": {"provider": "lastfm", "observed_at": "2026-10-01T00:00:00Z"},
                    "duration": {"provider": "musicbrainz", "observed_at": "2025-01-01T00:00:00Z",
                                 "next_check_after": "2027-01-01T00:00:00Z"},
                }},
            })
            report = build_plan(root, limit=10, market="US", now=now)
            selected = {(row["field_family"], row["provider"], row["market"]) for row in report["selected"]}
            self.assertIn(("spotify_playability", "spotify", "US"), selected)
            self.assertIn(("track_tags", "lastfm", None), selected)
            self.assertNotIn(("album_profile", "lastfm", None), selected)
            self.assertNotIn(("duration", "musicbrainz", None), selected)
            self.assertEqual(report["provider_requests"], 0)
            self.assertEqual(report["writes"], 0)

    def test_existing_track_metadata_timestamps_and_provider_sources_are_used(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            now = datetime(2026, 11, 2, tzinfo=timezone.utc)
            self.write_song(root, "song-three", {
                "id": "song-three",
                "identity": {"artist": "Artist", "title": "Song"},
                "evidence": {"track_metadata": {
                    "duration_ms": 210000,
                    "duration_source": "Last.fm track.getInfo",
                    "lastfm_checked_at": "2025-01-01T00:00:00Z",
                    "lastfm_status": "no_tags",
                    "musicbrainz_checked_at": "2026-10-30T00:00:00Z",
                    "musicbrainz_status": "matched",
                }},
            })
            report = build_plan(root, limit=10, now=now)
            selected = {(row["field_family"], row["provider"]) for row in report["selected"]}
            self.assertIn(("track_tags", "lastfm"), selected)
            self.assertIn(("duration", "lastfm"), selected)
            self.assertNotIn(("track_tags", "musicbrainz"), selected)

    def test_relative_provider_retry_cooldown_blocks_stale_field(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            now = datetime(2026, 11, 2, tzinfo=timezone.utc)
            observed = (now - timedelta(hours=1)).isoformat()
            self.write_song(root, "song-cooldown", {
                "id": "song-cooldown",
                "identity": {"artist": "Artist", "title": "Song"},
                "evidence": {"track_metadata": {
                    "duration_ms": 200000,
                    "duration_source": "Last.fm track.getInfo",
                    "lastfm_checked_at": observed,
                    "lastfm_status": "no_tags",
                    "lastfm_retry_after": 7200,
                }},
            })
            report = build_plan(root, limit=10, now=now)
            self.assertFalse(any(row["provider"] == "lastfm" for row in report["selected"]))
            self.assertGreaterEqual(report["counts"]["cooldown"], 2)

    def test_source_stamped_artist_and_album_profiles_are_scheduled(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            now = datetime(2026, 11, 2, tzinfo=timezone.utc)
            artist = root / "artists" / "ar" / "artist-one" / "artist.json"
            artist.parent.mkdir(parents=True)
            artist.write_text(json.dumps({
                "id": "artist-one", "artist": "Artist",
                "evidence": {"source": "Last.fm artist.getTopTags", "checked_at": "2025-01-01T00:00:00Z"},
            }), encoding="utf-8")
            album = root / "albums" / "al" / "album-one" / "album.json"
            album.parent.mkdir(parents=True)
            album.write_text(json.dumps({
                "id": "album-one", "album": "Album", "artist": "Artist",
                "evidence": {"source": "Last.fm album.getInfo", "checked_at": "2025-01-01T00:00:00Z"},
            }), encoding="utf-8")
            report = build_plan(root, limit=10, now=now)
            selected = {(row["entity_type"], row["field_family"], row["provider"]) for row in report["selected"]}
            self.assertIn(("artist", "artist_profile", "lastfm"), selected)
            self.assertIn(("album", "album_profile", "lastfm"), selected)

    def test_unknown_market_is_not_treated_as_fresh_and_missing_timestamps_are_not_fetched(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_song(root, "song-two", {
                "id": "song-two",
                "identity": {"artist": "Artist", "title": "Song", "spotify_id": "abcdefghijklmnopqrstuv"},
                "evidence": {"spotify_playability": {"latest_by_market": {
                    "UNKNOWN": {"checked_at": "2026-10-30T00:00:00Z", "status": "unknown"}
                }}},
                "last_modified": "2026-11-01T00:00:00Z",
            })
            report = build_plan(root, market="from_token", now=datetime(2026, 11, 2, tzinfo=timezone.utc))
            self.assertEqual(report["selected"][0]["status"], "missing_observation")
            self.assertEqual(report["selected"][0]["market"], "from_token")
            self.assertGreater(report["counts"]["missing_timestamp"], 0)
            self.assertEqual(report["provider_requests"], 0)

    def test_planning_is_deterministic_bounded_and_does_not_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for number in range(5):
                self.write_song(root, f"song-{number}", {
                    "id": f"song-{number}",
                    "identity": {"artist": "Artist", "title": f"Song {number}",
                                 "spotify_id": f"{number:022d}"},
                })
            before = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            now = datetime(2026, 11, 2, tzinfo=timezone.utc)
            first = build_plan(root, limit=2, now=now)
            second = build_plan(root, limit=2, now=now)
            after = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            self.assertEqual(first["selected"], second["selected"])
            self.assertEqual(first["selected_task_count"], 2)
            self.assertEqual(first["due_task_count"], 5)
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()


# FILE OVERVIEW
# Purpose: Tests for the read-only field-level freshness planner.
# Scope: Market-specific playability, stale/fresh fields, cooldowns, unknown timestamps,
#        deterministic bounded selection, and no-write/no-network behavior.
# Run: python -m unittest tests.test_metadata_freshness -v
