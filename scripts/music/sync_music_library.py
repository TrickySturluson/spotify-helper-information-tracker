#!/usr/bin/env python3
"""Merge every stored enrichment export into the canonical per-recording library."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.music.music_library import MusicLibrary

MUSIC = ROOT / "assistant_data" / "music"
LYRICS = ROOT / "assistant_data" / "recommendations" / "lyric_features.json"


def read(path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return fallback


def lyric_rows(value):
    if isinstance(value, list):
        return [row for row in value if isinstance(row, dict)]
    if isinstance(value, dict):
        nested = value.get("tracks")
        if isinstance(nested, dict):
            return [row for row in nested.values() if isinstance(row, dict)]
        return [row for row in value.values() if isinstance(row, dict)]
    return []


def main():
    profiles = read(MUSIC / "track_profiles.json", {})
    artists = read(MUSIC / "artist_profiles.json", {})
    albums = read(MUSIC / "album_profiles.json", {})
    audio = read(MUSIC / "audio_profiles.json", {})
    lyrics = lyric_rows(read(LYRICS, []))
    if not isinstance(profiles, dict):
        raise SystemExit("Refusing to sync: track_profiles.json must be an object.")
    result = MusicLibrary().put_catalogue(
        list(profiles.values()), artists, albums, audio, lyrics
    )
    audit = MusicLibrary().audit()
    print(json.dumps({
        "sync_result": result,
        "audit": audit,
        "inputs": {
            "track_profiles": len(profiles),
            "artist_profiles": len(artists) if isinstance(artists, dict) else 0,
            "album_profiles": len(albums) if isinstance(albums, dict) else 0,
            "audio_profiles": len(audio.get("tracks", audio)) if isinstance(audio, dict) else 0,
            "lyric_features": len(lyrics),
        },
    }, indent=2))
    return 0 if audit.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())


# FILE OVERVIEW
# Purpose: Reconcile all durable metadata exports into the canonical per-recording library.
# Inputs: track_profiles, artist_profiles, album_profiles, audio_profiles and compact
#         lyric_features exports. Full lyric text is neither read nor stored.
# Behavior: Uses MusicLibrary.put_catalogue so identity safeguards and preservation
#           rules apply; ambiguous name matches are not promoted to verified IDs.
# Run: python scripts/music/sync_music_library.py
# Related: scripts/music/music_library.py; scripts/music/migrate_full_music_library.py.
