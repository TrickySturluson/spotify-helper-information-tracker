#!/usr/bin/env python3
"""Incrementally enrich individual scrobbled tracks with sourced community tags.

Last.fm supplies crowd-ranked track tags. MusicBrainz supplies recording tags
and genres when a verified recording MBID is already present. No fuzzy MBID
search is used here: uncertain identity matches are left unresolved.
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
ROOT = Path("assistant_data/music")
SHARD_ROOT = ROOT / "artists"
OUT = ROOT / "track_profiles.json"
LASTFM_URL = "https://ws.audioscrobbler.com/2.0/"
MUSICBRAINZ_URL = "https://musicbrainz.org/ws/2/recording/"
API_KEY = os.environ.get("LASTFM_API_KEY")
LIMIT = int(os.environ.get("TRACK_PROFILE_LOOKUPS_PER_RUN", "120"))
RETRY_DAYS = 30
SHARDS = 32
UA = "TrickyLastFM/1.2 (track profile enrichment; https://github.com/TrickySturluson/tricky-lastfm)"


def read(path, default):
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, separators=(",", ":"))
        handle.write("\n")
    tmp.replace(path)


def clean(value):
    return str(value or "").strip() or "[Unknown]"


def norm(value):
    return re.sub(r"\s+", " ", clean(value)).casefold()


def artist_id(row):
    mbid = str(row.get("artist_mbid") or "").strip().casefold()
    return "mbid:" + mbid if mbid else "name:" + hashlib.sha1(norm(row.get("artist")).encode()).hexdigest()[:16]


def track_id(row, aid):
    mbid = str(row.get("track_mbid") or "").strip().casefold()
    return "mbid:" + mbid if mbid else "track:" + hashlib.sha1((aid + "\0" + norm(row.get("track"))).encode()).hexdigest()[:16]


def request_json(url, params=None, user_agent=UA):
    if params:
        url += ("&" if "?" in url else "?") + urlencode(params)
    request = Request(url, headers={"User-Agent": user_agent, "Accept": "application/json"})
    with urlopen(request, timeout=25) as response:
        return json.loads(response.read().decode("utf-8"))


def lastfm_tags(item):
    params = {"method": "track.getTopTags", "api_key": API_KEY, "format": "json", "autocorrect": 0}
    if item.get("track_mbid"):
        params["mbid"] = item["track_mbid"]
    else:
        params.update({"artist": item["artist"], "track": item["track"]})
    payload = request_json(LASTFM_URL, params)
    if "error" in payload:
        code = str(payload.get("error"))
        if code in {"11", "16", "29"}:
            raise RuntimeError("Temporary Last.fm API error " + code)
        return [], "not_found" if code == "6" else "api_error_" + code
    top = payload.get("toptags") or {}
    # Last.fm returns the requested identity even when the tag list is empty.
    returned_artist = clean(top.get("@attr", {}).get("artist"))
    returned_track = clean(top.get("@attr", {}).get("track"))
    if item.get("track_mbid"):
        if returned_artist != "[Unknown]" and (norm(returned_artist) != norm(item["artist"]) or norm(returned_track) != norm(item["track"])):
            return [], "identity_mismatch"
    else:
        if returned_artist == "[Unknown]" or returned_track == "[Unknown]":
            return [], "identity_unverified"
        if norm(returned_artist) != norm(item["artist"]) or norm(returned_track) != norm(item["track"]):
            return [], "identity_mismatch"
    rows = top.get("tag") or []
    if isinstance(rows, dict):
        rows = [rows]
    tags = []
    for row in rows:
        label = str(row.get("name") or "").strip()
        if not label:
            continue
        try:
            count = int(row.get("count") or 0)
        except (TypeError, ValueError):
            count = 0
        tags.append({"tag": label, "count": count, "source": "Last.fm track.getTopTags"})
    tags.sort(key=lambda row: (-row["count"], row["tag"].casefold()))
    return tags, "matched" if tags else "no_tags"


def musicbrainz_tags(item):
    mbid = str(item.get("track_mbid") or "").strip()
    if not mbid:
        return [], [], "no_recording_mbid"
    payload = request_json(MUSICBRAINZ_URL + mbid, {"fmt": "json", "inc": "tags+genres"})
    returned_id = str(payload.get("id") or "").casefold()
    if returned_id != mbid.casefold():
        return [], [], "identity_mismatch"
    recordings = payload.get("tags") or []
    genres = payload.get("genres") or []
    tags = [{"tag": str(row.get("name") or "").strip(), "count": int(row.get("count") or 0),
             "source": "MusicBrainz recording tag"} for row in recordings if row.get("name")]
    genre_tags = [{"tag": str(row.get("name") or "").strip(), "count": int(row.get("count") or 0),
                   "source": "MusicBrainz recording genre"} for row in genres if row.get("name")]
    return tags, genre_tags, "matched" if tags or genre_tags else "no_tags"


def main():
    if not API_KEY:
        raise RuntimeError("LASTFM_API_KEY is required.")
    rows = read(SOURCE, [])
    if not rows:
        raise RuntimeError("Refusing to enrich an empty archive.")

    catalogue = {}
    for row in rows:
        aid = artist_id(row)
        tid = track_id(row, aid)
        rec = catalogue.setdefault(tid, {"track_id": tid, "artist_id": aid,
            "artist": clean(row.get("artist")), "track": clean(row.get("track")),
            "track_mbid": row.get("track_mbid") or None, "plays": 0})
        rec["plays"] += 1
        if row.get("track_mbid"):
            rec["track_mbid"] = row["track_mbid"]

    profiles = read(OUT, {})
    now = int(time.time())
    due = []
    for tid, item in catalogue.items():
        old = profiles.get(tid, {})
        lastfm_done = old.get("lastfm_status") in {"matched", "no_tags", "not_found"}
        if lastfm_done and (old.get("retry_after", 0) == 0 or int(old.get("retry_after", 0) or 0) > now):
            continue
        if int(old.get("retry_after", 0) or 0) > now:
            continue
        due.append(item)
    due.sort(key=lambda row: (-row["plays"], row["artist"].casefold(), row["track"].casefold()))

    looked = found = mb_looked = mb_found = 0
    for item in due[:LIMIT]:
        tid = item["track_id"]
        old = profiles.get(tid, {})
        try:
            tags, status = lastfm_tags(item)
        except (HTTPError, URLError, TimeoutError, ValueError, RuntimeError) as exc:
            print(f"Last.fm track-tag lookup interrupted at {item['artist']} — {item['track']}: {exc}")
            break
        looked += 1
        old.update({"track_id": tid, "artist_id": item["artist_id"], "artist": item["artist"],
            "track": item["track"], "track_mbid": item.get("track_mbid"),
            "lastfm_tags": tags, "lastfm_status": status,
            "lastfm_checked_at": datetime.now(timezone.utc).isoformat()})
        if tags:
            found += 1
        time.sleep(0.25)

        # MusicBrainz calls are made only for an existing recording MBID.
        if item.get("track_mbid") and not old.get("musicbrainz_checked_at"):
            try:
                mb_tags, mb_genres, mb_status = musicbrainz_tags(item)
            except (HTTPError, URLError, TimeoutError, ValueError) as exc:
                print(f"MusicBrainz tag lookup interrupted at {item['artist']} — {item['track']}: {exc}")
                profiles[tid] = old
                break
            mb_looked += 1
            old.update({"musicbrainz_tags": mb_tags, "musicbrainz_genres": mb_genres,
                "musicbrainz_status": mb_status,
                "musicbrainz_checked_at": datetime.now(timezone.utc).isoformat()})
            if mb_tags or mb_genres:
                mb_found += 1
            time.sleep(1.05)
        old["retry_after"] = 0 if status in {"matched", "no_tags", "not_found"} else now + RETRY_DAYS * 86400
        profiles[tid] = old

    write(OUT, profiles)
    matched = sum(1 for row in profiles.values() if row.get("lastfm_tags") or row.get("musicbrainz_tags") or row.get("musicbrainz_genres"))
    print(f"Track profiles: {matched:,} with sourced tags; {looked:,} Last.fm lookups ({found:,} tagged); "
          f"{mb_looked:,} MusicBrainz lookups ({mb_found:,} tagged); {max(0, len(due)-looked):,} pending.")


if __name__ == "__main__":
    main()
