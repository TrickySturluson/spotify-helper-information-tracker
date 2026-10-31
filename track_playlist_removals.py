#!/usr/bin/env python3
"""Track manual removals across all owned Spotify playlists and detect duplicates.

Run: python track_playlist_removals.py
Optional: python track_playlist_removals.py PLAYLIST_ID
Add --dedupe to remove repeated occurrences from unlocked playlists only.
First run establishes baselines; later runs detect tracks removed since the
previous run and persist them in playlist_removed_tracks.json.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

import spotify_playlist_manager as manager

BASELINE = Path("playlist_removal_baseline.json")
BLACKLIST = Path("playlist_removed_tracks.json")


def read_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def process_playlist(sp, playlist, baseline_data, blacklist_data, dedupe):
    pid = playlist["id"]
    name = playlist.get("name", "")
    rows = manager.tracks(sp, playlist)
    current = {row["uri"]: row for row in rows if row.get("uri")}
    old_rows = baseline_data.get("playlists", {}).get(pid)
    pblack = blacklist_data.setdefault("playlists", {}).setdefault(
        pid, {"name": name, "removed": []}
    )
    pblack["name"] = name
    removed_rows = pblack.setdefault("removed", [])
    removed_uris = {r.get("uri") for r in removed_rows}
    if old_rows is None:
        print(f'BASELINE  {name}: {len(rows)} items (first snapshot; no historical removals can be inferred)')
    else:
        old = {r.get("uri"): r for r in old_rows if r.get("uri")}
        newly_removed = [old[u] for u in old.keys() - current.keys() if u not in removed_uris]
        newly_removed.sort(key=lambda r: (", ".join(r.get("artists", [])), r.get("name", "")))
        removed_rows.extend(newly_removed)
        print(f'REMOVALS  {name}: {len(newly_removed)} newly removed; {len(removed_rows)} blacklisted total')

    counts = Counter(r.get("uri") for r in rows if r.get("uri"))
    duplicates = {uri: count for uri, count in counts.items() if count > 1}
    if duplicates:
        by_uri = {r["uri"]: r for r in rows if r.get("uri")}
        print(f'DUPLICATES {name}: {sum(n - 1 for n in duplicates.values())} extra occurrence(s)')
        for uri, count in duplicates.items():
            track = by_uri[uri]
            print(f'  {", ".join(track.get("artists", []))} — {track.get("name")} x{count}')
        if dedupe:
            if not manager.unlocked(pid):
                print("  NOT REMOVED: playlist is locked; unlock it and rerun with --dedupe.")
            else:
                # Save a complete pre-change snapshot before removing every extra copy.
                backup = manager.save_snapshot(manager.snapshot(sp, playlist))
                for uri, count in duplicates.items():
                    manager.remove(sp, pid, [uri] * (count - 1))
                manager.audit(event="deduplicated", playlist_id=pid, name=name,
                              removed_occurrences=sum(n - 1 for n in duplicates.values()),
                              backup=backup)
                print(f"  DEDUPED; recovery snapshot: {backup}")
                rows = manager.tracks(sp, manager.find(sp, pid))
    else:
        print(f'OK        {name}: no duplicate track URIs')

    baseline_data.setdefault("playlists", {})[pid] = rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("playlist_id", nargs="?", help="Optional: process only this playlist")
    parser.add_argument("--dedupe", action="store_true",
                        help="Remove extra copies of duplicate tracks from unlocked playlists")
    args = parser.parse_args()

    sp = manager.Spotify()
    playlists = sp.playlists()
    if args.playlist_id:
        playlists = [p for p in playlists if p.get("id") == args.playlist_id]
        if not playlists:
            raise SystemExit("Playlist not found in your Spotify collection.")

    baseline_data = read_json(BASELINE, {"version": 1, "playlists": {}})
    blacklist_data = read_json(BLACKLIST, {"version": 1, "playlists": {}})
    for playlist in playlists:
        process_playlist(sp, playlist, baseline_data, blacklist_data, args.dedupe)

    write_json(BASELINE, baseline_data)
    write_json(BLACKLIST, blacklist_data)
    print(f"\nSaved baselines/removal history for {len(playlists)} playlist(s).")
    print("Commit and push playlist_removal_baseline.json and playlist_removed_tracks.json.")
    if not args.dedupe:
        print("To remove duplicate occurrences from unlocked playlists, rerun with --dedupe.")


if __name__ == "__main__":
    main()
