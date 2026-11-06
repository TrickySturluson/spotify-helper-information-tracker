#!/usr/bin/env python3
"""Use MusicBrainz as a cautious secondary duration source for unresolved tracks."""
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

SOURCE = Path("data/scrobbles.json")
ROOT = Path("assistant_data/music")
SHARDS = ROOT / "artists"
LIMIT = int(os.environ.get("MUSICBRAINZ_LOOKUPS_PER_RUN", "1000"))
UA = "TrickyLastFM/1.1 (personal listening analytics; https://github.com/TrickySturluson/spotify-helper-information-tracker)"
API = "https://musicbrainz.org/ws/2/recording/"

def clean(v):
    return str(v or "").strip() or "[Unknown]"

def norm(v):
    return re.sub(r"\s+", " ", clean(v)).casefold()

def read(path, default):
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def write(path, value):
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")
    tmp.replace(path)

def artist_id(row):
    mbid = str(row.get("artist_mbid") or "").strip().casefold()
    return "mbid:" + mbid if mbid else "name:" + hashlib.sha1(norm(row.get("artist")).encode()).hexdigest()[:16]

def track_id(row, aid):
    mbid = str(row.get("track_mbid") or "").strip().casefold()
    return "mbid:" + mbid if mbid else "track:" + hashlib.sha1((aid + "\0" + norm(row.get("track"))).encode()).hexdigest()[:16]

def main():
    rows = read(SOURCE, [])
    if not rows:
        raise RuntimeError("Refusing to enrich an empty archive.")
    shards = {}
    tracks = {}
    for i in range(32):
        p = SHARDS / f"shard-{i:02d}.json"
        data = read(p, {"artists": {}})
        shards[i] = data
        for aid, a in data.get("artists", {}).items():
            for tid, t in a.get("tracks", {}).items():
                tracks[tid] = t
    catalogue = {}
    for row in rows:
        aid = artist_id(row)
        tid = track_id(row, aid)
        rec = catalogue.setdefault(tid, {"track_id":tid,"artist_id":aid,"artist":clean(row.get("artist")),"track":clean(row.get("track")),"track_mbid":row.get("track_mbid"),"plays":0})
        rec["plays"] += 1
    now_epoch = int(time.time())
    due = [r for tid, r in catalogue.items() if not (tracks.get(tid) or {}).get("duration_ms") and int((tracks.get(tid) or {}).get("musicbrainz_retry_after", 0) or 0) <= now_epoch]
    due.sort(key=lambda r:(-r["plays"],r["artist"].casefold(),r["track"].casefold()))
    found = looked = 0
    now = datetime.now(timezone.utc).isoformat()
    now_epoch = int(time.time())
    for item in due[:LIMIT]:
        # Prefer direct recording MBID lookup, then fall back to strict text search.
        candidates = []
        try:
            if item.get("track_mbid"):
                url = API + item["track_mbid"] + "?fmt=json"
                req = Request(url, headers={"User-Agent":UA})
                try:
                    with urlopen(req, timeout=25) as res:
                        obj = json.loads(res.read().decode("utf-8"))
                    if obj.get("length"):
                        candidates = [obj]
                    else:
                        time.sleep(1.05)
                except HTTPError as exc:
                    if exc.code not in {400, 404}:
                        raise
                    # A stale/invalid MBID should not prevent exact text fallback.
                    print(f"Recording MBID lookup returned HTTP {exc.code}; trying exact artist/title search for {item['artist']} — {item['track']}")
                    time.sleep(1.05)
            if not candidates:
                query = 'recording:"' + item["track"].replace('"', '\\"') + '" AND artist:"' + item["artist"].replace('"', '\\"') + '"'
                url = API + "?" + urlencode({"query":query,"fmt":"json","limit":5})
                req = Request(url, headers={"User-Agent":UA})
                with urlopen(req, timeout=25) as res:
                    obj = json.loads(res.read().decode("utf-8"))
                for result in obj.get("recordings", []):
                    credit = result.get("artist-credit-phrase") or " ".join(
                        x.get("name", "") if isinstance(x, dict) else str(x) for x in result.get("artist-credit", [])
                    )
                    if norm(result.get("title")) == norm(item["track"]) and norm(credit) == norm(item["artist"]) and int(result.get("length") or 0) > 0:
                        candidates.append(result)
        except HTTPError as exc:
            # Missing recordings and invalid individual queries are isolated.
            if exc.code in {400, 404}:
                looked += 1
                existing = tracks.get(item["track_id"])
                if existing is not None:
                    existing["musicbrainz_checked_at"] = now
                    existing["musicbrainz_status"] = "not_found" if exc.code == 404 else "invalid_query"
                    existing["musicbrainz_error"] = f"HTTP {exc.code}"
                    existing["musicbrainz_retry_after"] = now_epoch + 30 * 86400
                print(f"Skipping MusicBrainz HTTP {exc.code} for {item['artist']} — {item['track']}")
                time.sleep(1.05)
                continue
            print(f"MusicBrainz transient HTTP {exc.code} at {item['artist']} — {item['track']}: {exc}")
            break
        except (URLError, TimeoutError, ValueError) as exc:
            print(f"MusicBrainz lookup interrupted at {item['artist']} — {item['track']}: {exc}")
            break
        looked += 1
        existing = tracks.get(item["track_id"])
        if existing is not None:
            existing["musicbrainz_checked_at"] = now
            existing["musicbrainz_retry_after"] = now_epoch + 30 * 86400
        if candidates:
            candidate = candidates[0]
            duration = int(candidate.get("length") or 0)
            # Find the existing artist shard/track record and update only metadata.
            if existing is not None and duration > 0:
                existing.update({
                    "duration_ms":duration,
                    "duration_source":"MusicBrainz recording",
                    "confidence":"high" if item.get("track_mbid") and str(candidate.get("id","")).casefold() == str(item["track_mbid"]).casefold() else "medium",
                    "match_type":"exact_mbid" if item.get("track_mbid") and str(candidate.get("id","")).casefold() == str(item["track_mbid"]).casefold() else "exact_artist_title",
                    "metadata_checked_at":now,
                    "metadata_status":"matched",
                    "retry_after":0,
                    "musicbrainz_retry_after":0
                })
                found += 1
        time.sleep(1.05)  # MusicBrainz requires no more than one request per second.
    if looked:
        for i, data in shards.items():
            write(SHARDS / f"shard-{i:02d}.json", data)
    print(f"MusicBrainz duration fallback: {found:,} matches from {looked:,} lookups; {max(0,len(due)-looked):,} unresolved tracks remain.")

if __name__ == "__main__":
    main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Fill unresolved recording durations from MusicBrainz as a secondary provider.
# Inputs: Reads data/scrobbles.json and assistant_data/music/artists/shard-*.json.
# Matching: Uses a verified recording MBID when available or exact artist/title identity;
#           ambiguous results are not accepted as a duration.
# Outputs: Updates only matching song records in their existing artist shards, recording
#          MusicBrainz source, match type, confidence, checked time, and retry timestamps.
# Provider policy: MUSICBRAINZ_LOOKUPS_PER_RUN defaults to 1,000; requests are spaced
#                  at least 1.05 seconds apart and unresolved records receive a 30-day retry.
# Run: python compat/enrich_musicbrainz_durations.py.
# Related: docs/AUTOMATED_AUDIO_METADATA.md and docs/ALBUM_METADATA_AND_LOOKUP_CONFIDENCE.md.
# -----------------------------------------------------------------------------
