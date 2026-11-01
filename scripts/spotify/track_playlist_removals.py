#!/usr/bin/env python3
"""Track manual removals across all owned Spotify playlists and detect duplicates.

Run: python track_playlist_removals.py
Optional: python track_playlist_removals.py PLAYLIST_ID
Add --dedupe to remove extra occurrences from unlocked playlists only.
First run establishes baselines; later runs detect tracks removed since the
previous run and persist them in playlist_removed_tracks.json.
"""
import argparse
import json
from collections import Counter, defaultdict
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


def save_state(baseline_data, blacklist_data):
    write_json(BASELINE, baseline_data)
    write_json(BLACKLIST, blacklist_data)


def process_playlist(sp, playlist, baseline_data, blacklist_data, dedupe):
    pid = playlist["id"]
    name = playlist.get("name", "")
    rows = manager.tracks(sp, playlist)
    current_uris = {row["uri"] for row in rows if row.get("uri")}
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
        newly_removed = [old[u] for u in old.keys() - current_uris if u not in removed_uris]
        newly_removed.sort(key=lambda r: (", ".join(r.get("artists", [])), r.get("name", "")))
        removed_rows.extend(newly_removed)
        print(f'REMOVALS  {name}: {len(newly_removed)} newly removed; {len(removed_rows)} blacklisted total')

    positions = defaultdict(list)
    for index, row in enumerate(rows):
        if row.get("uri"):
            positions[row["uri"]].append(index)
    duplicates = {uri: indexes for uri, indexes in positions.items() if len(indexes) > 1}
    if duplicates:
        by_uri = {r["uri"]: r for r in rows if r.get("uri")}
        extra_count = sum(len(indexes) - 1 for indexes in duplicates.values())
        print(f'DUPLICATES {name}: {extra_count} extra occurrence(s)')
        for uri, indexes in duplicates.items():
            track = by_uri[uri]
            print(f'  {", ".join(track.get("artists", []))} — {track.get("name")} x{len(indexes)}')
        if dedupe:
            if not manager.unlocked(pid):
                print("  NOT REMOVED: playlist is locked; unlock it and rerun with --dedupe.")
            else:
                # Remove only surplus positions, preserving the first copy of each URI.
                fresh_playlist = manager.find(sp, pid)
                backup = manager.save_snapshot(manager.snapshot(sp, fresh_playlist))
                items = [
                    {"uri": uri, "positions": indexes[1:]}
                    for uri, indexes in duplicates.items()
                ]
                sp.call("DELETE", f"/playlists/{pid}/items", {
                    "items": items,
                    "snapshot_id": fresh_playlist.get("snapshot_id"),
                })
                manager.audit(event="deduplicated", playlist_id=pid, name=name,
                              removed_occurrences=extra_count, backup=backup)
                print(f"  DEDUPED {extra_count} surplus occurrence(s); recovery snapshot: {backup}")
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
    processed = 0
    failed = []
    for playlist in playlists:
        try:
            process_playlist(sp, playlist, baseline_data, blacklist_data, args.dedupe)
            processed += 1
            # Persist each successful playlist so a later 403 cannot discard progress.
            save_state(baseline_data, blacklist_data)
        except manager.ManagerError as exc:
            failed.append((playlist.get("name", playlist.get("id", "unknown")), str(exc)))
            print(f'UNAVAILABLE {playlist.get("name", playlist.get("id", "unknown"))}: {exc}')
            continue

    save_state(baseline_data, blacklist_data)
    print(f"\nSaved baselines/removal history for {processed} accessible playlist(s).")
    if failed:
        print(f"Skipped {len(failed)} inaccessible playlist(s); rerun after resolving access if needed.")
    print("Commit and push playlist_removal_baseline.json and playlist_removed_tracks.json.")
    if not args.dedupe:
        print("To remove duplicate occurrences from unlocked playlists, rerun with --dedupe.")


if __name__ == "__main__":
    main()
