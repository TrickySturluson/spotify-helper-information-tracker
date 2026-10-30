#!/usr/bin/env python3
"""Owner-verified GitHub issue command handler for Spotify playlist control."""
import json
import os
import secrets
import sys
import urllib.error
from pathlib import Path

import spotify_playlist_manager as manager

STATE = Path(".github/spotify_playlist_manager_state.json")
OWNER = "TrickySturluson"
CONTROL_ISSUE_TITLE = "Spotify Playlist Manager Control"

DAILY_DESCRIPTIONS = [
    "Could be worse. Could be quiet.",
    "At least the music's good.",
    "Well, something here has decent taste.",
    "Familiar names. Unexpected detours",
    "Not too many hits yesterday, that was then this is an improvement.",
    "The skip button is there for a reason. Hope you don't need it.",
    "The playlist's doing the heavy lifting... again.",
    "I've made a few adjustments. You're welcome.",
    "Today's queue has considerably better judgment.",
    "A little less filler... maybe..",
    "Good music doesn't find itself, try not to miss it.",
    "Trust the queue. It's got a better track record.",
    "Some things are better left on repeat.",
    "A little distortion never hurt anybody.",
    "Nothing groundbreaking. Just breaking the silence.",
    "No encore necessary. I'll be here all day.",
    "Your daily dose of questionable taste.",
    "Today's queue. Don't say I never do anything for you.",
]


def fail(message):
    print(message, file=sys.stderr)
    raise SystemExit(1)


def owned_playlist(sp, pid, me):
    # Do not use /me/playlists for mutation checks: Spotify may return a stale
    # snapshot_id in that collection response after a playlist write. Fetch the
    # playlist resource directly so preview/confirm/undo compare the live version.
    try:
        p = sp.call("GET", f"/playlists/{pid}")
    except manager.ManagerError:
        fail("Rejected: playlist not found or not accessible by this account.")
    if not isinstance(p, dict) or p.get("id") != pid or (p.get("owner") or {}).get("id") != me.get("id"):
        fail("Rejected: playlist not found or not owned by this account.")
    return p


def snapshot_uris(snapshot):
    return [item.get("uri") for item in snapshot.get("items", [])]


def pending_state_matches(playlist, pending, current_snapshot=None):
    # Playlist edits and undo both operate on ordered items. Compare the exact
    # ordered URI list captured at preview instead of Spotify's unreliable
    # snapshot_id across separate workflow runners. Legacy pending previews
    # without expected_uris retain their original snapshot check.
    if "expected_uris" in pending:
        return (
            current_snapshot is not None
            and snapshot_uris(current_snapshot) == pending.get("expected_uris")
        )
    return playlist.get("snapshot_id") == pending.get("snapshot_id")


def completed_state_matches(playlist, completed, current_snapshot):
    # Validate the live playlist against the exact ordered contents recorded
    # immediately after the completed edit. Keep snapshot_id as a legacy fallback.
    if "after_uris" in completed:
        return snapshot_uris(current_snapshot) == completed.get("after_uris")
    return playlist.get("snapshot_id") == completed.get("after_snapshot_id")


def replace_playlist(sp, pid, uris):
    # Replace the first page, then append in order; duplicate URIs are preserved.
    if not manager.unlocked(pid):
        raise manager.ManagerError("Playlist is LOCKED; undo was stopped before restoration.")
    first = uris[:100]
    if first:
        sp.call("PUT", f"/playlists/{pid}/items", {"uris": first})
        for offset in range(100, len(uris), 100):
            if not manager.unlocked(pid):
                raise manager.ManagerError("Playlist locked during undo; remaining restoration stopped.")
            sp.call("POST", f"/playlists/{pid}/items", {"uris": uris[offset:offset + 100]})
    else:
        current = [item.get("uri") for item in manager.tracks(sp, manager.find(sp, pid)) if item.get("uri")]
        if current:
            manager.remove(sp, pid, current)


def execute(sp, pid, operations):
    for op in operations:
        if not manager.unlocked(pid):
            raise manager.ManagerError("Playlist locked during execution; remaining changes stopped.")
        action = op["action"]
        if action == "add":
            manager.add(sp, pid, op["uris"])
        elif action == "remove":
            manager.remove(sp, pid, op["uris"])
        elif action == "replace":
            current = [x["uri"] for x in manager.tracks(sp, manager.find(sp, pid)) if x.get("uri")]
            if current:
                manager.remove(sp, pid, current)
            manager.add(sp, pid, op["uris"])
        elif action == "reorder":
            current = manager.find(sp, pid)
            sp.call("PUT", f"/playlists/{pid}/items", {
                "range_start": op["range_start"],
                "insert_before": op["insert_before"],
                "range_length": op["range_length"],
                "snapshot_id": current.get("snapshot_id"),
            })
        elif action == "details":
            sp.call("PUT", f"/playlists/{pid}", {
                "name": op["name"],
                "description": op["description"],
            })


def main():
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    issue = event.get("issue") or {}
    sender = (event.get("sender") or {}).get("login", "")
    if sender.casefold() != OWNER.casefold():
        fail("Rejected: command sender is not the repository owner.")
    if issue.get("title") != CONTROL_ISSUE_TITLE or issue.get("state") != "open":
        fail("Rejected: this is not the active control issue.")

    try:
        command = json.loads(issue.get("body") or "")
    except json.JSONDecodeError:
        fail("Command body must be a JSON object.")
    if not isinstance(command, dict):
        fail("Rejected: command must be a JSON object.")
    action = command.get("command")
    allowed = {
        "status": {"command"},
        "inspect": {"command", "playlist_id"},
        "lock_all": {"command"},
        "lock": {"command", "playlist_id"},
        "unlock": {"command", "playlist_id"},
        "preview": {"command", "playlist_id", "operations"},
        "daily_preview": {"command", "playlist_id"},
        "confirm": {"command", "confirmation"},
        "undo": {"command"},
    }
    if action not in allowed or set(command) != allowed[action]:
        fail("Rejected: invalid command or fields.")
    if action in {"lock", "unlock", "preview", "daily_preview", "inspect"} and not isinstance(command.get("playlist_id"), str):
        fail("Rejected: a playlist_id is required.")
    if action == "confirm" and not isinstance(command.get("confirmation"), str):
        fail("Rejected: confirmation code is required.")

    manager.CID = os.environ["SPOTIFY_CLIENT_ID"]
    manager.TOKEN = Path(".spotify_playlist_token.json")
    manager.CONFIG = STATE
    manager.AUDIT = Path(".github/spotify_playlist_manager_audit.jsonl")
    manager.BACKUPS = Path("playlist_backups")
    manager.write(manager.TOKEN, {
        "refresh_token": os.environ["SPOTIFY_REFRESH_TOKEN"],
        "obtained_at": 0,
        "expires_in": 0,
    })
    sp = manager.Spotify()
    config = manager.config()
    manager.write(STATE, config)
    playlists = sp.playlists()
    me = sp.me()
    owned = [p for p in playlists if (p.get("owner") or {}).get("id") == me.get("id")]
    result = ""

    if action == "lock_all":
        for p in owned:
            config["playlists"][p["id"]] = {
                "name": p.get("name", ""), "state": "locked", "updated_at": manager.stamp()
            }
        config.pop("pending", None)
        manager.write(STATE, config)
        manager.audit(event="lock_all", count=len(owned))
        result = f"Locked all {len(owned)} playlists owned by this account."
    elif action in {"lock", "unlock"}:
        p = owned_playlist(sp, command["playlist_id"], me)
        state = "locked" if action == "lock" else "unlocked"
        config["playlists"][p["id"]] = {
            "name": p.get("name", ""), "state": state, "updated_at": manager.stamp()
        }
        if state == "locked" and (config.get("pending") or {}).get("playlist_id") == p["id"]:
            config.pop("pending", None)
        manager.write(STATE, config)
        manager.audit(event="permission_changed", playlist_id=p["id"], name=p.get("name"), state=state)
        result = f'{p.get("name")} is now {state.upper()}.'
    elif action == "inspect":
        pid = command["playlist_id"]
        p = owned_playlist(sp, pid, me)
        current = manager.snapshot(sp, p)
        lines = [f'PLAYLIST INSPECTION — {p.get("name")} [{pid}]', f'Items: {len(current["items"])}', "Read-only; no playlist changes have been made.", ""]
        for index, item in enumerate(current["items"], 1):
            artists = ", ".join(item.get("artists") or [])
            lines.append(f'{index:02d}. {artists} — {item.get("name")} [{item.get("uri")}]')
        result = "\\n".join(lines)
    elif action == "preview":
        pid, operations = manager.validate({
            "playlist_id": command["playlist_id"], "operations": command["operations"]
        })
        p = owned_playlist(sp, pid, me)
        if not manager.unlocked(pid):
            fail("Blocked: playlist is LOCKED. Unlock it explicitly before previewing edits.")
        preview_snapshot = manager.snapshot(sp, p)
        confirmation = secrets.token_urlsafe(12)
        config["pending"] = {
            "playlist_id": pid,
            "operations": operations,
            "snapshot_id": p.get("snapshot_id"),
            "expected_uris": snapshot_uris(preview_snapshot),
            "confirmation": confirmation,
        }
        manager.write(STATE, config)
        manager.audit(event="change_previewed", playlist_id=pid, operations=operations)
        lines = [f'PREVIEW — {p.get("name")} [{pid}]', "No playlist changes have been made."]
        for op in operations:
            if op["action"] in {"add", "remove", "replace"}:
                lines.append(f'{op["action"].upper()}: {len(op["uris"])} track URI(s)')
                lines.extend("  " + uri for uri in op["uris"])
            elif op["action"] == "details":
                lines.append(f'UPDATE DETAILS: name={op["name"]!r}; description={op["description"]!r}')
            else:
                lines.append(
                    f'REORDER: start {op["range_start"]}, before {op["insert_before"]}, '
                    f'length {op["range_length"]}'
                )
        lines.extend([
            "",
            "To execute this exact preview, submit a confirm command with this code:",
            confirmation,
            "The playlist must remain unlocked and unchanged until confirmation.",
        ])
        result = "\n".join(lines)
    elif action == "daily_preview":
        import spotify_discovery as daily
        pid = command["playlist_id"]
        p = owned_playlist(sp, pid, me)
        if p.get("name", "").strip().casefold() != "tricky daily":
            fail("Blocked: daily_preview is restricted to the playlist named Tricky Daily.")
        if not manager.unlocked(pid):
            fail("Blocked: Tricky Daily is LOCKED. Unlock it explicitly before requesting a daily preview.")
        current = manager.snapshot(sp, p)
        recommendations, skipped = daily.build_discovery_recommendations(sp, current["items"])
        uris = [row["uri"] for row in recommendations]
        operations = [{"action": "replace", "uris": uris}]
        confirmation = secrets.token_urlsafe(12)
        config["pending"] = {
            "playlist_id": pid, "operations": operations,
            "snapshot_id": p.get("snapshot_id"), "expected_uris": snapshot_uris(current),
            "confirmation": confirmation, "recommendation_date": manager.stamp(), "kind": "daily",
        }
        manager.write(STATE, config)
        manager.audit(event="daily_recommendations_previewed", playlist_id=pid, recommendation_count=len(recommendations), skipped_count=len(skipped))
        tier_counts = {tier: sum(1 for row in recommendations if row.get("tier") == tier) for tier in ("discovery", "rediscovery", "familiar")}
        liked_count = sum(1 for row in recommendations if row.get("liked"))
        lines = [
            f'DAILY DISCOVERY PREVIEW — {p.get("name")} [{pid}]',
            f'Recommended tracks: {len(recommendations)}; current items: {len(current["items"])}',
            f'Mix: {tier_counts["discovery"]} unheard tracks, {tier_counts["rediscovery"]} lightly heard tracks, {tier_counts["familiar"]} familiar tracks.',
            f'{liked_count} already-Liked track(s) survived a strong ranking penalty; prior scrobbles were penalized by frequency and recency, never hard-excluded.',
            "Candidates come from similar artists outside the scrobble archive, resolved against Spotify; max two tracks per artist.",
            "No playlist changes have been made.",
            "",
        ]
        for index, row in enumerate(recommendations, 1):
            familiarity = "already Liked" if row.get("liked") else ("unheard" if not row.get("plays") else f'{row.get("plays")} archive plays')
            popularity = row.get("popularity")
            popularity_label = f"Spotify popularity {popularity}" if isinstance(popularity, (int, float)) else "Spotify popularity unavailable from API"
            lines.append(f'{index:02d}. {row["artist"]} — {row["track"]} [{row.get("tier", "discovery").upper()}; {familiarity}; similarity {row.get("similarity", 0):.2f}; {popularity_label}]')
        lines.extend(["", f'Skipped {len(skipped)} candidates already present in Tricky Daily or without a usable Spotify match.', "To replace Tricky Daily with this exact set, submit confirm with this one-time code:", confirmation, "The playlist must remain unlocked and unchanged until confirmation."])
        result = "\n".join(lines)
    elif action == "undo":
        last = config.get("last_completed") or {}
        if not last:
            fail("Nothing to undo: no completed change has a recovery snapshot.")
        pid = last.get("playlist_id")
        if not manager.unlocked(pid):
            fail("Blocked: playlist is LOCKED. Unlock it explicitly before undo.")
        p = owned_playlist(sp, pid, me)
        current_snapshot = manager.snapshot(sp, p)
        if not completed_state_matches(p, last, current_snapshot):
            fail("Undo refused: playlist contents changed after the saved operation.")
        backup_path = Path(last.get("backup", ""))
        if not backup_path.is_file():
            fail("Recovery snapshot is unavailable. Check the original workflow artifact.")
        backup_data = manager.read(backup_path, None)
        if not isinstance(backup_data, dict) or (backup_data.get("playlist") or {}).get("id") != pid:
            fail("Recovery snapshot is invalid or belongs to another playlist.")
        restore_uris = [item.get("uri") for item in backup_data.get("items", [])]
        current_snapshot = manager.snapshot(sp, p)
        if any(not isinstance(uri, str) or not uri.startswith(("spotify:track:", "spotify:episode:")) for uri in restore_uris):
            fail("Undo refused: the snapshot contains unavailable or unsupported playlist items.")
        confirmation = secrets.token_urlsafe(12)
        config["pending"] = {
            "kind": "undo", "playlist_id": pid, "snapshot_id": p.get("snapshot_id"),
            "backup": str(backup_path), "confirmation": confirmation,
            "restore_count": len(restore_uris),
            "expected_uris": snapshot_uris(current_snapshot),
        }
        manager.write(STATE, config)
        manager.audit(event="undo_previewed", playlist_id=pid, restore_count=len(restore_uris), backup=str(backup_path))
        result = (
            f'UNDO PREVIEW — {p.get("name")} [{pid}]\n'
            f'Current items: {len(current_snapshot["items"])}\n'
            f'Restore previous snapshot: {len(restore_uris)} item(s), in original order.\n'
            "No changes have been made.\n\n"
            f'To restore this snapshot, submit confirm with this one-time code: {confirmation}'
        )
    elif action == "confirm":
        pending = config.get("pending") or {};
        if not pending or not secrets.compare_digest(
            command["confirmation"], pending.get("confirmation", "")
        ):
            fail("Rejected: no matching pending preview. Run preview again.")
        pid = pending["playlist_id"]
        if not manager.unlocked(pid):
            fail("Blocked: playlist is LOCKED; preview cancelled.")
        p = owned_playlist(sp, pid, me)
        kind = pending.get("kind", "edit")
        before = manager.snapshot(sp, p)
        if not pending_state_matches(p, pending, before):
            config.pop("pending", None)
            manager.write(STATE, config)
            message = (
                "Playlist contents changed after undo preview. Run undo again to review the latest state."
                if kind == "undo"
                else "Playlist changed after preview. Preview it again before confirming."
            )
            fail(message)
        backup = manager.save_snapshot(before)
        if kind == "undo":
            manager.audit(event="undo_started", playlist_id=pid, redo_snapshot=backup, recovery_snapshot=pending["backup"])
        else:
            manager.audit(
                event="change_started", playlist_id=pid, name=p.get("name"),
                operations=pending["operations"], backup=backup, user_id=me.get("id")
            )
        # Consume the one-time confirmation before the first write.
        config.pop("pending", None)
        manager.write(STATE, config)
        manager.audit(event="confirmation_consumed", playlist_id=pid, backup=backup, kind=kind)
        try:
            if kind == "undo":
                restore_data = manager.read(Path(pending["backup"]), None)
                if (
                    not isinstance(restore_data, dict)
                    or not isinstance(restore_data.get("items"), list)
                ):
                    raise manager.ManagerError(
                        "Recovery snapshot is unavailable in this workflow run; undo was stopped before restoration."
                    )
                replace_playlist(sp, pid, [item["uri"] for item in restore_data["items"]])
            else:
                execute(sp, pid, pending["operations"])
                if kind == "daily":
                    current_description = p.get("description") or ""
                    choices = [line for line in DAILY_DESCRIPTIONS if line != current_description]
                    if not choices:
                        raise manager.ManagerError("No alternate Tricky Daily description is available.")
                    new_description = secrets.choice(choices)
                    sp.call("PUT", f"/playlists/{pid}", {"description": new_description})
                    manager.audit(
                        event="daily_description_updated",
                        playlist_id=pid,
                        description=new_description,
                    )
            updated = owned_playlist(sp, pid, me)
        except Exception as operation_error:
            # A multi-request edit can fail after Spotify has accepted some writes.
            # Preserve an undo pointer to the pre-change snapshot even on partial failure.
            try:
                interrupted = owned_playlist(sp, pid, me)
                interrupted_snapshot = manager.snapshot(sp, interrupted)
                config["last_completed"] = {
                    "playlist_id": pid,
                    "backup": backup,
                    "backup_run_id": os.environ.get("GITHUB_RUN_ID", ""),
                    "after_snapshot_id": interrupted.get("snapshot_id"),
                    "after_uris": snapshot_uris(interrupted_snapshot),
                    "kind": "partial",
                }
                manager.write(STATE, config)
                manager.audit(
                    event="change_interrupted",
                    playlist_id=pid,
                    backup=backup,
                    kind=kind,
                    error_type=type(operation_error).__name__,
                )
            except Exception as recovery_error:
                manager.audit(
                    event="recovery_state_capture_failed",
                    playlist_id=pid,
                    backup=backup,
                    error_type=type(recovery_error).__name__,
                )
            raise
        updated_snapshot = manager.snapshot(sp, updated)
        config["last_completed"] = {
            "playlist_id": pid, "backup": backup,
            "backup_run_id": os.environ.get("GITHUB_RUN_ID", ""),
            "after_snapshot_id": updated.get("snapshot_id"),
            "after_uris": snapshot_uris(updated_snapshot),
            "kind": kind,
        }
        manager.write(STATE, config)
        manager.audit(event="change_completed", playlist_id=pid, backup=backup, kind=kind)
        count = (updated.get("items") or updated.get("tracks") or {}).get("total", "?")
        verb = "Restored the previous snapshot of" if kind == "undo" else "Completed the confirmed changes to"
        result = (
            f'{verb} "{updated.get("name")}". '
            f"Current status: {count} items; UNLOCKED. "
            "A pre-change recovery snapshot was saved as a workflow artifact."
        )
    else:
        manager.audit(event="status_requested")
        result = "Playlist status:"

    if action in {"status", "lock_all", "lock", "unlock"}:
        lines = [result, "", "| Playlist | Items | Lock | ID |", "|---|---:|---|---|"]
        for p in playlists:
            pid = p["id"]
            is_owned = (p.get("owner") or {}).get("id") == me.get("id")
            state = config["playlists"].get(pid, {}).get("state", "locked") if is_owned else "locked (not owned)"
            count = (p.get("items") or p.get("tracks") or {}).get("total", "?")
            safe_name = str(p.get("name", "")).replace("|", "\\|").replace("\n", " ")
            lines.append("| " + safe_name + " | " + str(count) + " | " + state.upper() + " | `" + pid + "` |")
        result = "\n".join(lines)

    if getattr(sp, "refresh_token_rotated", False):
        result += (
            "\\n\\nWARNING: Spotify issued a replacement refresh token during this run. "
            "The temporary runner cannot update the repository secret. Before the next command, "
            "reauthorize the playlist manager locally and replace SPOTIFY_REFRESH_TOKEN in "
            "GitHub Actions Secrets."
        )

    print(result)
    import uuid
    delimiter = "RESULT_" + uuid.uuid4().hex
    Path(os.environ["GITHUB_OUTPUT"]).write_text(
        f"result<<{delimiter}\n{result}\n{delimiter}\n", encoding="utf-8"
    )


if __name__ == "__main__":
    try:
        main()
    except (manager.ManagerError, OSError, KeyError, ValueError, urllib.error.URLError) as error:
        print("ERROR:", error, file=sys.stderr)
        raise SystemExit(1)
