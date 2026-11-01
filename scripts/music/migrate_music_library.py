#!/usr/bin/env python3
"""Local-only migration from aggregate profiles into The Library."""
import argparse
import json
from pathlib import Path
from music_library import MusicLibrary, select_recent_track_rows

ROOT = Path("assistant_data/music")
LYRICS = Path("assistant_data/recommendations/lyric_features.json")


def load(path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return fallback


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
        tracks, selection = select_recent_track_rows(tracks, recent_rows, args.recent_limit, window_days=recent.get('window_days'))

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
