#!/usr/bin/env python3
"""Read-only field-level freshness planner for the canonical music Library.

The planner makes no provider requests and writes no files. It schedules only
fields with explicit field/provider observation timestamps, plus Spotify
playability for the requested market. Missing timestamps are reported rather
than guessed from a record's modified time.

Run: python scripts/music/metadata_freshness.py [--limit 25] [--market from_token]
"""
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[2] / "assistant_data/music/library"
POLICIES = {
    "spotify_playability": {"provider": "spotify", "ttl_days": 90, "priority": 100},
    "track_tags": {"provider": "lastfm", "ttl_days": 180, "priority": 60},
    "artist_profile": {"provider": "lastfm", "ttl_days": 365, "priority": 35},
    "album_profile": {"provider": "lastfm", "ttl_days": 365, "priority": 30},
    "duration": {"provider": "musicbrainz", "ttl_days": 730, "priority": 20},
}


def _parse_time(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def _read(path):
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return None, f"{type(error).__name__}: {error}"


def _nested(value, *keys):
    current = value
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _generic_observation(record, field):
    freshness = record.get("freshness") if isinstance(record.get("freshness"), dict) else {}
    observations = freshness.get("observations") if isinstance(freshness.get("observations"), dict) else {}
    row = observations.get(field)
    if isinstance(row, dict) and "observed_at" in row:
        return row
    return None


def _task(song_id, record, field, provider, market, observed_at, policy, now):
    parsed = _parse_time(observed_at)
    age = (now - parsed).total_seconds() / 86400 if parsed else None
    return {
        "task_key": f"{song_id}:{field}:{provider}:{market or 'global'}",
        "song_id": song_id,
        "artist": _nested(record, "identity", "artist"),
        "title": _nested(record, "identity", "title"),
        "field_family": field,
        "provider": provider,
        "market": market,
        "observed_at": observed_at,
        "age_days": round(age, 2) if age is not None else None,
        "ttl_days": policy["ttl_days"],
        "priority": policy["priority"],
        "status": "missing_observation" if parsed is None else "stale",
    }


def build_plan(root=DEFAULT_ROOT, limit=25, market="from_token", now=None):
    """Build a deterministic, network-free plan from explicit observation evidence."""
    root = Path(root)
    if not 1 <= int(limit) <= 100:
        raise ValueError("limit must be between 1 and 100")
    market = "from_token" if str(market).casefold() == "from_token" else str(market).upper()
    if market != "from_token" and not re.fullmatch(r"[A-Z]{2}", market):
        raise ValueError("market must be from_token or a two-letter ISO country code")
    market_key = market.upper()
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    now = now.astimezone(timezone.utc)

    tasks, errors = [], []
    counts = {
        "songs_scanned": 0, "spotify_ids": 0, "fresh": 0,
        "stale": 0, "missing_observation": 0, "missing_timestamp": 0,
        "invalid_timestamp": 0, "cooldown": 0,
    }
    for path in sorted((root / "songs").rglob("song.json")):
        record, problem = _read(path)
        if problem or not isinstance(record, dict):
            errors.append({"path": str(path), "error": problem or "record must be an object"})
            continue
        counts["songs_scanned"] += 1
        song_id = record.get("id") or path.parent.name
        identity = record.get("identity") if isinstance(record.get("identity"), dict) else {}
        spotify_id = identity.get("spotify_id")
        if isinstance(spotify_id, str) and spotify_id.strip():
            counts["spotify_ids"] += 1
            playability = _nested(record, "evidence", "spotify_playability")
            latest_map = playability.get("latest_by_market") if isinstance(playability, dict) else {}
            latest = latest_map.get(market_key) if isinstance(latest_map, dict) else None
            observed_at = latest.get("checked_at") if isinstance(latest, dict) else None
            policy = POLICIES["spotify_playability"]
            parsed = _parse_time(observed_at)
            if parsed is None:
                # Unknown-market snapshots do not satisfy a current-market check.
                counts["missing_observation"] += 1
                tasks.append(_task(song_id, record, "spotify_playability", "spotify",
                                   market, None, policy, now))
            else:
                age = (now - parsed).total_seconds() / 86400
                if age >= policy["ttl_days"]:
                    counts["stale"] += 1
                    tasks.append(_task(song_id, record, "spotify_playability", "spotify",
                                       market, observed_at, policy, now))
                else:
                    counts["fresh"] += 1

        for field in ("track_tags", "artist_profile", "album_profile", "duration"):
            observation = _generic_observation(record, field)
            if observation is None:
                # No reliable field-specific timestamp: do not infer age from file/record timestamps.
                counts["missing_timestamp"] += 1
                continue
            provider = str(observation.get("provider") or POLICIES[field]["provider"])
            observed_at = observation.get("observed_at")
            parsed = _parse_time(observed_at)
            next_check = _parse_time(observation.get("next_check_after"))
            if next_check and next_check > now:
                counts["cooldown"] += 1
                continue
            if parsed is None:
                counts["invalid_timestamp"] += 1
                continue
            age = (now - parsed).total_seconds() / 86400
            if age >= POLICIES[field]["ttl_days"]:
                counts["stale"] += 1
                tasks.append(_task(song_id, record, field, provider, None,
                                   observed_at, POLICIES[field], now))
            else:
                counts["fresh"] += 1

    # Oldest observations first; stable task hash breaks ties and makes repeat plans identical.
    tasks.sort(key=lambda row: (
        row["observed_at"] or "",
        -row["priority"],
        hashlib.sha256(row["task_key"].encode("utf-8")).hexdigest(),
    ))
    selected = tasks[:int(limit)]
    return {
        "schema_version": 1,
        "generated_at": now.isoformat(),
        "mode": "read_only_plan",
        "market": market,
        "limit": int(limit),
        "policies": POLICIES,
        "counts": counts,
        "due_task_count": len(tasks),
        "selected_task_count": len(selected),
        "selected": selected,
        "unselected_due_count": max(0, len(tasks) - len(selected)),
        "errors": errors[:50],
        "provider_requests": 0,
        "writes": 0,
        "notes": [
            "Only explicit field/provider observation timestamps are eligible for stale metadata refresh.",
            "Record modified times are not used as metadata observation times.",
            "Missing field timestamps are reported, not automatically fetched.",
            "Spotify playability is evaluated separately for the requested market; unknown-market evidence is not treated as current-market confirmation.",
            "This planner does not execute lookups or mutate the Library.",
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--market", default="from_token")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = build_plan(args.root, args.limit, args.market)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if not report["errors"] else 2


if __name__ == "__main__":
    raise SystemExit(main())


# FILE OVERVIEW
# Purpose: Deterministic read-only planner for field/provider-specific metadata freshness.
# Scope: Spotify playability plus explicit freshness.observations for tags, artist/album profiles and duration.
# Safety: No network requests, writes, provider execution, or inference from record modification times.
# Scheduling: Oldest due observation first, stable hash tie-break, bounded selection.
# Related: project/goals/metadata-freshness/README.md, RETRY_QUEUE_SPEC.md, spotify_reference_library.py.
