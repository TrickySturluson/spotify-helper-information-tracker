#!/usr/bin/env python3
"""Detect manually removed tracks from a Spotify playlist and persist a no-readd list.

Run from the repository directory after playlist edits:
    python track_playlist_removals.py 4diIlnF8BlgoJrwUfejf49

First run establishes a baseline. Later runs compare the current playlist with the
last saved baseline, append missing tracks to playlist_removed_tracks.json, and
refresh the baseline. Commit/push the two JSON files after a run so the blacklist
is available to future curation sessions.
"""
import argparse
import json
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("playlist_id")
    args = parser.parse_args()

    sp = manager.Spotify()
    playlist = manager.find(sp, args.playlist_id)
    current_items = manager.tracks(sp, playlist)
    current = {row["uri"]: row for row in current_items if row.get("uri")}

    baseline_data = read_json(BASELINE, {"version": 1, "playlists": {}})
    old_rows = baseline_data.get("playlists", {}).get(args.playlist_id)
    blacklist_data = read_json(BLACKLIST, {"version": 1, "playlists": {}})
    playlist_data = blacklist_data.setdefault("playlists", {}).setdefault(
        args.playlist_id, {"name": playlist.get("name", ""), "removed": []}
    )
    playlist_data["name"] = playlist.get("name", "")
    removed_rows = playlist_data.setdefault("removed", [])
    removed_uris = {row.get("uri") for row in removed_rows if row.get("uri")}

    if old_rows is None:
        print(f'Baseline created for "{playlist.get("name")}" ({len(current_items)} items).')
        print("Run this again after you remove tracks to detect and blacklist them.")
    else:
        old = {row.get("uri"): row for row in old_rows if row.get("uri")}
        newly_removed = [old[uri] for uri in old.keys() - current.keys() if uri not in removed_uris]
        newly_removed.sort(key=lambda row: (", ".join(row.get("artists", [])), row.get("name", "")))
        if newly_removed:
            removed_rows.extend(newly_removed)
            print(f"Detected {len(newly_removed)} removed track(s):")
            for row in newly_removed:
                print(f'  {", ".join(row.get("artists", []))} — {row.get("name")} [{row.get("uri")}]')
        else:
            print("No new removals detected.")
        print(f"Blacklist total: {len(removed_rows)} track(s).")

    baseline_data.setdefault("playlists", {})[args.playlist_id] = current_items
    write_json(BASELINE, baseline_data)
    write_json(BLACKLIST, blacklist_data)
    print(f"Saved {BASELINE} and {BLACKLIST}. Commit and push them so future curation can use the blacklist.")


if __name__ == "__main__":
    main()
