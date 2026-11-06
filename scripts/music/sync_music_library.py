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
DISCOVERY = ROOT / "assistant_data" / "recommendations" / "discovery_candidates.json"


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
    candidates = lyric_rows(read(DISCOVERY, []))
    if not isinstance(profiles, dict):
        raise SystemExit("Refusing to sync: track_profiles.json must be an object.")
    # Discovery candidates are metadata intake, not listening events. Merge by
    # exact Spotify ID where possible; otherwise preserve a distinct candidate row.
    rows = list(profiles.values())
    by_spotify_id = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        sid = str(row.get("spotify_id") or row.get("spotify_track_id") or "").strip()
        if not sid and str(row.get("track_id") or "").startswith("spotify:track:"):
            sid = row["track_id"].rsplit(":", 1)[-1]
        if sid:
            by_spotify_id[sid] = row
    valid_candidates = 0
    for candidate in candidates:
        uri = str(candidate.get("spotify_uri") or candidate.get("uri") or "").strip()
        sid = str(candidate.get("spotify_id") or (uri.rsplit(":", 1)[-1] if uri.startswith("spotify:track:") else "")).strip()
        if not sid or not candidate.get("artist") or not candidate.get("track"):
            continue
        valid_candidates += 1
        evidence = candidate.get("discovery_evidence") or []
        existing = by_spotify_id.get(sid)
        if existing is not None:
            prior = existing.get("discovery_evidence") or []
            merged = {json.dumps(item, sort_keys=True): item for item in prior + evidence}
            existing["discovery_evidence"] = list(merged.values())
            continue
        row = {
            "track_id": "spotify:track:" + sid,
            "spotify_id": sid,
            "artist": candidate["artist"],
            "track": candidate["track"],
            "album": candidate.get("album"),
            "duration_ms": candidate.get("duration_ms"),
            "isrc": candidate.get("isrc"),
            "track_mbid": candidate.get("track_mbid"),
            "discovery_evidence": evidence,
            "discovery_only": True,
        }
        rows.append(row)
        by_spotify_id[sid] = row
    result = MusicLibrary().put_catalogue(rows, artists, albums, audio, lyrics)
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
            "discovery_candidates": len(candidates),
            "valid_discovery_candidates": valid_candidates,
        },
    }, indent=2))
    return 0 if audit.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())


# FILE OVERVIEW
# Purpose: Reconcile all durable metadata exports into the canonical per-recording library.
# Inputs: track_profiles, artist_profiles, album_profiles, audio_profiles and compact
#         lyric_features exports. Full lyric text is neither read nor stored.
# Outputs: Merges canonical song/artist/album records and discovery evidence; writes the
#          resolver index and prints a post-sync audit report.
# Behavior: Uses MusicLibrary.put_catalogue so identity safeguards and preservation
#           rules apply; ambiguous name matches are not promoted to verified IDs.
# Safety: Repository writer; constructing MusicLibrary may rebuild an incomplete derived index.
# Run: python scripts/music/sync_music_library.py
# Related: scripts/music/music_library.py; scripts/music/migrate_full_music_library.py.
