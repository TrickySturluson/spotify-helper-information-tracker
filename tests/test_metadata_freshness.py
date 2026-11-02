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
                    "lastfm_checked_at": "2024-01-01T00:00:00Z",
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

    def test_profile_caches_supply_artist_and_album_freshness(self):
        with tempfile.TemporaryDirectory() as directory:
            music = Path(directory) / "music"
            root = music / "library"
            (root / "artists" / "ar" / "artist-one").mkdir(parents=True)
            (root / "albums" / "al" / "album-one").mkdir(parents=True)
            (root / "artists" / "ar" / "artist-one" / "artist.json").write_text(json.dumps({
                "id": "artist-one", "artist": "Artist",
                "evidence": {"source": "Last.fm scrobble archive"},
            }), encoding="utf-8")
            (root / "albums" / "al" / "album-one" / "album.json").write_text(json.dumps({
                "id": "album-one", "album": "Album", "artist": "Artist",
                "evidence": {"source": "Last.fm scrobble archive"},
            }), encoding="utf-8")
            (music / "artist_profiles.json").write_text(json.dumps({
                "artist-one": {"artist_id": "artist-one", "artist": "Artist",
                               "source": "Last.fm artist.getTopTags", "status": "matched",
                               "checked_at": "2025-01-01T00:00:00Z", "retry_after": 0}
            }), encoding="utf-8")
            (music / "album_profiles.json").write_text(json.dumps({
                "album-one": {"album_id": "album-one", "album": "Album", "artist": "Artist",
                              "source": "Last.fm album.getInfo", "lastfm_info_status": "matched",
                              "lastfm_info_checked_at": "2025-01-01T00:00:00Z",
                              "lastfm_info_retry_after": 0}
            }), encoding="utf-8")
            now = datetime(2026, 11, 2, tzinfo=timezone.utc)
            report = build_plan(root, limit=10, now=now)
            selected = {(row["entity_type"], row["field_family"], row["provider"]) for row in report["selected"]}
            self.assertIn(("artist", "artist_profile", "lastfm"), selected)
            self.assertIn(("album", "album_profile", "lastfm"), selected)

    def test_track_profile_cache_resolves_through_recording_alias(self):
        with tempfile.TemporaryDirectory() as directory:
            music = Path(directory) / "music"
            root = music / "library"
            song_path = root / "songs" / "so" / "song-one" / "song.json"
            song_path.parent.mkdir(parents=True)
            (root / "artists").mkdir()
            (root / "albums").mkdir()
            song_path.write_text(json.dumps({
                "id": "song-one", "identity": {"artist": "Artist", "title": "Song",
                    "recording_mbid": "12345678-1234-1234-1234-123456789abc"},
                "evidence": {"track_metadata": {}},
            }), encoding="utf-8")
            (root / "library_index.json").write_text(json.dumps({
                "recording_mbids": {"12345678-1234-1234-1234-123456789abc": "song-one"},
                "source_track_ids": {}, "spotify_ids": {},
            }), encoding="utf-8")
            (music / "track_profiles.json").write_text(json.dumps({
                "mbid:12345678-1234-1234-1234-123456789abc": {
                    "track_id": "mbid:12345678-1234-1234-1234-123456789abc",
                    "track_mbid": "12345678-1234-1234-1234-123456789abc",
                    "lastfm_checked_at": "2025-01-01T00:00:00Z",
                    "lastfm_status": "no_tags",
                    "musicbrainz_checked_at": "2026-10-30T00:00:00Z",
                    "musicbrainz_status": "matched",
                }
            }), encoding="utf-8")
            report = build_plan(root, limit=10, now=datetime(2026, 11, 2, tzinfo=timezone.utc))
            self.assertTrue(any(row["song_id"] == "song-one" and row["field_family"] == "track_tags"
                                and row["provider"] == "lastfm" for row in report["selected"]))

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
            self.assertGreater(report["counts"]["no_data"], 0)
            self.assertEqual(report["provider_requests"], 0)

    def test_missing_timestamp_counts_only_data_bearing_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_song(root, "empty-song", {
                "id": "empty-song", "identity": {"artist": "Artist", "title": "Song"},
                "evidence": {"track_metadata": {}},
            })
            report = build_plan(root, limit=10, now=datetime(2026, 11, 2, tzinfo=timezone.utc))
            self.assertEqual(report["counts"]["missing_timestamp"], 0)
            self.assertGreater(report["counts"]["no_data"], 0)
            self.assertEqual(report["baseline_candidate_count"], 0)

    def test_unknown_age_baseline_sample_rotates_deterministically_by_week(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for song_id in ("song-one", "song-two"):
                self.write_song(root, song_id, {
                    "id": song_id,
                    "identity": {"artist": "Artist", "title": song_id},
                    "evidence": {"track_metadata": {
                        "lastfm_tags": [{"tag": "shoegaze"}],
                        "lastfm_status": "matched",
                    }},
                })
            week_one = datetime(2026, 11, 2, tzinfo=timezone.utc)
            week_two = datetime(2026, 11, 9, tzinfo=timezone.utc)
            first = build_plan(root, limit=1, now=week_one, include_unknown_age=True)
            repeat = build_plan(root, limit=1, now=week_one, include_unknown_age=True)
            next_week = build_plan(root, limit=1, now=week_two, include_unknown_age=True)
            self.assertEqual(first["due_task_count"], 0)
            self.assertEqual(first["baseline_candidate_count"], 2)
            self.assertEqual(first["selected_baseline_count"], 1)
            self.assertEqual(first["selected"], repeat["selected"])
            self.assertNotEqual(first["selected"][0]["task_key"], next_week["selected"][0]["task_key"])
            self.assertEqual(first["selected"][0]["status"], "baseline_required")
            self.assertEqual(first["provider_requests"], 0)
            self.assertEqual(first["writes"], 0)

    def test_known_stale_observation_deduplicates_unknown_age_baseline(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_song(root, "duplicate-song", {
                "id": "duplicate-song",
                "identity": {"artist": "Artist", "title": "Duplicate Song"},
                "evidence": {
                    "track_metadata": {
                        "lastfm_tags": [{"tag": "shoegaze"}],
                        "lastfm_status": "matched",
                    }
                },
                "freshness": {"observations": {
                    "track_tags": {
                        "provider": "lastfm",
                        "observed_at": "2025-01-01T00:00:00Z",
                    }
                }},
            })
            report = build_plan(
                root, limit=25, now=datetime(2026, 11, 2, tzinfo=timezone.utc),
                include_unknown_age=True,
            )
            self.assertEqual(report["due_task_count"], 1)
            self.assertEqual(report["baseline_candidate_count"], 0)
            self.assertEqual(report["selected_task_count"], 1)
            self.assertEqual(report["selected_due_count"], 1)
            self.assertEqual(report["selected_baseline_count"], 0)
            self.assertEqual(report["selected"][0]["status"], "stale")

    def test_due_tasks_take_priority_and_baseline_fills_only_remaining_slots(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_song(root, "due-song", {
                "id": "due-song",
                "identity": {"artist": "Artist", "title": "Due Song",
                             "spotify_id": "abcdefghijklmnopqrstuv"},
                "evidence": {"spotify_playability": {"latest_by_market": {
                    "FROM_TOKEN": {
                        "checked_at": "2025-01-01T00:00:00Z",
                        "status": "playable",
                        "is_playable": True,
                    }
                }}},
            })
            self.write_song(root, "baseline-song", {
                "id": "baseline-song",
                "identity": {"artist": "Artist", "title": "Baseline Song"},
                "evidence": {"track_metadata": {
                    "lastfm_tags": [{"tag": "shoegaze"}],
                    "lastfm_status": "matched",
                }},
            })
            report = build_plan(
                root, limit=2, market="from_token",
                now=datetime(2026, 11, 2, tzinfo=timezone.utc),
                include_unknown_age=True,
            )
            self.assertEqual(report["due_task_count"], 1)
            self.assertEqual(report["baseline_candidate_count"], 1)
            self.assertEqual(report["selected_due_count"], 1)
            self.assertEqual(report["selected_baseline_count"], 1)
            self.assertEqual(report["selected_task_count"], 2)
            self.assertEqual(report["selected"][0]["status"], "stale")
            self.assertEqual(report["selected"][1]["status"], "baseline_required")
            self.assertEqual(report["provider_requests"], 0)
            self.assertEqual(report["writes"], 0)

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
