#!/usr/bin/env python3
"""Append-only, source-aware recommendation memory for Tricky Daily.

The ledger is descriptive: it never changes candidate scoring, playlist policy,
playlist-manager state/audit, Spotify, Last.fm, or the canonical Music Library.
"""
import argparse
import gzip
import hashlib
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

DAILY_ID = "4yUVHSMQySfWeEowfIMcx7"
SCHEMA_VERSION = 1
STRATEGY_VERSION = "tricky-daily-discovery-v1"
MEMORY_PATH = Path("assistant_data/spotify/daily_recommendation_memory.jsonl")
ARCHIVE_DIR = Path("assistant_data/spotify/daily_recommendation_memory_archive")
MANIFEST_PATH = Path("assistant_data/spotify/daily_recommendation_memory_manifest.json")
CHECKPOINT_PATH = Path("assistant_data/spotify/daily_recommendation_memory_checkpoint.json")
FEEDBACK_PATH = Path("assistant_data/spotify/daily_feedback.json")
PLAYBACK_PATH = Path("playback_data/segments.jsonl")
SCROBBLES_PATH = Path("data/scrobbles.json")
SNAPSHOT_PATH = Path("assistant_data/spotify/playlists") / f"{DAILY_ID}.json"


class RecommendationMemoryError(ValueError):
    """Raised when the append-only Daily memory cannot be trusted."""


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def parse_time(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if result.tzinfo is None:
        return None
    return result.astimezone(timezone.utc)


def normalize(value):
    return re.sub(r"\s+", " ", str(value or "").strip()).casefold()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def make_event_id(prefix, *parts):
    return f"{prefix}:{digest(list(parts))}"


def track_identity(row):
    uri = row.get("uri") or row.get("spotify_uri")
    artist = row.get("artist") or row.get("artist_name")
    title = row.get("track") or row.get("name") or row.get("title")
    if not isinstance(uri, str) or not uri.startswith("spotify:track:"):
        raise RecommendationMemoryError("Daily recommendation memory requires a Spotify track URI.")
    if not isinstance(artist, str) or not artist.strip():
        raise RecommendationMemoryError("Daily recommendation memory requires a primary artist.")
    if not isinstance(title, str) or not title.strip():
        raise RecommendationMemoryError("Daily recommendation memory requires a track title.")
    normalized_artist = normalize(artist)
    normalized_title = normalize(title)
    identity_key = digest({"artist": normalized_artist, "title": normalized_title})
    return {
        "spotify_uri": uri,
        "spotify_id": uri.rsplit(":", 1)[-1],
        "artist": artist.strip(),
        "title": title.strip(),
        "normalized_artist": normalized_artist,
        "normalized_title": normalized_title,
        "identity_key": identity_key,
    }


def _validate_event(event):
    if not isinstance(event, dict):
        raise RecommendationMemoryError("Daily memory event must be an object.")
    if event.get("schema_version") != SCHEMA_VERSION:
        raise RecommendationMemoryError("Daily memory contains an unsupported schema version.")
    if not isinstance(event.get("event_id"), str) or not event["event_id"]:
        raise RecommendationMemoryError("Daily memory event has no stable event_id.")
    if not isinstance(event.get("event_type"), str) or not event["event_type"]:
        raise RecommendationMemoryError("Daily memory event has no event_type.")
    if not parse_time(event.get("occurred_at")):
        raise RecommendationMemoryError("Daily memory event has an invalid or timezone-naive timestamp.")
    if event.get("playlist_id") != DAILY_ID:
        raise RecommendationMemoryError("Daily memory event is outside the Tricky Daily playlist scope.")
    return event


def read_events(path=MEMORY_PATH):
    path = Path(path)
    if not path.is_file():
        return []
    events = []
    seen = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            raise RecommendationMemoryError(f"Daily memory contains a blank line at {line_number}.")
        try:
            event = json.loads(line)
        except ValueError as error:
            raise RecommendationMemoryError(
                f"Daily memory JSONL is malformed at line {line_number}; refusing to overwrite it."
            ) from error
        _validate_event(event)
        event_id = event["event_id"]
        if event_id in seen:
            raise RecommendationMemoryError(
                f"Daily memory contains duplicate event_id {event_id}; refusing to guess which copy is authoritative."
            )
        seen[event_id] = event
        events.append(event)
    return events


def _atomic_write_bytes(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def write_events(events, path=MEMORY_PATH):
    path = Path(path)
    payload = "".join(canonical(_validate_event(event)) + "\n" for event in events).encode("utf-8")
    _atomic_write_bytes(path, payload)


def append_events(new_events, path=MEMORY_PATH):
    """Atomically append unique immutable events; retries are idempotent."""
    existing = read_events(path)
    by_id = {event["event_id"]: event for event in existing}
    additions = []
    for event in new_events:
        _validate_event(event)
        previous = by_id.get(event["event_id"])
        if previous is not None:
            if canonical(previous) != canonical(event):
                raise RecommendationMemoryError(
                    f"Daily memory event_id collision with different content: {event['event_id']}"
                )
            continue
        by_id[event["event_id"]] = event
        additions.append(event)
    if additions:
        write_events([*existing, *additions], path)
    return len(additions)


def _base_event(event_id, event_type, occurred_at, **fields):
    event = {
        "schema_version": SCHEMA_VERSION,
        "event_id": event_id,
        "event_type": event_type,
        "occurred_at": occurred_at,
        "playlist_id": DAILY_ID,
    }
    event.update(fields)
    return event


def _source_provenance(row):
    evidence = {
        "lastfm_familiarity": {
            "plays": row.get("plays"),
            "last_scrobble": row.get("last_scrobble"),
        },
        "similar_artist": {
            "similarity": row.get("similarity"),
            "supporting_seeds": row.get("supporting_seeds"),
        },
        "spotify_liked_songs": {"liked_at_selection": row.get("liked")},
        "daily_feedback": {
            "positive_artist_count": row.get("positive_artist_count"),
            "removed_artist_count": row.get("removed_artist_count"),
            "whitelisted": bool(row.get("whitelisted")),
        },
        "listening_trends": {
            "affinity": row.get("daily_trend_affinity"),
            "confidence": row.get("daily_trend_confidence"),
        },
        "lyric_analysis": {
            "themes": row.get("lyric_themes") or [],
            "source_count": row.get("lyric_source_count", 0),
            "assessment": row.get("lyric_assessment"),
        },
    }
    sources = []
    if row.get("similarity") is not None:
        sources.append("lastfm_similar_artist")
    if row.get("plays") is not None or row.get("last_scrobble") is not None:
        sources.append("lastfm_familiarity")
    if isinstance(row.get("liked"), bool):
        sources.append("spotify_liked_songs")
    if row.get("positive_artist_count") or row.get("removed_artist_count") or row.get("whitelisted"):
        sources.append("daily_playlist_feedback")
    if row.get("daily_trend_confidence") in ("medium", "high"):
        sources.append("spotify_listening_trends")
    if int(row.get("lyric_source_count") or 0) > 0:
        sources.append("lyric_analysis")
    evidence["sources"] = sources or ["unknown"]
    return evidence


def record_recommendations(rows, context, path=MEMORY_PATH):
    """Persist selected Daily recommendations before stage publication."""
    if context.get("playlist_id", DAILY_ID) != DAILY_ID:
        raise RecommendationMemoryError("Recommendation memory only accepts Tricky Daily.")
    cycle_date = context.get("cycle_date_eastern")
    run_id = context.get("run_id")
    prewrite_snapshot_id = context.get("prewrite_snapshot_id")
    if not isinstance(cycle_date, str) or not cycle_date:
        raise RecommendationMemoryError("Daily recommendation memory requires the Eastern cycle date.")
    if not run_id and not prewrite_snapshot_id:
        raise RecommendationMemoryError("Daily recommendation memory requires a run ID or pre-write snapshot ID.")
    run_key = str(run_id or ("snapshot:" + str(prewrite_snapshot_id)))
    recommended_at = context.get("recommended_at") or utc_now()
    if not parse_time(recommended_at):
        raise RecommendationMemoryError("Daily recommendation timestamp must include a UTC offset.")
    strategy_config = context.get("strategy_config") or {}
    strategy = {
        "version": context.get("strategy_version") or STRATEGY_VERSION,
        "config_sha256": digest(strategy_config),
        "config": strategy_config,
        "source_commit": context.get("source_commit") or os.environ.get("GITHUB_SHA"),
    }
    liked_at_add = context.get("liked_at_add") or {}
    events = []
    event_ids = []
    for rank, row in enumerate(rows or [], start=1):
        track = track_identity(row)
        event_id = make_event_id("daily-rec", cycle_date, run_key, track["spotify_uri"])
        event_ids.append(event_id)
        events.append(_base_event(
            event_id,
            "recommendation_selected",
            recommended_at,
            recommendation_event_id=event_id,
            track=track,
            cycle={
                "cycle_date_eastern": cycle_date,
                "run_id": str(run_id) if run_id else None,
                "run_attempt": context.get("run_attempt"),
                "prewrite_snapshot_id": prewrite_snapshot_id,
                "stage_path": context.get("stage_path"),
                "payload_sha256": context.get("payload_sha256"),
            },
            strategy=strategy,
            selection={
                "rank": rank,
                "score": row.get("score"),
                "similarity": row.get("similarity"),
                "confidence": row.get("confidence"),
                "tier": row.get("tier"),
                "reasons": list(row.get("why") or []),
                "liked_at_selection": row.get("liked"),
                "liked_at_add": liked_at_add.get(track["spotify_uri"]),
                "artist_diversity_fallback": bool(row.get("artist_diversity_fallback")),
                "supporting_seeds": row.get("supporting_seeds"),
                "daily_trend_affinity": row.get("daily_trend_affinity"),
                "daily_trend_confidence": row.get("daily_trend_confidence"),
            },
            evidence_provenance=_source_provenance(row),
            publication_status="selected_not_yet_published",
            exposure_interval={"started_at": None, "ended_at": None},
            legacy=False,
        ))
    if len(event_ids) != len(set(event_ids)):
        raise RecommendationMemoryError("Daily recommendation event IDs are not unique.")
    append_events(events, path)
    return event_ids


def _existing_event_ids(path):
    return {event["event_id"] for event in read_events(path)}


def record_publication(event_ids, context, path=MEMORY_PATH):
    """Open an exposure interval immediately after Spotify accepts the replacement."""
    existing = _existing_event_ids(path)
    occurred_at = context.get("published_at") or utc_now()
    if not parse_time(occurred_at):
        raise RecommendationMemoryError("Daily publication timestamp must include a UTC offset.")
    stage_hash = context.get("payload_sha256") or "unknown-stage"
    events = []
    for recommendation_id in event_ids or []:
        if not isinstance(recommendation_id, str) or not recommendation_id:
            raise RecommendationMemoryError("Daily publication references an invalid recommendation event ID.")
        event_id = make_event_id("daily-pub", recommendation_id, stage_hash)
        if event_id in existing:
            continue
        events.append(_base_event(
            event_id,
            "publication_accepted",
            occurred_at,
            recommendation_event_id=recommendation_id,
            cycle_date_eastern=context.get("cycle_date_eastern"),
            run_id=context.get("run_id"),
            stage_path=context.get("stage_path"),
            payload_sha256=context.get("payload_sha256"),
            exposure_started_at=context.get("exposure_started_at") or occurred_at,
            exposure_start_precision=context.get("exposure_start_precision") or "provider_acceptance_time",
            recovery=bool(context.get("recovery")),
        ))
    return append_events(events, path)


def record_publication_verified(event_ids, context, path=MEMORY_PATH):
    existing = _existing_event_ids(path)
    verified_at = context.get("verified_at") or utc_now()
    snapshot_id = context.get("after_snapshot_id")
    if not snapshot_id:
        raise RecommendationMemoryError("Verified Daily publication requires an after-snapshot ID.")
    events = []
    for recommendation_id in event_ids or []:
        event_id = make_event_id("daily-verified", recommendation_id, snapshot_id)
        if event_id in existing:
            continue
        events.append(_base_event(
            event_id,
            "publication_verified",
            verified_at,
            recommendation_event_id=recommendation_id,
            after_snapshot_id=snapshot_id,
            after_snapshot_path=context.get("after_snapshot_path"),
        ))
    return append_events(events, path)


def _recommendations_by_uri(events):
    grouped = defaultdict(list)
    for event in events:
        if event.get("event_type") == "recommendation_selected":
            grouped[(event.get("track") or {}).get("spotify_uri")].append(event)
    for rows in grouped.values():
        rows.sort(key=lambda event: parse_time(event["occurred_at"]) or datetime.min.replace(tzinfo=timezone.utc))
    return grouped


def _closures_by_recommendation(events):
    result = defaultdict(list)
    for event in events:
        if event.get("event_type") == "exposure_closed":
            result[event.get("recommendation_event_id")].append(event)
    return result


def _append_closure_for_recommendation(recommendation, reason, occurred_at, source, source_event_id=None, path=MEMORY_PATH):
    recommendation_id = recommendation["recommendation_event_id"]
    event_id = make_event_id("daily-close", recommendation_id, reason, occurred_at, source_event_id or source)
    event = _base_event(
        event_id,
        "exposure_closed",
        occurred_at,
        recommendation_event_id=recommendation_id,
        spotify_uri=(recommendation.get("track") or {}).get("spotify_uri"),
        reason=reason,
        source=source,
        source_event_id=source_event_id,
        neutral=reason in ("curator_rotation", "recovery_rollback"),
    )
    return append_events([event], path)


def record_cycle_removals(removed_uris, reason="curator_rotation", occurred_at=None, path=MEMORY_PATH):
    """Close the most recent active Daily exposure for each rotated-out URI."""
    occurred_at = occurred_at or utc_now()
    events = read_events(path)
    closures = _closures_by_recommendation(events)
    recommendations = _recommendations_by_uri(events)
    changed = 0
    for uri in sorted(set(removed_uris or [])):
        active = []
        for recommendation in recommendations.get(uri, []):
            recommendation_id = recommendation["recommendation_event_id"]
            published = any(
                event.get("event_type") == "publication_accepted"
                and event.get("recommendation_event_id") == recommendation_id
                for event in events
            )
            if published and not closures.get(recommendation_id):
                active.append(recommendation)
        if active:
            recommendation = active[-1]
            changed += _append_closure_for_recommendation(
                recommendation, reason, occurred_at, "daily_cycle"
            , path=path)
            events = read_events(path)
            closures = _closures_by_recommendation(events)
    return changed


def record_recovery_resolution(event_ids, action, context, path=MEMORY_PATH):
    """Resolve only recommendation IDs stored in the verified immutable stage."""
    if action not in ("resume", "rollback", "discard"):
        raise RecommendationMemoryError("Daily memory recovery action is invalid.")
    stage_hash = context.get("payload_sha256") or "unknown-stage"
    occurred_at = context.get("occurred_at") or utc_now()
    if action == "resume":
        record_publication(event_ids, {
            **context,
            "published_at": occurred_at,
            "exposure_started_at": context.get("exposure_started_at") or occurred_at,
            "exposure_start_precision": context.get("exposure_start_precision") or "recovery_observed_live",
            "recovery": True,
        }, path)
    elif action == "rollback":
        events = read_events(path)
        for recommendation_id in event_ids or []:
            recommendation = next(
                (event for event in events
                 if event.get("event_type") == "recommendation_selected"
                 and event.get("recommendation_event_id") == recommendation_id),
                None,
            )
            if recommendation:
                _append_closure_for_recommendation(
                    recommendation, "recovery_rollback", occurred_at, "daily_stage_recovery",
                    source_event_id=stage_hash, path=path,
                )
                events = read_events(path)
    else:
        existing = _existing_event_ids(path)
        discarded = []
        for recommendation_id in event_ids or []:
            event_id = make_event_id("daily-discard", recommendation_id, stage_hash)
            if event_id in existing:
                continue
            discarded.append(_base_event(
                event_id,
                "recommendation_discarded",
                occurred_at,
                recommendation_event_id=recommendation_id,
                payload_sha256=stage_hash,
                stage_path=context.get("stage_path"),
                reason="owner_confirmed_stage_discard",
            ))
        append_events(discarded, path)

    existing = _existing_event_ids(path)
    resolved = []
    for recommendation_id in event_ids or []:
        event_id = make_event_id("daily-recovery", recommendation_id, stage_hash, action)
        if event_id in existing:
            continue
        resolved.append(_base_event(
            event_id,
            "recovery_resolved",
            occurred_at,
            recommendation_event_id=recommendation_id,
            action=action,
            payload_sha256=stage_hash,
            stage_path=context.get("stage_path"),
        ))
    return append_events(resolved, path)


def _read_json(path, expected_type=None):
    path = Path(path)
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError) as error:
        raise RecommendationMemoryError(f"Daily memory input is unreadable: {path}") from error
    if expected_type is not None and not isinstance(value, expected_type):
        raise RecommendationMemoryError(f"Daily memory input has an invalid shape: {path}")
    return value


def migrate_legacy_feedback(feedback_path=FEEDBACK_PATH, path=MEMORY_PATH):
    """Import only timestamped Daily additions; never inspect candidate-history rows."""
    feedback = _read_json(feedback_path, dict)
    if feedback is None:
        return 0
    events = read_events(path)
    marker_id = make_event_id("daily-migration", "daily_feedback_v1")
    if any(event["event_id"] == marker_id for event in events):
        return 0
    tracks = feedback.get("tracks")
    if not isinstance(tracks, dict):
        raise RecommendationMemoryError("Legacy Daily feedback has no valid tracks map.")
    additions = []
    for uri, row in tracks.items():
        if not isinstance(row, dict) or not isinstance(uri, str) or not uri.startswith("spotify:track:"):
            continue
        history = row.get("additions") or []
        if not isinstance(history, list):
            raise RecommendationMemoryError(f"Legacy Daily addition history is malformed for {uri}.")
        if not history and row.get("first_added_at"):
            history = [{
                "at": row.get("first_added_at"),
                "liked_at_add": row.get("liked_at_add"),
                "daily_playlist_id": DAILY_ID,
            }]
        for index, addition in enumerate(history):
            if not isinstance(addition, dict):
                continue
            added_at = addition.get("at")
            if not parse_time(added_at):
                continue
            track = track_identity({
                "uri": uri,
                "artist": row.get("artist"),
                "track": row.get("track"),
            })
            recommendation_id = make_event_id("daily-legacy-rec", uri, index, added_at)
            additions.append(_base_event(
                recommendation_id,
                "recommendation_selected",
                added_at,
                recommendation_event_id=recommendation_id,
                track=track,
                cycle={
                    "cycle_date_eastern": parse_time(added_at).astimezone(
                        __import__("zoneinfo").ZoneInfo("America/New_York")
                    ).date().isoformat(),
                    "run_id": None,
                    "run_attempt": None,
                    "prewrite_snapshot_id": None,
                    "stage_path": None,
                    "payload_sha256": None,
                },
                strategy={
                    "version": "legacy-unattributed",
                    "config_sha256": None,
                    "config": {},
                    "source_commit": None,
                },
                selection={
                    "rank": None,
                    "score": None,
                    "similarity": None,
                    "confidence": "unknown",
                    "tier": "legacy",
                    "reasons": [],
                    "liked_at_selection": addition.get("liked_at_add"),
                    "liked_at_add": addition.get("liked_at_add"),
                    "artist_diversity_fallback": None,
                    "supporting_seeds": None,
                    "daily_trend_affinity": None,
                    "daily_trend_confidence": "unknown",
                },
                evidence_provenance={
                    "sources": ["legacy_daily_feedback_additions"],
                    "migration_note": "No historical candidate rationale or null listening evidence was imported.",
                },
                publication_status="legacy_published",
                exposure_interval={"started_at": added_at, "ended_at": None},
                legacy=True,
            ))
            publication_id = make_event_id("daily-pub", recommendation_id, "legacy")
            additions.append(_base_event(
                publication_id,
                "publication_accepted",
                added_at,
                recommendation_event_id=recommendation_id,
                cycle_date_eastern=parse_time(added_at).astimezone(
                    __import__("zoneinfo").ZoneInfo("America/New_York")
                ).date().isoformat(),
                run_id=None,
                stage_path=None,
                payload_sha256="legacy",
                exposure_started_at=added_at,
                exposure_start_precision="legacy_addition_timestamp",
                recovery=False,
                legacy=True,
            ))
    additions.append(_base_event(
        marker_id,
        "migration_completed",
        utc_now(),
        source="assistant_data/spotify/daily_feedback.json",
        imported_recommendations=sum(1 for event in additions if event.get("event_type") == "recommendation_selected"),
        imported_candidate_rows=0,
        ignored_aggregate_outcomes=[
            "playback_observations_without_per-event timestamps",
            "lastfm_post_add_scrobbles aggregate counts",
            "assistant_data/recommendations/discovery_candidates.json",
        ],
    ))
    return append_events(additions, path)


def _load_playback_segments(path):
    path = Path(path)
    if not path.is_file():
        return [], {"status": "unknown", "reason": "segment_file_missing", "complete": False}
    rows = []
    malformed = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            malformed += 1
            continue
        if not isinstance(row, dict):
            malformed += 1
            continue
        uri = row.get("spotify_uri") or row.get("uri")
        when = parse_time(row.get("sampled_at") or row.get("started_at") or row.get("timestamp") or row.get("at"))
        if not isinstance(uri, str) or not when:
            malformed += 1
            continue
        try:
            played_ms = max(0, int(row.get("played_ms") or 0))
        except (TypeError, ValueError, OverflowError):
            played_ms = 0
        rows.append((uri, when, played_ms))
    return rows, {
        "status": "available" if rows else "unknown",
        "reason": None if rows else "no_valid_segments",
        "malformed_rows": malformed,
        "complete": False,
    }


def _load_scrobbles(path):
    rows = _read_json(path, list)
    if rows is None:
        return [], {"status": "unknown", "reason": "scrobble_archive_missing", "complete": False}
    result = []
    malformed = 0
    for row in rows:
        if not isinstance(row, dict):
            malformed += 1
            continue
        try:
            when = datetime.fromtimestamp(int(row.get("timestamp")), timezone.utc)
        except (TypeError, ValueError, OverflowError, OSError):
            malformed += 1
            continue
        result.append((
            normalize(row.get("artist")),
            normalize(row.get("track")),
            when,
        ))
    return result, {
        "status": "available" if result else "unknown",
        "reason": None if result else "no_valid_scrobbles",
        "malformed_rows": malformed,
        "complete": False,
    }


def _coverage_complete(feedback, source, start, end):
    coverage = (feedback or {}).get("coverage") or {}
    if source == "spotify_playback_tracker":
        detail = coverage.get("playback_tracker_detail") or {}
        complete = detail.get("coverage_complete") is True
        start_at = parse_time(detail.get("coverage_start_at"))
        end_at = parse_time(detail.get("coverage_complete_through"))
    else:
        detail = coverage.get("lastfm_detail") or {}
        complete = coverage.get("lastfm_coverage_complete") is True or detail.get("coverage_complete") is True
        start_at = parse_time(coverage.get("lastfm_coverage_start_at") or detail.get("coverage_start_at"))
        end_at = parse_time(coverage.get("lastfm_complete_through") or detail.get("coverage_complete_through"))
    return bool(complete and start_at and end_at and start_at <= start and end_at >= end)


def _sessions(rows):
    rows = sorted(rows, key=lambda item: item[0])
    count = 0
    previous = None
    played_ms = 0
    for when, duration in rows:
        if previous is None or (when - previous).total_seconds() > 90:
            count += 1
        previous = when
        played_ms += duration
    return count, played_ms


def _recommendation_publication(events, recommendation_id):
    return next((
        event for event in events
        if event.get("event_type") == "publication_accepted"
        and event.get("recommendation_event_id") == recommendation_id
    ), None)


def reconcile_outcomes(
    feedback_path=FEEDBACK_PATH,
    playback_path=PLAYBACK_PATH,
    scrobbles_path=SCROBBLES_PATH,
    snapshot_path=SNAPSHOT_PATH,
    path=MEMORY_PATH,
    observed_at=None,
):
    """Append source-specific observations for every published Daily exposure."""
    observed_at = observed_at or utc_now()
    observed_when = parse_time(observed_at)
    if not observed_when:
        raise RecommendationMemoryError("Daily outcome observation timestamp must include a UTC offset.")
    migrate_legacy_feedback(feedback_path, path)
    feedback = _read_json(feedback_path, dict) or {}
    tracks = feedback.get("tracks") or {}
    if not isinstance(tracks, dict):
        raise RecommendationMemoryError("Daily feedback tracks map is malformed.")
    playback_rows, playback_coverage = _load_playback_segments(playback_path)
    scrobble_rows, scrobble_coverage = _load_scrobbles(scrobbles_path)
    snapshot = _read_json(snapshot_path, dict) or {}
    snapshot_when = parse_time(snapshot.get("captured_at"))
    snapshot_id = snapshot.get("snapshot_id")
    current_uris = {
        row.get("uri") for row in snapshot.get("items", [])
        if isinstance(row, dict) and isinstance(row.get("uri"), str)
    } if snapshot.get("items_accessible") is True else set()

    events = read_events(path)
    recommendations = [
        event for event in events if event.get("event_type") == "recommendation_selected"
    ]
    new_events = []
    for recommendation in recommendations:
        recommendation_id = recommendation["recommendation_event_id"]
        publication = _recommendation_publication(events, recommendation_id)
        if not publication:
            continue
        start = parse_time(publication.get("exposure_started_at") or publication.get("occurred_at"))
        if not start:
            continue
        closures = [
            event for event in events
            if event.get("event_type") == "exposure_closed"
            and event.get("recommendation_event_id") == recommendation_id
        ]
        end_event = min(closures, key=lambda event: parse_time(event["occurred_at"])) if closures else None
        end = parse_time(end_event.get("occurred_at")) if end_event else observed_when
        if end < start:
            continue
        track = recommendation.get("track") or {}
        uri = track.get("spotify_uri")
        artist = normalize(track.get("artist"))
        title = normalize(track.get("title"))

        playback = [
            (when, duration) for row_uri, when, duration in playback_rows
            if row_uri == uri and start <= when <= end
        ]
        playback_sessions, playback_ms = _sessions(playback)
        playback_complete = _coverage_complete(feedback, "spotify_playback_tracker", start, end)
        if playback_sessions > 0 or playback_complete:
            fingerprint = {
                "sessions": playback_sessions,
                "played_ms": playback_ms,
                "window_start": start.isoformat(),
                "window_end": end.isoformat(),
                "latest_segment_at": max((when for when, _ in playback), default=None).isoformat()
                if playback else None,
                "coverage_complete": playback_complete,
            }
            new_events.append(_base_event(
                make_event_id("daily-outcome", recommendation_id, "spotify_playback_tracker", fingerprint),
                "outcome_observed",
                observed_at,
                recommendation_event_id=recommendation_id,
                spotify_uri=uri,
                source="spotify_playback_tracker",
                outcome="measured_playback",
                value=fingerprint,
                coverage_status="complete" if playback_complete else playback_coverage["status"],
            ))

        scrobbles = [
            when for row_artist, row_title, when in scrobble_rows
            if row_artist == artist and row_title == title and start <= when <= end
        ]
        lastfm_complete = _coverage_complete(feedback, "lastfm_scrobbles", start, end)
        if scrobbles or lastfm_complete:
            fingerprint = {
                "scrobbles": len(scrobbles),
                "window_start": start.isoformat(),
                "window_end": end.isoformat(),
                "latest_scrobble_at": max(scrobbles).isoformat() if scrobbles else None,
                "coverage_complete": lastfm_complete,
            }
            new_events.append(_base_event(
                make_event_id("daily-outcome", recommendation_id, "lastfm_scrobbles", fingerprint),
                "outcome_observed",
                observed_at,
                recommendation_event_id=recommendation_id,
                spotify_uri=uri,
                source="lastfm_scrobbles",
                outcome="scrobble_observation",
                value=fingerprint,
                coverage_status="complete" if lastfm_complete else scrobble_coverage["status"],
            ))

        feedback_row = tracks.get(uri) or {}
        liked_observations = feedback_row.get("liked_observations") or []
        for liked in liked_observations:
            liked_at = parse_time(liked.get("at")) if isinstance(liked, dict) else None
            if not liked_at or not (start <= liked_at <= end):
                continue
            value = {"liked": bool(liked.get("liked")), "observed_at": liked_at.isoformat()}
            new_events.append(_base_event(
                make_event_id("daily-outcome", recommendation_id, "spotify_liked_songs", value),
                "outcome_observed",
                liked_at.isoformat(),
                recommendation_event_id=recommendation_id,
                spotify_uri=uri,
                source="spotify_liked_songs",
                outcome="liked_status",
                value=value,
                liked_at_add=(recommendation.get("selection") or {}).get("liked_at_add"),
                coverage_status="observed",
            ))

        removal_events = feedback_row.get("removal_events") or []
        for removal in removal_events:
            if not isinstance(removal, dict):
                continue
            removed_at = parse_time(removal.get("at"))
            if not removed_at or not (start <= removed_at <= end):
                continue
            reason = removal.get("reason") or "unknown_removal"
            closure_id = make_event_id(
                "daily-close", recommendation_id, reason, removed_at.isoformat(),
                removal.get("last_present_cycle") or "feedback",
            )
            new_events.append(_base_event(
                closure_id,
                "exposure_closed",
                removed_at.isoformat(),
                recommendation_event_id=recommendation_id,
                spotify_uri=uri,
                reason=reason,
                source=removal.get("source") or "daily_feedback",
                source_event_id=removal.get("last_present_cycle"),
                neutral=reason in ("curator_rotation", "recovery_rollback"),
            ))
            outcome_id = make_event_id("daily-outcome", recommendation_id, "playlist_removal", reason, removed_at.isoformat())
            new_events.append(_base_event(
                outcome_id,
                "outcome_observed",
                removed_at.isoformat(),
                recommendation_event_id=recommendation_id,
                spotify_uri=uri,
                source="daily_playlist_feedback",
                outcome="manual_removal" if reason == "user_removed" else "playlist_removal",
                value={"reason": reason, "removed_at": removed_at.isoformat()},
                coverage_status="observed",
            ))

        if snapshot_when and snapshot_id and snapshot_when >= start and uri in current_uris:
            value = {"snapshot_id": snapshot_id, "captured_at": snapshot_when.isoformat(), "present": True}
            new_events.append(_base_event(
                make_event_id("daily-outcome", recommendation_id, "daily_snapshot_retention", snapshot_id),
                "outcome_observed",
                snapshot_when.isoformat(),
                recommendation_event_id=recommendation_id,
                spotify_uri=uri,
                source="daily_snapshot",
                outcome="retained_membership",
                value=value,
                coverage_status="observed",
            ))

        for source, coverage in (
            ("spotify_playback_tracker", playback_coverage),
            ("lastfm_scrobbles", scrobble_coverage),
        ):
            complete = playback_complete if source == "spotify_playback_tracker" else lastfm_complete
            if not complete and not (
                source == "spotify_playback_tracker" and playback_sessions > 0
            ) and not (source == "lastfm_scrobbles" and scrobbles):
                day = observed_when.date().isoformat()
                value = {
                    "status": coverage["status"],
                    "reason": coverage.get("reason"),
                    "complete": False,
                    "observed_at": observed_when.isoformat(),
                }
                new_events.append(_base_event(
                    make_event_id("daily-coverage", recommendation_id, source, day, value["status"], value["reason"]),
                    "coverage_observed",
                    observed_when.isoformat(),
                    recommendation_event_id=recommendation_id,
                    spotify_uri=uri,
                    source=source,
                    value=value,
                ))

    added = append_events(new_events, path)
    final_events = read_events(path)
    summaries = [
        summarize_recommendation(final_events, event["recommendation_event_id"], observed_when)
        for event in recommendations
    ]
    return {
        "recommendations": len(recommendations),
        "events_added": added,
        "published_exposures": sum(1 for event in recommendations if _recommendation_publication(final_events, event["recommendation_event_id"])),
        "high_play_then_removed": sum(1 for row in summaries if row["status"] == "high_play_then_removed"),
        "unplayed_then_removed": sum(1 for row in summaries if row["status"] == "unplayed_then_removed"),
        "unknown_incomplete_coverage": sum(1 for row in summaries if row["status"] == "unknown_incomplete_coverage"),
        "not_yet_observed": sum(1 for row in summaries if row["status"] == "not_yet_observed"),
        "updated_at": observed_at,
    }


def summarize_recommendation(events, recommendation_id, as_of=None):
    as_of = as_of or parse_time(utc_now())
    recommendation = next((
        event for event in events
        if event.get("event_type") == "recommendation_selected"
        and event.get("recommendation_event_id") == recommendation_id
    ), None)
    if recommendation is None:
        raise RecommendationMemoryError("Daily recommendation event was not found.")
    linked = [event for event in events if event.get("recommendation_event_id") == recommendation_id]
    publication = next((event for event in linked if event.get("event_type") == "publication_accepted"), None)
    if publication is None:
        return {"recommendation_event_id": recommendation_id, "status": "selected_not_published"}
    start = parse_time(publication.get("exposure_started_at") or publication.get("occurred_at"))
    closures = [event for event in linked if event.get("event_type") == "exposure_closed"]
    closure = min(closures, key=lambda event: parse_time(event["occurred_at"])) if closures else None
    playback = [
        event for event in linked
        if event.get("event_type") == "outcome_observed"
        and event.get("source") == "spotify_playback_tracker"
    ]
    scrobbles = [
        event for event in linked
        if event.get("event_type") == "outcome_observed"
        and event.get("source") == "lastfm_scrobbles"
    ]
    liked = [
        event for event in linked
        if event.get("event_type") == "outcome_observed"
        and event.get("source") == "spotify_liked_songs"
    ]
    retention = any(
        event.get("event_type") == "outcome_observed"
        and event.get("outcome") == "retained_membership"
        for event in linked
    )
    measured_plays = max(
        (int((event.get("value") or {}).get("sessions") or 0) for event in playback),
        default=0,
    )
    lastfm_plays = max(
        (int((event.get("value") or {}).get("scrobbles") or 0) for event in scrobbles),
        default=0,
    )
    liked_after_add = any(
        (event.get("value") or {}).get("liked") is True
        and (recommendation.get("selection") or {}).get("liked_at_add") is False
        for event in liked
    )
    coverage = {
        event.get("source"): (event.get("value") or {}).get("status")
        for event in linked if event.get("event_type") == "coverage_observed"
    }
    complete = (
        any((event.get("value") or {}).get("coverage_complete") is True for event in playback)
        and any((event.get("value") or {}).get("coverage_complete") is True for event in scrobbles)
    )
    engaged = measured_plays > 0 or lastfm_plays > 0 or liked_after_add
    reason = closure.get("reason") if closure else None
    if reason == "user_removed":
        if measured_plays >= 3 or lastfm_plays >= 3:
            status = "high_play_then_removed"
        elif engaged:
            status = "played_then_removed"
        elif complete:
            status = "unplayed_then_removed"
        else:
            status = "removed_without_observed_play_unknown_coverage"
    elif reason in ("curator_rotation", "recovery_rollback"):
        status = "curator_rotated_out_neutral" if reason == "curator_rotation" else "recovery_rolled_back"
    elif retention:
        if engaged:
            status = "retained_with_engagement"
        elif complete:
            status = "retained_unplayed"
        else:
            status = "retained_unknown_coverage"
    elif engaged:
        status = "observed_engagement"
    elif start and as_of and (as_of - start) < timedelta(hours=24):
        status = "not_yet_observed"
    elif complete:
        status = "no_observed_play"
    else:
        status = "unknown_incomplete_coverage"
    return {
        "recommendation_event_id": recommendation_id,
        "spotify_uri": (recommendation.get("track") or {}).get("spotify_uri"),
        "status": status,
        "measured_playback_sessions": measured_plays,
        "lastfm_scrobbles": lastfm_plays,
        "liked_after_add": liked_after_add,
        "retained": retention,
        "removal_reason": reason,
        "coverage": coverage,
        "coverage_complete": complete,
    }


def _load_manifest(manifest_path=MANIFEST_PATH, archive_dir=ARCHIVE_DIR):
    manifest = _read_json(manifest_path, dict)
    if manifest is not None:
        if manifest.get("schema_version") != SCHEMA_VERSION or not isinstance(manifest.get("archives"), list):
            raise RecommendationMemoryError("Daily memory archive manifest is malformed.")
        return manifest
    archives = []
    for archive_path in sorted(Path(archive_dir).glob("archive-*.jsonl.gz")) if Path(archive_dir).exists() else []:
        raw = gzip.decompress(archive_path.read_bytes())
        checksum = hashlib.sha256(raw).hexdigest()
        events = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
        archives.append({
            "path": str(archive_path),
            "sha256": checksum,
            "event_count": len(events),
            "event_ids": [event.get("event_id") for event in events],
        })
    return {"schema_version": SCHEMA_VERSION, "archives": archives}


def _archived_events(manifest):
    events = []
    for entry in manifest.get("archives", []):
        archive_path = Path(entry.get("path") or "")
        raw = gzip.decompress(archive_path.read_bytes())
        if hashlib.sha256(raw).hexdigest() != entry.get("sha256"):
            raise RecommendationMemoryError(f"Daily memory archive hash mismatch: {archive_path}")
        rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
        if len(rows) != entry.get("event_count"):
            raise RecommendationMemoryError(f"Daily memory archive count mismatch: {archive_path}")
        for row in rows:
            _validate_event(row)
        events.extend(rows)
    return events


def compact_memory(now=None, retention_days=365, path=MEMORY_PATH):
    """Archive only old, closed recommendation groups; never discard event detail."""
    now = parse_time(now or utc_now())
    if not now:
        raise RecommendationMemoryError("Daily memory compaction timestamp is invalid.")
    if int(retention_days) < 30:
        raise RecommendationMemoryError("Daily memory compaction retention must be at least 30 days.")
    cutoff = now - timedelta(days=int(retention_days))
    events = read_events(path)
    by_recommendation = defaultdict(list)
    for event in events:
        recommendation_id = event.get("recommendation_event_id")
        if recommendation_id:
            by_recommendation[recommendation_id].append(event)
    compact_ids = set()
    for recommendation_id, group in by_recommendation.items():
        recommendation = next((row for row in group if row.get("event_type") == "recommendation_selected"), None)
        closure = next((row for row in group if row.get("event_type") == "exposure_closed"), None)
        if not recommendation or not closure:
            continue
        times = [parse_time(row.get("occurred_at")) for row in group]
        if any(value is None or value >= cutoff for value in times):
            continue
        compact_ids.update(row["event_id"] for row in group)

    if not compact_ids:
        return {"archived_events": 0, "archive_path": None, "remaining_events": len(events)}

    archived = [row for row in events if row["event_id"] in compact_ids]
    raw = "".join(canonical(row) + "\n" for row in archived).encode("utf-8")
    checksum = hashlib.sha256(raw).hexdigest()
    archive_dir = Path(ARCHIVE_DIR)
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_path = archive_dir / f"archive-{checksum[:20]}.jsonl.gz"
    if archive_path.is_file():
        if gzip.decompress(archive_path.read_bytes()) != raw:
            raise RecommendationMemoryError("Existing Daily memory archive has a conflicting payload.")
    else:
        _atomic_write_bytes(archive_path, gzip.compress(raw, mtime=0))

    manifest = _load_manifest()
    if not any(entry.get("sha256") == checksum for entry in manifest["archives"]):
        manifest["archives"].append({
            "path": str(archive_path),
            "sha256": checksum,
            "event_count": len(archived),
            "event_ids": [row["event_id"] for row in archived],
            "first_occurred_at": min(row["occurred_at"] for row in archived),
            "last_occurred_at": max(row["occurred_at"] for row in archived),
        })
    _atomic_write_bytes(MANIFEST_PATH, (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))

    all_archived = _archived_events(manifest)
    summaries = {}
    for event in all_archived:
        track = event.get("track") or {}
        key = track.get("identity_key") or event.get("spotify_uri")
        if not key:
            continue
        summary = summaries.setdefault(key, {
            "spotify_uri": track.get("spotify_uri") or event.get("spotify_uri"),
            "artist": track.get("artist"),
            "title": track.get("title"),
            "recommendation_events": 0,
            "manual_removals": 0,
            "curator_rotations": 0,
            "measured_playback_sessions": 0,
            "lastfm_scrobbles": 0,
            "last_event_at": None,
        })
        if event.get("event_type") == "recommendation_selected":
            summary["recommendation_events"] += 1
        if event.get("event_type") == "exposure_closed":
            if event.get("reason") == "user_removed":
                summary["manual_removals"] += 1
            elif event.get("reason") == "curator_rotation":
                summary["curator_rotations"] += 1
        if event.get("event_type") == "outcome_observed":
            value = event.get("value") or {}
            if event.get("source") == "spotify_playback_tracker":
                summary["measured_playback_sessions"] = max(summary["measured_playback_sessions"], int(value.get("sessions") or 0))
            elif event.get("source") == "lastfm_scrobbles":
                summary["lastfm_scrobbles"] = max(summary["lastfm_scrobbles"], int(value.get("scrobbles") or 0))
        summary["last_event_at"] = max(summary["last_event_at"] or "", event["occurred_at"])
    checkpoint = {
        "schema_version": SCHEMA_VERSION,
        "derived_from_archives": [entry["sha256"] for entry in manifest["archives"]],
        "compacted_at": now.isoformat(),
        "tracks": summaries,
    }
    _atomic_write_bytes(CHECKPOINT_PATH, (json.dumps(checkpoint, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))

    remaining = [row for row in events if row["event_id"] not in compact_ids]
    write_events(remaining, path)
    return {
        "archived_events": len(archived),
        "archive_path": str(archive_path),
        "remaining_events": len(remaining),
        "checkpoint_tracks": len(summaries),
    }


def read_full_history(path=MEMORY_PATH):
    """Load active events plus hash-verified cold archives for audit/rebuild."""
    active = read_events(path)
    manifest = _load_manifest()
    archived = _archived_events(manifest)
    seen = {event["event_id"] for event in archived}
    if any(event["event_id"] in seen for event in active):
        raise RecommendationMemoryError("Daily memory event exists in both active and archived stores.")
    return [*archived, *active]


def observe(
    feedback_path=FEEDBACK_PATH,
    playback_path=PLAYBACK_PATH,
    scrobbles_path=SCROBBLES_PATH,
    snapshot_path=SNAPSHOT_PATH,
    path=MEMORY_PATH,
):
    report = reconcile_outcomes(
        feedback_path=feedback_path,
        playback_path=playback_path,
        scrobbles_path=scrobbles_path,
        snapshot_path=snapshot_path,
        path=path,
    )
    print(
        "Daily recommendation memory observed: "
        f"{report['recommendations']} recommendation events; "
        f"{report['events_added']} new outcome/coverage events; "
        f"{report['high_play_then_removed']} high-play removals; "
        f"{report['unplayed_then_removed']} unplayed removals; "
        f"{report['unknown_incomplete_coverage']} unknown-coverage events."
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("observe", help="Append source-attributed outcomes from local Daily evidence.")
    compact_parser = subparsers.add_parser("compact", help="Archive old closed Daily recommendation events.")
    compact_parser.add_argument("--retention-days", type=int, default=365)
    args = parser.parse_args()
    if args.command == "observe":
        observe()
    elif args.command == "compact":
        report = compact_memory(retention_days=args.retention_days)
        print(f"Daily recommendation memory compaction: {report['archived_events']} events archived.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RecommendationMemoryError, OSError, KeyError, TypeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Append-only, playlist-specific recommendation and outcome memory for Tricky Daily.
# State: Versioned JSONL events with atomic writes, deterministic IDs, legacy migration,
#        explicit exposure intervals, source-attributed observations, and cold compaction archives.
# Evidence: Spotify playback-tracker segments, Last.fm scrobbles, liked status, Daily removals,
#           and read-only snapshot retention are kept distinct; incomplete coverage stays unknown.
# Safety: Does not write Spotify/Last.fm, candidate scoring, playlist-manager state/audit,
#         whitelist/blacklist policy, or the canonical Music Library.
# Commands: python scripts/spotify/daily_recommendation_memory.py observe
#           python scripts/spotify/daily_recommendation_memory.py compact --retention-days 365
# Related: docs/TRICKY_DAILY_RECOMMENDATION_MEMORY.md and the Tricky Daily roadmap.
# -----------------------------------------------------------------------------
