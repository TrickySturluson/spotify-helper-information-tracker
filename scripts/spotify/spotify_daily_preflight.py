#!/usr/bin/env python3
"""Read-only live preflight for the Tricky Daily automatic rotation."""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPAT = ROOT / "compat"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(COMPAT) not in sys.path:
    sys.path.insert(0, str(COMPAT))

import spotify_playlist_manager as manager

DAILY_ID = "4yUVHSMQySfWeEowfIMcx7"


def validate_live_playlist(sp):
    """Verify live Spotify identity, playlist ownership, permission and readability."""
    me = sp.me()
    playlist = sp.call("GET", f"/playlists/{DAILY_ID}")
    if not isinstance(me, dict) or not me.get("id"):
        raise manager.ManagerError("Spotify /me did not return an authenticated user ID.")
    if not isinstance(playlist, dict) or playlist.get("id") != DAILY_ID:
        raise manager.ManagerError("Spotify did not return the exact Tricky Daily playlist.")
    if (playlist.get("owner") or {}).get("id") != me["id"]:
        raise manager.ManagerError("Tricky Daily is not owned by the authenticated Spotify account.")
    if (playlist.get("name") or "").strip().casefold() != "tricky daily":
        raise manager.ManagerError("The Tricky Daily playlist name does not match the configured ID.")
    manager.assert_managed(DAILY_ID)
    if not manager.unlocked(DAILY_ID):
        raise manager.ManagerError("Tricky Daily is locked; automatic rotation is safely blocked.")
    items = sp.items(DAILY_ID)
    return {
        "status": "passed",
        "mode": "read_only_live_preflight",
        "spotify_user_id_present": True,
        "playlist_id": DAILY_ID,
        "playlist_name": playlist.get("name"),
        "playlist_items_read": len(items),
        "playlist_mutation": False,
    }


def main():
    manager.CID = os.environ["SPOTIFY_CLIENT_ID"]
    manager.TOKEN = Path(".spotify_daily_preflight_token.json")
    manager.write(manager.TOKEN, {
        "refresh_token": os.environ["SPOTIFY_REFRESH_TOKEN"],
        "obtained_at": 0,
        "expires_in": 0,
    })
    try:
        report = validate_live_playlist(manager.Spotify())
        print(json.dumps(report, indent=2))
    finally:
        manager.TOKEN.unlink(missing_ok=True)


if __name__ == "__main__":
    main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Live read-only credential and Tricky Daily access preflight.
# Safety: Calls Spotify GET endpoints only; never mutates playlists or project state.
# Run: SPOTIFY_CLIENT_ID=... SPOTIFY_REFRESH_TOKEN=... python scripts/spotify/spotify_daily_preflight.py
# Related: docs/TRICKY_DAILY_CYCLE.md and scripts/spotify/spotify_daily_cycle.py.
# -----------------------------------------------------------------------------
