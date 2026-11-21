#!/usr/bin/env python3
"""Fail-closed, owner-confirmed recovery for immutable Tricky Daily production stages."""

import hashlib
import html
import json
import os
import secrets
import subprocess
from datetime import date
from pathlib import Path

DAILY_RECOVERY_CONFIRMATION = "RECOVER TRICKY DAILY"
DAILY_RECOVERY_RESOLVED_STATUSES = {"completed", "rolled_back", "discarded"}


def _safe_stage_path(cycle, value):
    if not isinstance(value, str) or not value.strip():
        raise cycle.manager.ManagerError("A committed Tricky Daily stage path is required.")
    path = Path(value)
    if ".." in path.parts or path.suffix != ".json":
        raise cycle.manager.ManagerError("Daily recovery stage path is invalid; refusing recovery.")
    if os.environ.get("GITHUB_ACTIONS", "").lower() == "true" and path.is_absolute():
        raise cycle.manager.ManagerError("Daily recovery requires a repository-relative committed stage path.")
    try:
        if path.resolve().parent != cycle.DAILY_STAGE_DIR.resolve() or path.is_symlink():
            raise cycle.manager.ManagerError("Daily recovery stage must be a direct production-stage file.")
    except OSError as error:
        raise cycle.manager.ManagerError("Daily recovery stage path cannot be resolved.") from error
    return path


def _safe_backup_path(cycle, value):
    if not isinstance(value, str) or not value.strip():
        raise cycle.manager.ManagerError("The Daily stage does not reference a recovery backup.")
    path = Path(value)
    if ".." in path.parts or path.suffix != ".json":
        raise cycle.manager.ManagerError("Daily recovery backup path is invalid; refusing recovery.")
    if os.environ.get("GITHUB_ACTIONS", "").lower() == "true" and path.is_absolute():
        raise cycle.manager.ManagerError("Daily recovery requires a repository-relative committed backup path.")
    try:
        if path.resolve().parent != Path(cycle.manager.BACKUPS).resolve() or path.is_symlink():
            raise cycle.manager.ManagerError("Daily recovery backup must be a direct managed-backup file.")
    except OSError as error:
        raise cycle.manager.ManagerError("Daily recovery backup path cannot be resolved.") from error
    return path


def _read_committed_json(cycle, path, label):
    try:
        if os.environ.get("GITHUB_ACTIONS", "").lower() == "true":
            if path.is_absolute():
                raise cycle.manager.ManagerError(f"Committed Daily {label} path must be repository-relative.")
            result = subprocess.run(
                ["git", "show", f"HEAD:{path.as_posix()}"],
                check=True, capture_output=True, text=True,
            )
            raw = result.stdout
        else:
            raw = path.read_text(encoding="utf-8")
        value = json.loads(raw)
    except cycle.manager.ManagerError:
        raise
    except (OSError, ValueError, TypeError, subprocess.CalledProcessError) as error:
        raise cycle.manager.ManagerError(
            f"Committed Daily {label} is missing or unreadable; refusing recovery."
        ) from error
    if not isinstance(value, dict):
        raise cycle.manager.ManagerError(f"Committed Daily {label} is malformed; refusing recovery.")
    return value


def load_verified_daily_stage(cycle, stage_path):
    """Load a production stage and its exact committed pre-write backup; never trust input paths."""
    path = _safe_stage_path(cycle, stage_path)
    stage = _read_committed_json(cycle, path, "stage")
    if (
        stage.get("schema_version") != 1
        or stage.get("playlist_id") != cycle.DAILY_ID
        or stage.get("playlist_name") != "Tricky Daily"
        or stage.get("stage_mode") != "production"
        or stage.get("status") != "staged_before_spotify_write"
    ):
        raise cycle.manager.ManagerError("Daily recovery stage is not a supported immutable production stage.")
    cycle_date = stage.get("cycle_date_eastern")
    run_id = stage.get("run_id")
    try:
        date.fromisoformat(cycle_date)
    except (TypeError, ValueError):
        raise cycle.manager.ManagerError("Daily recovery stage has an invalid Eastern cycle date.")
    if not isinstance(run_id, str) or not run_id or path.name != f"{cycle_date}-{run_id}.json":
        raise cycle.manager.ManagerError("Daily recovery stage filename does not match its recorded run.")

    prewrite_uris = stage.get("prewrite_uris")
    target_uris = stage.get("target_uris")
    candidates = stage.get("candidate_tracks")
    if (
        not isinstance(prewrite_uris, list)
        or any(not isinstance(uri, str) or not uri.startswith("spotify:track:") for uri in prewrite_uris)
        or not isinstance(target_uris, list)
        or len(target_uris) != cycle.DAILY_TARGET_SIZE
        or any(not isinstance(uri, str) or not uri.startswith("spotify:track:") for uri in target_uris)
        or len(set(target_uris)) != cycle.DAILY_TARGET_SIZE
        or not isinstance(candidates, list)
        or len(candidates) != cycle.DAILY_TARGET_SIZE
    ):
        raise cycle.manager.ManagerError("Daily recovery stage has an invalid pre-write or target URI list.")
    for index, row in enumerate(candidates):
        if (
            not isinstance(row, dict)
            or not isinstance(row.get("artist"), str) or not row["artist"].strip()
            or not isinstance(row.get("track"), str) or not row["track"].strip()
            or row.get("uri") != target_uris[index]
        ):
            raise cycle.manager.ManagerError("Daily recovery stage candidate metadata does not match its ordered target.")
    description = stage.get("target_description")
    snapshot_id = stage.get("prewrite_snapshot_id")
    if (
        not isinstance(description, str) or not description.strip() or len(description) > 300
        or not isinstance(snapshot_id, str) or not snapshot_id
    ):
        raise cycle.manager.ManagerError("Daily recovery stage is missing its target description or pre-write snapshot ID.")

    digest = stage.get("payload_sha256")
    hash_payload = {key: value for key, value in stage.items() if key != "payload_sha256"}
    calculated = hashlib.sha256(
        json.dumps(hash_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if not isinstance(digest, str) or len(digest) != 64 or not secrets.compare_digest(digest, calculated):
        raise cycle.manager.ManagerError("Daily recovery stage hash does not match its committed payload.")

    backup_path = _safe_backup_path(cycle, stage.get("backup_path"))
    backup = _read_committed_json(cycle, backup_path, "recovery backup")
    playlist = backup.get("playlist")
    items = backup.get("items")
    if (
        not isinstance(playlist, dict)
        or playlist.get("id") != cycle.DAILY_ID
        or (playlist.get("name") or "").strip().casefold() != "tricky daily"
        or playlist.get("snapshot_id") != snapshot_id
        or not isinstance(playlist.get("description"), str)
        or not isinstance(items, list)
    ):
        raise cycle.manager.ManagerError("Daily recovery backup does not match the staged pre-write playlist identity.")
    backup_uris = []
    for row in items:
        if not isinstance(row, dict):
            raise cycle.manager.ManagerError("Daily recovery backup contains a malformed track row.")
        uri = row.get("uri")
        artists = row.get("artists") or []
        artist = artists[0] if artists else row.get("artist", "")
        title = row.get("name") or row.get("track") or ""
        if (
            not isinstance(uri, str) or not uri.startswith("spotify:track:")
            or not isinstance(artist, str) or not artist.strip()
            or not isinstance(title, str) or not title.strip()
        ):
            raise cycle.manager.ManagerError("Daily recovery backup contains incomplete track identity metadata.")
        backup_uris.append(uri)
    if backup_uris != prewrite_uris:
        raise cycle.manager.ManagerError("Daily recovery backup ordered URIs do not exactly match the staged pre-write list.")
    return stage, backup, path


def assert_stage_recoverable(cycle, stage_path, stage, config):
    if not isinstance(config, dict):
        raise cycle.manager.ManagerError("Playlist-manager state is malformed; refusing Daily recovery.")
    resolutions = config.get("daily_recovery", {})
    if not isinstance(resolutions, dict):
        raise cycle.manager.ManagerError("Daily recovery resolution ledger is malformed; refusing recovery.")
    existing = resolutions.get(stage_path)
    if existing is not None:
        if not isinstance(existing, dict):
            raise cycle.manager.ManagerError("Daily recovery resolution entry is malformed; refusing recovery.")
        if existing.get("status") in DAILY_RECOVERY_RESOLVED_STATUSES:
            raise cycle.manager.ManagerError("This Daily stage already has an audited recovery resolution.")
        if existing.get("status") not in (None, "in_progress"):
            raise cycle.manager.ManagerError("Daily stage has an unknown recovery state; refusing recovery.")
        if existing.get("payload_sha256") not in (None, stage.get("payload_sha256")):
            raise cycle.manager.ManagerError("Daily recovery ledger hash does not match the committed stage.")

    daily_state = config.get("daily_cycle", {})
    if not isinstance(daily_state, dict):
        raise cycle.manager.ManagerError("Tricky Daily cycle state is malformed; refusing recovery.")
    current_date = daily_state.get("last_cycle_date_eastern")
    if current_date:
        try:
            date.fromisoformat(current_date)
        except (TypeError, ValueError):
            raise cycle.manager.ManagerError("Tricky Daily cycle date is malformed; refusing recovery.")
        if current_date > stage["cycle_date_eastern"]:
            raise cycle.manager.ManagerError("This Daily stage is stale because a later Eastern cycle is already recorded.")
        if current_date == stage["cycle_date_eastern"] and daily_state.get("status") in (
            "completed", "recovery_rolled_back", "recovery_discarded"
        ):
            raise cycle.manager.ManagerError("This Eastern date already has a terminal Daily cycle or recovery state.")
    if daily_state.get("stage_path") == stage_path and daily_state.get("status") == "completed":
        raise cycle.manager.ManagerError("This Daily stage is already recorded as completed.")
    last_completed = config.get("last_completed", {})
    if (
        isinstance(last_completed, dict)
        and last_completed.get("kind") == "daily"
        and last_completed.get("stage_path") == stage_path
    ):
        raise cycle.manager.ManagerError("Playlist-manager state already records this Daily stage as completed.")


def classify_live_state(cycle, playlist, snapshot, stage, backup):
    """Classify only exact pre-write/target states with the known staged descriptions."""
    if (
        not isinstance(playlist, dict)
        or playlist.get("id") != cycle.DAILY_ID
        or (playlist.get("name") or "").strip().casefold() != "tricky daily"
    ):
        raise cycle.manager.ManagerError("Live playlist identity differs from the Daily recovery stage.")
    items = snapshot.get("items") if isinstance(snapshot, dict) else None
    reported = (playlist.get("items") or playlist.get("tracks") or {}).get("total")
    if not isinstance(items, list) or not isinstance(reported, int) or reported != len(items):
        raise cycle.manager.ManagerError("Live Daily recovery read-back is incomplete; refusing recovery.")
    live_uris = [row.get("uri") if isinstance(row, dict) else None for row in items]
    if any(not isinstance(uri, str) or not uri.startswith("spotify:track:") for uri in live_uris):
        raise cycle.manager.ManagerError("Live Daily recovery read-back contains invalid or unavailable tracks.")

    live_description = html.unescape(playlist.get("description") or "")
    before_description = html.unescape((backup.get("playlist") or {}).get("description") or "")
    target_description = html.unescape(stage.get("target_description") or "")
    before_uris = stage["prewrite_uris"]
    target_uris = stage["target_uris"]

    if before_uris == target_uris and live_uris == before_uris:
        if live_description == before_description and playlist.get("snapshot_id") == stage["prewrite_snapshot_id"]:
            return "prewrite"
        if live_description == target_description and target_description != before_description:
            return "target"
        raise cycle.manager.ManagerError("Daily live state matches both stage orders but its description/snapshot is conflicting.")
    if live_uris == target_uris and live_description == target_description:
        return "target"
    if live_uris == target_uris and live_description == before_description:
        return "target_description_pending"
    if live_uris == before_uris and live_description == target_description and target_description != before_description:
        return "prewrite_description_applied"
    if (
        live_uris == before_uris
        and live_description == before_description
        and playlist.get("snapshot_id") == stage["prewrite_snapshot_id"]
    ):
        return "prewrite"
    raise cycle.manager.ManagerError(
        "Live Tricky Daily matches neither the exact staged pre-write state nor the exact target/known description states. "
        "Partial or conflicting state is not recoverable automatically."
    )


def assert_tracks_allowed(cycle, rows, feedback, label):
    blocked = 0
    for row in rows:
        if not isinstance(row, dict):
            raise cycle.manager.ManagerError(f"{label} contains malformed track metadata; refusing recovery.")
        artists = row.get("artists") or []
        artist = row.get("artist") or (artists[0] if artists else "")
        title = row.get("track") or row.get("name") or row.get("title") or ""
        uri = row.get("uri")
        if (
            not isinstance(artist, str) or not artist.strip()
            or not isinstance(title, str) or not title.strip()
            or not isinstance(uri, str) or not uri.startswith("spotify:track:")
        ):
            raise cycle.manager.ManagerError(f"{label} contains incomplete track identity metadata; refusing recovery.")
        if cycle.discovery.is_playlist_candidate_blocked(artist, title, uri, feedback):
            blocked += 1
    if blocked:
        raise cycle.manager.ManagerError(
            f"{label} contains {blocked} currently blacklisted tracks; refusing to re-add or resume them."
        )


def validate_recovery_snapshot(cycle, playlist, snapshot, expected_uris, expected_description, owner_id, feedback):
    if (
        not isinstance(playlist, dict)
        or playlist.get("id") != cycle.DAILY_ID
        or (playlist.get("name") or "").strip().casefold() != "tricky daily"
        or (playlist.get("owner") or {}).get("id") != owner_id
    ):
        raise cycle.manager.ManagerError("Daily recovery read-back no longer confirms the exact owner-controlled playlist.")
    items = snapshot.get("items") if isinstance(snapshot, dict) else None
    reported = (playlist.get("items") or playlist.get("tracks") or {}).get("total")
    if not isinstance(items, list) or not isinstance(reported, int) or reported != len(items):
        raise cycle.manager.ManagerError("Daily recovery after-snapshot is incomplete; recovery remains pending.")
    actual_uris = [row.get("uri") if isinstance(row, dict) else None for row in items]
    if actual_uris != expected_uris:
        raise cycle.manager.ManagerError("Daily recovery after-snapshot does not match the exact ordered recovery target.")
    if any(not isinstance(uri, str) or not uri.startswith("spotify:track:") for uri in actual_uris):
        raise cycle.manager.ManagerError("Daily recovery after-snapshot contains invalid track URIs.")
    if len(set(actual_uris)) != len(actual_uris):
        raise cycle.manager.ManagerError("Daily recovery after-snapshot contains duplicate track URIs.")
    assert_tracks_allowed(cycle, items, feedback, "Daily recovery after-snapshot")
    observed_description = html.unescape(playlist.get("description") or "")
    if expected_description is not None and observed_description != expected_description:
        raise cycle.manager.ManagerError("Daily recovery description read-back does not match the selected recovery action.")
    return observed_description


def _record_started(cycle, stage_path, stage, action, classification):
    cycle.set_action_output("recovery_started", "true")
    config = cycle.manager.config()
    resolutions = config.setdefault("daily_recovery", {})
    if not isinstance(resolutions, dict):
        raise cycle.manager.ManagerError("Daily recovery resolution ledger is malformed; refusing recovery.")
    existing = resolutions.get(stage_path)
    if isinstance(existing, dict) and existing.get("status") in DAILY_RECOVERY_RESOLVED_STATUSES:
        raise cycle.manager.ManagerError("This Daily stage already has an audited recovery resolution.")
    daily_state = config.setdefault("daily_cycle", {})
    if not isinstance(daily_state, dict):
        raise cycle.manager.ManagerError("Tricky Daily cycle state is malformed; refusing recovery.")
    current_date = daily_state.get("last_cycle_date_eastern")
    if current_date and current_date > stage["cycle_date_eastern"]:
        raise cycle.manager.ManagerError("A later Daily cycle was recorded before recovery began.")
    resolutions[stage_path] = {
        "action": action,
        "status": "in_progress",
        "cycle_date_eastern": stage["cycle_date_eastern"],
        "payload_sha256": stage["payload_sha256"],
        "classification": classification,
        "started_at": (existing or {}).get("started_at") if isinstance(existing, dict) else cycle.manager.stamp(),
    }
    daily_state.update({
        "last_cycle_date_eastern": stage["cycle_date_eastern"],
        "playlist_id": cycle.DAILY_ID,
        "status": "recovery_in_progress",
        "stage_path": stage_path,
        "payload_sha256": stage["payload_sha256"],
    })
    cycle.manager.write(cycle.manager.CONFIG, config)
    cycle.manager.audit(
        event="daily_recovery_started",
        playlist_id=cycle.DAILY_ID,
        stage_path=stage_path,
        payload_sha256=stage["payload_sha256"],
        cycle_date_eastern=stage["cycle_date_eastern"],
        action=action,
        live_classification=classification,
    )


def _complete(cycle, stage_path, stage, action, final_description, after_snapshot_path=None, after_snapshot_id=None, before_snapshot_paths=None):
    config = cycle.manager.config()
    resolutions = config.setdefault("daily_recovery", {})
    daily_state = config.setdefault("daily_cycle", {})
    if not isinstance(resolutions, dict) or not isinstance(daily_state, dict):
        raise cycle.manager.ManagerError("Daily recovery state became malformed before resolution.")
    entry = resolutions.get(stage_path)
    if not isinstance(entry, dict) or entry.get("status") != "in_progress":
        raise cycle.manager.ManagerError("Daily recovery has no matching in-progress state; refusing to resolve.")
    if entry.get("payload_sha256") != stage["payload_sha256"] or entry.get("action") != action:
        raise cycle.manager.ManagerError("Daily recovery state no longer matches the verified stage/action.")
    current_date = daily_state.get("last_cycle_date_eastern")
    if current_date and current_date > stage["cycle_date_eastern"]:
        raise cycle.manager.ManagerError("A later Daily cycle appeared before recovery could be finalized.")

    resolved_status = {"resume": "completed", "rollback": "rolled_back", "discard": "discarded"}[action]
    entry.update({
        "status": resolved_status,
        "resolved_at": cycle.manager.stamp(),
        "before_snapshot_paths": list(before_snapshot_paths or []),
        "after_snapshot_path": after_snapshot_path,
        "after_snapshot_id": after_snapshot_id,
        "final_description": final_description,
    })
    daily_status = {
        "resume": "completed",
        "rollback": "recovery_rolled_back",
        "discard": "recovery_discarded",
    }[action]
    daily_state.update({
        "last_cycle_date_eastern": stage["cycle_date_eastern"],
        "playlist_id": cycle.DAILY_ID,
        "description": final_description,
        "status": daily_status,
        "stage_path": stage_path,
        "payload_sha256": stage["payload_sha256"],
    })
    if action in ("resume", "rollback"):
        daily_state["last_cycle_at"] = cycle.manager.stamp()
        daily_state["after_snapshot_path"] = after_snapshot_path
        daily_state["after_snapshot_id"] = after_snapshot_id
    cycle.manager.write(cycle.manager.CONFIG, config)
    cycle.set_action_output("recovery_resolved", "true")
    cycle.manager.audit(
        event="daily_recovery_resolved",
        playlist_id=cycle.DAILY_ID,
        stage_path=stage_path,
        payload_sha256=stage["payload_sha256"],
        cycle_date_eastern=stage["cycle_date_eastern"],
        action=action,
        status=resolved_status,
        before_snapshot_paths=list(before_snapshot_paths or []),
        after_snapshot=after_snapshot_path,
        after_snapshot_id=after_snapshot_id,
    )


def _replace_tracks(cycle, sp, before_snapshot, target_uris, target_rows, stage_path, stage, action, owner_id):
    manager = cycle.manager
    cycle_date = stage["cycle_date_eastern"]
    before_path = manager.save_snapshot(before_snapshot)
    before_uris = [row.get("uri") for row in before_snapshot.get("items", [])]
    manager.audit(
        event="daily_recovery_track_write_started",
        playlist_id=cycle.DAILY_ID,
        stage_path=stage_path,
        action=action,
        before_snapshot=before_path,
        before_snapshot_id=(before_snapshot.get("playlist") or {}).get("snapshot_id"),
        target_track_count=len(target_uris),
    )
    before_commit_sha = cycle.persist_daily_snapshot(before_path, cycle_date, "before")
    cycle.assert_repository_head_unchanged(before_commit_sha)
    cycle.assert_live_snapshot_unchanged(sp, before_snapshot, owner_id)
    fresh_feedback = cycle.discovery.load_playlist_feedback([], cycle.DAILY_ID)
    assert_tracks_allowed(cycle, target_rows, fresh_feedback, "Daily recovery target")
    if not manager.unlocked(cycle.DAILY_ID):
        raise manager.ManagerError("Tricky Daily was locked before recovery mutation; refusing the write.")
    try:
        cycle.cloud.replace_playlist(sp, cycle.DAILY_ID, target_uris, expected_before_uris=before_uris)
    except Exception as error:
        try:
            _updated, _snapshot, after_path = cycle.capture_and_persist_after_snapshot(sp, cycle_date)
            manager.audit(
                event="daily_recovery_track_write_failed_after_snapshot",
                playlist_id=cycle.DAILY_ID,
                stage_path=stage_path,
                action=action,
                before_snapshot=before_path,
                after_snapshot=after_path,
                error_type=type(error).__name__,
            )
        except Exception as snapshot_error:
            manager.audit(
                event="daily_recovery_track_write_after_snapshot_failed",
                playlist_id=cycle.DAILY_ID,
                stage_path=stage_path,
                action=action,
                before_snapshot=before_path,
                error_type=type(error).__name__,
                snapshot_error_type=type(snapshot_error).__name__,
            )
        raise manager.ManagerError(
            "Daily recovery track write did not reach a verified target; the immutable stage remains unresolved."
        ) from error
    try:
        updated, snapshot, after_path = cycle.capture_and_persist_after_snapshot(sp, cycle_date)
    except Exception as error:
        manager.audit(
            event="daily_recovery_track_write_after_snapshot_failed",
            playlist_id=cycle.DAILY_ID,
            stage_path=stage_path,
            action=action,
            before_snapshot=before_path,
            error_type=type(error).__name__,
        )
        raise manager.ManagerError(
            "Daily recovery write was accepted but its durable after-snapshot failed; recovery remains pending."
        ) from error
    fresh_feedback = cycle.discovery.load_playlist_feedback([], cycle.DAILY_ID)
    validate_recovery_snapshot(cycle, updated, snapshot, target_uris, None, owner_id, fresh_feedback)
    manager.audit(
        event="daily_recovery_track_write_verified",
        playlist_id=cycle.DAILY_ID,
        stage_path=stage_path,
        action=action,
        before_snapshot=before_path,
        after_snapshot=after_path,
        after_snapshot_id=updated.get("snapshot_id"),
        target_track_count=len(target_uris),
    )
    return updated, snapshot, before_path, after_path


def _update_description(cycle, sp, before_snapshot, description, stage_path, stage, action, owner_id):
    manager = cycle.manager
    cycle_date = stage["cycle_date_eastern"]
    before_path = manager.save_snapshot(before_snapshot)
    manager.audit(
        event="daily_recovery_description_write_started",
        playlist_id=cycle.DAILY_ID,
        stage_path=stage_path,
        action=action,
        before_snapshot=before_path,
        before_snapshot_id=(before_snapshot.get("playlist") or {}).get("snapshot_id"),
    )
    before_commit_sha = cycle.persist_daily_snapshot(before_path, cycle_date, "before")
    cycle.assert_repository_head_unchanged(before_commit_sha)
    cycle.assert_live_snapshot_unchanged(sp, before_snapshot, owner_id)
    try:
        updated, snapshot, after_path = cycle.update_description_and_capture_after_snapshot(
            sp, description, cycle_date
        )
    except Exception as error:
        manager.audit(
            event="daily_recovery_description_write_unverified",
            playlist_id=cycle.DAILY_ID,
            stage_path=stage_path,
            action=action,
            before_snapshot=before_path,
            error_type=type(error).__name__,
        )
        raise
    manager.audit(
        event="daily_recovery_description_write_verified",
        playlist_id=cycle.DAILY_ID,
        stage_path=stage_path,
        action=action,
        before_snapshot=before_path,
        after_snapshot=after_path,
        after_snapshot_id=updated.get("snapshot_id"),
    )
    return updated, snapshot, before_path, after_path


def run_daily_stage_recovery(cycle, sp, stage_path, action, owner_id):
    """Owner-confirmed resume/rollback/discard for one immutable production stage."""
    manager = cycle.manager
    if action not in ("resume", "rollback", "discard"):
        raise manager.ManagerError("Daily recovery action must be resume, rollback, or discard.")
    config = manager.config()
    stage, backup, verified_path = load_verified_daily_stage(cycle, stage_path)
    stage_key = verified_path.as_posix()
    assert_stage_recoverable(cycle, stage_key, stage, config)

    playlist = sp.call("GET", f"/playlists/{cycle.DAILY_ID}")
    if (
        not isinstance(playlist, dict)
        or playlist.get("id") != cycle.DAILY_ID
        or (playlist.get("name") or "").strip().casefold() != "tricky daily"
        or (playlist.get("owner") or {}).get("id") != owner_id
    ):
        raise manager.ManagerError("Daily recovery could not confirm exact playlist ID, name, and authenticated owner.")
    manager.assert_managed(cycle.DAILY_ID)
    snapshot = manager.snapshot(sp, playlist)
    classification = classify_live_state(cycle, playlist, snapshot, stage, backup)
    live_uris = [row.get("uri") for row in snapshot.get("items", [])]
    live_description = html.unescape(playlist.get("description") or "")
    before_description = html.unescape((backup.get("playlist") or {}).get("description") or "")
    target_description = html.unescape(stage["target_description"])

    if action == "discard":
        if classification != "prewrite":
            raise manager.ManagerError(
                "Discard is allowed only when the exact pre-write tracks, description, and snapshot ID are still live."
            )
        _record_started(cycle, stage_key, stage, action, classification)
        _complete(
            cycle, stage_key, stage, action, before_description,
            after_snapshot_path=None, after_snapshot_id=None, before_snapshot_paths=[],
        )
        print(f"Tricky Daily stage discarded without Spotify writes: {stage_key}")
        return 0

    if action == "resume":
        target_uris = list(stage["target_uris"])
        target_rows = stage["candidate_tracks"]
        feedback = cycle.discovery.load_playlist_feedback([], cycle.DAILY_ID)
        assert_tracks_allowed(cycle, target_rows, feedback, "Staged Daily target")
        needs_track_write = live_uris != target_uris
        desired_description = target_description
        needs_description_write = live_description != desired_description
    else:
        target_uris = [row.get("uri") for row in (backup.get("items") or [])]
        target_rows = backup["items"]
        if not target_uris or len(set(target_uris)) != len(target_uris):
            raise manager.ManagerError("Daily rollback backup is empty or contains duplicate tracks; refusing restoration.")
        feedback = cycle.discovery.load_playlist_feedback([], cycle.DAILY_ID)
        assert_tracks_allowed(cycle, target_rows, feedback, "Daily rollback backup")
        needs_track_write = live_uris != target_uris
        desired_description = before_description
        needs_description_write = live_description != desired_description

    if needs_track_write or needs_description_write:
        if not manager.unlocked(cycle.DAILY_ID):
            raise manager.ManagerError("Tricky Daily is locked; recovery will not override the playlist lock.")
    _record_started(cycle, stage_key, stage, action, classification)
    before_snapshot_paths = []
    current_playlist = playlist
    current_snapshot = snapshot
    after_snapshot_path = None

    if needs_track_write:
        current_playlist, current_snapshot, before_path, after_snapshot_path = _replace_tracks(
            cycle, sp, current_snapshot, target_uris, target_rows, stage_key, stage, action, owner_id
        )
        before_snapshot_paths.append(before_path)

    feedback = cycle.discovery.load_playlist_feedback([], cycle.DAILY_ID)
    validate_recovery_snapshot(cycle, current_playlist, current_snapshot, target_uris, None, owner_id, feedback)

    if html.unescape(current_playlist.get("description") or "") != desired_description:
        feedback = cycle.discovery.load_playlist_feedback([], cycle.DAILY_ID)
        assert_tracks_allowed(cycle, current_snapshot.get("items") or [], feedback, "Daily recovery live tracks")
        if not manager.unlocked(cycle.DAILY_ID):
            raise manager.ManagerError("Tricky Daily was locked before the recovery description update.")
        current_playlist, current_snapshot, before_path, after_snapshot_path = _update_description(
            cycle, sp, current_snapshot, desired_description, stage_key, stage, action, owner_id
        )
        before_snapshot_paths.append(before_path)
    elif after_snapshot_path is None:
        current_playlist, current_snapshot, after_snapshot_path = cycle.capture_and_persist_after_snapshot(
            sp, stage["cycle_date_eastern"]
        )

    feedback = cycle.discovery.load_playlist_feedback([], cycle.DAILY_ID)
    final_description = validate_recovery_snapshot(
        cycle, current_playlist, current_snapshot, target_uris, desired_description, owner_id, feedback
    )
    if action == "resume":
        baseline_rows = [
            {"uri": row["uri"], "track": row["track"], "artist": row["artist"]}
            for row in stage["candidate_tracks"]
        ]
    else:
        baseline_rows = backup["items"]
    cycle.discovery.write_daily_removal_baseline(baseline_rows, manager.stamp())
    _complete(
        cycle, stage_key, stage, action, final_description,
        after_snapshot_path=after_snapshot_path,
        after_snapshot_id=current_playlist.get("snapshot_id"),
        before_snapshot_paths=before_snapshot_paths,
    )
    print(f"Tricky Daily stage {action} recovery verified: {stage_key}")
    return 0


# FILE OVERVIEW
# Purpose: Owner-confirmed recovery of one immutable Tricky Daily production stage.
# Actions: Resume the exact staged target, restore its exact pre-write backup, or
#          discard only when the original pre-write playlist is still provably live.
# Safety: Requires exact committed stage/backup hashes, exact live ordered URI and
#         description classification, current blacklist checks, managed-playlist
#         permission, explicit unlock for writes, and owner-only manual confirmation.
# Persistence: Every recovery write commits a before snapshot and an after snapshot;
#              state/audit record the in-progress and terminal resolution separately.
# Scope: No automatic recovery, no non-Daily playlist writes, and no Library mutation.
