#!/usr/bin/env python3
"""Generate and safely refresh metadata-based Spotify playlist descriptions.

Descriptions are generated from current playlist membership and the existing
SHIT playlist-intelligence profile. Non-empty descriptions are treated as
manual unless this tool previously recorded them as SHIT-generated.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import spotify_playlist_manager as manager
import playlist_intelligence as intelligence

STATE = Path("assistant_data/spotify/playlist_descriptions.json")
MAX_DESCRIPTION_LENGTH = 300


def _tags(rows, limit=3):
    result = []
    for row in rows or []:
        value = row.get("tag") if isinstance(row, dict) else row
        if isinstance(value, str) and value.strip() and value.strip().casefold() not in {x.casefold() for x in result}:
            result.append(value.strip())
        if len(result) >= limit:
            break
    return result


def build_description(name, items, profile):
    """Build a short, factual description from supported profile evidence."""
    count = len(items or [])
    moods = _tags(profile.get("moods"), 3)
    track_moods = _tags((profile.get("track_metadata") or {}).get("moods"), 3)
    genres = _tags(profile.get("genres"), 3)
    themes = _tags(profile.get("themes"), 3)
    lyric_themes = _tags((profile.get("track_metadata") or {}).get("lyric_themes"), 3)
    sound = _tags(((profile.get("sound_tags") or {}).get("families") or []), 2)

    mood_terms = track_moods or moods
    theme_terms = lyric_themes or themes
    sound_terms = sound
    parts = []
    if mood_terms:
        parts.append("Mood: " + ", ".join(mood_terms))
    if genres:
        parts.append("Sounds: " + ", ".join(genres))
    elif sound_terms:
        parts.append("Sound: " + ", ".join(sound_terms))
    if theme_terms:
        parts.append("Themes: " + ", ".join(theme_terms))
    if not parts:
        artists = [row.get("artist") for row in (profile.get("top_artists") or []) if isinstance(row, dict) and row.get("artist")][:3]
        if artists:
            parts.append("Featuring " + ", ".join(artists))
        else:
            parts.append("A changing collection shaped by its current tracklist")
    description = f"{name} — " + ". ".join(parts) + f". {count} tracks, evolving with the playlist."
    description = " ".join(description.split()).strip()
    if len(description) > MAX_DESCRIPTION_LENGTH:
        description = description[:MAX_DESCRIPTION_LENGTH - 1].rstrip(" ,;:.") + "…"
    return description


def profile_signature(items, description):
    payload = {
        "items": [row.get("uri") or [row.get("name"), row.get("artists")] for row in items or []],
        "description": description,
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def description_state():
    data = manager.read(STATE, {"schema_version": 1, "playlists": {}})
    if not isinstance(data, dict) or not isinstance(data.get("playlists"), dict):
        raise manager.ManagerError("Playlist description state is invalid; refusing updates.")
    return data


def plan_description(playlist, items, profile, state):
    """Return an update plan, preserving every user-authored description."""
    pid = playlist.get("id")
    current = playlist.get("description") or ""
    entry = state.get("playlists", {}).get(pid, {})
    last_generated = entry.get("generated_description")
    is_owned_generated = bool(last_generated and current == last_generated)
    if current.strip() and not is_owned_generated:
        return {"status": "manual_description_preserved", "playlist_id": pid, "current": current}
    proposed = build_description(playlist.get("name") or "Playlist", items, profile)
    signature = profile_signature(items, proposed)
    if is_owned_generated and current == proposed and entry.get("profile_signature") == signature:
        return {"status": "unchanged", "playlist_id": pid, "description": current}
    return {
        "status": "update" if current != proposed else "unchanged",
        "playlist_id": pid,
        "description": proposed,
        "profile_signature": signature,
    }


def apply_description(sp, playlist, items, profile, state):
    """Apply one generated description only to explicitly managed, unlocked playlists."""
    pid = playlist.get("id")
    manager.assert_managed(pid)
    if not manager.unlocked(pid):
        raise manager.ManagerError("Playlist is LOCKED; unlock it explicitly before updating its description.")
    plan = plan_description(playlist, items, profile, state)
    if plan["status"] != "update":
        return plan
    sp.call("PUT", f"/playlists/{pid}", {"description": plan["description"]})
    state.setdefault("playlists", {})[pid] = {
        "generated_description": plan["description"],
        "profile_signature": plan["profile_signature"],
        "updated_at": manager.stamp(),
        "source": "playlist_intelligence",
    }
    manager.write(STATE, state)
    manager.audit(
        event="playlist_description_auto_updated",
        playlist_id=pid,
        description=plan["description"],
        profile_signature=plan["profile_signature"],
    )
    return plan


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("playlist_id")
    parser.add_argument("--apply", action="store_true", help="apply only when managed and explicitly unlocked")
    args = parser.parse_args(argv)
    sp = manager.Spotify()
    playlist = manager.find(sp, args.playlist_id)
    snapshot = manager.snapshot(sp, playlist)
    profile = intelligence.build_playlist_profile(snapshot["items"])
    state = description_state()
    plan = plan_description(playlist, snapshot["items"], profile, state)
    print(json.dumps({**plan, "apply_requested": args.apply}, indent=2, ensure_ascii=False))
    if not args.apply or plan["status"] != "update":
        return 0
    result = apply_description(sp, playlist, snapshot["items"], profile, state)
    print("Updated." if result["status"] == "update" else result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Keep non-manual Spotify playlist descriptions aligned with their contents.
# Scope: Deterministic descriptions from SHIT playlist-intelligence metadata.
# Safety: Non-empty user descriptions are preserved; writes require managed status,
#         explicit unlock, and the CLI --apply flag. No bulk personal-playlist edits.
# Run: python compat/spotify_playlist_descriptions.py PLAYLIST_ID [--apply]
# Related: scripts/spotify/playlist_intelligence.py and spotify_playlist_manager.py.
# -----------------------------------------------------------------------------
