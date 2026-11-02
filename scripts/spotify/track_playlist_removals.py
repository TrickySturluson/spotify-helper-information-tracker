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


def process_removal_rows(pid, name, rows, baseline_data, blacklist_data):
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
    baseline_data.setdefault("playlists", {})[pid] = rows


def process_playlist(sp, playlist, baseline_data, blacklist_data, dedupe):
    pid = playlist["id"]
    name = playlist.get("name", "")
    rows = manager.tracks(sp, playlist)
    process_removal_rows(pid, name, rows, baseline_data, blacklist_data)

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
                manager.mutate_with_snapshots(
                    sp,pid,lambda: sp.call("DELETE", f"/playlists/{pid}/items", {
                        "items": items, "snapshot_id": manager.find(sp,pid).get("snapshot_id"),
                    }),event="removal_tracker_dedupe",removed_occurrences=extra_count)
                manager.audit(event="deduplicated", playlist_id=pid, name=name,
                              removed_occurrences=extra_count, backup=backup)
                print(f"  DEDUPED {extra_count} surplus occurrence(s); recovery snapshot: {backup}")
                deduped_playlist = manager.find(sp, pid)
                rows = manager.tracks(sp, deduped_playlist)
                after_snapshot = manager.save_snapshot(manager.snapshot(sp, deduped_playlist))
                manager.audit(event="dedupe_post_snapshot_saved", playlist_id=pid,
                              snapshot=after_snapshot, removed_occurrences=extra_count)
    else:
        print(f'OK        {name}: no duplicate track URIs')

    # Persist the post-dedupe state so cleanup is not classified as user feedback.
    baseline_data.setdefault("playlists", {})[pid] = rows



def seed_from_reference_library(baseline_data):
    """Seed a missing baseline from the last known complete snapshots before refresh.

    This deliberately runs BEFORE the live reference-library sync so removals
    made since the previous sync are still detectable in the subsequent poll.
    Inaccessible or incomplete snapshots are never treated as empty playlists.
    """
    root = Path("assistant_data/spotify")
    catalog = read_json(root / "playlists.json", {"playlists": []})
    seeded = 0
    skipped = 0
    rows_by_id = baseline_data.setdefault("playlists", {})
    for entry in catalog.get("playlists", []):
        pid = entry.get("id")
        if not pid or pid in rows_by_id:
            continue
        path = root / "playlists" / f"{pid}.json"
        if not path.is_file():
            skipped += 1
            continue
        record = read_json(path, {})
        items = record.get("items") or []
        reported = record.get("total_items_reported")
        fetched = record.get("item_count_fetched")
        if (not record.get("items_accessible") or not isinstance(reported, int)
                or reported != fetched or len(items) != fetched):
            skipped += 1
            continue
        rows_by_id[pid] = [{
            "uri": item.get("uri"), "name": item.get("name"),
            "artists": item.get("artists") or [], "album": item.get("album") or "",
        } for item in items]
        seeded += 1
    baseline_data["version"] = max(1, int(baseline_data.get("version", 1)))
    baseline_data["seeded_from_reference_library_at"] = manager.stamp()
    baseline_data["seeded_playlist_count"] = seeded
    save_state(baseline_data, read_json(BLACKLIST, {"version": 1, "playlists": {}}))
    print(f"Seeded {seeded} playlist baselines from prior complete reference snapshots; skipped {skipped} missing/incomplete snapshots.")
    return seeded, skipped


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("playlist_id", nargs="?", help="Optional: process only this playlist")
    parser.add_argument("--dedupe", action="store_true",
                        help="Remove extra copies of duplicate tracks from unlocked playlists")
    parser.add_argument("--seed-from-reference-library", action="store_true",
                        help="Seed only missing baselines from prior complete reference snapshots; make no Spotify requests")
    parser.add_argument("--from-reference-library", action="store_true",
                        help="Compare against freshly synced complete reference snapshots; make no Spotify requests")
    args = parser.parse_args()

    if args.seed_from_reference_library:
        baseline_data = read_json(BASELINE, {"version": 1, "playlists": {}})
        seed_from_reference_library(baseline_data)
        return

    if args.from_reference_library:
        root = Path("assistant_data/spotify")
        catalog = read_json(root / "playlists.json", {"playlists": []})
        baseline_data = read_json(BASELINE, {"version": 1, "playlists": {}})
        blacklist_data = read_json(BLACKLIST, {"version": 1, "playlists": {}})
        processed = skipped = 0
        for entry in catalog.get("playlists", []):
            pid = entry.get("id")
            if not pid or (args.playlist_id and pid != args.playlist_id):
                continue
            path = root / "playlists" / f"{pid}.json"
            if not path.is_file():
                skipped += 1
                continue
            record = read_json(path, {})
            items = record.get("items") or []
            reported, fetched = record.get("total_items_reported"), record.get("item_count_fetched")
            if (not record.get("items_accessible") or not isinstance(reported, int)
                    or reported != fetched or len(items) != fetched):
                print(f'SKIP      {entry.get("name", pid)}: snapshot missing, inaccessible or incomplete')
                skipped += 1
                continue
            rows = [{"uri": item.get("uri"), "name": item.get("name"),
                     "artists": item.get("artists") or [], "album": item.get("album") or ""}
                    for item in items]
            process_removal_rows(pid, record.get("name") or entry.get("name", ""),
                                 rows, baseline_data, blacklist_data)
            save_state(baseline_data, blacklist_data)
            processed += 1
        print(f"\\nCompared {processed} complete refreshed playlist snapshots; skipped {skipped} inaccessible/incomplete playlists.")
        return

    sp = manager.Spotify()
    if args.playlist_id:
        try:
            playlist = manager.fetch_playlist(sp, args.playlist_id)
        except manager.ManagerError as error:
            raise SystemExit(f"Could not read the requested playlist: {error}") from error
        playlists = [playlist]
    else:
        playlists = sp.playlists()

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

    # A targeted refresh is a safety precondition for staging and confirmation.
    # Do not return success when that exact playlist could not be read, or the
    # caller could continue with a stale removal blacklist.
    if args.playlist_id and failed:
        name, error = failed[0]
        raise SystemExit(f"Could not refresh removal history for {name}: {error}")

    save_state(baseline_data, blacklist_data)
    print(f"\nSaved baselines/removal history for {processed} accessible playlist(s).")
    if failed:
        print(f"Skipped {len(failed)} inaccessible playlist(s); rerun after resolving access if needed.")
    print("Commit and push playlist_removal_baseline.json and playlist_removed_tracks.json.")
    if not args.dedupe:
        print("To remove duplicate occurrences from unlocked playlists, rerun with --dedupe.")


if __name__ == "__main__":
    main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Track manual removals across all owned Spotify playlists and detect duplicates. Run: python track_playlist_removals.py Optional: python track_playlist_removals.py PLAYLIST_ID Add --dedupe to remove extra occurrences from unlocked playlists only. First run establishes baselines; later runs detect tracks removed since the previous run and persist them in playlist_removed_tracks.json.
# Location: Maintained implementation in scripts/spotify/track_playlist_removals.py.
# Data flow: Uses the canonical archives and/or generated project data; consult
#            this module's configuration and command options for exact paths.
# Run: python compat/track_playlist_removals.py (legacy command entry point, when applicable).
# Related: tests/ contains regression coverage; docs/ contains extended guides.
# -----------------------------------------------------------------------------
