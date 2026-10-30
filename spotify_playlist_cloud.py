#!/usr/bin/env python3
"""GitHub Actions command handler for the Spotify playlist manager.

The issue body is a strict JSON command envelope. Only the repository owner may
invoke it; playlist names/IDs/counts/lock states are returned, never tracklists.
"""
import json
import os
import sys
from pathlib import Path

import spotify_playlist_manager as manager

STATE = Path(".github/spotify_playlist_manager_state.json")
OWNER = "TrickySturluson"
CONTROL_ISSUE_TITLE = "Spotify Playlist Manager Control"


def fail(message):
    print(message, file=sys.stderr)
    raise SystemExit(1)


def main():
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    issue = event.get("issue") or {}
    sender = (event.get("sender") or {}).get("login", "")
    if sender.casefold() != OWNER.casefold():
        fail("Rejected: command sender is not the repository owner.")
    if issue.get("title") != CONTROL_ISSUE_TITLE or issue.get("state") != "open":
        fail("Rejected: this is not the active control issue.")

    raw = issue.get("body") or ""
    try:
        command = json.loads(raw)
    except json.JSONDecodeError:
        fail("Command body must be a JSON object. See the control issue instructions.")
    if not isinstance(command, dict) or set(command) - {"command", "playlist_id"}:
        fail("Rejected: unsupported command fields.")
    action = command.get("command")
    if action not in {"status", "lock_all", "lock", "unlock"}:
        fail("Rejected: command must be status, lock_all, lock, or unlock.")
    if action in {"lock", "unlock"} and not isinstance(command.get("playlist_id"), str):
        fail("Rejected: lock/unlock requires a playlist_id.")

    manager.CID = os.environ["SPOTIFY_CLIENT_ID"]
    manager.TOKEN = Path(".spotify_playlist_token.json")
    manager.CONFIG = STATE
    manager.AUDIT = Path(".github/spotify_playlist_manager_audit.jsonl")
    manager.BACKUPS = Path("playlist_backups")
    token = {
        "refresh_token": os.environ["SPOTIFY_REFRESH_TOKEN"],
        "obtained_at": 0,
        "expires_in": 0,
    }
    manager.write(manager.TOKEN, token)
    sp = manager.Spotify()
    config = manager.config()
    manager.write(STATE, config)
    playlists = sp.playlists()
    me = sp.me()
    owned = [p for p in playlists if (p.get("owner") or {}).get("id") == me.get("id")]

    if action == "lock_all":
        for p in owned:
            config["playlists"][p["id"]] = {
                "name": p.get("name", ""), "state": "locked", "updated_at": manager.stamp()
            }
        manager.write(STATE, config)
        manager.audit(event="lock_all", count=len(owned))
        result = f"Locked all {len(owned)} playlists owned by this account."
    elif action in {"lock", "unlock"}:
        pid = command["playlist_id"]
        p = next((p for p in owned if p.get("id") == pid), None)
        if p is None:
            fail("Rejected: playlist not found or not owned by this account.")
        state = "locked" if action == "lock" else "unlocked"
        config["playlists"][pid] = {
            "name": p.get("name", ""), "state": state, "updated_at": manager.stamp()
        }
        manager.write(STATE, config)
        manager.audit(event="permission_changed", playlist_id=pid, name=p.get("name"), state=state)
        result = f'{p.get("name")} is now {state.upper()}.'
    else:
        manager.audit(event="status_requested")
        result = "Playlist status:"
    lines = [result, "", "| Playlist | Items | Lock | ID |", "|---|---:|---|---|"]
    for p in playlists:
        pid = p["id"]
        is_owned = (p.get("owner") or {}).get("id") == me.get("id")
        state = config["playlists"].get(pid, {}).get("state", "locked") if is_owned else "locked (not owned)"
        count = (p.get("items") or p.get("tracks") or {}).get("total", "?")
        safe_name = str(p.get("name", "")).replace("|", "\\|").replace("\n", " ")
        lines.append("| " + safe_name + " | " + str(count) + " | " + state.upper() + " | `" + pid + "` |")
    output = "\n".join(lines)
    print(output)
    # The workflow posts this as an issue comment; GITHUB_TOKEN comments do not
    # trigger another issues-edited workflow run.
    import uuid
    delimiter = "RESULT_" + uuid.uuid4().hex
    Path(os.environ["GITHUB_OUTPUT"]).write_text(
        f"result<<{delimiter}\n{output}\n{delimiter}\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
