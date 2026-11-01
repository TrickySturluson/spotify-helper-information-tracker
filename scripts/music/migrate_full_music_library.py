#!/usr/bin/env python3
"""Full offline migration of stored tracks and accessible Spotify playlist snapshots."""
import argparse, json
from pathlib import Path
from music_library import MusicLibrary

ROOT = Path("assistant_data/music")
PLAYLISTS = Path("assistant_data/spotify/playlists")
LYRICS = Path("assistant_data/recommendations/lyric_features.json")

def load(path, fallback):
    try: return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError): return fallback

def collect_playlist_rows():
    rows, stats = [], {"snapshots": 0, "inaccessible": 0, "invalid": 0}
    for path in sorted(PLAYLISTS.glob("*.json")):
        snap = load(path, None)
        if not isinstance(snap, dict):
            stats["invalid"] += 1
            continue
        stats["snapshots"] += 1
        if snap.get("items_accessible") is False:
            stats["inaccessible"] += 1
            continue
        for item in snap.get("items") or []:
            if not isinstance(item, dict) or item.get("type") not in (None, "track"):
                continue
            title = item.get("name") or item.get("track")
            artists = item.get("artists") or []
            artist = artists[0] if artists else item.get("artist")
            sid = item.get("id") or item.get("uri")
            if not title or not artist or not sid:
                continue
            sid = str(sid).rsplit(":", 1)[-1]
            ext = item.get("external_ids") or {}
            rows.append({
                "track_id": "spotify:track:" + sid, "spotify_id": sid,
                "artist": artist, "track": title, "album": item.get("album") or "",
                "artist_spotify_id": (item.get("artist_ids") or [None])[0],
                "spotify_album_id": item.get("album_id"),
                "duration_ms": item.get("duration_ms"), "isrc": ext.get("isrc"),
                "playlist_sources": [snap.get("id")],
                "playlist_positions": [{"playlist_id": snap.get("id"), "position": item.get("position")}],
                "metadata_source": "stored Spotify playlist snapshot",
            })
    return rows, stats

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT / "library")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    profiles = load(ROOT / "track_profiles.json", {})
    artists = load(ROOT / "artist_profiles.json", {})
    albums = load(ROOT / "album_profiles.json", {})
    audio = load(ROOT / "audio_profiles.json", {})
    lyrics = load(LYRICS, [])
    if not isinstance(profiles, dict):
        raise SystemExit("Refusing: track_profiles.json is not an object")
    playlist_rows, snapshot_stats = collect_playlist_rows()
    # Preserve each profile row; the library resolver deduplicates only on
    # explicit recording IDs or exact stable Spotify IDs, never name alone.
    rows = list(profiles.values()) + playlist_rows
    existing_index = load(args.root / "library_index.json", {})
    existing_index = existing_index if isinstance(existing_index, dict) else {}
    report = {
        "existing_library_records": {
            "songs": len(existing_index.get("songs") or {}),
            "artists": len(existing_index.get("artists") or {}),
            "albums": len(existing_index.get("albums") or {}),
            "preservation": "existing indexed records and accumulated evidence are merged, not replaced",
        },
        "track_profile_rows": len(profiles), "playlist_snapshot_stats": snapshot_stats,
        "playlist_track_occurrences": len(playlist_rows),
        "unique_playlist_spotify_ids": len({r["spotify_id"] for r in playlist_rows}),
        "combined_input_rows": len(rows), "artist_profiles": len(artists),
        "album_profiles": len(albums),
        "audio_profiles": len(audio.get("tracks", audio)) if isinstance(audio, dict) else 0,
        "lyric_features": len(lyrics) if isinstance(lyrics, list) else 0,
        "provider_requests": 0, "spotify_playlist_writes": 0,
    }
    if args.dry_run:
        print(json.dumps({**report, "writes": 0}, indent=2))
        return
    result = MusicLibrary(args.root).put_catalogue(rows, artists, albums, audio, lyrics)
    report["migration_result"] = result
    report["library_audit"] = MusicLibrary(args.root).audit()
    if not report["library_audit"].get("ok"):
        report["status"] = "migration completed with library audit errors; inspect library_audit.errors"
    else:
        report["status"] = "migrated stored profiles and accessible playlist snapshots; library audit passed"
    report["limitations"] = [
        "Raw Last.fm scrobbles absent from track_profiles.json are not included.",
        "Inaccessible playlist snapshots are skipped and counted.",
        "No provider metadata is fetched; missing recording-level mood evidence stays unknown.",
    ]
    target = args.root / "migration_report.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(target)
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()

# FILE OVERVIEW
# Migrates every stored track-profile row and every track in accessible Spotify
# playlist snapshots into per-song records. No network calls or playlist writes.
# IDs are kept distinct unless a verified recording ID or Spotify ID matches.
# Mood fields are intentionally not fabricated: missing evidence remains unknown.
# Dry run: python compat/migrate_full_music_library.py --dry-run
# Full run: python compat/migrate_full_music_library.py
