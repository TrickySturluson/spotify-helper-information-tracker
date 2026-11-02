"""Offline, read-only evaluation against the user's broad playlist references.

Run: python -m unittest tests.test_spotify_playlist_reference_evaluation -v

This test reads checked-in playlist snapshots and canonical Library evidence. It
never authenticates to Spotify, calls metadata providers, writes Library records,
or applies a playlist change. Hell's full catalogue is scored; a deterministic
192-track spread is used for the expensive ordering comparison.
"""
import json
import unittest
from collections import Counter
from pathlib import Path
from time import perf_counter

import spotify_playlist_sequencer as sequencer


ROOT = Path(__file__).resolve().parents[1]
REFERENCES = {
    "All Time": {
        "id": "6ZsqAs5OnRMVudhfB2QzTx",
        "role": "broad_taste_reference",
        "sample_limit": None,
    },
    "Hell": {
        "id": "3XQz9AyZP6ADcr9i8iBaVx",
        "role": "broad_taste_reference",
        "sample_limit": 192,
    },
}


def _load_profiles(items):
    """Mirror the sequencer's Library-first, per-record legacy fallback."""
    library = sequencer.load_library_profiles(items)
    if library is None:
        artists = sequencer.index_artists(sequencer.read_json(sequencer.ARTIST_PROFILES, {}))
        tracks = sequencer.index_tracks(sequencer.read_json(sequencer.TRACK_PROFILES, {}))
        tracks = sequencer.merge_lyric_features(
            tracks, sequencer.read_json(sequencer.LYRIC_FEATURES, [])
        )
        audio_rows = sequencer.read_json(sequencer.AUDIO_PROFILES, {})
        audio = sequencer.index_audio_profiles(
            audio_rows.get("tracks", audio_rows) if isinstance(audio_rows, dict) else {}
        )
        album_rows = sequencer.read_json(sequencer.ALBUM_PROFILES, {})
        albums = {
            (sequencer.norm(row.get("artist")), sequencer.norm(row.get("album"))): row
            for row in album_rows.values()
            if isinstance(row, dict) and row.get("artist") and row.get("album")
        }
        return artists, tracks, audio, albums

    artists, tracks, audio, albums = library
    legacy = sequencer.index_tracks(sequencer.read_json(sequencer.TRACK_PROFILES, {}))
    for item in items:
        names = item.get("artists") or ([item.get("artist")] if item.get("artist") else [])
        key = (sequencer.norm(names[0]) if names else "",
               sequencer.norm(item.get("name") or item.get("track")))
        if key not in tracks and key in legacy:
            tracks[key] = legacy[key]
    return artists, tracks, audio, albums


def _spread_sample(items, limit):
    if limit is None or len(items) <= limit:
        return list(items)
    if limit <= 1:
        return [items[0]]
    indexes = sorted({round(i * (len(items) - 1) / (limit - 1)) for i in range(limit)})
    return [items[index] for index in indexes]


def _score_in_original_order(items, profiles):
    artists, tracks, audio, albums = profiles
    rows = []
    for index, item in enumerate(items):
        rows.append({
            "original_index": index,
            "item": item,
            **sequencer.score_track(item, artists, tracks, audio, albums),
        })
    return rows


def _coverage(rows, profiles):
    _, tracks, _, _ = profiles
    evidence = sequencer.evidence_coverage_summary(rows)
    total = len(rows)
    theme = sum(bool(row.get("theme_groups")) for row in rows)
    genre = sum(bool(row.get("genre_groups")) for row in rows)
    mood = sum(row.get("mood_confidence") in {"medium", "high"} for row in rows)
    return {
        "profile_match_count": sum(
            (sequencer.norm(row.get("artist")), sequencer.norm(row.get("track"))) in tracks
            for row in rows
        ),
        "profile_match_rate": round(sum(
            (sequencer.norm(row.get("artist")), sequencer.norm(row.get("track"))) in tracks
            for row in rows
        ) / max(1, total), 4),
        "track_mood_supported": mood,
        "track_mood_supported_rate": round(mood / max(1, total), 4),
        "genre_tagged": genre,
        "genre_tagged_rate": round(genre / max(1, total), 4),
        "theme_tagged": theme,
        "theme_tagged_rate": round(theme / max(1, total), 4),
        "acoustic_confidence": evidence["acoustic_confidence"],
        "semantic_confidence": evidence["semantic_confidence"],
        "mood_confidence": evidence["mood_confidence"],
        "mood_sources": evidence["mood_source_coverage"],
        "tempo_sources": evidence["tempo_sources"],
    }


def _transition_counts(rows):
    summary = sequencer.transition_summary(rows)
    return {
        "gentle": summary["gentle"],
        "moderate": summary["moderate"],
        "supported_potential_jumps": summary["potential_jumps"],
        "provisional": summary["provisional"],
        "uncertain": summary["uncertain"],
        "limited_evidence": summary["limited_evidence"],
        "largest_supported_jumps": sorted(
            [
                {
                    "cost": pair["cost"],
                    "energy_gap": pair["energy_gap"],
                    "tempo_relationship": pair["tempo_relationship"],
                    "label": pair["label"],
                    "reasons": pair["reasons"],
                }
                for pair in summary["pairs"]
                if pair["confidence"] == "supported"
            ],
            key=lambda row: row["cost"],
            reverse=True,
        )[:5],
    }


class PlaylistReferenceEvaluationTests(unittest.TestCase):
    def test_broad_references_have_complete_snapshots_and_read_only_sort_evaluation(self):
        reports = []
        for name, config in REFERENCES.items():
            with self.subTest(playlist=name):
                started = perf_counter()
                snapshot_path = ROOT / "assistant_data" / "spotify" / "playlists" / f"{config['id']}.json"
                snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
                self.assertEqual(snapshot.get("id"), config["id"])
                self.assertEqual(snapshot.get("name"), name)
                self.assertTrue(snapshot.get("items_accessible"))
                self.assertEqual(snapshot.get("item_count_fetched"), snapshot.get("total_items_reported"))
                items = snapshot.get("items") or []
                self.assertEqual(len(items), snapshot.get("item_count_fetched"))
                self.assertTrue(items)
                self.assertTrue(all(row.get("uri", "").startswith("spotify:track:") for row in items))

                profiles = _load_profiles(items)
                original = _score_in_original_order(items, profiles)
                sample = _spread_sample(items, config["sample_limit"])
                sorted_rows = sequencer.sequence_tracks(
                    sample, profiles[0], profiles[1],
                    journey="rising", peak_position=85, peak_shape="gradual",
                    audio_profiles=profiles[2], album_profiles=profiles[3],
                )
                self.assertEqual(
                    Counter(row["item"]["uri"] for row in sorted_rows),
                    Counter(row["uri"] for row in sample),
                )

                baseline_items = sample
                baseline_rows = _score_in_original_order(baseline_items, profiles)
                report = {
                    "playlist": name,
                    "playlist_id": config["id"],
                    "role": config["role"],
                    "snapshot_id": snapshot.get("snapshot_id"),
                    "captured_at": snapshot.get("captured_at"),
                    "reported_items": snapshot.get("total_items_reported"),
                    "fetched_items": len(items),
                    "ordering_sample_size": len(sample),
                    "ordering_sample_method": "full playlist" if len(sample) == len(items) else "deterministic evenly-spaced sample",
                    "profile_coverage_full_catalogue": _coverage(original, profiles),
                    "baseline_transitions_sample": _transition_counts(baseline_rows),
                    "sequenced_transitions_sample": _transition_counts(sorted_rows),
                    "top_track_themes_in_sample": Counter(
                        theme for row in sorted_rows for theme in (row.get("theme_groups") or [])
                    ).most_common(12),
                    "top_genres_in_sample": Counter(
                        genre for row in sorted_rows for genre in (row.get("genre_groups") or [])
                    ).most_common(12),
                    "elapsed_seconds": round(perf_counter() - started, 3),
                    "playlist_write_count": 0,
                    "provider_request_count": 0,
                    "library_write_count": 0,
                }
                reports.append(report)
        print("OFFLINE_PLAYLIST_REFERENCE_EVALUATION=" + json.dumps(reports, ensure_ascii=False, sort_keys=True))
        self.assertEqual(len(reports), len(REFERENCES))
        self.assertTrue(all(row["playlist_write_count"] == 0 for row in reports))
        self.assertTrue(all(row["provider_request_count"] == 0 for row in reports))
        self.assertTrue(all(row["library_write_count"] == 0 for row in reports))


if __name__ == "__main__":
    unittest.main()
