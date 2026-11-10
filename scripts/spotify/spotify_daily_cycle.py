#!/usr/bin/env python3
"""Rotate Tricky Daily at midnight America/New_York with a recoverable snapshot.

This is a dedicated discovery workflow, not a playlist-fit feedback event.
Tracks removed by a scheduled rotation are recorded as neutral curator rotation.
"""
import argparse
import hashlib
import html
import json
import os
import secrets
import subprocess
import sys
import time
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
COMPAT = ROOT / "compat"
SOURCE_DIR = ROOT / "scripts" / "spotify"
# Maintained modules must win over legacy compatibility launchers regardless
# of whether this file is invoked directly or through compat/spotify_daily_cycle.py.
for entry in (ROOT, COMPAT):
    if str(entry) in sys.path:
        sys.path.remove(str(entry))
    sys.path.append(str(entry))
if str(SOURCE_DIR) in sys.path:
    sys.path.remove(str(SOURCE_DIR))
sys.path.insert(0, str(SOURCE_DIR))

import spotify_playlist_manager as manager
import spotify_discovery as discovery
import spotify_daily_feedback as daily_feedback
import spotify_listening_trends as listening_trends
import spotify_playlist_cloud as cloud
from scripts.music.discovery_ingestion import append_candidates

DAILY_ID = "4yUVHSMQySfWeEowfIMcx7"
EASTERN = ZoneInfo("America/New_York")
DAILY_TARGET_SIZE = 60
MINIMUM_RECOMMENDATIONS = DAILY_TARGET_SIZE
DAILY_STAGE_DIR = Path("assistant_data/spotify/staging/tricky_daily")

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
    """Return whether this Eastern date already has an accepted cycle, regardless of force."""
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


def assert_no_pending_daily_stage(cycle_date):
    """Block same-date retries when a durable pre-write stage survives a failed run."""
    if not DAILY_STAGE_DIR.exists():
        return
    pending = sorted(DAILY_STAGE_DIR.glob(f"{cycle_date}-*.json"))
    if pending:
        examples = ", ".join(str(path) for path in pending[:3])
        raise manager.ManagerError(
            f"A durable Tricky Daily stage already exists for {cycle_date} Eastern "
            f"({examples}). Automatic retry is blocked until the staged payload and live "
            "playlist are inspected."
        )


def persist_daily_stage(stage_path, backup_path, cycle_date):
    """Commit the immutable stage and recovery snapshot before any Spotify write."""
    if os.environ.get("GITHUB_ACTIONS", "").lower() != "true":
        return False
    paths = [
        str(stage_path),
        str(backup_path),
        ".github/spotify_playlist_manager_audit.jsonl",
        "assistant_data/spotify/daily_feedback.json",
        "assistant_data/spotify/listening_trends.json",
        "playlist_removal_baseline.json",
        "playlist_removed_tracks.json",
        "assistant_data/recommendations/discovery_candidates.json",
    ]
    existing = [path for path in paths if Path(path).is_file() and path != str(backup_path)]
    backup_exists = Path(backup_path).is_file()
    subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
    subprocess.run(
        ["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"],
        check=True,
    )
    if existing:
        subprocess.run(["git", "add", "--", *existing], check=True)
    if backup_exists:
        # playlist_backups/ is intentionally ignored by default; the one exact
        # recovery snapshot paired with this stage must still be committed.
        subprocess.run(["git", "add", "-f", "--", str(backup_path)], check=True)
    subprocess.run(
        ["git", "commit", "-m", f"Stage Tricky Daily payload for {cycle_date}"],
        check=True,
    )
    # A non-fast-forward rejection is a hard stop before the Spotify mutation.
    subprocess.run(["git", "push", "origin", "HEAD:main"], check=True)
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def assert_repository_head_unchanged(stage_commit_sha):
    """Abort if another main-branch commit lands after the durable stage push."""
    if os.environ.get("GITHUB_ACTIONS", "").lower() != "true" or not stage_commit_sha:
        return
    subprocess.run(["git", "fetch", "origin", "main"], check=True, capture_output=True, text=True)
    local_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    remote_sha = subprocess.run(
        ["git", "rev-parse", "origin/main"], check=True, capture_output=True, text=True
    ).stdout.strip()
    if local_sha != stage_commit_sha or remote_sha != stage_commit_sha:
        raise manager.ManagerError(
            "Repository main changed after the Daily payload was durably staged; "
            "aborting before Spotify mutation so newer lock/state changes cannot be overwritten."
        )


def verify_daily_stage(stage_path, expected_hash, expected_uris, before_uris, before_snapshot_id):
    """Verify the on-disk/committed stage is exactly the payload about to be written."""
    if os.environ.get("GITHUB_ACTIONS", "").lower() == "true":
        result = subprocess.run(
            ["git", "show", f"HEAD:{stage_path}"],
            check=True, capture_output=True, text=True,
        )
        staged = json.loads(result.stdout)
    else:
        staged = manager.read(Path(stage_path), None)
    if not isinstance(staged, dict):
        raise manager.ManagerError("Durable Daily stage is missing or malformed; refusing playlist mutation.")
    hash_payload = {key: value for key, value in staged.items() if key != "payload_sha256"}
    digest = hashlib.sha256(
        json.dumps(hash_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if (
        digest != expected_hash
        or staged.get("payload_sha256") != expected_hash
        or staged.get("target_uris") != expected_uris
        or staged.get("prewrite_uris") != before_uris
        or staged.get("prewrite_snapshot_id") != before_snapshot_id
    ):
        raise manager.ManagerError(
            "Durable Daily stage failed exact hash/order/pre-write snapshot verification; refusing playlist mutation."
        )
    return staged


def create_daily_stage(cycle_date, before, before_uris, recommendations, uris, backup, description, test_mode=False):
    """Write and durably publish the exact ordered Daily payload before mutation."""
    if len(uris) != DAILY_TARGET_SIZE or len(set(uris)) != DAILY_TARGET_SIZE:
        raise manager.ManagerError("Cannot stage Daily payload: expected 60 unique ordered URIs.")
    if any(not isinstance(uri, str) or not uri.startswith("spotify:track:") for uri in uris):
        raise manager.ManagerError("Cannot stage Daily payload: one or more URIs are invalid.")
    run_id = os.environ.get("GITHUB_RUN_ID") or f"local-{int(time.time())}"
    stage_dir = DAILY_STAGE_DIR / "tests" if test_mode else DAILY_STAGE_DIR
    stage_path = stage_dir / f"{cycle_date}-{run_id}.json"
    if stage_path.exists():
        raise manager.ManagerError(f"Daily stage already exists for this run: {stage_path}")
    candidate_rows = [
        {
            "artist": row.get("artist"),
            "track": row.get("track"),
            "uri": row.get("uri"),
            "artist_diversity_fallback": bool(row.get("artist_diversity_fallback")),
        }
        for row in recommendations
    ]
    record = {
        "schema_version": 1,
        "playlist_id": DAILY_ID,
        "playlist_name": "Tricky Daily",
        "cycle_date_eastern": cycle_date,
        "run_id": run_id,
        "created_at": manager.stamp(),
        "prewrite_snapshot_id": (before.get("playlist") or {}).get("snapshot_id"),
        "prewrite_uris": list(before_uris),
        "target_uris": list(uris),
        "candidate_tracks": candidate_rows,
        "target_description": description,
        "backup_path": str(backup),
        "status": "staged_before_spotify_write",
        "stage_mode": "test_only" if test_mode else "production",
    }
    payload_sha256 = hashlib.sha256(
        json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    record["payload_sha256"] = payload_sha256
    manager.write(stage_path, record)
    manager.audit(
        event="daily_cycle_payload_staged",
        playlist_id=DAILY_ID,
        cycle_date_eastern=cycle_date,
        stage_path=str(stage_path),
        payload_sha256=payload_sha256,
        target_track_count=len(uris),
        prewrite_snapshot_id=record["prewrite_snapshot_id"],
    )
    stage_commit_sha = persist_daily_stage(stage_path, backup, cycle_date)
    if os.environ.get("GITHUB_ACTIONS", "").lower() == "true" and not stage_commit_sha:
        raise manager.ManagerError("Daily stage was not durably committed; refusing playlist mutation.")
    verify_daily_stage(
        str(stage_path), payload_sha256, uris, before_uris,
        (before.get("playlist") or {}).get("snapshot_id"),
    )
    return str(stage_path), payload_sha256, stage_commit_sha


def assert_live_snapshot_unchanged(sp, expected_snapshot, expected_owner_id):
    """Fail closed if Daily changed while candidate generation was in progress."""
    expected_playlist = expected_snapshot.get("playlist") or {}
    expected_items = expected_snapshot.get("items") or []
    expected_uris = [row.get("uri") for row in expected_items]
    live = sp.call("GET", f"/playlists/{DAILY_ID}")
    if not isinstance(live, dict) or live.get("id") != DAILY_ID:
        raise manager.ManagerError("Pre-write guard could not confirm the exact Tricky Daily playlist.")
    if (live.get("owner") or {}).get("id") != expected_owner_id:
        raise manager.ManagerError("Pre-write guard found a changed or unexpected Daily owner.")
    if (live.get("name") or "").strip().casefold() != "tricky daily":
        raise manager.ManagerError("Pre-write guard found a changed Daily playlist name.")
    expected_description = html.unescape(expected_playlist.get("description") or "")
    live_description = html.unescape(live.get("description") or "")
    if live_description != expected_description:
        raise manager.ManagerError("Pre-write guard found a changed Daily description; aborting before write.")
    if not manager.unlocked(DAILY_ID):
        raise manager.ManagerError("Tricky Daily was locked during candidate generation; aborting before write.")

    live_snapshot = manager.snapshot(sp, live)
    live_items = live_snapshot.get("items") or []
    live_uris = [row.get("uri") for row in live_items]
    reported = (live.get("items") or live.get("tracks") or {}).get("total")
    if not isinstance(reported, int) or reported != len(live_items):
        raise manager.ManagerError(
            f"Pre-write guard could not verify complete pagination (reported={reported}, fetched={len(live_items)}); aborting."
        )
    if any(not isinstance(uri, str) or not uri.startswith("spotify:track:") for uri in live_uris):
        raise manager.ManagerError("Pre-write guard found unavailable or invalid live track rows; aborting.")
    if (
        live.get("snapshot_id") != expected_playlist.get("snapshot_id")
        or live_uris != expected_uris
    ):
        manager.audit(
            event="daily_prewrite_snapshot_changed",
            playlist_id=DAILY_ID,
            expected_snapshot_id=expected_playlist.get("snapshot_id"),
            observed_snapshot_id=live.get("snapshot_id"),
            expected_track_count=len(expected_uris),
            observed_track_count=len(live_uris),
            ordered_contents_match=live_uris == expected_uris,
        )
        raise manager.ManagerError(
            "Tricky Daily changed after candidate generation; the pre-write snapshot guard "
            "aborted without replacing any tracks."
        )
    return live, live_snapshot


def validate_daily_post_write(updated_playlist, updated_snapshot, expected_uris, feedback):
    """Validate exact ordered payload, pagination, unique tracks, artists, and removal policy."""
    items = updated_snapshot.get("items") or []
    actual_uris = [row.get("uri") for row in items]
    reported = (updated_playlist.get("items") or updated_playlist.get("tracks") or {}).get("total")
    if not isinstance(reported, int) or reported != len(items):
        raise manager.ManagerError(
            f"Post-write read-back was incomplete (reported={reported}, fetched={len(items)})."
        )
    if len(items) != DAILY_TARGET_SIZE or len(actual_uris) != DAILY_TARGET_SIZE:
        raise manager.ManagerError(
            f"Post-write read-back contains {len(items)} tracks; expected exactly {DAILY_TARGET_SIZE}."
        )
    if actual_uris != expected_uris:
        mismatch = next(
            (i for i, (actual, expected) in enumerate(zip(actual_uris, expected_uris)) if actual != expected),
            min(len(actual_uris), len(expected_uris)),
        )
        raise manager.ManagerError(
            f"Post-write ordered URI read-back differs from the staged payload at position {mismatch + 1}."
        )
    if len(set(actual_uris)) != len(actual_uris):
        raise manager.ManagerError("Post-write read-back contains duplicate track URIs.")
    if any(not isinstance(uri, str) or not uri.startswith("spotify:track:") for uri in actual_uris):
        raise manager.ManagerError("Post-write read-back contains an invalid track URI.")

    artists = [
        discovery.norm((row.get("artists") or [""])[0])
        for row in items
    ]
    if any(not artist for artist in artists):
        raise manager.ManagerError("Post-write read-back contains a track without a valid primary artist.")
    blocked = [
        row for row in items
        if discovery.is_playlist_candidate_blocked(
            (row.get("artists") or [""])[0],
            row.get("name") or row.get("track") or "",
            row.get("uri"),
            feedback,
        )
    ]
    if blocked:
        labels = [
            f"{(row.get('artists') or [''])[0]} — {row.get('name') or row.get('track')}"
            for row in blocked[:8]
        ]
        raise manager.ManagerError(
            f"Post-write read-back contains {len(blocked)} blacklisted tracks: " + ", ".join(labels)
        )
    return artists


def update_description_and_verify(sp, description):
    """Apply Daily's rotating line and tolerate brief Spotify read-after-write lag."""
    sp.call("PUT", f"/playlists/{DAILY_ID}", {"description": description})
    last_seen = None
    for attempt in range(5):
        verified = sp.call("GET", f"/playlists/{DAILY_ID}")
        last_seen = html.unescape((verified or {}).get("description") or "")
        if last_seen == description:
            return
        if attempt < 4:
            time.sleep(1.0)
    raise manager.ManagerError(
        "Spotify accepted the Tricky Daily description update but read-back "
        f"did not confirm it after retries (last value: {last_seen!r})."
    )


def configure():
    manager.CID = os.environ["SPOTIFY_CLIENT_ID"]
    manager.TOKEN = Path(".spotify_playlist_token.json")
    manager.CONFIG = Path(".github/spotify_playlist_manager_state.json")
    manager.AUDIT = Path(".github/spotify_playlist_manager_audit.jsonl")
    manager.BACKUPS = Path("playlist_backups")
    if os.environ.get("SHIT_AUTH_MODE", "").strip().lower() != "broker":
        manager.write(manager.TOKEN, {
            "refresh_token": os.environ["SPOTIFY_REFRESH_TOKEN"],
            "obtained_at": 0,
            "expires_in": 0,
        })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Allow a manually dispatched run outside midnight.")
    parser.add_argument("--description-only", action="store_true", help="Rotate and verify only the Tricky Daily description; leave tracks untouched.")
    parser.add_argument("--verify-only", action="store_true", help="Verify the live Daily playlist without changing tracks or description.")
    parser.add_argument("--stage-only", action="store_true", help="Build and durably verify a Daily payload without changing Spotify.")
    args = parser.parse_args()
    if args.stage_only and (args.description_only or args.verify_only):
        raise manager.ManagerError("--stage-only cannot be combined with --description-only or --verify-only.")
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
    if not (args.description_only or args.verify_only) and cycle_already_completed(config, cycle_date):
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

    if args.description_only:
        next_description = choose_daily_description(cycle_date, playlist.get("description", ""))
        update_description_and_verify(sp, next_description)
        config = manager.config()
        daily_state = config.setdefault("daily_cycle", {})
        daily_state.update({
            "playlist_id": DAILY_ID,
            "description": next_description,
            "last_description_date_eastern": cycle_date,
            "description_status": "accepted_pending_verification",
        })
        manager.write(manager.CONFIG, config)
        set_action_output("description_updated", "true")
        manager.audit(
            event="daily_description_update_accepted",
            playlist_id=DAILY_ID,
            cycle_date_eastern=cycle_date,
            description=next_description,
        )
        config = manager.config()
        config.setdefault("daily_cycle", {}).update({
            "description": next_description,
            "last_description_date_eastern": cycle_date,
            "description_status": "completed",
        })
        manager.write(manager.CONFIG, config)
        manager.audit(
            event="daily_description_update_completed",
            playlist_id=DAILY_ID,
            cycle_date_eastern=cycle_date,
            description=next_description,
        )
        print(f"Tricky Daily description updated and verified: {next_description}")
        return 0

    if args.verify_only:
        snapshot = manager.snapshot(sp, playlist)
        items = snapshot["items"]
        uris = [row.get("uri") for row in items]
        if len(items) != DAILY_TARGET_SIZE:
            raise manager.ManagerError(
                f"Live Tricky Daily has {len(items)} tracks; expected exactly {DAILY_TARGET_SIZE}."
            )
        if len(set(uris)) != len(uris):
            raise manager.ManagerError("Live Tricky Daily contains duplicate track URIs.")
        feedback = discovery.load_playlist_feedback([], DAILY_ID)
        blocked = [
            row for row in items
            if discovery.is_playlist_candidate_blocked(
                (row.get("artists") or [""])[0],
                row.get("name") or row.get("track") or "",
                row.get("uri"),
                feedback,
            )
        ]
        if blocked:
            raise manager.ManagerError(
                f"Live Tricky Daily contains {len(blocked)} blacklisted tracks: "
                + ", ".join(f"{(row.get('artists') or [''])[0]} — {row.get('name') or row.get('track')}" for row in blocked[:8])
            )
        expected_description = (config.get("daily_cycle") or {}).get("description", "")
        live_description = html.unescape(playlist.get("description") or "")
        if expected_description and live_description != expected_description:
            raise manager.ManagerError(
                f"Live description mismatch: expected {expected_description!r}, got {live_description!r}."
            )
        print(
            f"Tricky Daily live verification passed: {len(items)} unique tracks; "
            f"0 blacklisted; description={live_description!r}; "
            f"snapshot_id={playlist.get('snapshot_id')}"
        )
        return 0

    # Re-read immediately before planning/mutation in case state changed after
    # startup. The workflow concurrency group also serializes cycle executions.
    config = manager.config()
    if cycle_already_completed(config, cycle_date):
        print(f"Tricky Daily already cycled for {cycle_date} Eastern; skipping duplicate run.")
        set_action_output("cycled", "false")
        return 0
    assert_no_pending_daily_stage(cycle_date)

    before = manager.snapshot(sp, playlist)
    before_uris = [row.get("uri") for row in before.get("items", [])]
    previous_cycle_marker = (config.get("daily_cycle") or {}).get("last_cycle_at")
    removal_sync = discovery.reconcile_daily_manual_removals(before["items"], previous_cycle_marker)
    manager.audit(event="daily_manual_removals_reconciled", playlist_id=DAILY_ID, cycle_date_eastern=cycle_date, **removal_sync)
    trend_report = listening_trends.generate()
    manager.audit(
        event="daily_listening_trends_generated", playlist_id=DAILY_ID,
        coverage=trend_report.get("coverage", {}),
        top_genres=[row.get("tag") for row in trend_report.get("genres", [])[:8]],
    )
    recommendations, skipped = discovery.build_discovery_recommendations(
        sp, before["items"], today=local_now.date(), playlist_id=DAILY_ID,
        target_size=DAILY_TARGET_SIZE,
    )
    if len(recommendations) != DAILY_TARGET_SIZE:
        raise manager.ManagerError(
            f"Daily discovery returned {len(recommendations)} tracks; exactly "
            f"{DAILY_TARGET_SIZE} are required. Playlist left unchanged."
        )
    artist_keys = [discovery.norm(row.get("artist")) for row in recommendations]
    artist_counts = {artist: artist_keys.count(artist) for artist in set(artist_keys)}
    if any(not artist for artist in artist_keys):
        raise manager.ManagerError(
            "Daily discovery returned a track without a valid primary artist. "
            "Playlist left unchanged."
        )
    if len(recommendations) != DAILY_TARGET_SIZE:
        raise manager.ManagerError("Daily discovery did not return exactly 60 tracks. Playlist left unchanged.")
    if any(row.get("artist_diversity_fallback") for row in recommendations):
        manager.audit(
            event="daily_artist_diversity_fallback_used",
            playlist_id=DAILY_ID,
            cycle_date_eastern=cycle_date,
            distinct_primary_artists=len(artist_counts),
            repeated_artist_tracks=sum(count - 1 for count in artist_counts.values() if count > 1),
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
        liked_baseline = daily_feedback.query_liked_status(sp, uris)
    except Exception as error:
        manager.audit(
            event="daily_liked_baseline_unavailable",
            error_type=type(error).__name__,
            error=str(error),
        )

    backup = manager.save_snapshot(before)
    # Re-read the exact ordered live playlist immediately before mutation. A
    # user edit during discovery must never be overwritten by a stale candidate run.
    playlist, _ = assert_live_snapshot_unchanged(sp, before, me.get("id"))
    fresh_feedback = discovery.load_playlist_feedback([], DAILY_ID)
    newly_blocked = [
        row for row in recommendations
        if discovery.is_playlist_candidate_blocked(
            row.get("artist") or "",
            row.get("track") or "",
            row.get("uri"),
            fresh_feedback,
        )
    ]
    if newly_blocked:
        raise manager.ManagerError(
            f"Daily candidates now include {len(newly_blocked)} blacklisted tracks; "
            "aborting before playlist mutation."
        )
    next_description = choose_daily_description(cycle_date, playlist.get("description", ""))
    stage_path, payload_sha256, stage_commit_sha = create_daily_stage(
        cycle_date, before, before_uris, recommendations, uris, backup, next_description,
        test_mode=args.stage_only,
    )
    # The durable stage commit can take time; verify main did not advance
    # (for example, a concurrent lock change) and recheck the live playlist.
    assert_repository_head_unchanged(stage_commit_sha)
    playlist, _ = assert_live_snapshot_unchanged(sp, before, me.get("id"))
    fresh_feedback = discovery.load_playlist_feedback([], DAILY_ID)
    newly_blocked = [
        row for row in recommendations
        if discovery.is_playlist_candidate_blocked(
            row.get("artist") or "", row.get("track") or "", row.get("uri"), fresh_feedback
        )
    ]
    if newly_blocked:
        raise manager.ManagerError(
            f"Daily candidates now include {len(newly_blocked)} blacklisted tracks "
            "after durable staging; aborting before playlist mutation."
        )
    if args.stage_only:
        print(
            "Tricky Daily stage-only verification succeeded; "
            f"stage={stage_path}, payload_sha256={payload_sha256}, "
            f"stage_commit={stage_commit_sha or 'local-only'}. No Spotify playlist write was attempted."
        )
        set_action_output("cycled", "false")
        return 0

    manager.audit(
        event="daily_cycle_started", playlist_id=DAILY_ID, cycle_date_eastern=cycle_date,
        recommendation_count=len(recommendations), skipped_count=len(skipped), backup=backup,
        prewrite_snapshot_id=playlist.get("snapshot_id"),
        stage_path=stage_path,
        payload_sha256=payload_sha256,
    )
    try:
        cloud.replace_playlist(sp, DAILY_ID, uris, expected_before_uris=before_uris)
    except cloud.AmbiguousPlaylistMutationError as error:
        # Persist the date guard even when the write outcome cannot be proven.
        # A second scheduled/forced delivery must not blindly repeat a partial write.
        config["daily_cycle"] = {
            "last_cycle_date_eastern": cycle_date,
            "last_cycle_at": manager.stamp(),
            "playlist_id": DAILY_ID,
            "description": html.unescape(playlist.get("description") or ""),
            "status": "replacement_outcome_ambiguous",
            "stage_path": stage_path,
            "payload_sha256": payload_sha256,
        }
        manager.write(manager.CONFIG, config)
        set_action_output("cycled", "true")
        manager.audit(
            event="daily_cycle_replacement_outcome_ambiguous",
            playlist_id=DAILY_ID,
            cycle_date_eastern=cycle_date,
            backup=backup,
            error=str(error),
        )
        raise

    # Rotate Daily's short editorial description after the track replacement.
    # The description was fixed in the immutable pre-write stage.

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
        "stage_path": stage_path,
        "payload_sha256": payload_sha256,
    }
    manager.write(manager.CONFIG, config)
    # Publish immediately after the durable local guard; preserve state if later verification fails.
    set_action_output("cycled", "true")
    discovery.write_daily_removal_baseline(
        [{"uri": row.get("uri"), "track": row.get("track"), "artist": row.get("artist")} for row in recommendations],
        config["daily_cycle"]["last_cycle_at"],
    )
    update_description_and_verify(sp, next_description)
    manager.audit(
        event="daily_cycle_replacement_accepted",
        playlist_id=DAILY_ID,
        cycle_date_eastern=cycle_date,
        backup=backup,
    )

    updated = sp.call("GET", f"/playlists/{DAILY_ID}")
    if html.unescape(updated.get("description") or "") != next_description:
        raise manager.ManagerError(
            "Tricky Daily tracks were replaced, but Spotify read-back did not confirm "
            "the new playlist description; cycle remains pending verification."
        )
    updated_snapshot = manager.snapshot(sp, updated)
    verified_items = updated_snapshot["items"]
    try:
        verified_artists = validate_daily_post_write(
            updated, updated_snapshot, uris, fresh_feedback
        )
    except manager.ManagerError as error:
        manager.audit(
            event="daily_post_change_validation_failed",
            playlist_id=DAILY_ID,
            cycle_date_eastern=cycle_date,
            observed_track_count=len(verified_items),
            expected_track_count=DAILY_TARGET_SIZE,
            validation_error=str(error),
            expected_uris=uris,
            observed_uris=[row.get("uri") for row in verified_items],
        )
        raise manager.ManagerError(
            f"{error} Cycle remains pending verification; do not retry blindly."
        )
    verified_artist_counts = {artist: verified_artists.count(artist) for artist in set(verified_artists)}
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
        "stage_path": stage_path,
        "payload_sha256": payload_sha256,
    }
    manager.write(manager.CONFIG, config)
    discovery.write_daily_removal_baseline(updated_snapshot["items"], config["daily_cycle"]["last_cycle_at"])

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
        manager.audit(event="daily_liked_song_observation_failed", error_type=type(error).__name__, error=str(error))
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
# Purpose: Rotate Tricky Daily to exactly 60 tracks once per Eastern calendar day.
# Candidates: Seek one track per primary artist; after alternate search-page retries, relax
#             the artist cap from two only as needed to reach 60 unique URIs; audit fallback.
# Schedule: UTC cron 04:00/04:15 and 05:00/05:15; ZoneInfo selects Eastern midnight.
# Safety: Exact playlist identity/owner, managed policy, explicit unlock, URI/deduplication,
#         pre-change backup and 60-track read-back. Same-Eastern-date idempotency guard
#         remains active even when --force bypasses the clock-window gate.
# Feedback: Rotation removals are neutral curator_rotation events, never negative preference.
# Dispatch: --force bypasses only the clock window; --description-only and --verify-only
#           are separate actions.
# Recovery: Workflow uploads the pre-change backup and links it in manager state.
# -----------------------------------------------------------------------------
