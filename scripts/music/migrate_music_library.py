#!/usr/bin/env python3
"""Local-only migration from aggregate profiles into The Library."""
import argparse
import json
from pathlib import Path
from music_library import MusicLibrary

ROOT = Path("assistant_data/music")
LYRICS = Path("assistant_data/recommendations/lyric_features.json")


def load(path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return fallback


def select_recent_track_rows(track_rows, recent_rows, limit):
    """Select a bounded, deduplicated recent batch without making provider calls."""
    if not isinstance(track_rows, dict) or not isinstance(recent_rows, list):
        return {}, {"selected": 0, "unmatched": 0, "duplicates": 0}
    by_mbid = {}
    by_track_id = {}
    for row in track_rows.values():
        if not isinstance(row, dict):
            continue
        if row.get("track_id"):
            by_track_id[str(row["track_id"]).casefold()] = row
        mbid = str(row.get("track_mbid") or row.get("recording_mbid") or "").strip().casefold()
        if mbid:
            current = by_mbid.get(mbid)
            score = sum(len(row.get(field) or []) for field in ("lastfm_tags", "musicbrainz_tags", "musicbrainz_genres"))
            current_score = sum(len(current.get(field) or []) for field in ("lastfm_tags", "musicbrainz_tags", "musicbrainz_genres")) if current else -1
            if score > current_score:
                by_mbid[mbid] = row

    selected = {}
    seen = set()
    unmatched = duplicates = 0
    for recent in recent_rows:
        if not isinstance(recent, dict):
            continue
        mbid = str(recent.get("track_mbid") or "").strip().casefold()
        track_id = str(recent.get("track_id") or "").strip().casefold()
        row = by_mbid.get(mbid) if mbid else None
        row = row or by_track_id.get(track_id)
        if not row:
            unmatched += 1
            continue
        identity = mbid or str(row.get("track_id") or track_id).casefold()
        if identity in seen:
            duplicates += 1
            continue
        seen.add(identity)
        enriched = dict(row)
        enriched["listening_context"] = {
            "source": "Last.fm scrobble archive",
            "window_days": recent.get("window_days"),
            "recent_plays": recent.get("recent_plays"),
            "all_time_plays": recent.get("all_time_plays"),
        }
        selected[str(row.get("track_id") or identity)] = enriched
        if len(selected) >= limit:
            break
    return selected, {"selected": len(selected), "unmatched": unmatched, "duplicates": duplicates}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT / "library")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--recent-limit", type=int, default=0,
        help="migrate at most N unique songs from recent_top_tracks.json (no network calls)",
    )
    args = parser.parse_args()
    if args.recent_limit < 0:
        parser.error("--recent-limit must be zero or greater")

    tracks = load(ROOT / "track_profiles.json", {})
    selection = {"selected": len(tracks) if isinstance(tracks, dict) else 0, "unmatched": 0, "duplicates": 0}
    if args.recent_limit:
        recent = load(ROOT / "recent_top_tracks.json", {})
        recent_rows = recent.get("tracks", []) if isinstance(recent, dict) else []
        tracks, selection = select_recent_track_rows(tracks, recent_rows, args.recent_limit)

    artists = load(ROOT / "artist_profiles.json", {})
    albums = load(ROOT / "album_profiles.json", {})
    audio = load(ROOT / "audio_profiles.json", {})
    lyrics = load(LYRICS, [])
    if args.dry_run:
        print(json.dumps({
            "track_profiles_selected": len(tracks) if isinstance(tracks, dict) else 0,
            "artist_profiles": len(artists) if isinstance(artists, dict) else 0,
            "album_profiles": len(albums) if isinstance(albums, dict) else 0,
            "audio_profiles": len(audio.get("tracks", audio)) if isinstance(audio, dict) else 0,
            "lyric_features": len(lyrics) if isinstance(lyrics, list) else 0,
            "selection": selection,
            "writes": 0,
            "provider_requests": 0,
        }, indent=2))
        return
    result = MusicLibrary(args.root).put_catalogue(tracks, artists, albums, audio, lyrics)
    result["selection"] = selection
    result["provider_requests"] = 0
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()


# FILE OVERVIEW
# - Reads existing profile exports and performs a no-network migration.
# - Supports a bounded, deduplicated recent-song batch for safe staged rollout.
# - Writes canonical artist, album, and song records plus a compact resolver index.
# - Leaves aggregate files untouched for compatibility and rollback.
