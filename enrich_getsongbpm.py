#!/usr/bin/env python3
"""Optional GetSongBPM tempo/key fallback for SHIT's track catalogue.

Requires GETSONGBPM_API_KEY. Searches artist + title, accepts only one exact
artist/title match, and never overwrites an existing primary BPM measurement.
"""
import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path("assistant_data/music")
SHARDS = ROOT / "artists"
OUTPUT = ROOT / "audio_profiles.json"
STATE = ROOT / "getsongbpm_lookup_state.json"
API = "https://api.getsong.co/search/"
API_KEY = os.environ.get("GETSONGBPM_API_KEY", "").strip()
LIMIT = int(os.environ.get("GETSONGBPM_LOOKUPS_PER_RUN", "300"))
DELAY = float(os.environ.get("GETSONGBPM_DELAY_SECONDS", "1.25"))
RETRY_DAYS = 30
UA = "SHIT-AudioMetadata/1.0 (+https://github.com/TrickySturluson/spotify-helper-information-tracker)"


def read(path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return fallback


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    tmp.replace(path)


def norm(value):
    return re.sub(r"\\s+", " ", str(value or "").strip()).casefold()


def artist_name(song):
    artist = song.get("artist")
    if isinstance(artist, dict):
        return artist.get("name") or ""
    if isinstance(artist, list):
        return (artist[0] or {}).get("name", "") if artist and isinstance(artist[0], dict) else ""
    return str(artist or "")


def exact_match(results, artist, title):
    matches = []
    for row in results if isinstance(results, list) else []:
        if norm(row.get("title")) == norm(title) and norm(artist_name(row)) == norm(artist):
            matches.append(row)
    return matches[0] if len(matches) == 1 else None


def track_key(artist, title):
    return hashlib.sha256((norm(artist) + "\\0" + norm(title)).encode("utf-8")).hexdigest()


def main():
    if not API_KEY:
        print("GETSONGBPM_API_KEY is not configured; optional fallback skipped.")
        return
    catalogue = {}
    for shard_no in range(32):
        data = read(SHARDS / f"shard-{shard_no:02d}.json", {})
        for artist_row in (data.get("artists") or {}).values():
            artist = artist_row.get("artist") or ""
            for track in (artist_row.get("tracks") or {}).values():
                title = track.get("track") or ""
                if artist and title:
                    catalogue.setdefault((norm(artist), norm(title)), (artist, title))

    payload = read(OUTPUT, {"schema_version": 1, "tracks": {}})
    profiles = payload.setdefault("tracks", {})
    state = read(STATE, {"checked": {}})
    checked = state.setdefault("checked", {})
    indexed = {(norm(row.get("artist")), norm(row.get("track"))): row
               for row in profiles.values() if isinstance(row, dict)}
    now = int(time.time())
    todo = []
    for key, (artist, title) in catalogue.items():
        profile = indexed.get(key)
        if profile and profile.get("tempo_bpm") is not None:
            continue
        cache_key = track_key(artist, title)
        prior = checked.get(cache_key) or {}
        if int(prior.get("retry_after", 0) or 0) > now:
            continue
        todo.append((cache_key, artist, title))
    looked = matched = 0
    for cache_key, artist, title in todo[:LIMIT]:
        lookup = f"song:{title} artist:{artist}"
        url = API + "?" + urlencode({"type": "both", "lookup": lookup, "limit": 10})
        req = Request(url, headers={"X-API-KEY": API_KEY, "User-Agent": UA, "Accept": "application/json"})
        try:
            with urlopen(req, timeout=30) as response:
                obj = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code in (429, 503):
                print(f"GetSongBPM rate limited ({exc.code}); stopping for this run.")
                break
            print(f"GetSongBPM HTTP {exc.code}; stopping to retry next run.")
            break
        except (URLError, TimeoutError, ValueError) as exc:
            print(f"Transient GetSongBPM error; stopping to retry: {exc}")
            break
        row = exact_match(obj.get("search"), artist, title)
        looked += 1
        checked[cache_key] = {
            "artist": artist, "track": title,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "retry_after": now + RETRY_DAYS * 86400,
            "status": "matched" if row else "no_exact_unique_match",
        }
        if row:
            profile_key = "getsongbpm:" + cache_key
            profile = indexed.get((norm(artist), norm(title))) or {
                "artist": artist, "track": title,
            }
            try:
                tempo = float(row.get("tempo")) if row.get("tempo") not in (None, "") else None
            except (TypeError, ValueError):
                tempo = None
            profile["getsongbpm"] = {
                "song_id": row.get("id"), "uri": row.get("uri"),
                "tempo_bpm": tempo, "key": row.get("key_of"),
                "open_key": row.get("open_key"), "time_signature": row.get("time_sig"),
                "danceability": row.get("danceability"), "acousticness": row.get("acousticness"),
                "source": "GetSongBPM API",
            }
            if tempo is not None and profile.get("tempo_bpm") is None:
                profile["tempo_bpm"] = tempo
                profile["tempo_source"] = "GetSongBPM API"
            profiles[profile_key] = profile
            indexed[(norm(artist), norm(title))] = profile
            matched += 1
        if looked % 25 == 0:
            payload["generated_at"] = datetime.now(timezone.utc).isoformat()
            write(OUTPUT, payload)
            write(STATE, state)
            print(f"Progress: {looked} lookups; {matched} exact matches.")
        time.sleep(DELAY)
    payload["generated_at"] = datetime.now(timezone.utc).isoformat()
    payload["getsongbpm"] = {"lookups_this_run": looked, "matches_this_run": matched}
    write(OUTPUT, payload)
    write(STATE, state)
    print(f"GetSongBPM: {matched} exact matches from {looked} lookups; {len(todo)} candidates were due.")


if __name__ == "__main__":
    main()
