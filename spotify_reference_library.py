#!/usr/bin/env python3
"""Canonical, read-only Spotify playlist reference library and Daily feedback helpers.

Run: python spotify_reference_library.py sync
The command reads every playlist returned by the authorized Spotify account and
writes dated snapshots. It never changes Spotify playlists.
"""
import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import spotify_playlist_manager as manager

ROOT = Path("assistant_data/spotify")
CATALOG = ROOT / "playlists.json"
PLAYLIST_DIR = ROOT / "playlists"
HISTORY_DIR = ROOT / "history"
INDEX = ROOT / "reference_index.json"
DAILY_ID = "4yUVHSMQySfWeEowfIMcx7"


def stamp():
    return datetime.now(timezone.utc).isoformat()


def item_record(entry, position):
    item = entry.get("item") or entry.get("track") or entry.get("episode") or {}
    artists = item.get("artists") or []
    album = item.get("album") or {}
    return {
        "position": position,
        "added_at": entry.get("added_at"),
        "added_by": (entry.get("added_by") or {}).get("id"),
        "type": item.get("type") or ("episode" if item.get("show") else "unknown"),
        "id": item.get("id"),
        "uri": item.get("uri"),
        "name": item.get("name"),
        "artists": [artist.get("name") for artist in artists if artist.get("name")],
        "artist_ids": [artist.get("id") for artist in artists if artist.get("id")],
        "album": album.get("name"),
        "album_id": album.get("id"),
        "duration_ms": item.get("duration_ms"),
        "is_local": bool(item.get("is_local")),
        "is_playable": item.get("is_playable"),
        "linked_from": (item.get("linked_from") or {}).get("uri"),
        "external_ids": item.get("external_ids") or {},
        "available_markets_count": len(item.get("available_markets") or []),
    }


def playlist_record(sp, playlist):
    items_accessible = True
    items_error = None
    try:
        entries = sp.items(playlist["id"])
    except manager.ManagerError as error:
        if "HTTP 403" not in str(error):
            raise
        entries = []
        items_accessible = False
        items_error = "Spotify API does not expose item contents for this playlist to the current account/app."
    rows = [item_record(entry, i) for i, entry in enumerate(entries)]
    owner = playlist.get("owner") or {}
    return {
        "schema_version": 1,
        "captured_at": stamp(),
        "id": playlist["id"],
        "name": playlist.get("name"),
        "description": playlist.get("description"),
        "owner": {"id": owner.get("id"), "display_name": owner.get("display_name")},
        "public": playlist.get("public"),
        "collaborative": playlist.get("collaborative"),
        "snapshot_id": playlist.get("snapshot_id"),
        "total_items_reported": (playlist.get("items") or playlist.get("tracks") or {}).get("total"),
        "item_count_fetched": len(rows),
        "items_accessible": items_accessible,
        "items_error": items_error,
        "items": rows,
    }


def sync(sp):
    ROOT.mkdir(parents=True, exist_ok=True)
    PLAYLIST_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    previous = manager.read(CATALOG, {"version": 1, "playlists": []})
    previous_by_id = {row.get("id"): row for row in previous.get("playlists", [])}
    catalog = []
    index_tracks, index_artists = defaultdict(list), defaultdict(list)
    changed = 0
    for playlist in sp.playlists():
        record = playlist_record(sp, playlist)
        pid = record["id"]
        path = PLAYLIST_DIR / f"{pid}.json"
        old = manager.read(path, {})
        # Snapshot only when Spotify's snapshot ID or ordered item data changes.
        content_signature = [(x.get("uri"), x.get("name"), x.get("artists")) for x in record["items"]]
        old_signature = [(x.get("uri"), x.get("name"), x.get("artists")) for x in old.get("items", [])]
        if not old or old.get("snapshot_id") != record["snapshot_id"] or content_signature != old_signature:
            history = HISTORY_DIR / pid
            history.mkdir(parents=True, exist_ok=True)
            manager.write(history / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".json"), record)
            manager.write(path, record)
            changed += 1
        owner = record["owner"]
        catalog.append({
            "id": pid, "name": record["name"], "owner": owner,
            "public": record["public"], "collaborative": record["collaborative"],
            "snapshot_id": record["snapshot_id"], "item_count": len(record["items"]),
            "captured_at": record["captured_at"], "record_path": str(path),
            "changed": bool(not old or old.get("snapshot_id") != record["snapshot_id"] or content_signature != old_signature),
        })
        for item in record["items"]:
            uri = item.get("uri")
            if uri:
                index_tracks[uri].append(pid)
            for artist in item.get("artists", []):
                index_artists[artist.casefold()].append(pid)
    catalog.sort(key=lambda row: (row["name"] or "").casefold())
    manager.write(CATALOG, {"version": 1, "captured_at": stamp(), "playlist_count": len(catalog), "playlists": catalog})
    manager.write(INDEX, {
        "version": 1, "generated_at": stamp(),
        "track_playlists": dict(index_tracks), "artist_playlists": dict(index_artists),
    })
    print(f"Reference library synced: {len(catalog)} playlists; {changed} new/changed snapshots.")
    print(f"Catalog: {CATALOG}; history: {HISTORY_DIR}")


def exposure_summary(added_at, playback_segments, scrobbles=None, removed_at=None):
    """Measure post-add plays; absent tracker coverage is unknown, never zero."""
    def parse(value):
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
    start, end = parse(added_at), parse(removed_at)
    if start is None:
        raise ValueError("added_at must be an ISO timestamp")
    measured_ms = 0
    measured_plays = set()
    for row in playback_segments or []:
        at = parse(row.get("started_at") or row.get("timestamp") or row.get("at"))
        if at and at >= start and (end is None or at <= end):
            uri = row.get("spotify_uri") or row.get("uri")
            if uri:
                measured_plays.add((uri, at.isoformat()))
            measured_ms += int(row.get("played_ms") or row.get("duration_ms") or 0)
    scrobble_count = 0
    for row in scrobbles or []:
        at = parse(row.get("uts") or row.get("date") or row.get("timestamp"))
        if at and at >= start and (end is None or at <= end):
            scrobble_count += 1
    return {
        "added_at": added_at, "removed_at": removed_at,
        "measured_play_events": len(measured_plays),
        "measured_playback_ms": measured_ms,
        "lastfm_scrobbles_after_add": scrobble_count,
        "tracker_status": "measured" if playback_segments is not None else "unknown",
        "lastfm_status": "available" if scrobbles is not None else "unknown",
    }


def retention_signal(liked, measured_plays, lastfm_plays, tracker_known=True):
    """Return transparent, bounded evidence components rather than a hidden score."""
    measured = max(0, int(measured_plays or 0)) if tracker_known else None
    scrobbles = max(0, int(lastfm_plays or 0)) if lastfm_plays is not None else None
    return {
        "liked": bool(liked) if liked is not None else None,
        "liked_signal": 1.0 if liked is True else (0.0 if liked is False else None),
        "measured_post_add_plays": measured,
        "lastfm_post_add_plays": scrobbles,
        "playback_signal": round(min(1.0, (measured or 0) / 5.0), 4) if measured is not None else None,
        "status": "observed" if liked is not None or measured is not None or scrobbles is not None else "unknown",
    }


def lookup(query):
    needle = query.casefold().strip()
    catalog = manager.read(CATALOG, {"playlists": []})
    matches = []
    for playlist in catalog.get("playlists", []):
        path = Path(playlist.get("record_path") or PLAYLIST_DIR / (playlist["id"] + ".json"))
        record = manager.read(path, {})
        playlist_match = needle in str(record.get("name") or "").casefold()
        matched_items = []
        for item in record.get("items", []):
            text = " ".join([item.get("name") or "", item.get("album") or ""] + item.get("artists", []))
            if needle in text.casefold():
                matched_items.append(item)
        if playlist_match or matched_items:
            matches.append((record, matched_items))
    for record, items in matches:
        print(f'{record.get("name")} [{record.get("id")}] — {record.get("item_count_fetched", 0)} items')
        if not record.get("items_accessible", True):
            print("  Item contents unavailable through this Spotify API authorization.")
        for item in items[:25]:
            print(f'  {item.get("position", 0) + 1:3}. {", ".join(item.get("artists") or [])} — {item.get("name")}')
    print(f"Matched {len(matches)} playlist(s).")
    return matches


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("sync", help="Read Spotify and refresh the reference library")
    sub.add_parser("list", help="List saved reference playlists")
    search = sub.add_parser("lookup", help="Search saved playlists, tracks, artists and albums")
    search.add_argument("query")
    args = parser.parse_args()
    if args.command == "sync":
        sync(manager.Spotify())
    elif args.command == "list":
        for row in manager.read(CATALOG, {"playlists": []}).get("playlists", []):
            print(f'{row.get("name")} | {row.get("item_count")} items | {row.get("id")}')
    elif args.command == "lookup":
        lookup(args.query)


if __name__ == "__main__":
    main()
