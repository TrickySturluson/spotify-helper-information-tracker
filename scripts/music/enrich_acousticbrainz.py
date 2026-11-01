#!/usr/bin/env python3
"""Bulk-enrich SHIT track profiles from the public AcousticBrainz archive/API.

Uses existing MusicBrainz recording IDs in the 32 artist shards. No audio files,
Spotify streams, or per-track manual work are required. The API is queried in
batches of 25 MBIDs; results are checkpointed after each batch.
"""
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path("assistant_data/music")
SHARDS = ROOT / "artists"
OUTPUT = ROOT / "audio_profiles.json"
STATE = ROOT / "acousticbrainz_lookup_state.json"
MISS_RETRY_DAYS = max(30, int(os.environ.get("ACOUSTICBRAINZ_MISS_RETRY_DAYS", "180")))
RECENT_TOP = ROOT / "recent_top_tracks.json"
API = "https://acousticbrainz.org/api/v1/low-level"
UA = "SHIT-AudioMetadata/1.0 (https://github.com/TrickySturluson/spotify-helper-information-tracker)"
BATCH_SIZE = 25
MAX_BATCHES = int(os.environ.get("ACOUSTICBRAINZ_MAX_BATCHES", "1000"))
SLEEP_SECONDS = float(os.environ.get("ACOUSTICBRAINZ_SLEEP_SECONDS", "1.1"))


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


def extract(doc, artist, track, mbid):
    low = doc.get("lowlevel") or {}
    rhythm = low.get("rhythm") or {}
    meta = doc.get("metadata") or {}
    props = meta.get("audio_properties") or {}
    def number(obj, key):
        value = obj.get(key) if isinstance(obj, dict) else None
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None
    return {
        "artist": artist, "track": track, "recording_mbid": mbid,
        "tempo_bpm": number(rhythm, "bpm"),
        "bpm_first_peak": number(rhythm.get("bpm_histogram_first_peak_bpm") or {}, "mean"),
        "bpm_second_peak": number(rhythm.get("bpm_histogram_second_peak_bpm") or {}, "mean"),
        "average_loudness": number(low, "average_loudness"),
        "dynamic_complexity": number(low, "dynamic_complexity"),
        "danceability": number(rhythm, "danceability"),
        "onset_rate": number(rhythm, "onset_rate"),
        "beats_count": rhythm.get("beats_count"),
        "replay_gain_db": number(props, "replay_gain"),
        "source": "AcousticBrainz low-level",
        "source_license": "CC0",
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "measurement_note": "AcousticBrainz average_loudness is not LUFS; no within-track loudness envelope is supplied by this endpoint."
    }



def aggregate_submissions(docs, artist, track, mbid):
    """Collapse all archived submissions robustly and retain disagreement data."""
    rows = [extract(doc, artist, track, mbid) for doc in docs
            if isinstance(doc, dict) and isinstance(doc.get("lowlevel"), dict)]
    if not rows:
        return None
    numeric = ("tempo_bpm", "bpm_first_peak", "bpm_second_peak", "average_loudness",
               "dynamic_complexity", "danceability", "onset_rate",
               "beats_count", "replay_gain_db")
    result = dict(rows[0])
    for field in numeric:
        values = sorted(float(row[field]) for row in rows if row.get(field) is not None)
        if not values:
            result[field] = None
            continue
        middle = len(values) // 2
        result[field] = (values[middle] if len(values) % 2
                         else (values[middle - 1] + values[middle]) / 2)
        if field == "tempo_bpm":
            result["tempo_submission_values_bpm"] = values
            result["tempo_spread_bpm"] = round(max(values) - min(values), 2)
            result["tempo_submission_count"] = len(values)
            result["tempo_confidence"] = (
                "medium" if len(values) >= 2 and max(values) - min(values) <= 4
                else "low"
            )
    result["submission_count"] = len(rows)
    result["submission_policy"] = "median of all returned submissions; spread retained"
    result["source"] = "AcousticBrainz low-level"
    result["measurement_note"] += " Multiple submissions are summarized by median; disagreement is retained."
    return result

def norm(value):
    import re
    return re.sub(r"\s+", " ", str(value or "").strip()).casefold()


def recent_priority(path=RECENT_TOP):
    try:
        rows = read(path, {}).get("tracks", [])
    except (AttributeError, TypeError):
        rows = []
    return {(norm(row.get("artist")), norm(row.get("track"))): rank
            for rank, row in enumerate(rows)
            if row.get("artist") and row.get("track")}


def main():
    priority = recent_priority()
    tracks = {}
    for shard_no in range(32):
        data = read(SHARDS / f"shard-{shard_no:02d}.json", {})
        for artist_row in (data.get("artists") or {}).values():
            artist = artist_row.get("artist") or ""
            for track in (artist_row.get("tracks") or {}).values():
                mbid = str(track.get("track_mbid") or "").strip().lower()
                if len(mbid) == 36 and artist and track.get("track"):
                    tracks[mbid] = (artist, track["track"])

    payload = read(OUTPUT, {"schema_version": 2, "analysis_engine": "AcousticBrainz", "tracks": {}})
    results = payload.setdefault("tracks", {})
    state = read(STATE, {"checked": {}})
    checked = state.setdefault("checked", {})
    now = int(time.time())
    provider_retry_after = int(state.get("provider_retry_after", 0) or 0)
    if provider_retry_after > now:
        print(f"AcousticBrainz provider cooldown active for {provider_retry_after - now}s; no request sent.")
        return
    todo = [mbid for mbid in tracks
            if (mbid not in results or results[mbid].get("source") != "AcousticBrainz low-level"
                or not results[mbid].get("submission_count"))
            and int((checked.get(mbid) or {}).get("retry_after", 0) or 0) <= now]
    todo.sort(key=lambda mbid: (
        priority.get((norm(tracks[mbid][0]), norm(tracks[mbid][1])), 10**9),
        norm(tracks[mbid][0]), norm(tracks[mbid][1]), mbid,
    ))
    recent_due = sum(1 for mbid in todo
                     if priority.get((norm(tracks[mbid][0]), norm(tracks[mbid][1])), 10**9) < 200)
    print(f"Recent top-200 priority: {recent_due:,} recordings with resolved MBIDs are eligible for AcousticBrainz.")
    batches = [todo[i:i+BATCH_SIZE] for i in range(0, len(todo), BATCH_SIZE)]
    batches = batches[:MAX_BATCHES]
    found = 0
    misses = 0
    batch_no = 0
    for batch_no, batch in enumerate(batches, 1):
        query = urlencode({"recording_ids": ";".join(batch)})
        req = Request(API + "?" + query, headers={"User-Agent": UA, "Accept": "application/json"})
        try:
            with urlopen(req, timeout=45) as response:
                data = json.loads(response.read().decode("utf-8"))
                reset = response.headers.get("X-RateLimit-Reset-In")
        except HTTPError as exc:
            if exc.code in (429, 503):
                header = (exc.headers.get("X-RateLimit-Reset-In") or exc.headers.get("Retry-After")) if exc.headers else None
                try:
                    wait = max(60, int(float(header))) if header else 3600
                except (TypeError, ValueError):
                    wait = 3600
                state["provider_retry_after"] = int(time.time()) + wait
                write(STATE, state)
                print(f"AcousticBrainz returned HTTP {exc.code}; provider cooldown saved for {wait}s. Stop and resume later.")
                break
            raise
        except (TimeoutError, URLError, OSError) as exc:
            # A transient transport failure is not a negative result for any MBID.
            # Keep prior batch checkpoints, leave this batch eligible, and stop
            # this provider politely instead of aborting the entire migration.
            wait = 300
            state["provider_retry_after"] = int(time.time()) + wait
            state["last_transport_error"] = type(exc).__name__
            write(STATE, state)
            print(
                f"AcousticBrainz transport {type(exc).__name__}; saved a {wait}s "
                "provider cooldown. Current batch remains unmarked and can resume later."
            )
            break
        state["provider_retry_after"] = 0
        for mbid in batch:
            docs = data.get(mbid) or data.get(mbid.upper()) or {}
            if isinstance(docs, list):
                submissions = docs
            elif isinstance(docs, dict):
                submissions = [docs[key] for key in sorted(docs, key=lambda value: str(value))
                               if isinstance(docs[key], dict)]
            else:
                submissions = []
            artist, title = tracks[mbid]
            profile = aggregate_submissions(submissions, artist, title, mbid)
            checked[mbid] = {
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "retry_after": now + MISS_RETRY_DAYS * 86400,
                "status": "found" if profile else "no_archived_submission",
            }
            if profile:
                results[mbid] = profile
                found += 1
            else:
                misses += 1
        payload.update({
            "schema_version": 2, "analysis_engine": "AcousticBrainz",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "recording_ids_considered": len(tracks),
            "recordings_with_acousticbrainz_data": sum(1 for x in results.values() if x.get("source") == "AcousticBrainz low-level"),
            "tracks": results
        })
        write(OUTPUT, payload)
        write(STATE, state)
        print(f"Batch {batch_no}/{len(batches)}: checked {len(batch)} IDs; found cumulative {found}; misses this run {misses}; total profiles {payload['recordings_with_acousticbrainz_data']}")
        try:
            wait = float(reset or 0)
        except (TypeError, ValueError):
            wait = 0
        if wait > 0:
            if wait > 15:
                state["provider_retry_after"] = now + int(wait)
                write(STATE, state)
                print(f"Server reset is {wait:.0f}s away; checkpointed cooldown and stopping rather than retrying early.")
                break
            time.sleep(max(wait, SLEEP_SECONDS))
        elif batch_no < len(batches):
            time.sleep(SLEEP_SECONDS)
    print(f"AcousticBrainz enrichment complete for this run. Candidate MBIDs: {len(tracks)}; total stored profiles: {len(results)}; negative-cache entries: {sum(1 for row in checked.values() if row.get('status') == 'no_archived_submission')}; batches run: {batch_no}")


if __name__ == "__main__":
    main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Enrich SHIT track profiles from historical AcousticBrainz submissions using verified MusicBrainz recording IDs. Aggregates submissions, preserves disagreement, caches misses, and checkpoints each batch.
# Location: Maintained implementation in scripts/music/enrich_acousticbrainz.py.
# Data flow: Uses the canonical archives and/or generated project data; consult
#            this module's configuration and command options for exact paths.
# Run: python compat/enrich_acousticbrainz.py (legacy command entry point, when applicable).
# Related: tests/ contains regression coverage; docs/ contains extended guides.
# -----------------------------------------------------------------------------
