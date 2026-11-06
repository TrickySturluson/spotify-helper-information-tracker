#!/usr/bin/env python3
"""Read-only Spotify playlist snapshot collector with repository-side Library evidence writes.

Run: python spotify_reference_library.py sync
The command reads every playlist returned by the authorized Spotify account and
writes dated snapshots. It never changes Spotify playlists.
"""
import argparse
import json
import re
import shutil
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import spotify_playlist_manager as manager
from scripts.music.music_library import MusicLibrary

ROOT = Path("assistant_data/spotify")
CATALOG = ROOT / "playlists.json"
PLAYLIST_DIR = ROOT / "playlists"
HISTORY_DIR = ROOT / "history"
INDEX = ROOT / "reference_index.json"
DAILY_ID = "4yUVHSMQySfWeEowfIMcx7"


def stamp():
    return datetime.now(timezone.utc).isoformat()


def item_record(entry, position, market=None):
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
        "is_playable_present": "is_playable" in item,
        "playability_checked_at": stamp() if "is_playable" in item else None,
        "playability_market": market if "is_playable" in item else None,
        "restrictions": item.get("restrictions") or {},
        "linked_from": (item.get("linked_from") or {}).get("uri"),
        "external_ids": item.get("external_ids") or {},
        "available_markets_count": len(item.get("available_markets") or []),
    }


def playability_observation(item, playlist_id, snapshot_id, fallback_checked_at=None, fallback_market="unknown", snapshot_accessible=True, source="read_only_playlist_snapshot", requested_spotify_id=None):
    """Convert explicit Spotify response fields into a provenance-rich observation."""
    if not isinstance(item, dict):
        return None
    restrictions = item.get("restrictions") or {}
    explicit = item.get("is_playable_present") or isinstance(item.get("is_playable"), bool) or bool(restrictions)
    if not explicit:
        return None
    playable = item.get("is_playable")
    reason = restrictions.get("reason") if isinstance(restrictions, dict) else None
    linked = item.get("linked_from")
    linked_uri = linked.get("uri") if isinstance(linked, dict) else linked
    linked_id = linked.get("id") if isinstance(linked, dict) else (
        linked_uri.rsplit(":", 1)[-1] if isinstance(linked_uri, str) else None
    )
    market = item.get("playability_market") or fallback_market or "unknown"
    market_context = (
        "spotify_user_account_country" if market == "from_token" else
        "explicit_country_market" if market != "unknown" else
        "market_not_established"
    )
    requested_id = requested_spotify_id or linked_id or item.get("id")
    returned_id = item.get("id")
    return {
        "status": (
            "restricted" if reason else
            "playable" if playable is True else
            "unplayable" if playable is False else
            "unknown"
        ),
        "is_playable": playable,
        "market": market,
        "market_context": market_context,
        "latest_snapshot_accessible": bool(snapshot_accessible) if source == "read_only_playlist_snapshot" else None,
        "checked_at": item.get("playability_checked_at") or fallback_checked_at,
        "provider": "Spotify",
        "source": source,
        "playlist_id": playlist_id,
        "playlist_snapshot_id": snapshot_id,
        "requested_spotify_id": requested_id,
        "returned_spotify_id": item.get("id"),
        "linked_from_spotify_uri": linked_uri,
        "linked_from_spotify_id": linked_id,
        "restrictions": restrictions,
        "restrictions_reason": reason,
        "is_local": item.get("is_local"),
        "available_markets_count": item.get("available_markets_count"),
    }


def playlist_record(sp, playlist, cached=None):
    # Reuse complete local item pages while Spotify's snapshot_id is unchanged.
    # This avoids re-downloading every page for every playlist on each sync.
    if (
        isinstance(cached, dict)
        and cached.get("items_accessible") is True
        and cached.get("items_snapshot_id", cached.get("snapshot_id")) == playlist.get("snapshot_id")
        and isinstance(cached.get("items"), list)
    ):
        owner = playlist.get("owner") or {}
        return {
            **cached,
            "captured_at": stamp(),
            "id": playlist["id"],
            "name": playlist.get("name"),
            "description": playlist.get("description"),
            "owner": {"id": owner.get("id"), "display_name": owner.get("display_name")},
            "public": playlist.get("public"),
            "collaborative": playlist.get("collaborative"),
            "snapshot_id": playlist.get("snapshot_id"),
            "total_items_reported": (playlist.get("items") or playlist.get("tracks") or {}).get("total"),
            "item_count_fetched": len(cached["items"]),
            "items_accessible": True,
            "items_error": None,
            "items_snapshot_id": playlist.get("snapshot_id"),
            "playability_market": cached.get("playability_market") or "from_token",
            "playability_market_context": "spotify_user_account_country",
        }

    items_accessible = True
    items_error = None
    try:
        entries = sp.items(playlist["id"], market="from_token")
    except manager.ManagerError as error:
        message = str(error)
        status = next((code for code in ("HTTP 403", "HTTP 404") if code in message), None)
        if status is None:
            raise
        entries = []
        items_accessible = False
        items_error = (
            f"Spotify API returned {status} while fetching playlist items; "
            "contents are unavailable and are not treated as an empty playlist."
        )
    rows = [item_record(entry, i, market="from_token") for i, entry in enumerate(entries)]
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
        "last_items_accessible_at": stamp() if items_accessible else None,
        "items_snapshot_id": playlist.get("snapshot_id") if items_accessible else None,
        "playability_market": "from_token",
        "playability_market_context": "spotify_user_account_country",
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
    library_rows = []
    playability_observations = []
    seen_ids = set()
    for playlist in sp.playlists():
        # Spotify pagination can occasionally repeat a playlist across pages.
        # Process each stable playlist ID once so catalog/index counts stay canonical.
        pid = playlist.get("id")
        if not pid or pid in seen_ids:
            continue
        seen_ids.add(pid)
        path = PLAYLIST_DIR / f"{pid}.json"
        old = manager.read(path, {})
        record = playlist_record(sp, playlist, old)
        # A 403 is not an empty playlist. Preserve the last known ordered contents,
        # mark them stale/inaccessible, and never snapshot the failed empty response.
        if not record["items_accessible"] and old:
            record["items"] = old.get("items", [])
            record["item_count_fetched"] = old.get("item_count_fetched", len(record["items"]))
            record["last_items_accessible_at"] = old.get("last_items_accessible_at") or old.get("captured_at")
            record["items_snapshot_id"] = old.get("items_snapshot_id") or old.get("snapshot_id")
        content_signature = [(x.get("uri"), x.get("name"), x.get("artists")) for x in record["items"]]
        old_signature = [(x.get("uri"), x.get("name"), x.get("artists")) for x in old.get("items", [])]
        changed_now = bool(record["items_accessible"] and (
            not old or old.get("items_snapshot_id", old.get("snapshot_id")) != record["snapshot_id"]
            or content_signature != old_signature
        ))
        if changed_now or (not old and record["items_accessible"]):
            history = HISTORY_DIR / pid
            history.mkdir(parents=True, exist_ok=True)
            # Preserve the previous complete snapshot before replacing the live
            # pointer. Historical candidate audits must remain resolvable after
            # the current playlist changes.
            if old and old.get("items_accessible"):
                old_items = old.get("items") or []
                old_reported = old.get("total_items_reported")
                old_fetched = old.get("item_count_fetched")
                if (isinstance(old_reported, int) and old_reported == old_fetched
                        and len(old_items) == old_fetched and old.get("snapshot_id")):
                    old_stamp = old.get("captured_at")
                    try:
                        old_dt = datetime.fromisoformat(str(old_stamp).replace("Z", "+00:00"))
                        old_name = old_dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".json"
                    except (TypeError, ValueError):
                        old_name = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "_prior.json"
                    old_history = history / old_name
                    if not old_history.exists():
                        manager.write(old_history, old)
            manager.write(history / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".json"), record)
        # Always persist access status, even when retaining an older content snapshot.
        manager.write(path, record)
        changed += int(changed_now)
        owner = record["owner"]
        catalog.append({
            "id": pid, "name": record["name"], "owner": owner,
            "public": record["public"], "collaborative": record["collaborative"],
            "snapshot_id": record["snapshot_id"], "item_count": record["item_count_fetched"],
            "items_accessible": record["items_accessible"],
            "last_items_accessible_at": record.get("last_items_accessible_at"),
            "captured_at": record["captured_at"], "record_path": str(path),
            "changed": changed_now,
        })
        for item in record["items"]:
            uri = item.get("uri")
            if uri:
                index_tracks[uri].append(pid)
            for artist in item.get("artists", []):
                index_artists[artist.casefold()].append(pid)
            if item.get("type") == "track" and item.get("name") and item.get("artists"):
                spotify_id = item.get("id") or (uri.rsplit(":", 1)[-1] if uri else None)
                observation = playability_observation(
                    item, pid, record.get("snapshot_id"),
                    item.get("playability_checked_at") or record.get("last_items_accessible_at") or record.get("captured_at"),
                    fallback_market=record.get("playability_market") or "from_token",
                    snapshot_accessible=record.get("items_accessible", True),
                )
                if observation and observation.get("requested_spotify_id"):
                    playability_observations.append(observation)
                # A relinked response describes the replacement recording, while
                # linked_from identifies the originally requested playlist track.
                # Do not merge replacement metadata into that original song.
                if item.get("linked_from"):
                    continue
                if spotify_id:
                    library_rows.append({
                        "track_id": uri or ("spotify:track:" + str(spotify_id)),
                        "spotify_id": spotify_id,
                        "artist": item["artists"][0],
                        "artist_spotify_id": (item.get("artist_ids") or [None])[0],
                        "track": item["name"],
                        "album": item.get("album") or "",
                        "spotify_album_id": item.get("album_id"),
                        "duration_ms": item.get("duration_ms"),
                        "isrc": (item.get("external_ids") or {}).get("isrc"),
                        "playlist_sources": [pid],
                        "playlist_positions": [{
                            "playlist_id": pid, "position": item.get("position"),
                            "playlist_name": record.get("name"),
                            "snapshot_id": record.get("snapshot_id"),
                        }],
                        "listening_context": {
                            "source": "Spotify reference-library snapshot",
                            "playlist_ids": [pid],
                        },
                    })
    if library_rows:
        library_result = MusicLibrary().put_catalogue(library_rows)
        print("Canonical music library updated from Spotify snapshots: "
              f"{library_result['songs']:,} songs, "
              f"{library_result['artists']:,} artists, "
              f"{library_result['albums']:,} albums.")
    playability_updated = playability_unmatched = 0
    if playability_observations:
        library = MusicLibrary()
        for observation in playability_observations:
            result = library.add_spotify_playability_observation(
                observation["requested_spotify_id"], observation
            )
            if result.get("status") == "updated":
                playability_updated += 1
            elif result.get("status") == "unmatched":
                playability_unmatched += 1
    print(f"Spotify playability observations: {len(playability_observations)} collected; "
          f"{playability_updated} song records updated; {playability_unmatched} unmatched.")
    catalog.sort(key=lambda row: (row["name"] or "").casefold())
    manager.write(CATALOG, {"version": 1, "captured_at": stamp(), "playlist_count": len(catalog), "playlists": catalog})
    manager.write(INDEX, {
        "version": 1, "generated_at": stamp(),
        "track_playlists": dict((key, list(dict.fromkeys(value))) for key, value in index_tracks.items()), "artist_playlists": dict((key, list(dict.fromkeys(value))) for key, value in index_artists.items()),
    })
    report = build_health_report(catalog, index_tracks, index_artists)
    manager.write(ROOT / "health.json", report)
    print(f"Reference library synced: {len(catalog)} playlists; {changed} new/changed snapshots.")
    print(f"Accessible item lists: {report['playlists']['accessible']}; inaccessible: {report['playlists']['inaccessible']}; incomplete: {report['playlists']['incomplete']}.")
    print(f"Catalog: {CATALOG}; history: {HISTORY_DIR}")


def _parse_observation_time(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def refresh_playability_from_spotify(library_root=None, limit=25, stale_days=90,
                                     market="from_token", sp=None, execute=False,
                                     sleep_seconds=0.25):
    """Plan or perform a bounded refresh using individual GET /tracks/{id} requests."""
    if not 1 <= int(limit) <= 50:
        raise ValueError("Playability refresh limit must be between 1 and 50 tracks.")
    if int(stale_days) < 1:
        raise ValueError("stale_days must be at least 1.")
    if market != "from_token" and not re.fullmatch(r"[A-Z]{2}", str(market)):
        raise ValueError("Market must be from_token or a two-letter ISO country code.")
    library = MusicLibrary(library_root) if library_root else MusicLibrary()
    now = datetime.now(timezone.utc)
    due = []
    spotify_ids_available = 0
    songs = library.index.get("songs") or {}
    for song_id, entry in songs.items():
        path = library.root / (entry.get("path") or "")
        record = manager.read(path, None)
        if not isinstance(record, dict):
            continue
        identity = record.get("identity") if isinstance(record.get("identity"), dict) else {}
        spotify_id = identity.get("spotify_id")
        if not isinstance(spotify_id, str) or not re.fullmatch(r"[A-Za-z0-9]{22}", spotify_id):
            continue
        spotify_ids_available += 1
        evidence = record.get("evidence") if isinstance(record.get("evidence"), dict) else {}
        playability = evidence.get("spotify_playability") if isinstance(evidence.get("spotify_playability"), dict) else {}
        latest = (playability.get("latest_by_market") or {}).get(str(market).upper())
        checked = _parse_observation_time(latest.get("checked_at")) if isinstance(latest, dict) else None
        if isinstance(latest, dict) and latest.get("latest_snapshot_accessible") is False:
            checked = None
        age_days = (now - checked).total_seconds() / 86400 if checked else None
        if checked and age_days < stale_days:
            continue
        due.append({
            "song_id": song_id,
            "spotify_id": spotify_id,
            "last_checked_at": latest.get("checked_at") if isinstance(latest, dict) else None,
            "age_days": round(age_days, 2) if age_days is not None else None,
        })
    due.sort(key=lambda row: (row["last_checked_at"] or "", row["song_id"]))
    selected = due[:int(limit)]
    report = {
        "mode": "execute" if execute else "plan",
        "market": market,
        "stale_days": int(stale_days),
        "limit": int(limit),
        "spotify_ids_available": spotify_ids_available,
        "due_count": len(due),
        "selected_count": len(selected),
        "selected": selected,
        "provider_requests": 0,
        "updated": 0,
        "unchanged": 0,
        "not_found_or_unavailable": 0,
        "unmatched": 0,
        "backup_path": None,
    }
    if not execute:
        return report
    if sp is None:
        raise ValueError("An authenticated Spotify client is required for execute mode.")

    backed_up = set()
    backup_root = None
    for position, candidate in enumerate(selected):
        spotify_id = candidate["spotify_id"]
        checked_at = datetime.now(timezone.utc).isoformat()
        try:
            track = sp.track(spotify_id, market=market)
            report["provider_requests"] += 1
            response_status = 200
        except manager.ManagerError as error:
            report["provider_requests"] += 1
            if "HTTP 404" not in str(error):
                raise
            track = None
            response_status = 404
            report["not_found_or_unavailable"] += 1

        if isinstance(track, dict):
            item = {
                "id": track.get("id"),
                "linked_from": track.get("linked_from"),
                "is_playable": track.get("is_playable"),
                "is_playable_present": "is_playable" in track,
                "playability_market": market,
                "playability_checked_at": checked_at,
                "restrictions": track.get("restrictions") or {},
                "is_local": track.get("is_local", False),
            }
            observation = playability_observation(
                item, None, None, checked_at, fallback_market=market,
                source="spotify_get_track", requested_spotify_id=spotify_id,
            )
            if observation is None:
                observation = {
                    "status": "unknown",
                    "is_playable": None,
                    "market": market,
                    "market_context": "spotify_user_account_country" if market == "from_token" else "explicit_country_market",
                    "checked_at": checked_at,
                    "provider": "Spotify",
                    "source": "spotify_get_track",
                    "playlist_id": None,
                    "playlist_snapshot_id": None,
                    "requested_spotify_id": spotify_id,
                    "returned_spotify_id": track.get("id"),
                    "linked_from_spotify_id": None,
                    "restrictions": track.get("restrictions") or {},
                    "restrictions_reason": None,
                    "reason": "is_playable_not_returned",
                    "response_status": response_status,
                }
        else:
            observation = {
                "status": "unknown",
                "is_playable": None,
                "market": market,
                "market_context": "spotify_user_account_country" if market == "from_token" else "explicit_country_market",
                "checked_at": checked_at,
                "provider": "Spotify",
                "source": "spotify_get_track",
                "playlist_id": None,
                "playlist_snapshot_id": None,
                "requested_spotify_id": spotify_id,
                "returned_spotify_id": None,
                "linked_from_spotify_id": None,
                "restrictions": {},
                "restrictions_reason": None,
                "reason": "spotify_track_not_found_or_unavailable",
                "response_status": response_status,
            }

        match = library.lookup_song(spotify_id=spotify_id)
        if match.get("status") != "matched":
            report["unmatched"] += 1
        else:
            song_id = match["song_id"]
            entry = (library.index.get("songs") or {}).get(song_id) or {}
            source_path = library.root / (entry.get("path") or "")
            if song_id not in backed_up and source_path.is_file():
                if backup_root is None:
                    stamp_id = now.strftime("%Y%m%d-%H%M%S-%f")
                    backup_root = library.root.with_name(library.root.name + ".playability-refresh-backup-" + stamp_id)
                target = backup_root / source_path.relative_to(library.root)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, target)
                backed_up.add(song_id)
            result = library.add_spotify_playability_observation(spotify_id, observation)
            if result.get("status") == "updated":
                report["updated"] += 1
            elif result.get("status") == "unchanged":
                report["unchanged"] += 1
        if sleep_seconds and position + 1 < len(selected):
            time.sleep(float(sleep_seconds))
    report["backup_path"] = str(backup_root) if backup_root else None
    return report


def backfill_playability_from_snapshots(playlist_dir=None, library_root=None):
    """Backfill timestamped playability from saved snapshots; makes no Spotify requests."""
    playlist_dir = Path(playlist_dir or PLAYLIST_DIR)
    library = MusicLibrary(library_root) if library_root else MusicLibrary()
    candidates = []
    stats = {
        "snapshots": 0, "inaccessible_snapshots": 0, "items_scanned": 0,
        "observations_found": 0, "already_present": 0, "unmatched": 0,
        "updated": 0, "backup_path": None, "provider_requests": 0,
        "spotify_playlist_writes": 0,
    }
    for path in sorted(playlist_dir.glob("*.json")):
        snapshot = manager.read(path, None)
        if not isinstance(snapshot, dict):
            continue
        stats["snapshots"] += 1
        if snapshot.get("items_accessible") is False:
            stats["inaccessible_snapshots"] += 1
        items = snapshot.get("items")
        if not isinstance(items, list):
            continue
        for item in items:
            stats["items_scanned"] += 1
            if not isinstance(item, dict) or item.get("type") not in (None, "track"):
                continue
            observation = playability_observation(
                item, snapshot.get("id") or path.stem, snapshot.get("items_snapshot_id") or snapshot.get("snapshot_id"),
                item.get("playability_checked_at") or snapshot.get("last_items_accessible_at") or snapshot.get("captured_at"),
                fallback_market=snapshot.get("playability_market") or "from_token",
                snapshot_accessible=snapshot.get("items_accessible", True),
            )
            if not observation or not observation.get("requested_spotify_id"):
                continue
            stats["observations_found"] += 1
            match = library.lookup_song(spotify_id=observation["requested_spotify_id"])
            if match.get("status") != "matched":
                stats["unmatched"] += 1
                continue
            song_id = match["song_id"]
            existing = (match.get("record", {}).get("evidence") or {}).get("spotify_playability") or {}
            if observation in (existing.get("observations") or []):
                stats["already_present"] += 1
                continue
            entry = (library.index.get("songs") or {}).get(song_id) or {}
            if entry.get("path"):
                candidates.append((song_id, observation, library.root / entry["path"]))

    if not candidates:
        return stats

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    backup_root = library.root.with_name(library.root.name + ".playability-backup-" + timestamp)
    backed_up = set()
    for song_id, observation, source_path in candidates:
        if song_id in backed_up:
            continue
        relative = source_path.relative_to(library.root)
        target = backup_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target)
        backed_up.add(song_id)
    stats["backup_path"] = str(backup_root)

    for song_id, observation, source_path in candidates:
        result = library.add_spotify_playability_observation(
            observation["requested_spotify_id"], observation
        )
        if result.get("status") == "updated":
            stats["updated"] += 1
    return stats


def build_health_report(catalog=None, index_tracks=None, index_artists=None):
    """Summarize reference-library completeness and observed feedback coverage."""
    catalog = catalog if catalog is not None else manager.read(CATALOG, {"playlists": []}).get("playlists", [])
    index_tracks = index_tracks if index_tracks is not None else manager.read(INDEX, {}).get("track_playlists", {})
    index_artists = index_artists if index_artists is not None else manager.read(INDEX, {}).get("artist_playlists", {})
    accessible = sum(1 for row in catalog if row.get("items_accessible", True))
    inaccessible = len(catalog) - accessible
    incomplete = 0
    mismatches = []
    for row in catalog:
        path = Path(row.get("record_path") or PLAYLIST_DIR / (row["id"] + ".json"))
        record = manager.read(path, {})
        total = record.get("total_items_reported")
        fetched = record.get("item_count_fetched", row.get("item_count", 0))
        if row.get("items_accessible", True) and isinstance(total, int) and total != fetched:
            incomplete += 1
            mismatches.append({"playlist_id": row["id"], "name": row.get("name"), "reported": total, "fetched": fetched})
    feedback_path = ROOT / "daily_feedback.json"
    feedback = manager.read(feedback_path, {})
    coverage = feedback.get("coverage", {})
    playback_detail = coverage.get("playback_tracker_detail", {})
    return {
        "schema_version": 1,
        "generated_at": stamp(),
        "playlists": {
            "total": len(catalog), "accessible": accessible,
            "inaccessible": inaccessible, "incomplete": incomplete,
            "item_count_mismatches": mismatches,
        },
        "index": {
            "unique_tracks": len(index_tracks), "unique_artists": len(index_artists),
        },
        "daily_feedback": {
            "tracks_observed": len(feedback.get("tracks", {})),
            "playback_tracker_status": coverage.get("playback_tracker", "unknown"),
            "playback_tracker_detail": playback_detail,
            "lastfm_status": coverage.get("lastfm", "unknown"),
            "liked_songs_status": coverage.get("liked_songs", "unknown"),
            "updated_at": feedback.get("updated_at"),
            "segments_file_in_sync_environment": Path("playback_data/segments.jsonl").is_file(),
        },
        "overall_status": "warning" if inaccessible or incomplete else "ok",
    }


def print_health_report():
    report = manager.read(ROOT / "health.json", None)
    if report is None:
        report = build_health_report()
    playlists = report["playlists"]
    print("SHIT Spotify reference-library health")
    print(f"Status: {report['overall_status']}")
    print(f"Playlists: {playlists['total']} total; {playlists['accessible']} accessible; {playlists['inaccessible']} inaccessible; {playlists['incomplete']} incomplete")
    print(f"Index: {report['index']['unique_tracks']} unique tracks; {report['index']['unique_artists']} unique artists")
    daily = report["daily_feedback"]
    print(f"Daily feedback: {daily['tracks_observed']} tracks; playback tracker {daily['playback_tracker_status']}; Last.fm {daily['lastfm_status']}; Liked Songs {daily['liked_songs_status']}")
    if not daily["segments_file_in_sync_environment"]:
        print("Playback segment file is not present in this environment; this does not mean zero listening.")
    return report


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
    sub.add_parser("health", help="Show reference-library and feedback coverage health")
    sub.add_parser("backfill-playability", help="Backfill song playability from saved snapshots without Spotify requests")
    refresh = sub.add_parser("refresh-playability", help="Plan or execute a bounded, stale-only Spotify playability refresh")
    refresh.add_argument("--limit", type=int, default=25, help="Maximum tracks to check (1-50)")
    refresh.add_argument("--stale-days", type=int, default=90, help="Recheck observations older than this many days")
    refresh.add_argument("--market", default="from_token", help="Spotify market code or from_token")
    refresh.add_argument("--execute", action="store_true", help="Perform Spotify lookups; default is read-only plan")
    refresh.add_argument("--yes", action="store_true", help="Confirm provider requests when using --execute")
    search = sub.add_parser("lookup", help="Search saved playlists, tracks, artists and albums")
    search.add_argument("query")
    args = parser.parse_args()
    if args.command == "sync":
        sync(manager.Spotify())
    elif args.command == "health":
        print_health_report()
    elif args.command == "backfill-playability":
        print(json.dumps(backfill_playability_from_snapshots(), indent=2))
    elif args.command == "refresh-playability":
        if args.execute and not args.yes:
            parser.error("refresh-playability --execute also requires --yes.")
        client = manager.Spotify() if args.execute else None
        result = refresh_playability_from_spotify(
            limit=args.limit, stale_days=args.stale_days, market=args.market,
            sp=client, execute=args.execute,
        )
        print(json.dumps(result, indent=2))
    elif args.command == "list":
        for row in manager.read(CATALOG, {"playlists": []}).get("playlists", []):
            print(f'{row.get("name")} | {row.get("item_count")} items | {row.get("id")}')
    elif args.command == "lookup":
        lookup(args.query)


if __name__ == "__main__":
    main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Collect read-only Spotify playlist snapshots and write canonical reference evidence.
# Inputs: Spotify playlist GET snapshots, configured reference/priority playlist IDs and
#         market-scoped track metadata/playability observations.
# Outputs: assistant_data/spotify snapshots/history/catalog/index/health, canonical MusicLibrary
#          song/artist/album catalogue evidence, playlist-source context and market-scoped playability.
# Semantics: Incomplete/inaccessible snapshots are not empty. Playlist membership is context,
#            not a Last.fm scrobble, measured playback, like, or proof of listening. Non-relinked
#            tracks retain identity/source/position; requested/relinked IDs stay distinct.
# Safety: Sync writes repository snapshots and canonical Library evidence but never mutates Spotify
#         playlists. Separate playability refresh is plan-only by default and requires --execute --yes
#         for bounded stale-only Spotify GETs; offline backfill uses backup-protected song-record writes.
# Run: python compat/spotify_reference_library.py sync|health|... (repository root).
# Related: docs/SPOTIFY_API_OPERATIONS.md; docs/WORKFLOWS.md;
#          scripts/spotify/track_playlist_removals.py.
# -----------------------------------------------------------------------------
