#!/usr/bin/env python3
"""Read-only, exposure-aware tracking for Spotify's Discover Weekly playlist.

Spotify does not expose the Discover Weekly "hide track" action or its event
history through the public Web API. Disappearances are therefore recorded as
playlist changes, never asserted to be explicit hides.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import spotify_playlist_manager as manager

ROOT = Path("assistant_data/spotify")
CATALOG = ROOT / "playlists.json"
PLAYLIST_DIR = ROOT / "playlists"
DATA = ROOT / "discover_weekly_feedback.json"
PLAYLIST_NAME = "Discover Weekly"


def now():
    return datetime.now(timezone.utc).isoformat()


def read_json(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.replace(path)


def find_playlist(catalog, playlist_name=PLAYLIST_NAME):
    rows = catalog.get("playlists", []) if isinstance(catalog, dict) else []
    matches = [row for row in rows if str(row.get("name") or "").strip().casefold() == playlist_name.casefold()]
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one {playlist_name!r} playlist in the Spotify reference catalog; found {len(matches)}. "
            "Refusing to guess or treat a missing playlist as empty."
        )
    return matches[0]


def _track_items(snapshot):
    return {
        row["uri"]: {
            "uri": row["uri"],
            "spotify_id": row.get("id") or row["uri"].rsplit(":", 1)[-1],
            "artist": (row.get("artists") or [""])[0],
            "track": row.get("name") or "",
            "album": row.get("album"),
        }
        for row in snapshot.get("items", [])
        if isinstance(row, dict) and isinstance(row.get("uri"), str) and row["uri"].startswith("spotify:track:")
    }


def _liked_status(sp, uris):
    result = {}
    ids = [uri.rsplit(":", 1)[-1] for uri in sorted(set(uris))]
    for offset in range(0, len(ids), 50):
        batch = ids[offset:offset + 50]
        if not batch:
            continue
        response = sp.call("GET", "/me/library/contains?uris=" + ",".join("spotify:track:" + item for item in batch))
        for track_id, liked in zip(batch, response or []):
            result["spotify:track:" + track_id] = bool(liked)
    return result


def _lastfm_counts(path, tracks, appeared_at):
    """Count Last.fm scrobbles after first recorded exposure; never call these Spotify plays."""
    path = Path(path)
    if not path.is_file():
        return None
    targets = {}
    for uri, row in tracks.items():
        key = (str(row.get("artist") or "").casefold(), str(row.get("track") or "").casefold())
        if all(key):
            targets.setdefault(key, []).append(uri)
    counts = {uri: 0 for uri in tracks}
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    for row in rows if isinstance(rows, list) else []:
        key = (str(row.get("artist") or "").casefold(), str(row.get("track") or "").casefold())
        for uri in targets.get(key, []):
            try:
                played = datetime.fromtimestamp(int(row["timestamp"]), timezone.utc)
                exposed = datetime.fromisoformat(appeared_at[uri].replace("Z", "+00:00"))
                if played >= exposed:
                    counts[uri] += 1
            except (KeyError, TypeError, ValueError, OSError):
                continue
    return counts


def observe(sp=None, *, catalog_path=CATALOG, playlist_dir=PLAYLIST_DIR,
            data_path=DATA, scrobbles_path=Path("data/scrobbles.json"), observed_at=None):
    """Record one complete reference snapshot and current liked status; never edits Spotify."""
    sp = sp or manager.Spotify()
    observed_at = observed_at or now()
    catalog = read_json(catalog_path, {})
    playlist = find_playlist(catalog)
    playlist_id = playlist.get("id")
    if not playlist_id:
        raise RuntimeError("Discover Weekly catalog entry has no playlist ID; refusing to guess.")
    snapshot = read_json(Path(playlist_dir) / (str(playlist_id) + ".json"), {})
    if snapshot.get("items_accessible") is not True:
        raise RuntimeError("Discover Weekly snapshot is inaccessible; refusing to infer an empty playlist.")
    reported, fetched = snapshot.get("total_items_reported"), snapshot.get("item_count_fetched")
    items = snapshot.get("items")
    if not isinstance(items, list) or not isinstance(reported, int) or reported != fetched or len(items) != fetched:
        raise RuntimeError("Discover Weekly snapshot is incomplete; refusing to publish feedback.")
    snapshot_id = snapshot.get("items_snapshot_id") or snapshot.get("snapshot_id")
    if not snapshot_id:
        raise RuntimeError("Discover Weekly snapshot has no Spotify snapshot ID.")

    data = read_json(data_path, {
        "version": 1, "playlist_id": playlist_id, "playlist_name": PLAYLIST_NAME,
        "tracks": {}, "snapshots": [], "coverage": {
            "playlist_snapshots": "unknown", "liked_songs": "unknown",
            "explicit_hidden_events": "unsupported_by_spotify_web_api",
            "spotify_playback_tracker": "unknown", "lastfm_scrobbles": "unknown",
        },
    })
    if data.get("playlist_id") not in (None, playlist_id):
        raise RuntimeError("Saved Discover Weekly feedback belongs to a different playlist ID.")
    data["playlist_id"] = playlist_id
    data["playlist_name"] = PLAYLIST_NAME
    current = _track_items(snapshot)
    previous = data.get("last_snapshot") or {}
    previous_uris = set(previous.get("uris") or [])
    current_uris = set(current)
    tracks = data.setdefault("tracks", {})
    is_new_snapshot = snapshot_id != previous.get("snapshot_id")
    has_previous = bool(previous.get("snapshot_id"))
    added = sorted(current_uris - previous_uris) if is_new_snapshot else []
    disappeared = sorted(previous_uris - current_uris) if has_previous and is_new_snapshot else []

    if is_new_snapshot:
        for uri in added:
            item = current[uri]
            row = tracks.setdefault(uri, {
                **item, "appearances": [], "disappearance_events": [],
                "liked_observations": [], "first_seen_at": observed_at,
            })
            row.update({key: value for key, value in item.items() if value not in (None, "")})
            row["appearances"].append({"at": observed_at, "snapshot_id": snapshot_id})
        for uri in disappeared:
            if uri in tracks:
                tracks[uri].setdefault("disappearance_events", []).append({
                    "at": observed_at, "snapshot_id": snapshot_id,
                    "reason": "absent_from_later_playlist_snapshot",
                    "explicitly_hidden": None,
                })
        data.setdefault("snapshots", []).append({
            "snapshot_id": snapshot_id, "captured_at": snapshot.get("captured_at") or observed_at,
            "observed_at": observed_at, "track_count": len(current),
            "uris": sorted(current_uris),
        })
        data["last_snapshot"] = {
            "snapshot_id": snapshot_id, "observed_at": observed_at,
            "uris": sorted(current_uris),
        }

    # Check liked status for every track ever exposed, not just current members.
    liked = _liked_status(sp, tracks.keys()) if tracks else {}
    for uri, value in liked.items():
        row = tracks[uri]
        observations = row.setdefault("liked_observations", [])
        if not observations or observations[-1].get("liked") != value:
            observations.append({"at": observed_at, "liked": value})
        appearances = row.get("appearances") or []
        if appearances and appearances[0].get("liked_at_appearance") is None:
            appearances[0]["liked_at_appearance"] = value
    appeared_at = {
        uri: (row.get("first_seen_at") or observed_at)
        for uri, row in tracks.items()
    }
    scrobbles = _lastfm_counts(scrobbles_path, tracks, appeared_at)
    if scrobbles is not None:
        for uri, count in scrobbles.items():
            tracks[uri]["lastfm_post_first_exposure_scrobbles"] = count
            tracks[uri]["lastfm_observed_at"] = observed_at

    data["coverage"].update({
        "playlist_snapshots": "observed",
        "liked_songs": "observed" if tracks else "no_tracks_to_check",
        "explicit_hidden_events": "unsupported_by_spotify_web_api",
        "spotify_playback_tracker": "unknown",
        "lastfm_scrobbles": "observed" if scrobbles is not None else "unknown",
    })
    data["updated_at"] = observed_at
    write_json(data_path, data)
    report = {
        "playlist_id": playlist_id, "snapshot_id": snapshot_id,
        "snapshot_changed": is_new_snapshot, "current_tracks": len(current),
        "newly_appeared": len(added), "disappeared_since_previous_snapshot": len(disappeared),
        "tracks_with_feedback_history": len(tracks),
        "liked_tracks_checked": len(liked),
        "explicit_hidden_events": "not exposed by Spotify Web API; disappearances are not labelled as hides",
        "lastfm_scrobbles": "observed" if scrobbles is not None else "unknown",
        "spotify_playback_tracker": "unknown",
        "data_path": str(data_path),
    }
    print("Discover Weekly feedback observation complete (read-only).")
    print(json.dumps(report, indent=2))
    return report


def main():
    try:
        observe()
    except RuntimeError as error:
        # Do not break the account-wide reference sync when Spotify does not
        # expose Discover Weekly in the user playlist catalog. Emit an explicit
        # warning; never manufacture an empty baseline.
        print(f"::warning::Discover Weekly observation skipped: {error}")


if __name__ == "__main__":
    main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Exposure-aware history and feedback observations for Spotify Discover Weekly.
# Evidence: Snapshot appearances/disappearances, Liked Songs status changes, and
#           separately labelled post-exposure Last.fm scrobbles.
# Limits: Spotify's public Web API does not expose explicit Discover Weekly hide
#         actions; disappearance is never asserted to mean a user hide.
# Safety: Read-only with respect to Spotify playlists; incomplete snapshots fail closed.
# Storage: assistant_data/spotify/discover_weekly_feedback.json
# Run: python compat/spotify_discover_weekly_feedback.py
# Related: scripts/spotify/spotify_reference_library.py; spotify_daily_feedback.py.
# -----------------------------------------------------------------------------
