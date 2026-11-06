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
        baseline = bool(liked_at_add[uri]) if liked_at_add and uri in liked_at_add else None
        row["additions"].append({"at": added_at, "daily_playlist_id": DAILY_ID, "liked_at_add": baseline})
        if baseline is not None:
            row["liked_at_add"] = baseline
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


def record_manual_removals(rows):
    """Idempotently mirror the durable Daily blacklist into outcome history.

    The complete blacklist is replayed on every snapshot refresh so a retry
    repairs partial publication. Existing feedback history is preserved.
    """
    data = read()
    changed = 0
    for item in rows if isinstance(rows, list) else []:
        if not isinstance(item, dict):
            continue
        uri = item.get("uri")
        if not isinstance(uri, str) or not uri.startswith("spotify:track:"):
            continue
        artists = item.get("artists") or []
        artist = artists[0] if artists else item.get("artist")
        track = item.get("name") or item.get("track")
        record = data["tracks"].setdefault(uri, {
            "uri": uri, "artist": artist, "track": track,
            "first_added_at": None, "additions": [], "liked_observations": [],
            "playback_observations": [], "removal_events": [], "liked_at_add": None,
        })
        events = record.setdefault("removal_events", [])
        if not isinstance(events, list):
            raise ValueError(f"Daily removal history is malformed for {uri}; refusing to overwrite it.")
        detected_at = item.get("detected_at") or item.get("removed_at") or "unknown"
        identity = (detected_at, "user_removed", item.get("last_present_cycle"))
        existing = {
            (event.get("at"), event.get("reason"), event.get("last_present_cycle"))
            for event in events if isinstance(event, dict)
        }
        if identity in existing:
            continue
        events.append({
            "at": detected_at, "reason": "user_removed",
            "source": "daily_snapshot_reconciliation",
            "last_present_cycle": item.get("last_present_cycle"),
        })
        record["last_removed_at"] = detected_at
        if artist and not record.get("artist"):
            record["artist"] = artist
        if track and not record.get("track"):
            record["track"] = track
        changed += 1
    if changed:
        data["updated_at"] = now()
        write(data)
    return changed

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
        data["coverage"]["playback_tracker_detail"] = {
            "status": "unknown", "reason": "segment_file_missing",
            "segment_count": 0, "latest_segment_at": None,
            "observed_at": now(), "file_present": False,
        }
        write(data)
        return
    events = {}
    valid_segments = 0
    latest_segment_at = None
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if not isinstance(row, dict):
            continue
        uri = row.get("spotify_uri") or row.get("uri")
        if not isinstance(uri, str) or uri not in data["tracks"]:
            continue
        played_at = row.get("sampled_at") or row.get("started_at") or row.get("timestamp") or row.get("at")
        if not isinstance(played_at, str) or not played_at:
            continue
        try:
            when = datetime.fromisoformat(played_at.replace("Z", "+00:00"))
            # Tracker timestamps should identify an absolute instant. Normalize offsets
            # before comparing or reporting the newest observation.
            if when.tzinfo is None:
                continue
            when = when.astimezone(timezone.utc)
        except (AttributeError, TypeError, ValueError):
            continue
        valid_segments += 1
        latest_segment_at = max(latest_segment_at or when.isoformat(), when.isoformat())
        last_added = data["tracks"][uri]["first_added_at"]
        try:
            added_when = datetime.fromisoformat(last_added.replace("Z", "+00:00"))
            if when < added_when:
                continue
        except (AttributeError, TypeError, ValueError):
            continue
        try:
            played_ms = max(0, int(row.get("played_ms") or 0))
        except (TypeError, ValueError, OverflowError):
            played_ms = 0
        events.setdefault(uri, []).append((when, played_ms))
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
    data["coverage"]["playback_tracker"] = "available" if valid_segments else "unknown"
    data["coverage"]["playback_tracker_detail"] = {
        "status": "available" if valid_segments else "unknown",
        "reason": None if valid_segments else "no_valid_segments_recorded",
        "segment_count": valid_segments,
        "latest_segment_at": latest_segment_at,
        "observed_at": now(),
        "file_present": True,
    }
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
            # Lifetime post-exposure scrobbles align with measured playback, which
            # is also accumulated from first_added_at. Individual additions remain
            # available in the event history for campaign-level analysis.
            added_at = data["tracks"][uri].get("first_added_at")
            # Removal-only legacy rows have no trustworthy exposure start.
            # Do not infer post-add scrobbles from an unknown timestamp.
            if not isinstance(added_at, str) or not added_at:
                continue
            try:
                if played_at >= datetime.fromisoformat(added_at.replace("Z", "+00:00")):
                    counts[uri] += 1
            except (AttributeError, TypeError, ValueError):
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
    additions = row.get("additions") or []
    latest_addition = additions[-1] if additions else {"at": row.get("first_added_at"), "liked_at_add": row.get("liked_at_add")}
    baseline = latest_addition.get("liked_at_add", row.get("liked_at_add"))
    liked_after_latest_add = None
    if latest_liked is not None and baseline is not None and liked:
        try:
            liked_after_latest_add = latest_liked is True and datetime.fromisoformat(liked[-1]["at"].replace("Z", "+00:00")) >= datetime.fromisoformat(latest_addition["at"].replace("Z", "+00:00")) and baseline is False
        except (KeyError, TypeError, ValueError):
            liked_after_latest_add = None
    playback = row.get("playback_observations") or []
    measured_plays = sum(int(x.get("plays") or 0) for x in playback) if playback else None
    measured_ms = sum(int(x.get("played_ms") or 0) for x in playback) if playback else None
    return {
        "status": "observed" if latest_liked is not None or measured_plays is not None or row.get("lastfm_post_add_scrobbles") is not None else "unknown",
        "liked": latest_liked,
        "liked_before_or_at_add": baseline,
        "liked_after_add": liked_after_latest_add,
        "liked_at": liked[-1].get("at") if liked else None,
        "post_add_measured_plays": measured_plays,
        "post_add_playback_ms": measured_ms,
        "playback_tracker_coverage": read().get("coverage", {}).get("playback_tracker", "unknown"),
        "post_add_lastfm_scrobbles": row.get("lastfm_post_add_scrobbles"),
        "removal_count": len(row.get("removal_events") or []),
        "additions": len(additions),
        "addition_history": additions,
        "no_listening_is_neutral": True,
    }


def observe_all(sp=None, playback_path=Path("playback_data/segments.jsonl"), scrobbles_path=Path("data/scrobbles.json")):
    """Refresh all available Daily outcomes without modifying any Spotify playlist."""
    import spotify_playlist_manager as manager
    sp = sp or manager.Spotify()
    uris = list(read()["tracks"])
    liked = observe_liked_songs(sp, uris) if uris else {}
    observe_playback_segments(playback_path)
    observe_lastfm_scrobbles(scrobbles_path)
    data = read()
    return {
        "tracks": len(data["tracks"]),
        "liked_tracks_checked": len(liked),
        "playback_tracker_status": data.get("coverage", {}).get("playback_tracker", "unknown"),
        "lastfm_status": data.get("coverage", {}).get("lastfm", "unknown"),
        "updated_at": data.get("updated_at"),
    }


def main():
    import argparse
    import spotify_playlist_manager as manager
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["observe"])
    parser.add_argument("--playback-path", type=Path, default=Path("playback_data/segments.jsonl"))
    parser.add_argument("--scrobbles-path", type=Path, default=Path("data/scrobbles.json"))
    args = parser.parse_args()
    report = observe_all(manager.Spotify(), args.playback_path, args.scrobbles_path)
    print("Daily feedback observation complete (read-only).")
    print(f"Tracks: {report['tracks']}; Liked Songs checked: {report['liked_tracks_checked']}")
    print(f"Playback tracker: {report['playback_tracker_status']}; Last.fm: {report['lastfm_status']}")


if __name__ == "__main__":
    main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Exposure-aware Tricky Daily observation store; records outcomes, not inferred preference.
# State: Reads/writes assistant_data/spotify/daily_feedback.json using a temporary file and atomic replace.
# Inputs: Spotify Liked Songs observations, playback_data/segments.jsonl measured intervals, and
#         data/scrobbles.json Last.fm history; these evidence sources remain explicitly separate.
# Records: First/subsequent Daily additions, likes at/after addition, measured post-add playback,
#          Last.fm scrobbles, removals, and coverage status.
# Semantics: No observed listening is neutral; missing tracker or archive coverage is unknown, not zero.
# Side effects: Local feedback JSON only; observation calls read Spotify state and never modify playlists.
# Run: python compat/spotify_daily_feedback.py observe [--playback-path PATH] [--scrobbles-path PATH].
# Related: Tricky Daily roadmap and docs/TRICKY_DAILY_CYCLE.md.
# -----------------------------------------------------------------------------
