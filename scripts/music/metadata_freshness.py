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
              provider_status=None, baseline_candidates=None, include_unknown_age=False,
              has_data=True):
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
        if not has_data:
            counts["no_data"] += 1
            return
        counts["missing_timestamp"] += 1
        if include_unknown_age and baseline_candidates is not None:
            baseline_candidates.append(_make_task(
                entity_type, entity_id, record, field, provider, market,
                None, policy, now, "baseline_required"
            ))
        return
    age = (now - parsed).total_seconds() / 86400
    if age >= policy["ttl_days"]:
        counts["stale"] += 1
        tasks.append(_make_task(entity_type, entity_id, record, field, provider,
                                market, observed_at, policy, now, "stale"))
    else:
        counts["fresh"] += 1


def _dedupe_tasks(rows):
    """Collapse duplicate provider/field tasks, preferring the newest known observation."""
    by_key = {}
    for row in rows:
        key = row["task_key"]
        prior = by_key.get(key)
        if prior is None:
            by_key[key] = row
            continue
        if prior.get("status") == "baseline_required" and row.get("status") != "baseline_required":
            by_key[key] = row
        elif row.get("observed_at") and str(row["observed_at"]) > str(prior.get("observed_at") or ""):
            by_key[key] = row
    return list(by_key.values())


def build_plan(root=DEFAULT_ROOT, limit=25, market="from_token", now=None, include_unknown_age=False):
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

    tasks, baseline_candidates, errors = [], [], []
    music_root = root.parent
    track_cache_raw, _ = _read(music_root / "track_profiles.json")
    artist_cache_raw, _ = _read(music_root / "artist_profiles.json")
    album_cache_raw, _ = _read(music_root / "album_profiles.json")
    album_state, _ = _read(music_root / "album_profile_state.json")
    track_cache_raw = track_cache_raw if isinstance(track_cache_raw, dict) else {}
    artist_cache_raw = artist_cache_raw if isinstance(artist_cache_raw, dict) else {}
    album_cache_raw = album_cache_raw if isinstance(album_cache_raw, dict) else {}
    album_state = album_state if isinstance(album_state, dict) else {}
    library_index, _ = _read(root / "library_index.json")
    library_index = library_index if isinstance(library_index, dict) else {}
    recording_aliases = library_index.get("recording_mbids") if isinstance(library_index.get("recording_mbids"), dict) else {}
    source_aliases = library_index.get("source_track_ids") if isinstance(library_index.get("source_track_ids"), dict) else {}
    spotify_aliases = library_index.get("spotify_ids") if isinstance(library_index.get("spotify_ids"), dict) else {}

    track_cache_by_song = {}
    unmatched_track_profiles = 0
    for profile_key, profile in track_cache_raw.items():
        if not isinstance(profile, dict):
            continue
        song_id = None
        mbid = str(profile.get("track_mbid") or "").strip().casefold()
        if mbid:
            song_id = recording_aliases.get(mbid) or recording_aliases.get("mbid:" + mbid)
        track_id = str(profile.get("track_id") or profile_key).strip().casefold()
        if not song_id and track_id.startswith("mbid:"):
            song_id = recording_aliases.get(track_id) or recording_aliases.get(track_id[5:])
        if not song_id and track_id.startswith("track:"):
            song_id = source_aliases.get(track_id)
        if not song_id and track_id.startswith("spotify:track:"):
            song_id = spotify_aliases.get(track_id.rsplit(":", 1)[-1])
        if song_id:
            prior = track_cache_by_song.get(song_id)
            if prior is None or str(profile.get("lastfm_checked_at") or "") >= str(prior.get("lastfm_checked_at") or ""):
                track_cache_by_song[song_id] = profile
        else:
            unmatched_track_profiles += 1

    counts = {
        "songs_scanned": 0, "artists_scanned": 0, "albums_scanned": 0,
        "spotify_ids": 0, "fresh": 0, "stale": 0,
        "missing_observation": 0, "missing_timestamp": 0, "no_data": 0, "missing_provenance": 0,
        "invalid_timestamp": 0, "cooldown": 0, "blocked": 0,
        "track_profile_cache_rows": len(track_cache_raw), "track_profile_cache_unmatched": unmatched_track_profiles,
        "artist_profile_cache_rows": len(artist_cache_raw), "album_profile_cache_rows": len(album_cache_raw),
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

        # Prefer the newest per-provider timestamp from canonical evidence or the saved profile cache.
        cached_track = track_cache_by_song.get(song_id) or {}
        for provider, timestamp_key, status_key, retry_key, field in (
            ("lastfm", "lastfm_checked_at", "lastfm_status", "lastfm_retry_after", "lastfm_track_tags"),
            ("musicbrainz", "musicbrainz_checked_at", "musicbrainz_status", "musicbrainz_retry_after", "musicbrainz_track_tags"),
        ):
            candidates = [row for row in (metadata, cached_track) if row.get(timestamp_key)]
            source_row = max(candidates, key=lambda row: str(row.get(timestamp_key) or "")) if candidates else metadata
            observed_at = source_row.get(timestamp_key)
            provider_status = source_row.get(status_key)
            tags_key = "lastfm_tags" if provider == "lastfm" else "musicbrainz_tags"
            has_data = bool(
                source_row.get(tags_key)
                or (provider == "musicbrainz" and source_row.get("musicbrainz_genres"))
                or provider_status
            )
            if observed_at or provider_status or has_data:
                _consider(tasks, counts, "song", song_id, record, "track_tags",
                          provider, observed_at, POLICIES[field], now,
                          next_check_after=source_row.get(retry_key) or source_row.get("retry_after"),
                          provider_status=provider_status, baseline_candidates=baseline_candidates,
                          include_unknown_age=include_unknown_age, has_data=has_data)
            else:
                counts["no_data"] += 1

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
                          next_check_after=metadata.get(provider + "_retry_after") or metadata.get("retry_after"),
                          provider_status=metadata.get(provider + "_status"), baseline_candidates=baseline_candidates,
                          include_unknown_age=include_unknown_age, has_data=True)
            else:
                counts["missing_provenance"] += 1

        # Newer ingestion paths may provide normalized explicit field observations.
        observations = _nested(record, "freshness", "observations") or {}
        if isinstance(observations, dict):
            for field in ("track_tags", "duration"):
                row = observations.get(field)
                if not isinstance(row, dict):
                    continue
                provider = str(row.get("provider") or "").strip()
                if not provider:
                    counts["blocked"] += 1
                    continue
                policy = POLICIES.get(field, {"ttl_days": 180, "priority": 20})
                _consider(tasks, counts, "song", song_id, record, field, provider,
                          row.get("observed_at"), policy, now,
                          next_check_after=row.get("next_check_after"), provider_status=row.get("status"),
                          baseline_candidates=baseline_candidates, include_unknown_age=include_unknown_age,
                          has_data=True)

    for path in sorted((root / "artists").rglob("artist.json")):
        record, problem = _read(path)
        if problem or not isinstance(record, dict):
            errors.append({"path": str(path), "error": problem or "record must be an object"})
            continue
        counts["artists_scanned"] += 1
        evidence = record.get("evidence") if isinstance(record.get("evidence"), dict) else {}
        artist_id = record.get("id") or path.parent.name
        cached_artist = artist_cache_raw.get(artist_id) or {}
        source = str(cached_artist.get("source") or evidence.get("source") or "").casefold()
        provider = "lastfm" if "last.fm" in source or "lastfm" in source else None
        checked_at = cached_artist.get("checked_at") or evidence.get("checked_at")
        has_profile_data = bool(
            cached_artist
            or evidence.get("tags") or evidence.get("genres") or evidence.get("themes")
            or (provider and evidence.get("status"))
        )
        if provider and (checked_at or has_profile_data):
            _consider(tasks, counts, "artist", artist_id, record, "artist_profile",
                      provider, checked_at, POLICIES["artist_profile"], now,
                      next_check_after=cached_artist.get("retry_after"),
                      provider_status=cached_artist.get("status") or evidence.get("status"),
                      baseline_candidates=baseline_candidates, include_unknown_age=include_unknown_age,
                      has_data=has_profile_data)
        else:
            counts["no_data"] += 1

    for path in sorted((root / "albums").rglob("album.json")):
        record, problem = _read(path)
        if problem or not isinstance(record, dict):
            errors.append({"path": str(path), "error": problem or "record must be an object"})
            continue
        counts["albums_scanned"] += 1
        evidence = record.get("evidence") if isinstance(record.get("evidence"), dict) else {}
        album_id = record.get("id") or path.parent.name
        cached_album = album_cache_raw.get(album_id) or {}
        source = str(cached_album.get("source") or evidence.get("source") or "").casefold()
        provider = "lastfm" if "last.fm" in source or "lastfm" in source else None
        observed_at = (
            cached_album.get("lastfm_info_checked_at") or cached_album.get("checked_at")
            or evidence.get("checked_at") or evidence.get("lastfm_checked_at")
        )
        global_album_cooldown = album_state.get("provider_retry_after")
        has_profile_data = bool(
            cached_album
            or evidence.get("lastfm_tracklist") or evidence.get("lastfm_summary")
            or evidence.get("lastfm_info_tags") or evidence.get("lastfm_artwork_url")
        )
        if provider and (observed_at or has_profile_data):
            _consider(tasks, counts, "album", album_id, record, "album_profile",
                      provider, observed_at, POLICIES["album_profile"], now,
                      next_check_after=max(
                          int(cached_album.get("lastfm_info_retry_after", 0) or 0),
                          int(global_album_cooldown or 0),
                      ),
                      provider_status=cached_album.get("lastfm_info_status") or cached_album.get("status") or evidence.get("status"),
                      baseline_candidates=baseline_candidates, include_unknown_age=include_unknown_age,
                      has_data=has_profile_data)
        else:
            counts["no_data"] += 1

    tasks = _dedupe_tasks(tasks)
    baseline_candidates = _dedupe_tasks(baseline_candidates)

    # Oldest observations first; stable task hash breaks ties.
    tasks.sort(key=lambda row: (
        row["observed_at"] or "",
        -row["priority"],
        hashlib.sha256(row["task_key"].encode("utf-8")).hexdigest(),
    ))
    baseline_candidates.sort(key=lambda row: row["task_key"])
    selected_due = tasks[:int(limit)]
    selected = list(selected_due)
    rotation_week = now.isocalendar().year * 53 + now.isocalendar().week - 1
    if include_unknown_age and len(selected) < int(limit) and baseline_candidates:
        offset = (rotation_week * int(limit)) % len(baseline_candidates)
        rotated = baseline_candidates[offset:] + baseline_candidates[:offset]
        selected.extend(rotated[:int(limit) - len(selected)])
    selected_baseline_count = sum(row["status"] == "baseline_required" for row in selected)
    return {
        "schema_version": 1,
        "generated_at": now.isoformat(),
        "mode": "read_only_plan",
        "market": market,
        "limit": int(limit),
        "include_unknown_age": bool(include_unknown_age),
        "baseline_rotation_week": rotation_week,
        "policies": POLICIES,
        "counts": counts,
        "due_task_count": len(tasks),
        "baseline_candidate_count": len(baseline_candidates),
        "selected_due_count": len(selected_due),
        "selected_baseline_count": selected_baseline_count,
        "selected_task_count": len(selected),
        "selected": selected,
        "unselected_due_count": max(0, len(tasks) - len(selected_due)),
        "unselected_baseline_count": max(0, len(baseline_candidates) - selected_baseline_count),
        "errors": errors[:50],
        "provider_requests": 0,
        "writes": 0,
        "notes": [
            "Only explicit field/provider observation timestamps are eligible for stale metadata refresh.",
            "Record modified times are not used as metadata observation times.",
            "Missing timestamps are counted only for fields with existing data; absent fields are reported separately as no_data.",
            "When enabled, unknown-age baseline candidates are rotated deterministically by ISO week; this still only plans and never fetches.",
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
    parser.add_argument("--include-unknown-age", action="store_true", help="include a deterministic rotating sample of fields with data but no observation timestamp")
    parser.add_argument("--include-unknown-age", action="store_true", help="include a deterministic rotating sample of fields with data but no observation timestamp")
    args = parser.parse_args(argv)
    report = build_plan(args.root, args.limit, args.market, include_unknown_age=args.include_unknown_age)
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
