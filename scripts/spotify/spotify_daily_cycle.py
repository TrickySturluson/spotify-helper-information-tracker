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
from datetime import datetime
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

# Short, user-approved-in-spirit rotating lines for the daily discovery queue.
# This is deliberately separate from the metadata description generator: Daily
# has an established non-empty editorial description and the user requested
# that it rotate on every successful daily cycle.
DAILY_DESCRIPTIONS = (
    "Could be worse. Could be quiet.",
    "At least the music's good.",
    "Familiar names. Unexpected detours",
    "Your daily dose of questionable taste.",
    "A little familiar, a little unhinged.",
    "No skips promised. Good luck.",
    "Today's detour starts here.",
    "The algorithm has questionable taste.",
)


def choose_daily_description(cycle_date, current_description=""):
    """Choose a deterministic daily line and guarantee it differs from current."""
    day = date.fromisoformat(cycle_date).toordinal()
    start = day % len(DAILY_DESCRIPTIONS)
    current = (current_description or "").strip()
    for offset in range(len(DAILY_DESCRIPTIONS)):
        candidate = DAILY_DESCRIPTIONS[(start + offset) % len(DAILY_DESCRIPTIONS)]
        if candidate != current:
            return candidate
    raise manager.ManagerError("No distinct Tricky Daily description is available.")


def should_run_cycle(local_now, force=False, event_name=None):
    """Allow delayed scheduled runs to catch up once per Eastern date.

    GitHub may queue scheduled workflows well after their nominal cron time.
    The daily_cycle date guard below makes catch-up safe and idempotent. During
    standard time, the 04:00 UTC cron lands at 23:00 Eastern on the prior date;
    that occurrence must wait for the 05:00 UTC midnight occurrence.
    Manual dispatches remain restricted unless --force is explicitly supplied.
    """
    if force:
        return True
    if event_name == "schedule":
        return local_now.hour != 23
    return local_now.hour == 0 and local_now.minute < 30


def cycle_already_completed(config, cycle_date):
    """Return whether the Eastern date has already been claimed by a cycle."""
    state = config.get("daily_cycle", {})
    if not isinstance(state, dict):
        raise manager.ManagerError("Tricky Daily cycle state is malformed; refusing a duplicate rotation.")
    return state.get("last_cycle_date_eastern") == cycle_date


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
    if not should_run_cycle(local_now, force=args.force, event_name=event_name):
        print(f"Outside the allowed Tricky Daily cycle window ({local_now.isoformat()}, event={event_name or 'manual'}); no Spotify requests sent.")
        set_action_output("cycled", "false")
        return 0
    cycle_date = local_now.date().isoformat()

    configure()
    # Check the persisted date before opening Spotify. Backup cron entries and
    # delayed duplicate deliveries should be cheap local no-ops after success.
    config = manager.config()
    if cycle_already_completed(config, cycle_date):
        print(f"Tricky Daily already cycled for {cycle_date} Eastern; skipping duplicate run.")
        set_action_output("cycled", "false")
        return 0

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

    # Re-read immediately before planning/mutation in case state changed after
    # startup. The workflow concurrency group also serializes cycle executions.
    config = manager.config()
    if cycle_already_completed(config, cycle_date):
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

    # Rotate Daily's short editorial description after the track replacement.
    # The description is intentionally owned by this dedicated Daily workflow,
    # not by the generic metadata generator (which protects manual descriptions).
    next_description = choose_daily_description(cycle_date, playlist.get("description", ""))
    sp.call("PUT", f"/playlists/{DAILY_ID}", {"description": next_description})

    # The playlist replacement has been accepted. Persist the idempotency guard
    # and publish the output immediately, so the workflow can preserve this state
    # even if post-change verification or feedback collection later fails.
    config = manager.config()
    config["daily_cycle"] = {
        "last_cycle_date_eastern": cycle_date,
        "last_cycle_at": manager.stamp(),
        "playlist_id": DAILY_ID,
        "description": next_description,
        "status": "replacement_accepted_pending_verification",
    }
    manager.write(manager.CONFIG, config)
    # Publish immediately after the durable local guard; if audit append fails,
    # the workflow still knows Spotify accepted the playlist replacement.
    set_action_output("cycled", "true")
    manager.audit(
        event="daily_cycle_replacement_accepted",
        playlist_id=DAILY_ID,
        cycle_date_eastern=cycle_date,
        backup=backup,
    )

    updated = sp.call("GET", f"/playlists/{DAILY_ID}")
    if (updated.get("description") or "") != next_description:
        raise manager.ManagerError(
            "Tricky Daily tracks were replaced, but Spotify read-back did not confirm "
            "the new playlist description; cycle remains pending verification."
        )
    updated_snapshot = manager.snapshot(sp, updated)
    after_snapshot = manager.save_snapshot(updated_snapshot)
    manager.audit(event="daily_post_change_snapshot_saved", playlist_id=DAILY_ID,
                  snapshot=after_snapshot, cycle_date_eastern=cycle_date)
    config = manager.config()
    config["daily_cycle"] = {
        "last_cycle_date_eastern": cycle_date,
        "last_cycle_at": manager.stamp(),
        "playlist_id": DAILY_ID,
        "description": next_description,
        "status": "completed",
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
# Schedule: GitHub Actions invokes this at 04:00 and 05:00 UTC; a ZoneInfo gate
#           ensures only the actual midnight America/New_York run proceeds.
# Safety: Exact playlist ID/name/owner checks, managed-playlist policy, explicit
#         unlocked state, recommendation minimum, URI validation, duplicate
#         prevention, per-day idempotency, and a pre-change recovery snapshot.
# Feedback: Removed tracks are recorded only as neutral curator_rotation events
#           in Daily's own feedback store, never as playlist-fit rejection.
# Recovery: The backup is uploaded by the workflow and linked in manager state.
# -----------------------------------------------------------------------------
