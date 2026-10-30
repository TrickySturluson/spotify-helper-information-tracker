#!/usr/bin/env python3
"""Incrementally enrich unique scrobbled tracks with cached Last.fm metadata.

Generated files are optimized for lookup: a compact manifest/index plus 32
artist-hash shards. The canonical scrobble archive is never modified.
"""
import hashlib
import json
import os
import re
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SOURCE = Path("data/scrobbles.json")
ROOT = Path("assistant_data/music")
TRACK_ROOT = ROOT / "artists"
API_URL = "https://ws.audioscrobbler.com/2.0/"
API_KEY = os.environ.get("LASTFM_API_KEY")
MAX_LOOKUPS_PER_RUN = int(os.environ.get("MUSIC_METADATA_LOOKUPS_PER_RUN", "120"))
RETRY_DAYS = 30
SHARD_COUNT = 32
USER_AGENT = "TrickyLastFM/1.0 (metadata enrichment)"


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


def clean(value):
    return str(value or "").strip() or "[Unknown]"


def norm(value):
    return re.sub(r"\s+", " ", clean(value)).casefold()


def stable_id(prefix, value):
    return prefix + ":" + hashlib.sha1(value.encode("utf-8")).hexdigest()[:16]


def artist_identity(item):
    mbid = str(item.get("artist_mbid") or "").strip().casefold()
    return "mbid:" + mbid if mbid else stable_id("name", norm(item.get("artist")))


def track_identity(item, artist_id):
    mbid = str(item.get("track_mbid") or "").strip().casefold()
    return "mbid:" + mbid if mbid else stable_id("track", artist_id + "\0" + norm(item.get("track")))


def shard_for(artist_id):
    return hashlib.sha1(artist_id.encode("utf-8")).digest()[0] % SHARD_COUNT


def api_track_info(track):
    params = {
        "method": "track.getInfo",
        "api_key": API_KEY,
        "format": "json",
        "autocorrect": 0,
    }
    if track.get("track_mbid"):
        params["mbid"] = track["track_mbid"]
    else:
        params["artist"] = track["artist"]
        params["track"] = track["track"]
    request = Request(API_URL + "?" + urlencode(params), headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=25) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if "error" in payload:
        code = str(payload.get("error"))
        if code in {"6"}:
            return None, "not_found"
        if code in {"11", "16", "29"}:
            raise RuntimeError("Temporary Last.fm API error " + code)
        raise RuntimeError("Last.fm API error " + code + ": " + str(payload.get("message", "")))
    return payload.get("track"), None


def main():
    if not SOURCE.exists():
        raise FileNotFoundError(SOURCE)
    scrobbles = read_json(SOURCE, [])
    if not scrobbles:
        raise RuntimeError("Refusing to build metadata from an empty archive.")
    now = int(time.time())
    old_manifest = read_json(ROOT / "manifest.json", {})
    existing_shards = {}
    for shard in range(SHARD_COUNT):
        path = TRACK_ROOT / f"shard-{shard:02d}.json"
        existing_shards[shard] = read_json(path, {"artists": {}})

    # Build unique track/artist catalogue and album occurrence metadata.
    catalogue = {}
    artist_names = {}
    artist_mbids = {}
    artist_album_counts = defaultdict(Counter)
    artist_album_mbids = defaultdict(dict)
    for row in scrobbles:
        artist = clean(row.get("artist"))
        track_name = clean(row.get("track"))
        aid = artist_identity(row)
        tid = track_identity(row, aid)
        artist_names.setdefault(aid, artist)
        if row.get("artist_mbid"):
            artist_mbids[aid] = row["artist_mbid"]
        album = clean(row.get("album"))
        if album != "[Unknown]":
            artist_album_counts[aid][album] += 1
            if row.get("album_mbid"):
                artist_album_mbids[aid][album] = row["album_mbid"]
        record = catalogue.setdefault(tid, {
            "track_id": tid, "artist_id": aid, "artist": artist,
            "track": track_name, "track_mbid": row.get("track_mbid") or None,
            "plays": 0, "first_scrobble": int(row["timestamp"]),
            "last_scrobble": int(row["timestamp"]), "albums": Counter(),
        })
        record["plays"] += 1
        record["first_scrobble"] = min(record["first_scrobble"], int(row["timestamp"]))
        record["last_scrobble"] = max(record["last_scrobble"], int(row["timestamp"]))
        if album != "[Unknown]":
            record["albums"][album] += 1

    # Load prior records by canonical track ID, retaining cached values.
    previous = {}
    for shard_data in existing_shards.values():
        for aid, artist_data in shard_data.get("artists", {}).items():
            for tid, track_data in artist_data.get("tracks", {}).items():
                previous[tid] = track_data

    due = []
    for tid, item in catalogue.items():
        old = previous.get(tid)
        if old and old.get("duration_ms") and old.get("confidence") in {"high", "medium"}:
            continue
        retry_after = int((old or {}).get("retry_after", 0) or 0)
        if retry_after > now:
            continue
        due.append(item)
    due.sort(key=lambda x: (-x["plays"], x["artist"].casefold(), x["track"].casefold()))

    looked_up = 0
    found = 0
    for item in due[:MAX_LOOKUPS_PER_RUN]:
        tid = item["track_id"]
        old = previous.get(tid, {})
        try:
            info, error = api_track_info(item)
        except (HTTPError, URLError, TimeoutError, RuntimeError) as exc:
            # Stop on service/network failures; preserve successful work and retry later.
            print(f"Lookup interrupted for {item['artist']} — {item['track']}: {exc}")
            break
        looked_up += 1
        if info:
            returned_artist = clean((info.get("artist") or {}).get("name"))
            returned_track = clean(info.get("name"))
            duration = int(info.get("duration") or 0)
            exact_labels = norm(returned_artist) == norm(item["artist"]) and norm(returned_track) == norm(item["track"])
            if duration > 0 and exact_labels:
                old.update({
                    "duration_ms": duration,
                    "duration_source": "Last.fm track.getInfo",
                    "confidence": "high" if item.get("track_mbid") and info.get("mbid") and item["track_mbid"].casefold() == str(info["mbid"]).casefold() else "medium",
                    "match_type": "exact_mbid" if item.get("track_mbid") and info.get("mbid") and item["track_mbid"].casefold() == str(info["mbid"]).casefold() else "exact_artist_title",
                    "metadata_checked_at": now,
                    "metadata_status": "matched",
                    "retry_after": 0,
                })
                found += 1
            else:
                old.update({"metadata_checked_at": now, "metadata_status": "ambiguous_or_missing_duration", "retry_after": now + RETRY_DAYS * 86400})
        else:
            old.update({"metadata_checked_at": now, "metadata_status": error or "not_found", "retry_after": now + RETRY_DAYS * 86400})
        previous[tid] = old
        time.sleep(0.25)

    # Assemble artist-oriented records into fixed-size shards.
    shard_artists = {i: {} for i in range(SHARD_COUNT)}
    artist_index = {}
    track_index = {}
    artist_totals = {}
    duration_plays = 0
    duration_ms_total = 0
    high_conf_plays = 0
    medium_conf_plays = 0
    unknown_plays = 0

    for aid, artist in artist_names.items():
        shard = shard_for(aid)
        shard_artists[shard][aid] = {
            "artist": artist,
            "artist_mbid": artist_mbids.get(aid),
            "albums": [
                {"album": name, "album_mbid": artist_album_mbids[aid].get(name), "scrobbles": count}
                for name, count in artist_album_counts[aid].most_common()
            ],
            "tracks": {},
        }
        artist_index[aid] = {"artist": artist, "shard": f"artists/shard-{shard:02d}.json", "track_count": 0}

    artist_plays = Counter()
    artist_known_plays = Counter()
    artist_known_ms = Counter()
    artist_high_plays = Counter()
    artist_medium_plays = Counter()
    for tid, item in catalogue.items():
        aid = item["artist_id"]
        artist_plays[aid] += item["plays"]
        meta = dict(previous.get(tid, {}))
        meta.update({
            "track_id": tid, "track": item["track"], "track_mbid": item.get("track_mbid"),
            "plays": item["plays"],
            "first_scrobble": datetime.fromtimestamp(item["first_scrobble"], timezone.utc).isoformat(),
            "last_scrobble": datetime.fromtimestamp(item["last_scrobble"], timezone.utc).isoformat(),
            "albums": [{"album": name, "scrobbles": count} for name, count in item["albums"].most_common()],
        })
        shard = shard_for(aid)
        shard_artists[shard][aid]["tracks"][tid] = meta
        artist_index[aid]["track_count"] += 1
        track_index[tid] = {"artist_id": aid, "shard": f"artists/shard-{shard:02d}.json"}
        duration = int(meta.get("duration_ms") or 0)
        confidence = meta.get("confidence")
        if duration:
            duration_plays += item["plays"]
            duration_ms_total += duration * item["plays"]
            artist_known_plays[aid] += item["plays"]
            artist_known_ms[aid] += duration * item["plays"]
            if confidence == "high":
                high_conf_plays += item["plays"]
                artist_high_plays[aid] += item["plays"]
            else:
                medium_conf_plays += item["plays"]
                artist_medium_plays[aid] += item["plays"]
        else:
            unknown_plays += item["plays"]

    for aid, artist in artist_names.items():
        plays = artist_plays[aid]
        known = artist_known_plays[aid]
        artist_totals[aid] = {
            "artist": artist, "plays": plays, "tracks": artist_index[aid]["track_count"],
            "duration_covered_plays": known,
            "duration_coverage": round(known / plays, 6) if plays else 0,
            "estimated_full_track_hours": round(artist_known_ms[aid] / 3600000, 3),
            "high_confidence_plays": artist_high_plays[aid],
            "medium_confidence_plays": artist_medium_plays[aid],
        }

    for shard, artists in shard_artists.items():
        write_json(TRACK_ROOT / f"shard-{shard:02d}.json", {
            "schema_version": 1, "shard": shard, "shard_count": SHARD_COUNT, "artists": artists
        })

    write_json(ROOT / "indexes" / "artists.json", artist_index)
    write_json(ROOT / "indexes" / "tracks.json", track_index)
    write_json(ROOT / "artist_duration_totals.json", sorted(
        artist_totals.values(), key=lambda x: (-x["estimated_full_track_hours"], x["artist"].casefold())
    ))

    total_plays = len(scrobbles)
    coverage = duration_plays / total_plays if total_plays else 0
    overview = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "data/scrobbles.json",
        "total_scrobbles": total_plays,
        "unique_tracks": len(catalogue),
        "unique_artists": len(artist_names),
        "tracks_with_duration": sum(1 for tid in catalogue if previous.get(tid, {}).get("duration_ms")),
        "scrobbles_with_duration": duration_plays,
        "scrobble_duration_coverage": round(coverage, 6),
        "high_confidence_scrobbles": high_conf_plays,
        "medium_confidence_scrobbles": medium_conf_plays,
        "unknown_duration_scrobbles": unknown_plays,
        "estimated_full_track_hours": round(duration_ms_total / 3600000, 2),
        "estimate_note": "Duration multiplied by scrobble count; estimates full-track-equivalent time, not actual playback time. Skips and partial plays are unknown.",
        "lookup": {
            "provider": "Last.fm track.getInfo",
            "lookups_this_run": looked_up, "matches_this_run": found,
            "pending_tracks": max(0, len(due) - looked_up),
            "max_lookups_per_run": MAX_LOOKUPS_PER_RUN,
            "retry_days_for_unmatched": RETRY_DAYS,
        },
        "files": {
            "artist_index": "indexes/artists.json",
            "track_index": "indexes/tracks.json",
            "artist_duration_totals": "artist_duration_totals.json",
            "artist_shards": [f"artists/shard-{i:02d}.json" for i in range(SHARD_COUNT)],
        },
    }
    write_json(ROOT / "overview.json", overview)
    manifest = {
        "schema_version": 1, "source_scrobbles": total_plays,
        "unique_tracks": len(catalogue), "unique_artists": len(artist_names),
        "shard_count": SHARD_COUNT, "duration_coverage": round(coverage, 6),
        "lookup_provider": "Last.fm track.getInfo",
        "lookup_policy": "Incremental; successful durations are cached; unmatched tracks retry after 30 days; max 120 lookups per workflow run.",
        "files": overview["files"],
        "lookup_hint": "Read overview.json, then indexes/artists.json to find an artist shard; artist shard contains all that artist's track metadata.",
    }
    write_json(ROOT / "manifest.json", manifest)
    print(f"Music metadata: {len(catalogue):,} tracks, {duration_plays:,}/{total_plays:,} scrobbles duration-covered ({coverage:.1%}); {looked_up} lookups, {found} matches this run.")


if __name__ == "__main__":
    main()
