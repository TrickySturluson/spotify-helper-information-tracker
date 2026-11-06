#!/usr/bin/env python3
"""Resumable, local-only migration into SHIT's canonical per-recording Library.

Run through the project launcher:
  python shit.py migration status
  python shit.py migration preview
  python shit.py migration run
  python shit.py migration resume
  python shit.py migration audit

This stage reads committed SHIT exports only. It makes no Spotify, Last.fm,
MusicBrainz, Discogs, or other provider requests and never edits playlists.
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "scripts" / "music") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts" / "music"))

from music_library import MusicLibrary, norm, select_recent_track_rows

MUSIC_ROOT = REPO_ROOT / "assistant_data" / "music"
SPOTIFY_ROOT = REPO_ROOT / "assistant_data" / "spotify"
DEFAULT_ROOT = MUSIC_ROOT / "library"
LYRICS = REPO_ROOT / "assistant_data" / "recommendations" / "lyric_features.json"


def load(path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return fallback


def playlist_track_rows():
    """Read complete saved playlist snapshots; never fetch Spotify during migration."""
    catalog = load(SPOTIFY_ROOT / "playlists.json", {})
    playlists = catalog.get("playlists", []) if isinstance(catalog, dict) else []
    rows, accessible, inaccessible, incomplete = [], 0, 0, []
    for playlist in playlists:
        if not isinstance(playlist, dict):
            continue
        record_path = REPO_ROOT / str(playlist.get("record_path") or "")
        record = load(record_path, {})
        if record.get("items_accessible") is not True:
            inaccessible += 1
            continue
        accessible += 1
        items = record.get("items")
        fetched = record.get("item_count_fetched")
        if not isinstance(items, list) or not isinstance(fetched, int) or fetched != len(items):
            incomplete.append({
                "playlist_id": playlist.get("id"),
                "name": playlist.get("name"),
                "reported_fetched": fetched,
                "actual_items": len(items) if isinstance(items, list) else None,
            })
            continue
        for item in items:
            if not isinstance(item, dict) or item.get("type") != "track" or item.get("is_local"):
                continue
            artists = item.get("artists") or []
            artist = next((str(x).strip() for x in artists if str(x).strip()), "")
            if not artist or not item.get("name") or not item.get("id"):
                continue
            artist_ids = item.get("artist_ids") or []
            row = {
                "track_id": "spotify:track:" + str(item["id"]),
                "spotify_id": str(item["id"]),
                "artist": artist,
                "artists": list(artists),
                "artist_spotify_ids": list(artist_ids),
                "track": item["name"],
                "album": item.get("album") or "",
                "spotify_album_id": item.get("album_id"),
                "duration_ms": item.get("duration_ms"),
                "isrc": (item.get("external_ids") or {}).get("isrc"),
                "playlist_memberships": [{
                    "playlist_id": playlist.get("id"),
                    "playlist_name": playlist.get("name"),
                    "position": item.get("position"),
                    "added_at": item.get("added_at"),
                }],
                "spotify_item_uri": item.get("uri"),
            }
            rows.append(row)
    return rows, {
        "playlists_total": len(playlists),
        "playlists_accessible": accessible,
        "playlists_inaccessible": inaccessible,
        "incomplete_playlists": incomplete,
        "playlist_track_occurrences": len(rows),
    }


def merge_source_rows(profile_rows, playlist_rows):
    """Join profile evidence onto Spotify identities without guessing ambiguous names."""
    profiles = list(profile_rows.values()) if isinstance(profile_rows, dict) else []
    by_mbid, by_source_id, by_name = defaultdict(list), defaultdict(list), defaultdict(list)
    for row in profiles:
        if not isinstance(row, dict):
            continue
        mbid = str(row.get("track_mbid") or row.get("recording_mbid") or "").casefold()
        if mbid:
            by_mbid[mbid].append(row)
        source_id = str(row.get("track_id") or "").casefold()
        if source_id:
            by_source_id[source_id].append(row)
        if row.get("artist") and (row.get("track") or row.get("name")):
            by_name[(norm(row["artist"]), norm(row.get("track") or row.get("name")))].append(row)

    combined = {}
    profile_only = 0
    matched_profiles = set()
    for item in playlist_rows:
        key = str(item.get("spotify_id") or "").casefold()
        row = dict(item)
        matches = []
        mbid = str(item.get("track_mbid") or "").casefold()
        if mbid:
            matches = by_mbid.get(mbid, [])
        if not matches:
            matches = by_name.get((norm(item.get("artist")), norm(item.get("track"))), [])
            if len(matches) > 1:
                exact_album = [p for p in matches if norm(p.get("album")) == norm(item.get("album"))]
                matches = exact_album if len(exact_album) == 1 else []
        if len(matches) == 1:
            profile = matches[0]
            matched_profiles.add(str(profile.get("track_id") or id(profile)))
            for field, value in profile.items():
                if value not in (None, "", [], {}) and field not in {"artist", "track", "name", "album"}:
                    row[field] = value
            row["profile_source_track_id"] = profile.get("track_id")
        combined[key] = row

    for profile in profiles:
        if not isinstance(profile, dict):
            continue
        pid = str(profile.get("track_id") or "").casefold()
        if pid in matched_profiles:
            continue
        key = "profile:" + (pid or str(len(combined)))
        # Keep profile-only evidence; it can be resolved by MBID or exact names later.
        combined[key] = dict(profile)
        profile_only += 1
    return list(combined.values()), {
        "profile_rows": len(profiles),
        "profile_rows_joined_to_spotify": len(matched_profiles),
        "profile_only_rows_retained": profile_only,
        "spotify_unique_tracks": len({str(x.get("spotify_id")) for x in playlist_rows if x.get("spotify_id")}),
        "combined_source_rows": len(combined),
    }


def collect_sources():
    tracks = load(MUSIC_ROOT / "track_profiles.json", {})
    artists = load(MUSIC_ROOT / "artist_profiles.json", {})
    albums = load(MUSIC_ROOT / "album_profiles.json", {})
    audio = load(MUSIC_ROOT / "audio_profiles.json", {})
    lyrics = load(LYRICS, [])
    playlist_rows, playlist_report = playlist_track_rows()
    rows, merge_report = merge_source_rows(tracks, playlist_rows)
    return rows, artists, albums, audio, lyrics, {**playlist_report, **merge_report}


def status(root=DEFAULT_ROOT):
    library = MusicLibrary(root)
    report = library.audit()
    return {
        "library_root": str(root.relative_to(REPO_ROOT)) if root.is_relative_to(REPO_ROOT) else str(root),
        "exists": library.index_path.exists(),
        "songs": report["songs"],
        "artists": report["artists"],
        "albums": report["albums"],
        "audit_ok": report["ok"],
        "audit_errors": report["errors"][:20],
    }


def preview(root=DEFAULT_ROOT):
    rows, artists, albums, audio, lyrics, sources = collect_sources()
    library = MusicLibrary(root)
    existing = library.audit()
    return {
        "sources": sources,
        "artist_profiles": len(artists) if isinstance(artists, dict) else 0,
        "album_profiles": len(albums) if isinstance(albums, dict) else 0,
        "audio_profiles": len(audio.get("tracks", audio)) if isinstance(audio, dict) else 0,
        "lyric_features": len(lyrics) if isinstance(lyrics, list) else 0,
        "existing_library": {
            "songs": existing["songs"], "artists": existing["artists"],
            "albums": existing["albums"], "audit_ok": existing["ok"],
        },
        "provider_requests": 0,
        "spotify_writes": 0,
        "playlist_writes": 0,
        "library_writes": 0,
        "incomplete_playlists_block_execution": bool(sources["incomplete_playlists"]),
    }


def run(root=DEFAULT_ROOT):
    rows, artists, albums, audio, lyrics, sources = collect_sources()
    if sources["incomplete_playlists"]:
        raise RuntimeError(
            "Migration stopped: one or more accessible playlist snapshots are incomplete. "
            "Refresh/repair the reference library before migrating. "
            + json.dumps(sources["incomplete_playlists"][:10], ensure_ascii=False)
        )
    result = MusicLibrary(root).put_catalogue(rows, artists, albums, audio, lyrics)
    audit = MusicLibrary(root).audit()
    if not audit["ok"]:
        raise RuntimeError("Post-migration Library audit failed: " + json.dumps(audit["errors"][:20]))
    return {
        "migration": result,
        "sources": sources,
        "audit": audit,
        "provider_requests": 0,
        "spotify_writes": 0,
        "playlist_writes": 0,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("status", "preview", "run", "resume", "audit"), nargs="?", default="preview")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--recent-limit", type=int, default=0,
                        help="legacy compatibility: limit profile rows to a recent batch")
    parser.add_argument("--dry-run", action="store_true",
                        help="report selected source rows without writing")
    args = parser.parse_args()
    root = args.root if args.root.is_absolute() else REPO_ROOT / args.root
    if args.recent_limit < 0:
        parser.error("--recent-limit must be zero or greater")

    # Preserve the earlier bounded-batch compatibility command used by tests
    # and staged local rollouts. It remains offline and does not replace the
    # full Great Migration entry point (migrate_full_music_library.py).
    if args.recent_limit:
        tracks = load(MUSIC_ROOT / "track_profiles.json", {})
        recent = load(MUSIC_ROOT / "recent_top_tracks.json", {})
        recent_rows = recent.get("tracks", []) if isinstance(recent, dict) else []
        selected, selection = select_recent_track_rows(
            tracks, recent_rows, args.recent_limit,
            window_days=recent.get("window_days") if isinstance(recent, dict) else None,
        )
        if args.dry_run:
            print(json.dumps({
                "track_profiles_selected": len(selected),
                "selection": selection,
                "provider_requests": 0,
                "writes": 0,
            }, indent=2))
            return
        artists = load(MUSIC_ROOT / "artist_profiles.json", {})
        albums = load(MUSIC_ROOT / "album_profiles.json", {})
        audio = load(MUSIC_ROOT / "audio_profiles.json", {})
        lyrics = load(LYRICS, [])
        result = MusicLibrary(root).put_catalogue(selected, artists, albums, audio, lyrics)
        print(json.dumps({
            "migration_result": result, "selection": selection,
            "provider_requests": 0, "writes": 1,
        }, indent=2))
        return
    if args.dry_run and args.action in {"run", "resume"}:
        result = preview(root)
        result["writes"] = 0
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.action == "status":
        result = status(root)
    elif args.action in {"preview", "audit"}:
        result = preview(root) if args.action == "preview" else status(root)
        if args.action == "audit":
            result["audit"] = MusicLibrary(root).audit()
    else:
        # 'resume' is intentionally the same idempotent merge operation as 'run':
        # completed records are reused/preserved and missing records are rebuilt.
        result = run(root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.action == "audit" and not result.get("audit", {}).get("ok", False):
        raise SystemExit(2)


if __name__ == "__main__":
    main()


# FILE OVERVIEW
# Purpose: resumable, local-only migration into the canonical per-artist/album/song Library.
# Inputs: track/artist/album/audio profiles, lyric features, and complete saved Spotify playlist snapshots.
# Outputs: sharded artist/album/song records and a compact resolver index under assistant_data/music/library/.
# Safety: no provider/API requests, no Spotify writes, no playlist edits; incomplete snapshots block execution.
# Write boundary: status/preview/audit construct MusicLibrary and may rebuild library_index.json.
# Recovery: legacy run/resume and --recent-limit writes do not create their own backup. Use
#           `python shit.py library migrate --yes` for the supported backup-protected full migration.
# Related: scripts/music/music_library.py, compat/migrate_music_library.py, shit.py, docs/.
