#!/usr/bin/env python3
"""Incrementally enrich artist profiles with community tags for recommendation use."""
import hashlib
import json
import os
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

SOURCE = Path("data/scrobbles.json")
ROOT = Path("assistant_data/music")
OUT = ROOT / "artist_profiles.json"
API_URL = "https://ws.audioscrobbler.com/2.0/"
API_KEY = os.environ.get("LASTFM_API_KEY")
LIMIT = int(os.environ.get("MUSIC_PROFILE_LOOKUPS_PER_RUN", "120"))
RETRY_DAYS = 30
UA = "TrickyLastFM/1.1 (artist profile enrichment)"

# Deliberately broad, explainable starter vocabulary; raw tags are always retained.
GENRE_HINTS = {
    "alternative", "ambient", "ambient pop", "art pop", "black metal", "blues",
    "breakbeat", "classical", "country", "dance", "dark ambient", "death metal",
    "disco", "dream pop", "drone", "drum and bass", "dub", "dubstep", "electronic",
    "emo", "experimental", "folk", "funk", "garage rock", "glitch", "gothic",
    "grunge", "hardcore", "hard rock", "heavy metal", "hip hop", "house", "hyperpop",
    "indie", "indie pop", "indie rock", "industrial", "instrumental", "jazz",
    "j-pop", "k-pop", "krautrock", "math rock", "metal", "minimal", "new wave",
    "noise", "noise pop", "noise rock", "post-hardcore", "post-metal", "post-punk",
    "post-rock", "power pop", "progressive rock", "psychedelic", "punk", "r&b",
    "rap", "reggae", " shoegaze", "singer-songwriter", "soul", "soundtrack",
    "synth pop", "synthwave", "techno", "trance", "trip hop", "vaporwave", "world"
}
MOOD_HINTS = {
    "aggressive", "angsty", "atmospheric", "beautiful", "calm", "chill", "cold",
    "dark", "dreamy", "eerie", "emotional", "energetic", "epic", "ethereal",
    "euphoric", "haunting", "happy", "heavy", "hopeful", "hypnotic", "melancholy",
    "mellow", "menacing", "nostalgic", " ominous", "peaceful", "playful", "romantic",
    "sad", "scary", "soothing", "spooky", "uplifting", "warm", "weird"
}

def norm(value):
    value = str(value or "").strip().casefold()
    return re.sub(r"[^a-z0-9+#& ]+", "", re.sub(r"\s+", " ", value))

def read_json(path, default):
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")
    tmp.replace(path)

def main():
    if not API_KEY:
        raise RuntimeError("LASTFM_API_KEY is required.")
    scrobbles = read_json(SOURCE, [])
    if not scrobbles:
        raise RuntimeError("Refusing to build profiles from an empty archive.")
    artists = {}
    for row in scrobbles:
        name = str(row.get("artist") or "[Unknown]").strip()
        mbid = str(row.get("artist_mbid") or "").strip()
        aid = "mbid:" + mbid.casefold() if mbid else "name:" + hashlib.sha1(norm(name).encode()).hexdigest()[:16]
        rec = artists.setdefault(aid, {"artist_id": aid, "artist": name, "artist_mbid": mbid or None, "plays": 0})
        rec["plays"] += 1
        if mbid:
            rec["artist_mbid"] = mbid
    profiles = read_json(OUT, {})
    now = int(time.time())
    due = []
    for aid, artist in artists.items():
        old = profiles.get(aid, {})
        if old.get("status") == "matched" and old.get("tags"):
            continue
        if int(old.get("retry_after", 0) or 0) > now:
            continue
        due.append(artist)
    due.sort(key=lambda x: (-x["plays"], x["artist"].casefold()))
    looked_up = found = 0
    for artist in due[:LIMIT]:
        params = {"method": "artist.getTopTags", "api_key": API_KEY, "format": "json", "autocorrect": 0}
        if artist.get("artist_mbid"):
            params["mbid"] = artist["artist_mbid"]
        else:
            params["artist"] = artist["artist"]
        req = Request(API_URL + "?" + urlencode(params), headers={"User-Agent": UA})
        try:
            with urlopen(req, timeout=25) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError) as exc:
            print(f"Profile lookup interrupted at {artist['artist']}: {exc}")
            break
        if "error" in payload:
            if str(payload.get("error")) in {"11", "16", "29"}:
                print(f"Temporary Last.fm API error for {artist['artist']}; stopping.")
                break
            profiles[artist["artist_id"]] = {
                **artist, "status": "not_found", "tags": [], "genres": [], "moods": [],
                "themes": [], "source": "Last.fm artist.getTopTags",
                "checked_at": datetime.now(timezone.utc).isoformat(), "retry_after": now + RETRY_DAYS * 86400
            }
        else:
            raw_tags = (payload.get("toptags") or {}).get("tag") or []
            if isinstance(raw_tags, dict):
                raw_tags = [raw_tags]
            tags = []
            for tag in raw_tags:
                label = str(tag.get("name") or "").strip()
                if label:
                    try:
                        count = int(tag.get("count") or 0)
                    except (TypeError, ValueError):
                        count = 0
                    tags.append({"tag": label, "count": count})
            tags.sort(key=lambda x: (-x["count"], x["tag"].casefold()))
            genre_norms = {norm(x) for x in GENRE_HINTS}
            mood_norms = {norm(x) for x in MOOD_HINTS}
            genres = [t["tag"] for t in tags if norm(t["tag"]) in genre_norms]
            moods = [t["tag"] for t in tags if norm(t["tag"]) in mood_norms]
            genre_set, mood_set = {norm(x) for x in genres}, {norm(x) for x in moods}
            themes = [t["tag"] for t in tags if norm(t["tag"]) not in genre_set | mood_set and norm(t["tag"]) not in {"seen live", "favorites", "favourites", "spotify", "all"}]
            profiles[artist["artist_id"]] = {
                **artist, "status": "matched" if tags else "no_tags",
                "tags": tags, "genres": genres, "moods": moods, "themes": themes,
                "source": "Last.fm artist.getTopTags",
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "retry_after": 0 if tags else now + RETRY_DAYS * 86400
            }
            if tags:
                found += 1
        looked_up += 1
        time.sleep(0.25)
    write_json(OUT, profiles)
    matched = sum(1 for p in profiles.values() if p.get("status") == "matched")
    print(f"Artist profiles: {matched:,} matched; {looked_up:,} lookups this run; {found:,} profiles with tags found; {max(0, len(due)-looked_up):,} pending.")

if __name__ == "__main__":
    main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Incrementally build artist-level community-tag profiles for discovery and playlist analysis.
# Inputs: Reads canonical data/scrobbles.json and existing assistant_data/music/artist_profiles.json.
# Provider: Uses Last.fm artist tag metadata; requires LASTFM_API_KEY and defaults to
#           120 artist lookups/run (MUSIC_PROFILE_LOOKUPS_PER_RUN), with 30-day retry timing.
# Output: Rewrites assistant_data/music/artist_profiles.json with raw community tags,
#         lookup status/provenance, and conservative derived genres, moods, and themes.
# Semantics: Raw tags are retained; derived categories are artist-context signals, not
#            recording-level truth and must not be copied onto every track.
# Run: python compat/build_music_profiles.py.
# Related: scripts/spotify/spotify_discovery.py and docs/AUTOMATED_AUDIO_METADATA.md.
# -----------------------------------------------------------------------------
