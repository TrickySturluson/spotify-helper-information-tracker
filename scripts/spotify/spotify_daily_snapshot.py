#!/usr/bin/env python3
"""Refresh only the Tricky Daily Spotify snapshot and reconcile manual removals.

This is a read-only Spotify operation. It never adds, removes, reorders, or edits
playlist metadata. Repository snapshot, history, baseline, blacklist, and audit
files may be updated after a complete live read.
"""
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# Keep maintained implementations ahead of compatibility launchers.
# The compat shims import these modules by their legacy top-level names; placing
# compat first makes a shim import itself (for example, spotify_listening_trends).
SOURCE_DIR = ROOT / "scripts" / "spotify"
COMPAT_DIR = ROOT / "compat"
for entry in (ROOT, COMPAT_DIR):
    if str(entry) in sys.path:
        sys.path.remove(str(entry))
    sys.path.append(str(entry))
if str(SOURCE_DIR) in sys.path:
    sys.path.remove(str(SOURCE_DIR))
sys.path.insert(0, str(SOURCE_DIR))

import spotify_playlist_manager as manager
import spotify_discovery as discovery
import spotify_reference_library as reference_library
import spotify_daily_feedback as daily_feedback

DAILY_ID = "4yUVHSMQySfWeEowfIMcx7"
SNAPSHOT_PATH = Path("assistant_data/spotify/playlists") / f"{DAILY_ID}.json"
HISTORY_PATH = Path("assistant_data/spotify/history") / DAILY_ID


def build_daily_reference_updates(catalog, index, previous, record):
    """Update only Tricky Daily's catalog row and track/artist index memberships."""
    if not isinstance(catalog, dict) or not isinstance(catalog.get("playlists"), list):
        raise manager.ManagerError("Spotify reference catalog is missing or malformed; refusing a partial Daily refresh.")
    if not isinstance(index, dict):
        raise manager.ManagerError("Spotify reference index is missing or malformed; refusing a partial Daily refresh.")
    track_map = index.get("track_playlists")
    artist_map = index.get("artist_playlists")
    if not isinstance(track_map, dict) or not isinstance(artist_map, dict):
        raise manager.ManagerError("Spotify reference index maps are missing or malformed; refusing a partial Daily refresh.")
    rows = catalog["playlists"]
    daily_row = next((row for row in rows if isinstance(row, dict) and row.get("id") == DAILY_ID), None)
    if daily_row is None:
        raise manager.ManagerError("Tricky Daily is absent from the reference catalog; refusing to invent a partial catalog.")

    old_items = previous.get("items", []) if isinstance(previous, dict) else []
    new_items = record.get("items", [])
    if not isinstance(old_items, list) or not isinstance(new_items, list):
        raise manager.ManagerError("Daily snapshot item lists are malformed; refusing to update reference indexes.")

    def track_keys(items):
        return {
            row.get("uri") for row in items
            if isinstance(row, dict) and isinstance(row.get("uri"), str) and row.get("uri")
        }

    def artist_keys(items):
        return {
            artist.casefold()
            for row in items if isinstance(row, dict)
            for artist in (row.get("artists") or [])
            if isinstance(artist, str) and artist.strip()
        }

    def reconcile_memberships(mapping, new_keys, label):
        # Reconcile every existing Daily membership, not only keys in the prior
        # snapshot: a previous interrupted/stale sync may already have left
        # orphaned Daily links outside that snapshot.
        for key, values in list(mapping.items()):
            if not isinstance(values, list):
                raise manager.ManagerError(f"Reference {label} index entry is malformed for {key!r}.")
            if DAILY_ID in values and key not in new_keys:
                remaining = list(dict.fromkeys(pid for pid in values if pid != DAILY_ID))
                if remaining:
                    mapping[key] = remaining
                else:
                    mapping.pop(key, None)
        for key in new_keys:
            values = mapping.get(key, [])
            if not isinstance(values, list):
                raise manager.ManagerError(f"Reference {label} index entry is malformed for {key!r}.")
            if DAILY_ID not in values:
                mapping[key] = [*values, DAILY_ID]

    old_track_keys = track_keys(old_items)
    new_track_keys = track_keys(new_items)
    new_artist_keys = artist_keys(new_items)
    reconcile_memberships(track_map, new_track_keys, "track")
    reconcile_memberships(artist_map, new_artist_keys, "artist")

    changed = (
        previous.get("snapshot_id") != record.get("snapshot_id")
        or old_track_keys != new_track_keys
    ) if isinstance(previous, dict) else True
    daily_row.update({
        "name": record.get("name"),
        "owner": record.get("owner"),
        "public": record.get("public"),
        "collaborative": record.get("collaborative"),
        "snapshot_id": record.get("snapshot_id"),
        "item_count": record.get("item_count_fetched"),
        "items_accessible": True,
        "last_items_accessible_at": record.get("last_items_accessible_at") or record.get("captured_at"),
        "captured_at": record.get("captured_at"),
        "record_path": str(SNAPSHOT_PATH),
        "changed": changed,
    })
    catalog["captured_at"] = record.get("captured_at")
    index["generated_at"] = record.get("captured_at")
    return catalog, index


def refresh():
    manager.CID = os.environ["SPOTIFY_CLIENT_ID"]
    manager.TOKEN = Path(".spotify_playlist_token.json")
    manager.CONFIG = Path(".github/spotify_playlist_manager_state.json")
    manager.AUDIT = Path(".github/spotify_playlist_manager_audit.jsonl")
    manager.write(manager.TOKEN, {
        "refresh_token": os.environ["SPOTIFY_REFRESH_TOKEN"],
        "obtained_at": 0,
        "expires_in": 0,
    })

    config = manager.config()
    cycle_state = config.get("daily_cycle") or {}
    cycle_marker = cycle_state.get("last_cycle_at")
    if not cycle_marker:
        raise manager.ManagerError(
            "Daily snapshot refresh is blocked: no accepted-cycle marker exists "
            "to safely reconcile manual removals."
        )

    manager.check_spotify_cooldown()
    sp = manager.Spotify()
    me = sp.me()
    playlist = sp.call("GET", f"/playlists/{DAILY_ID}")
    if not isinstance(playlist, dict) or playlist.get("id") != DAILY_ID:
        raise manager.ManagerError("Spotify did not return the exact Tricky Daily playlist.")
    if (playlist.get("owner") or {}).get("id") != me.get("id"):
        raise manager.ManagerError("Tricky Daily is not owned by the authenticated Spotify account.")
    if (playlist.get("name") or "").strip().casefold() != "tricky daily":
        raise manager.ManagerError("The exact playlist ID no longer has the expected Tricky Daily name.")

    cached = manager.read(SNAPSHOT_PATH, {})
    record = reference_library.playlist_record(sp, playlist, cached)
    if record.get("items_accessible") is not True:
        raise manager.ManagerError(
            "Spotify did not provide accessible Tricky Daily items; refusing to replace "
            "the last known-good snapshot or removal baseline."
        )
    reported = record.get("total_items_reported")
    fetched = record.get("item_count_fetched")
    items = record.get("items")
    if not isinstance(reported, int) or reported != fetched or not isinstance(items, list) or len(items) != fetched:
        raise manager.ManagerError(
            f"Tricky Daily snapshot is incomplete (reported={reported}, fetched={fetched}); "
            "refusing to replace the last known-good snapshot."
        )
    uris = [row.get("uri") for row in items if isinstance(row, dict)]
    if len(uris) != len(items) or any(not isinstance(uri, str) or not uri.startswith("spotify:track:") for uri in uris):
        raise manager.ManagerError("Tricky Daily snapshot contains unavailable or invalid track rows.")

    catalog = manager.read(reference_library.CATALOG, None)
    index = manager.read(reference_library.INDEX, None)
    catalog_update, index_update = build_daily_reference_updates(
        catalog, index, cached if isinstance(cached, dict) else {}, record
    )

    removal_result = discovery.reconcile_daily_manual_removals(
        items, cycle_marker,
        baseline_path=Path("playlist_removal_baseline.json"),
        blacklist_path=Path("playlist_removed_tracks.json"),
    )
    if removal_result.get("status") == "skipped":
        manager.audit(
            event="daily_snapshot_refresh_removal_reconciliation_skipped",
            playlist_id=DAILY_ID,
            reason=removal_result.get("reason"),
            cycle_marker=cycle_marker,
            snapshot_id=record.get("snapshot_id"),
        )
        raise manager.ManagerError(
            "Live snapshot was readable, but the manual-removal baseline was not aligned "
            f"with the accepted Daily cycle ({removal_result.get('reason')}); refusing to "
            "advance the baseline or publish a potentially unsafe snapshot."
        )

    # Replay the complete blacklist to recover interrupted feedback publication.
    removal_payload = manager.read(Path("playlist_removed_tracks.json"), {})
    daily_removals = (
        ((removal_payload.get("playlists") or {}).get(DAILY_ID) or {}).get("removed", [])
        if isinstance(removal_payload, dict) else []
    )
    feedback_events_added = daily_feedback.record_manual_removals(daily_removals)
    previous = cached if isinstance(cached, dict) else {}
    if (
        previous.get("items_accessible") is True
        and previous.get("snapshot_id")
        and previous.get("snapshot_id") != record.get("snapshot_id")
    ):
        HISTORY_PATH.mkdir(parents=True, exist_ok=True)
        captured = previous.get("captured_at")
        try:
            old_name = datetime.fromisoformat(str(captured).replace("Z", "+00:00")).astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".json"
        except (TypeError, ValueError):
            old_name = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "_prior.json"
        old_path = HISTORY_PATH / old_name
        if not old_path.exists():
            manager.write(old_path, previous)

    manager.write(SNAPSHOT_PATH, record)
    manager.write(reference_library.CATALOG, catalog_update)
    manager.write(reference_library.INDEX, index_update)
    manager.write(
        reference_library.ROOT / "health.json",
        reference_library.build_health_report(
            catalog_update["playlists"],
            index_update["track_playlists"],
            index_update["artist_playlists"],
        ),
    )
    baseline_count = discovery.write_daily_removal_baseline(
        items, cycle_marker, baseline_path=Path("playlist_removal_baseline.json")
    )
    manager.audit(
        event="daily_snapshot_refresh_completed",
        playlist_id=DAILY_ID,
        snapshot_id=record.get("snapshot_id"),
        captured_at=record.get("captured_at"),
        item_count=fetched,
        unique_uri_count=len(set(uris)),
        duplicate_uri_count=len(uris) - len(set(uris)),
        removal_reconciliation=removal_result,
        manual_removal_feedback_events_added=feedback_events_added,
        baseline_count=baseline_count,
        spotify_requests=sp.request_metrics,
        spotify_playlist_mutations=0,
    )
    print(
        f"Tricky Daily snapshot refreshed: {fetched} accessible items; "
        f"{len(set(uris))} unique URIs; {removal_result.get('newly_removed', 0)} "
        f"new manual removals recorded; {removal_result.get('removed_total', 0)} "
        f"total blacklisted; {feedback_events_added} removal feedback events reconciled; "
        f"snapshot_id={record.get('snapshot_id')}."
    )


if __name__ == "__main__":
    try:
        refresh()
    except (manager.ManagerError, OSError, KeyError, ValueError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Refresh only the Tricky Daily reference snapshot and detect manual removals.
# Spotify access: GET-only; validates account ownership, exact playlist identity,
#                 item accessibility, and complete pagination before publishing.
# Repository outputs: Daily snapshot/history, catalog/index/health, removal baseline, blacklist, feedback, manager audit.
# Safety: Reconciles removals against the last accepted-cycle marker before advancing
#         the baseline. An unaligned baseline or incomplete live read fails closed.
# Run: python scripts/spotify/spotify_daily_snapshot.py (repository root).
# Related: spotify_discovery.py, spotify_reference_library.py, TRICKY_DAILY_CYCLE.md.
# -----------------------------------------------------------------------------
