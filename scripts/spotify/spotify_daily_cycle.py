#!/usr/bin/env python3
"""Rotate Tricky Daily at midnight America/New_York with a recoverable snapshot.

This is a dedicated discovery workflow, not a playlist-fit feedback event.
Tracks removed by a scheduled rotation are recorded as neutral curator rotation.
"""
import argparse
import json
import os
import secrets
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
COMPAT = ROOT / "compat"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(COMPAT) not in sys.path:
    sys.path.insert(0, str(COMPAT))
SOURCE_DIR = ROOT / "scripts" / "spotify"
if str(SOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIR))

import spotify_playlist_manager as manager
import spotify_discovery as discovery
import spotify_daily_feedback as daily_feedback
import spotify_listening_trends as listening_trends
import spotify_playlist_cloud as cloud
from scripts.music.discovery_ingestion import append_candidates

DAILY_ID = "4yUVHSMQySfWeEowfIMcx7"
EASTERN = ZoneInfo("America/New_York")
MINIMUM_RECOMMENDATIONS = 20


def should_run_cycle(local_now, force=False, event_name=None, schedule_cron=None):
    """Gate scheduled runs against the UTC cron that matches Eastern DST.

    GitHub can queue a scheduled run after its nominal time, so a correctly
    matched cron may catch up later on the same Eastern date. The per-date
    state guard below makes that catch-up idempotent. Separate cron strings
    let us reject the stale DST counterpart before making any Spotify calls.
    Manual dispatches remain restricted unless --force is explicitly supplied.
    """
    if force:
        return True
    if event_name == "schedule":
        expected_offsets = {
            "0 4 * * *": timedelta(hours=-4),  # Eastern Daylight Time
            "0 5 * * *": timedelta(hours=-5),  # Eastern Standard Time
        }
        expected_offset = expected_offsets.get(schedule_cron)
        return expected_offset is not None and local_now.utcoffset() == expected_offset
    return local_now.hour == 0 and local_now.minute < 30


def set_action_output(name, value):
    """Publish a GitHub Actions step output when running inside Actions."""
    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path:
        with open(output_path, "a", encoding="utf-8") as handle:
            handle.write(f"{name}={value}\n")


def configure():
    manager.CID = os.environ["SPOTIFY_CLIENT_ID"]
    manager.TOKEN = Path(".spotify_playlist_token.json")
    manager.CONFIG = Path(".github/spotify_playlist_manager_state.json")
    manager.AUDIT = Path(".github/spotify_playlist_manager_audit.jsonl")
    manager.BACKUPS = Path("playlist_backups")
    manager.write(manager.TOKEN, {
        "refresh_token": os.environ["SPOTIFY_REFRESH_TOKEN"],
        "obtained_at": 0,
        "expires_in": 0,
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Allow a manually dispatched run outside midnight.")
    args = parser.parse_args()
    local_now = datetime.now(EASTERN)
    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    schedule_cron = os.environ.get("SCHEDULE_CRON", "")
    if not should_run_cycle(
        local_now, force=args.force, event_name=event_name, schedule_cron=schedule_cron
    ):
        print(f"Outside the allowed Tricky Daily cycle window ({local_now.isoformat()}, event={event_name or 'manual'}); no Spotify requests sent.")
        set_action_output("cycled", "false")
        return 0
    cycle_date = local_now.date().isoformat()

    configure()
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
    manager.assert_managed(DAILY_ID)
    if not manager.unlocked(DAILY_ID):
        raise manager.ManagerError("Tricky Daily is locked; automatic rotation will not override the lock.")

    config = manager.config()
    cycle_state = config.setdefault("daily_cycle", {})
    if cycle_state.get("last_cycle_date_eastern") == cycle_date:
        print(f"Tricky Daily already cycled for {cycle_date} Eastern; skipping duplicate run.")
        set_action_output("cycled", "false")
        return 0

    before = manager.snapshot(sp, playlist)
    trend_report = listening_trends.generate()
    manager.audit(
        event="daily_listening_trends_generated", playlist_id=DAILY_ID,
        coverage=trend_report.get("coverage", {}),
        top_genres=[row.get("tag") for row in trend_report.get("genres", [])[:8]],
    )
    recommendations, skipped = discovery.build_discovery_recommendations(
        sp, before["items"], today=local_now.date(), playlist_id=DAILY_ID
    )
    if len(recommendations) < MINIMUM_RECOMMENDATIONS:
        raise manager.ManagerError(
            f"Only {len(recommendations)} recommendations resolved; at least "
            f"{MINIMUM_RECOMMENDATIONS} are required. Playlist left unchanged."
        )
    uris = [row.get("uri") for row in recommendations]
    if any(not isinstance(uri, str) or not uri.startswith("spotify:track:") for uri in uris):
        raise manager.ManagerError("Recommendation set contains an invalid Spotify track URI.")
    if len(set(uris)) != len(uris):
        raise manager.ManagerError("Recommendation set contains duplicate track URIs.")

    # Record surfaced recommendations before playlist mutation. This is discovery
    # evidence only; playback, scrobbles, and saves remain separate evidence.
    discovery_result = append_candidates(
        recommendations,
        source="tricky_daily_recommendations",
        context={"playlist_id": DAILY_ID, "cycle_date_eastern": cycle_date},
    )
    manager.audit(
        event="daily_discovery_candidates_persisted",
        playlist_id=DAILY_ID,
        cycle_date_eastern=cycle_date,
        input_rows=discovery_result["input_rows"],
        new_candidates=discovery_result["new_candidates"],
        unique_candidates=discovery_result["unique_candidates"],
    )

    liked_baseline = {}
    try:
        for offset in range(0, len(uris), 50):
            batch = uris[offset:offset + 50]
            saved = sp.call("GET", "/me/library/contains?uris=" + ",".join(batch))
            liked_baseline.update(dict(zip(batch, [bool(value) for value in (saved or [])])))
    except Exception as error:
        manager.audit(event="daily_liked_baseline_unavailable", error_type=type(error).__name__)

    backup = manager.save_snapshot(before)
    manager.audit(
        event="daily_cycle_started", playlist_id=DAILY_ID, cycle_date_eastern=cycle_date,
        recommendation_count=len(recommendations), skipped_count=len(skipped), backup=backup,
    )
    cloud.replace_playlist(sp, DAILY_ID, uris)

    # Persist the per-day guard immediately after Spotify accepts the replacement.
    # If a later observation fails, a rerun cannot accidentally rotate twice.
    updated = sp.call("GET", f"/playlists/{DAILY_ID}")
    updated_snapshot = manager.snapshot(sp, updated)
    after_snapshot = manager.save_snapshot(updated_snapshot)
    manager.audit(event="daily_post_change_snapshot_saved", playlist_id=DAILY_ID,
                  snapshot=after_snapshot, cycle_date_eastern=cycle_date)
    config = manager.config()
    config["daily_cycle"] = {
        "last_cycle_date_eastern": cycle_date,
        "last_cycle_at": manager.stamp(),
        "playlist_id": DAILY_ID,
    }
    config["last_completed"] = {
        "playlist_id": DAILY_ID,
        "backup": backup,
        "backup_run_id": os.environ.get("GITHUB_RUN_ID", ""),
        "after_snapshot_id": updated.get("snapshot_id"),
        "after_uris": [row.get("uri") for row in updated_snapshot["items"]],
        "kind": "daily",
        "cycle_date_eastern": cycle_date,
    }
    manager.write(manager.CONFIG, config)

    old_uris = {row.get("uri") for row in before["items"] if row.get("uri")}
    new_uris = set(uris)
    metadata = {row["uri"]: {"artist": row.get("artist"), "track": row.get("track")}
                for row in recommendations}
    daily_feedback.record_additions(
        [{"uri": uri, **metadata.get(uri, {})} for uri in uris],
        added_at=manager.stamp(), liked_at_add=liked_baseline,
    )
    for old_uri in old_uris - new_uris:
        daily_feedback.record_removal(old_uri, removed_at=manager.stamp(), reason="curator_rotation")

    manager.audit(
        event="daily_cycle_completed", playlist_id=DAILY_ID, cycle_date_eastern=cycle_date,
        recommendation_count=len(recommendations), removed_by_rotation=len(old_uris - new_uris),
        backup=backup, spotify_requests=sp.request_metrics,
    )

    try:
        daily_feedback.observe_liked_songs(sp, uris)
    except Exception as error:
        manager.audit(event="daily_liked_song_observation_failed", error_type=type(error).__name__)
    try:
        daily_feedback.observe_playback_segments()
    except Exception as error:
        manager.audit(event="daily_playback_observation_failed", error_type=type(error).__name__)
    try:
        daily_feedback.observe_lastfm_scrobbles()
    except Exception as error:
        manager.audit(event="daily_lastfm_observation_failed", error_type=type(error).__name__)

    set_action_output("cycled", "true")
    print(
        f"Tricky Daily cycled for {cycle_date} Eastern: {len(recommendations)} tracks; "
        f"{len(old_uris - new_uris)} tracks rotated out neutrally. "
        f"Recovery snapshot: {backup}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (manager.ManagerError, OSError, KeyError, ValueError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Automatically refresh Tricky Daily once per Eastern calendar day.
# Schedule: Separate 04:00/05:00 UTC cron entries are matched to the current
#           America/New_York UTC offset before any Spotify request is sent.
# Safety: Exact playlist ID/name/owner checks, managed-playlist policy, explicit
#         unlocked state, recommendation minimum, URI validation, duplicate
#         prevention, per-day idempotency, and a pre-change recovery snapshot.
# Feedback: Removed tracks are recorded only as neutral curator_rotation events
#           in Daily's own feedback store, never as playlist-fit rejection.
# Recovery: The backup is uploaded by the workflow and linked in manager state.
# -----------------------------------------------------------------------------
