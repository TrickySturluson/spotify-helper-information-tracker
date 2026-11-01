#!/usr/bin/env python3
"""Local-only migration from aggregate profile JSON to the normalized music library."""
import argparse
import json
from pathlib import Path
from music_library import MusicLibrary

ROOT = Path("assistant_data/music")
LYRICS = Path("assistant_data/recommendations/lyric_features.json")

def load(path, fallback):
    try: return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError): return fallback

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT / "music_library")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    tracks = load(ROOT / "track_profiles.json", {})
    artists = load(ROOT / "artist_profiles.json", {})
    albums = load(ROOT / "album_profiles.json", {})
    audio = load(ROOT / "audio_profiles.json", {})
    lyrics = load(LYRICS, [])
    if args.dry_run:
        print(json.dumps({"track_profiles": len(tracks), "artist_profiles": len(artists), "album_profiles": len(albums), "audio_profiles": len(audio), "lyric_features": len(lyrics)}, indent=2))
        return
    print(json.dumps(MusicLibrary(args.root).put_catalogue(tracks, artists, albums, audio, lyrics), indent=2))

if __name__ == "__main__":
    main()

# FILE OVERVIEW
# - Reads existing profile exports and performs a no-network migration.
# - Writes canonical individual records and a compact resolver index.
# - Leaves aggregate files untouched for compatibility and rollback.
