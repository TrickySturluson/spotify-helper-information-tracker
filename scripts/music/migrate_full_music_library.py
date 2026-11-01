#!/usr/bin/env python3
"""Full offline migration of stored tracks and accessible Spotify playlist snapshots."""
import argparse, json, shutil, sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from scripts.music.music_library import MusicLibrary

ROOT = REPO_ROOT / "assistant_data/music"
PLAYLISTS = REPO_ROOT / "assistant_data/spotify/playlists"
LYRICS = REPO_ROOT / "assistant_data/recommendations/lyric_features.json"

def load(path, fallback):
    try: return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError): return fallback

def collect_playlist_rows():
    """Collect one row per Spotify recording and retain every playlist membership."""
    rows_by_id, stats = {}, {
        "snapshots": 0, "inaccessible": 0, "invalid": 0,
        "incomplete": 0, "incomplete_details": [], "playlist_track_occurrences": 0,
    }
    for path in sorted(PLAYLISTS.glob("*.json")):
        snap = load(path, None)
        if not isinstance(snap, dict):
            stats["invalid"] += 1
            continue
        stats["snapshots"] += 1
        if snap.get("items_accessible") is False:
            stats["inaccessible"] += 1
            continue
        items = snap.get("items")
        fetched = snap.get("item_count_fetched")
        reported = snap.get("total_items_reported")
        if (
            not isinstance(items, list)
            or not isinstance(fetched, int)
            or fetched != len(items)
            or (isinstance(reported, int) and reported != fetched)
        ):
            stats["incomplete"] += 1
            stats["incomplete_details"].append({
                "playlist_id": snap.get("id") or path.stem,
                "name": snap.get("name"),
                "reported": reported,
                "fetched": fetched,
                "actual_items": len(items) if isinstance(items, list) else None,
            })
            continue
        for item in items:
            if not isinstance(item, dict) or item.get("type") not in (None, "track"):
                continue
            if item.get("is_local"):
                continue
            title = item.get("name") or item.get("track")
            artists = item.get("artists") or []
            artist = artists[0] if artists else item.get("artist")
            sid = item.get("id") or item.get("uri")
            if not title or not artist or not sid:
                continue
            sid = str(sid).rsplit(":", 1)[-1]
            ext = item.get("external_ids") or {}
            row = rows_by_id.setdefault(sid, {
                "track_id": "spotify:track:" + sid,
                "spotify_id": sid,
                "artist": artist,
                "artists": list(artists),
                "album": item.get("album") or "",
                "artist_spotify_id": (item.get("artist_ids") or [None])[0],
                "spotify_album_id": item.get("album_id"),
                "duration_ms": item.get("duration_ms"),
                "isrc": ext.get("isrc"),
                "playlist_sources": [],
                "playlist_positions": [],
                "metadata_source": "stored Spotify playlist snapshots",
            })
            # Keep source metadata and all playlist memberships when the same
            # recording appears more than once. Do not let later duplicates
            # overwrite the earlier membership list.
            playlist_id = snap.get("id") or path.stem
            if playlist_id not in row["playlist_sources"]:
                row["playlist_sources"].append(playlist_id)
            row["playlist_positions"].append({
                "playlist_id": playlist_id,
                "playlist_name": snap.get("name"),
                "position": item.get("position"),
                "added_at": item.get("added_at"),
            })
            stats["playlist_track_occurrences"] += 1
    stats["unique_playlist_spotify_ids"] = len(rows_by_id)
    return list(rows_by_id.values()), stats

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT / "library")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-backup", action="store_true",
                        help="Skip the automatic pre-migration library backup (not recommended)")
    args = parser.parse_args()
    profiles = load(ROOT / "track_profiles.json", {})
    artists = load(ROOT / "artist_profiles.json", {})
    albums = load(ROOT / "album_profiles.json", {})
    audio = load(ROOT / "audio_profiles.json", {})
    lyrics = load(LYRICS, [])
    if not isinstance(profiles, dict):
        raise SystemExit("Refusing: track_profiles.json is not an object")
    playlist_rows, snapshot_stats = collect_playlist_rows()
    if snapshot_stats["incomplete"]:
        raise SystemExit(
            "Refusing to migrate: accessible playlist snapshots are incomplete. "
            + json.dumps(snapshot_stats["incomplete_details"][:10], ensure_ascii=False)
        )
    # Preserve every profile row and add one deduplicated row per Spotify ID.
    # The snapshot stats separately retain total playlist occurrences.
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
        "playlist_track_occurrences": snapshot_stats["playlist_track_occurrences"],
        "unique_playlist_spotify_ids": snapshot_stats["unique_playlist_spotify_ids"],
        "combined_input_rows": len(rows), "artist_profiles": len(artists),
        "album_profiles": len(albums),
        "audio_profiles": len(audio.get("tracks", audio)) if isinstance(audio, dict) else 0,
        "lyric_features": len(lyrics) if isinstance(lyrics, list) else 0,
        "provider_requests": 0, "spotify_playlist_writes": 0,
    }
    if args.dry_run:
        print(json.dumps({**report, "writes": 0}, indent=2))
        return
    backup_path = None
    if args.root.exists() and (args.root / "library_index.json").exists() and not args.no_backup:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        backup_path = args.root.with_name(args.root.name + ".backup-" + stamp)
        shutil.copytree(args.root, backup_path)
        report["backup_path"] = str(backup_path)
    result = MusicLibrary(args.root).put_catalogue(rows, artists, albums, audio, lyrics)
    report["migration_result"] = result
    report["library_audit"] = MusicLibrary(args.root).audit()
    if not report["library_audit"].get("ok"):
        report["status"] = "failed: post-migration Library audit errors"
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
    if not report["library_audit"].get("ok"):
        raise SystemExit(2)

if __name__ == "__main__":
    main()

# FILE OVERVIEW
# Migrates every stored track-profile row and every track in accessible Spotify
# playlist snapshots into per-song records. No network calls or playlist writes.
# IDs are kept distinct unless a verified recording ID or Spotify ID matches.
# Mood fields are intentionally not fabricated: missing evidence remains unknown.
# Dry run: python compat/migrate_full_music_library.py --dry-run
# Full run: python compat/migrate_full_music_library.py
