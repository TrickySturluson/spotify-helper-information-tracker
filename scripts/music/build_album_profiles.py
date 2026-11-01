#!/usr/bin/env python3
"""Incrementally enrich album context with Last.fm's album.getTopTags.

Album tags are release-level context, never recording-level proof. The output is
kept separate from track_profiles.json so the sequencer can use it only as a
low-confidence fallback. Requests are exact artist/album lookups, identity
checked, rate limited, and negative cached.
"""
import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SOURCE = Path("data/scrobbles.json")
PLAYLIST_ROOT = Path("assistant_data/spotify/playlists")
ROOT = Path("assistant_data/music")
OUT = ROOT / "album_profiles.json"
STATE = ROOT / "album_profile_state.json"
API_URL = "https://ws.audioscrobbler.com/2.0/"
API_KEY = os.environ.get("LASTFM_API_KEY", "").strip()
LIMIT = max(1, int(os.environ.get("ALBUM_PROFILE_LOOKUPS_PER_RUN", "100")))
RETRY_DAYS = 30
DELAY = max(0.35, float(os.environ.get("ALBUM_PROFILE_DELAY_SECONDS", "0.4")))
UA = "SHIT-Album-Profile-Enrichment/1.0 (https://github.com/TrickySturluson/spotify-helper-information-tracker)"


def read(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return default


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    temp.replace(path)


def clean(value):
    if isinstance(value, dict):
        value = value.get("#text") or value.get("name")
    return str(value or "").strip()


def norm(value):
    return re.sub(r"\\s+", " ", clean(value)).casefold()


def album_id(artist, album):
    return "album:" + hashlib.sha1((norm(artist) + "\\0" + norm(album)).encode()).hexdigest()[:20]


def build_catalogue(scrobbles, playlist_ids=(), playlist_root=PLAYLIST_ROOT):
    """Deduplicate album lookups; priority playlists rank ahead of general history."""
    catalogue = {}
    now = int(time.time())
    recent_since = now - 90 * 86400

    def add(artist, album, track="", plays=0, recent=0, playlist_id=None):
        artist, album = clean(artist), clean(album)
        if artist in {"", "[Unknown]"} or album in {"", "[Unknown]"}:
            return
        key = album_id(artist, album)
        row = catalogue.setdefault(key, {
            "album_id": key, "artist": artist, "album": album,
            "plays": 0, "recent_plays": 0, "priority_playlist_ids": [],
            "track_keys": set(),
        })
        row["plays"] += int(plays or 0)
        row["recent_plays"] += int(recent or 0)
        if playlist_id and playlist_id not in row["priority_playlist_ids"]:
            row["priority_playlist_ids"].append(playlist_id)
        track_key = norm(track)\n        if track_key:\n            row["track_keys"].add(track_key)

    for row in scrobbles:
        album = clean(row.get("album") or row.get("album_name"))
        try:
            stamp = int(row.get("timestamp") or row.get("uts") or 0)
        except (TypeError, ValueError):
            stamp = 0
        add(row.get("artist"), album, row.get("track") or row.get("name"), 1, int(stamp >= recent_since))

    for playlist_id in playlist_ids:
        snap = read(Path(playlist_root) / (playlist_id + ".json"), {})
        if not (isinstance(snap, dict) and snap.get("id") == playlist_id and snap.get("items_accessible")):
            continue
        for item in snap.get("items") or []:
            if not isinstance(item, dict) or item.get("type", "track") != "track":
                continue
            artists = item.get("artists") or []
            add(artists[0] if artists else "", item.get("album"), item.get("name"), playlist_id=playlist_id)

    return catalogue


def fetch_album_tags(artist, album):
    params = {
        "method": "album.getTopTags", "artist": artist, "album": album,
        "api_key": API_KEY, "format": "json", "autocorrect": 0,
    }
    request = Request(API_URL + "?" + urlencode(params), headers={
        "User-Agent": UA, "Accept": "application/json",
    })
    with urlopen(request, timeout=25) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if "error" in payload:
        code = str(payload.get("error"))
        if code in {"11", "16", "29"}:
            raise RuntimeError("temporary_lastfm_" + code)
        return [], "not_found" if code == "6" else "api_error_" + code
    top = payload.get("toptags") or {}
    attrs = top.get("@attr") or {}
    returned_artist, returned_album = clean(attrs.get("artist")), clean(attrs.get("album"))
    if not returned_artist or not returned_album:
        return [], "identity_unverified"
    if norm(returned_artist) != norm(artist) or norm(returned_album) != norm(album):
        return [], "identity_mismatch"
    rows = top.get("tag") or []
    if isinstance(rows, dict):
        rows = [rows]
    tags = []
    for row in rows:
        label = clean(row.get("name"))
        if not label:
            continue
        try:
            count = int(row.get("count") or 0)
        except (TypeError, ValueError):
            count = 0
        tags.append({"tag": label, "count": count, "source": "Last.fm album.getTopTags"})
    tags.sort(key=lambda item: (-item["count"], item["tag"].casefold()))
    return tags, "matched" if tags else "no_tags"


def main():
    if not API_KEY:
        raise RuntimeError("LASTFM_API_KEY is required.")
    scrobbles = read(SOURCE, [])
    if not scrobbles:
        raise RuntimeError("Refusing to enrich an empty scrobble archive.")
    raw_ids = os.environ.get("ALBUM_PROFILE_PRIORITY_PLAYLISTS") or os.environ.get("TRACK_PROFILE_PRIORITY_PLAYLISTS", "")
    playlist_ids = tuple(x.strip() for x in raw_ids.split(",") if x.strip())
    catalogue = build_catalogue(scrobbles, playlist_ids)
    profiles = read(OUT, {})
    state = read(STATE, {})
    now = int(time.time())
    provider_retry = int(state.get("provider_retry_after", 0) or 0)
    if provider_retry > now:
        print(f"Last.fm album-tag cooldown active for {provider_retry-now}s; no request sent.")
        return

    due = []
    for key, item in catalogue.items():
        old = profiles.get(key, {})
        if old.get("status") in {"matched", "no_tags", "not_found"} and int(old.get("retry_after", 0) or 0) > now:
            continue
        if old.get("status") == "matched":
            continue
        if int(old.get("retry_after", 0) or 0) > now:
            continue
        due.append(item)
    due.sort(key=lambda row: (
        not bool(row["priority_playlist_ids"]),
        -row["recent_plays"], -row["plays"], row["artist"].casefold(), row["album"].casefold(),
    ))
    looked = found = 0
    provider_cooldown = False
    for item in due[:LIMIT]:
        key = item["album_id"]
        try:
            tags, status = fetch_album_tags(item["artist"], item["album"])
        except HTTPError as exc:
            if exc.code == 429:
                try:
                    wait = max(60, int(exc.headers.get("Retry-After", "3600")))
                except (TypeError, ValueError, AttributeError):
                    wait = 3600
            else:
                wait = 3600
            state["provider_retry_after"] = int(time.time()) + wait
            write(STATE, state)
            provider_cooldown = True
            print(f"Last.fm album lookup HTTP {exc.code}; saved provider cooldown {wait}s and stopped.")
            break
        except (URLError, TimeoutError, ValueError, RuntimeError) as exc:
            wait = 6 * 3600
            if "temporary_lastfm_29" in str(exc):
                wait = 6 * 3600
            state["provider_retry_after"] = int(time.time()) + wait
            write(STATE, state)
            provider_cooldown = True
            print(f"Last.fm album lookup interrupted ({exc}); saved cooldown and stopped.")
            break
        checked = datetime.now(timezone.utc).isoformat()
        profiles[key] = {
            **item, "lastfm_tags": tags, "status": status,
            "source": "Last.fm album.getTopTags",
            "checked_at": checked,
            "retry_after": 0 if status == "matched" else int(time.time()) + RETRY_DAYS * 86400,
            "identity_verified": status in {"matched", "no_tags"},
        }
        looked += 1
        found += int(bool(tags))
        write(OUT, profiles)
        time.sleep(DELAY)
    if not provider_cooldown:\n        state["provider_retry_after"] = 0\n    state["last_run_at"] = datetime.now(timezone.utc).isoformat()
    write(STATE, state)
    matched = sum(row.get("status") == "matched" for row in profiles.values())
    print(f"Album profiles: {matched:,} matched; {looked:,} lookups this run; {found:,} tagged; {len(due)-looked:,} due/pending; {len(catalogue):,} catalogue albums.")


if __name__ == "__main__":
    main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Incrementally fetch exact Last.fm album-level community tags for
#          unique albums in the scrobble archive and configured priority playlists.
# Inputs: data/scrobbles.json and accessible Spotify playlist snapshots.
# Outputs: assistant_data/music/album_profiles.json and album_profile_state.json.
# Data flow: One lookup per normalized artist/album pair; playlist-priority and
#            recent-listening ordering; exact response identity validation.
# Tracking: Stores provider status, check timestamp, retry-after, source and
#           identity verification. Empty results are cached for 30 days.
# Safety: Sequential requests, minimum 0.35s delay, bounded batch, provider-wide
#         cooldown, atomic checkpoints; album tags remain release context only.
# Run: python compat/build_album_profiles.py
# Related: scripts/spotify/spotify_playlist_sequencer.py; docs/TRANSITION_SCORING.md.
# -----------------------------------------------------------------------------
