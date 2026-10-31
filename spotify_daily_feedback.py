#!/usr/bin/env python3
"""Exposure-aware Tricky Daily feedback: saves, post-add plays and removals.

This module records observed outcomes only. Lack of Daily listening is neutral;
missing tracker coverage is unknown rather than zero.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

DATA = Path("assistant_data/spotify/daily_feedback.json")
DAILY_ID = "4yUVHSMQySfWeEowfIMcx7"


def now():
    return datetime.now(timezone.utc).isoformat()


def read():
    if not DATA.exists():
        return {"version": 1, "tracks": {}, "coverage": {"playback_tracker": "unknown", "lastfm": "unknown"}}
    value = json.loads(DATA.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("tracks"), dict):
        raise ValueError("Daily feedback data is malformed; refusing to overwrite it.")
    return value


def write(data):
    DATA.parent.mkdir(parents=True, exist_ok=True)
    temp = DATA.with_suffix(".json.tmp")
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    try:
        temp.chmod(0o600)
    except OSError:
        pass
    temp.replace(DATA)


def record_additions(items, added_at=None, liked_at_add=None):
    """Record first and subsequent Daily additions without resetting history."""
    added_at = added_at or now()
    data = read()
    for item in items:
        uri = item.get("uri")
        if not isinstance(uri, str) or not uri.startswith("spotify:track:"):
            continue
        row = data["tracks"].setdefault(uri, {
            "uri": uri, "artist": item.get("artist"), "track": item.get("track"),
            "first_added_at": added_at, "additions": [], "liked_observations": [],
            "playback_observations": [], "removal_events": [], "liked_at_add": None,
        })
        row["additions"].append({"at": added_at, "daily_playlist_id": DAILY_ID})
        if liked_at_add and uri in liked_at_add:
            row["liked_at_add"] = bool(liked_at_add[uri])
        row["last_added_at"] = added_at
    data["updated_at"] = now()
    write(data)
    return data


def record_removal(uri, removed_at=None, reason="curator_rotation"):
    data = read()
    if uri in data["tracks"]:
        data["tracks"][uri]["removal_events"].append({
            "at": removed_at or now(), "reason": reason,
        })
        data["updated_at"] = now()
        write(data)


def observe_liked_songs(sp, uris, observed_at=None):
    """Check Spotify Liked Songs status for up to 50 tracks per request."""
    observed_at = observed_at or now()
    data = read()
    ids = [uri.rsplit(":", 1)[-1] for uri in uris if isinstance(uri, str) and uri.startswith("spotify:track:")]
    liked = {}
    for offset in range(0, len(ids), 50):
        batch = ids[offset:offset + 50]
        if not batch:
            continue
        result = sp.call("GET", "/me/library/contains?uris=" + ",".join("spotify:track:" + track_id for track_id in batch))
        for track_id, is_liked in zip(batch, result or []):
            liked["spotify:track:" + track_id] = bool(is_liked)
    for uri, value in liked.items():
        if uri in data["tracks"]:
            observations = data["tracks"][uri]["liked_observations"]
            if not observations or observations[-1].get("liked") != value:
                observations.append({"at": observed_at, "liked": value})
    data["updated_at"] = now()
    data["coverage"]["liked_songs"] = "observed"
    write(data)
    return liked


def observe_playback_segments(path=Path("playback_data/segments.jsonl")):
    """Aggregate measured tracker intervals into distinct post-add listening sessions."""
    data = read()
    if not path.is_file():
        data["coverage"]["playback_tracker"] = "unknown"
        write(data)
        return
    events = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        uri = row.get("spotify_uri") or row.get("uri")
        if uri not in data["tracks"]:
            continue
        played_at = row.get("sampled_at") or row.get("started_at") or row.get("timestamp") or row.get("at")
        if not played_at:
            continue
        last_added = data["tracks"][uri]["first_added_at"]
        try:
            when = datetime.fromisoformat(played_at.replace("Z", "+00:00"))
            if when < datetime.fromisoformat(last_added.replace("Z", "+00:00")):
                continue
        except (TypeError, ValueError):
            continue
        events.setdefault(uri, []).append((when, int(row.get("played_ms") or 0)))
    for uri, rows in events.items():
        rows.sort(key=lambda item: item[0])
        sessions = 0
        previous = None
        played_ms = 0
        for when, duration in rows:
            if previous is None or (when - previous).total_seconds() > 90:
                sessions += 1
            previous = when
            played_ms += duration
        data["tracks"][uri]["playback_observations"] = [{
            "at": now(), "plays": sessions, "played_ms": played_ms,
            "source": "spotify_playback_tracker_sessions",
        }]
    data["coverage"]["playback_tracker"] = "available"
    data["updated_at"] = now()
    write(data)


def observe_lastfm_scrobbles(path=Path("data/scrobbles.json")):
    """Count canonical Last.fm scrobbles after each Daily addition, separately from measured playback."""
    data = read()
    if not path.is_file():
        data["coverage"]["lastfm"] = "unknown"
        write(data)
        return
    targets = {}
    for uri, row in data["tracks"].items():
        artist, track = row.get("artist"), row.get("track")
        if artist and track:
            targets.setdefault((str(artist).casefold(), str(track).casefold()), []).append(uri)
    counts = {uri: 0 for uri in data["tracks"]}
    for row in json.loads(path.read_text(encoding="utf-8")):
        artist = str(row.get("artist") or "").casefold()
        track = str(row.get("track") or "").casefold()
        uris = targets.get((artist, track), [])
        if not uris:
            continue
        try:
            played_at = datetime.fromtimestamp(int(row["timestamp"]), timezone.utc)
        except (KeyError, TypeError, ValueError, OSError):
            continue
        for uri in uris:
            added_at = data["tracks"][uri].get("last_added_at") or data["tracks"][uri]["first_added_at"]
            try:
                if played_at >= datetime.fromisoformat(added_at.replace("Z", "+00:00")):
                    counts[uri] += 1
            except (TypeError, ValueError):
                continue
    for uri, count in counts.items():
        data["tracks"][uri]["lastfm_post_add_scrobbles"] = count
        data["tracks"][uri]["lastfm_observed_at"] = now()
    data["coverage"]["lastfm"] = "available"
    data["updated_at"] = now()
    write(data)


def feedback_for(uri):
    row = read()["tracks"].get(uri)
    if not row:
        return {"status": "unknown"}
    liked = row.get("liked_observations") or []
    latest_liked = liked[-1]["liked"] if liked else None
    playback = row.get("playback_observations") or []
    measured_plays = sum(int(x.get("plays") or 0) for x in playback) if playback else None
    measured_ms = sum(int(x.get("played_ms") or 0) for x in playback) if playback else None
    return {
        "status": "observed" if latest_liked is not None or measured_plays is not None or row.get("lastfm_post_add_scrobbles") is not None else "unknown",
        "liked": latest_liked,
        "liked_before_or_at_add": row.get("liked_at_add"),
        "liked_after_add": (latest_liked is True and row.get("liked_at_add") is False) if latest_liked is not None and row.get("liked_at_add") is not None else None,
        "liked_at": liked[-1].get("at") if liked else None,
        "post_add_measured_plays": measured_plays,
        "post_add_playback_ms": measured_ms,
        "post_add_lastfm_scrobbles": row.get("lastfm_post_add_scrobbles"),
        "removal_count": len(row.get("removal_events") or []),
        "additions": len(row.get("additions") or []),
        "no_listening_is_neutral": True,
    }


if __name__ == "__main__":
    raise SystemExit("Import this module from the protected Daily curator workflow.")
