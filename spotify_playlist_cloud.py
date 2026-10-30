#!/usr/bin/env python3
"""Owner-verified GitHub issue command handler for Spotify playlist control."""
import json
import os
import secrets
import sys
from pathlib import Path

import spotify_playlist_manager as manager

STATE = Path(".github/spotify_playlist_manager_state.json")
OWNER = "TrickySturluson"
CONTROL_ISSUE_TITLE = "Spotify Playlist Manager Control"


def fail(message):
    print(message, file=sys.stderr)
    raise SystemExit(1)


def owned_playlist(sp, pid, me):
    p = next((x for x in sp.playlists() if x.get("id") == pid), None)
    if p is None or (p.get("owner") or {}).get("id") != me.get("id"):
        fail("Rejected: playlist not found or not owned by this account.")
    return p


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
        "lock_all": {"command"},
        "lock": {"command", "playlist_id"},
        "unlock": {"command", "playlist_id"},
        "preview": {"command", "playlist_id", "operations"},
        "confirm": {"command", "confirmation"},
        "undo": {"command"},
    }
    if action not in allowed or set(command) != allowed[action]:
        fail("Rejected: invalid command or fields.")
    if action in {"lock", "unlock", "preview"} and not isinstance(command.get("playlist_id"), str):
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
    elif action == "preview":
        pid, operations = manager.validate({
            "playlist_id": command["playlist_id"], "operations": command["operations"]
        })
        p = owned_playlist(sp, pid, me)
        if not manager.unlocked(pid):
            fail("Blocked: playlist is LOCKED. Unlock it explicitly before previewing edits.")
        confirmation = secrets.token_urlsafe(12)
        config["pending"] = {
            "playlist_id": pid,
            "operations": operations,
            "snapshot_id": p.get("snapshot_id"),
            "confirmation": confirmation,
        }
        manager.write(STATE, config)
        manager.audit(event="change_previewed", playlist_id=pid, operations=operations)
        lines = [f'PREVIEW — {p.get("name")} [{pid}]', "No playlist changes have been made."]
        for op in operations:
            if op["action"] in {"add", "remove", "replace"}:
                lines.append(f'{op["action"].upper()}: {len(op["uris"])} track URI(s)')
                lines.extend("  " + uri for uri in op["uris"])
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
    elif action == "undo":
        last = config.get("last_completed") or {}
        if not last:
            fail("Nothing to undo: no completed change has a recovery snapshot.")
        pid = last.get("playlist_id")
        if not manager.unlocked(pid):
            fail("Blocked: playlist is LOCKED. Unlock it explicitly before undo.")
        p = owned_playlist(sp, pid, me)
        if p.get("snapshot_id") != last.get("after_snapshot_id"):
            fail("Undo refused: the playlist changed after the saved operation.")
        backup_path = Path(last.get("backup", ""))
        if not backup_path.is_file():
            fail("Recovery snapshot is unavailable. Check the original workflow artifact.")
        backup_data = manager.read(backup_path, None)
        if not isinstance(backup_data, dict) or (backup_data.get("playlist") or {}).get("id") != pid:
            fail("Recovery snapshot is invalid or belongs to another playlist.")
        restore_uris = [item.get("uri") for item in backup_data.get("items", [])]
        if any(not isinstance(uri, str) or not uri.startswith(("spotify:track:", "spotify:episode:")) for uri in restore_uris):
            fail("Undo refused: the snapshot contains unavailable or unsupported playlist items.")
        confirmation = secrets.token_urlsafe(12)
        config["pending"] = {
            "kind": "undo", "playlist_id": pid, "snapshot_id": p.get("snapshot_id"),
            "backup": str(backup_path), "confirmation": confirmation,
            "restore_count": len(restore_uris),
        }
        manager.write(STATE, config)
        manager.audit(event="undo_previewed", playlist_id=pid, restore_count=len(restore_uris), backup=str(backup_path))
        result = (
            f'UNDO PREVIEW — {p.get("name")} [{pid}]\n'
            f'Current items: {(p.get("items") or p.get("tracks") or {}).get("total", "?")}\n'
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
        if p.get("snapshot_id") != pending.get("snapshot_id"):
            config.pop("pending", None)
            manager.write(STATE, config)
            fail("Playlist changed after preview. Preview it again before confirming.")
        before = manager.snapshot(sp, p)
        backup = manager.save_snapshot(before)
        kind = pending.get("kind", "edit")
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
        if kind == "undo":
            restore_data = manager.read(pending["backup"], None)
            replace_playlist(sp, pid, [item["uri"] for item in restore_data["items"]])
        else:
            execute(sp, pid, pending["operations"])
        updated = owned_playlist(sp, pid, me)
        config["last_completed"] = {
            "playlist_id": pid, "backup": backup,
            "backup_run_id": os.environ.get("GITHUB_RUN_ID", ""),
            "after_snapshot_id": updated.get("snapshot_id"),
            "kind": "undo" if kind == "undo" else "edit",
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

    print(result)
    import uuid
    delimiter = "RESULT_" + uuid.uuid4().hex
    Path(os.environ["GITHUB_OUTPUT"]).write_text(
        f"result<<{delimiter}\n{result}\n{delimiter}\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
