#!/usr/bin/env python3
"""Read-only field-level freshness planner for the canonical music Library.

The planner makes no provider requests and writes no files. It uses explicit
field/provider observation timestamps already present in song and artist
evidence, plus market-scoped Spotify playability. Missing timestamps are
reported rather than guessed from record/file modification times.

Run: python scripts/music/metadata_freshness.py [--limit 25] [--market from_token]
"""
import argparse
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[2] / "assistant_data/music/library"
POLICIES = {
    "spotify_playability": {"provider": "spotify", "ttl_days": 90, "priority": 100},
    "lastfm_track_tags": {"provider": "lastfm", "ttl_days": 180, "priority": 70},
    "musicbrainz_track_tags": {"provider": "musicbrainz", "ttl_days": 365, "priority": 55},
    "duration": {"provider": "source_recorded_on_song", "ttl_days": 730, "priority": 45},
    "artist_profile": {"provider": "source_recorded_on_artist", "ttl_days": 365, "priority": 35},
    "album_profile": {"provider": "source_recorded_on_album", "ttl_days": 365, "priority": 30},
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


def _cooldown_active(value, observed_at, now):
    """Respect ISO next-check times, Unix epochs, and relative retry-after seconds."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if value <= 0:
            return False
        if value > 1_000_000_000:
            try:
                return datetime.fromtimestamp(value, timezone.utc) > now
            except (OverflowError, OSError, ValueError):
                return True
        base = _parse_time(observed_at)
        # If a relative cooldown lacks a timestamp anchor, fail closed.
        return base is None or base + timedelta(seconds=value) > now
    parsed = _parse_time(value)
    return bool(parsed and parsed > now)


def _make_task(entity_type, entity_id, record, field, provider, market,
               observed_at, policy, now, status):
    parsed = _parse_time(observed_at)
    age = (now - parsed).total_seconds() / 86400 if parsed else None
    identity = record.get("identity") if isinstance(record.get("identity"), dict) else {}
    task = {
        "task_key": f"{entity_type}:{entity_id}:{field}:{provider}:{market or 'global'}",
        "entity_type": entity_type,
        "entity_id": entity_id,
        "artist": identity.get("artist") or record.get("artist"),
        "title": identity.get("title") or record.get("album") or record.get("artist"),
        "field_family": field,
        "provider": provider,
        "market": market,
        "observed_at": observed_at,
        "age_days": round(age, 2) if age is not None else None,
        "ttl_days": policy["ttl_days"],
        "priority": policy["priority"],
        "status": status,
    }
    if entity_type == "song":
        task["song_id"] = entity_id
    return task


def _consider(tasks, counts, entity_type, entity_id, record, field, provider,
              observed_at, policy, now, market=None, next_check_after=None,
              provider_status=None):
    """Count and optionally schedule one explicit field/provider observation."""
    if _cooldown_active(next_check_after, observed_at, now):
        counts["cooldown"] += 1
        return
    status = str(provider_status or "").casefold()
    if status in {"http_400", "authentication_error", "unauthorized", "blocked", "invalid_query"}:
        counts["blocked"] += 1
        return
    parsed = _parse_time(observed_at)
    if observed_at and parsed is None:
        counts["invalid_timestamp"] += 1
        return
    if parsed is None:
        counts["missing_timestamp"] += 1
        return
    age = (now - parsed).total_seconds() / 86400
    if age >= policy["ttl_days"]:
        counts["stale"] += 1
        tasks.append(_make_task(entity_type, entity_id, record, field, provider,
                                market, observed_at, policy, now, "stale"))
    else:
        counts["fresh"] += 1


def build_plan(root=DEFAULT_ROOT, limit=25, market="from_token", now=None):
    """Build a deterministic, network-free plan from field-specific evidence."""
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
        "songs_scanned": 0, "artists_scanned": 0, "albums_scanned": 0,
        "spotify_ids": 0, "fresh": 0, "stale": 0,
        "missing_observation": 0, "missing_timestamp": 0,
        "invalid_timestamp": 0, "cooldown": 0, "blocked": 0,
    }

    for path in sorted((root / "songs").rglob("song.json")):
        record, problem = _read(path)
        if problem or not isinstance(record, dict):
            errors.append({"path": str(path), "error": problem or "record must be an object"})
            continue
        counts["songs_scanned"] += 1
        song_id = record.get("id") or path.parent.name
        identity = record.get("identity") if isinstance(record.get("identity"), dict) else {}
        evidence = record.get("evidence") if isinstance(record.get("evidence"), dict) else {}
        metadata = evidence.get("track_metadata") if isinstance(evidence.get("track_metadata"), dict) else {}

        spotify_id = identity.get("spotify_id")
        if isinstance(spotify_id, str) and spotify_id.strip():
            counts["spotify_ids"] += 1
            playability = evidence.get("spotify_playability")
            latest_map = playability.get("latest_by_market") if isinstance(playability, dict) else {}
            latest = latest_map.get(market_key) if isinstance(latest_map, dict) else None
            observed_at = latest.get("checked_at") if isinstance(latest, dict) else None
            if not isinstance(latest, dict):
                counts["missing_observation"] += 1
                tasks.append(_make_task(
                    "song", song_id, record, "spotify_playability", "spotify",
                    market, None, POLICIES["spotify_playability"], now, "missing_observation"
                ))
            else:
                _consider(tasks, counts, "song", song_id, record, "spotify_playability",
                          "spotify", observed_at, POLICIES["spotify_playability"], now,
                          market=market, provider_status=latest.get("status"))

        # Track tags can be checked independently at Last.fm and MusicBrainz.
        for provider, timestamp_key, status_key, retry_key, field in (
            ("lastfm", "lastfm_checked_at", "lastfm_status", "lastfm_retry_after", "lastfm_track_tags"),
            ("musicbrainz", "musicbrainz_checked_at", "musicbrainz_status", "musicbrainz_retry_after", "musicbrainz_track_tags"),
        ):
            observed_at = metadata.get(timestamp_key)
            provider_status = metadata.get(status_key)
            if observed_at or provider_status:
                _consider(tasks, counts, "song", song_id, record, "track_tags",
                          provider, observed_at, POLICIES[field], now,
                          next_check_after=metadata.get(retry_key, metadata.get("retry_after")), provider_status=provider_status)
            else:
                counts["missing_timestamp"] += 1

        # Duration freshness follows the provider that actually supplied the duration.
        duration_source = str(metadata.get("duration_source") or "").casefold()
        if metadata.get("duration_ms") is not None:
            if "last.fm" in duration_source or "lastfm" in duration_source:
                provider, checked = "lastfm", metadata.get("lastfm_checked_at")
            elif "musicbrainz" in duration_source:
                provider, checked = "musicbrainz", metadata.get("musicbrainz_checked_at")
            else:
                provider, checked = None, None
            if provider:
                _consider(tasks, counts, "song", song_id, record, "duration",
                          provider, checked, POLICIES["duration"], now,
                          next_check_after=metadata.get(provider + "_retry_after", metadata.get("retry_after")),
                          provider_status=metadata.get(provider + "_status"))
            else:
                counts["missing_timestamp"] += 1

        # Newer ingestion paths may provide normalized explicit field observations.
        observations = _nested(record, "freshness", "observations") or {}
        if isinstance(observations, dict):
            for field in ("track_tags", "duration"):
                row = observations.get(field)
                if not isinstance(row, dict):
                    continue
                provider = str(row.get("provider") or POLICIES[field]["provider"])
                policy = POLICIES.get(field, {"ttl_days": 180, "priority": 20})
                _consider(tasks, counts, "song", song_id, record, field, provider,
                          row.get("observed_at"), policy, now,
                          next_check_after=row.get("next_check_after"), provider_status=row.get("status"))

    for path in sorted((root / "artists").rglob("artist.json")):
        record, problem = _read(path)
        if problem or not isinstance(record, dict):
            errors.append({"path": str(path), "error": problem or "record must be an object"})
            continue
        counts["artists_scanned"] += 1
        evidence = record.get("evidence") if isinstance(record.get("evidence"), dict) else {}
        source = str(evidence.get("source") or "").casefold()
        provider = "lastfm" if "last.fm" in source or "lastfm" in source else None
        if provider and evidence.get("checked_at"):
            _consider(tasks, counts, "artist", record.get("id") or path.parent.name,
                      record, "artist_profile", provider, evidence.get("checked_at"),
                      POLICIES["artist_profile"], now, provider_status=evidence.get("status"))
        else:
            counts["missing_timestamp"] += 1

    for path in sorted((root / "albums").rglob("album.json")):
        record, problem = _read(path)
        if problem or not isinstance(record, dict):
            errors.append({"path": str(path), "error": problem or "record must be an object"})
            continue
        counts["albums_scanned"] += 1
        evidence = record.get("evidence") if isinstance(record.get("evidence"), dict) else {}
        source = str(evidence.get("source") or "").casefold()
        provider = "lastfm" if "last.fm" in source or "lastfm" in source else None
        observed_at = evidence.get("checked_at") or evidence.get("lastfm_checked_at")
        if provider and observed_at:
            _consider(tasks, counts, "album", record.get("id") or path.parent.name,
                      record, "album_profile", provider, observed_at,
                      POLICIES["album_profile"], now, provider_status=evidence.get("status"))
        else:
            counts["missing_timestamp"] += 1

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
            "Artist and album profile freshness uses only source-stamped evidence; records without a field timestamp remain unscheduled.",
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
# Scope: Spotify playability, track tags/duration, and source-stamped artist/album profiles.
# Safety: No network requests, writes, provider execution, or inference from record modification times.
# Scheduling: Oldest due observation first, stable hash tie-break, bounded selection.
# Related: project/goals/metadata-freshness/README.md, RETRY_QUEUE_SPEC.md, spotify_reference_library.py.
