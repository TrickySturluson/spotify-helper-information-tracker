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
API = "https://acousticbrainz.org/api/v1/low-level"
UA = "SHIT-AudioMetadata/1.0 (https://github.com/TrickySturluson/tricky-lastfm)"
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


def main():
    tracks = {}
    for shard_no in range(32):
        data = read(SHARDS / f"shard-{shard_no:02d}.json", {})
        for artist_row in (data.get("artists") or {}).values():
            artist = artist_row.get("artist") or ""
            for track in (artist_row.get("tracks") or {}).values():
                mbid = str(track.get("track_mbid") or "").strip().lower()
                if len(mbid) == 36 and artist and track.get("track"):
                    tracks[mbid] = (artist, track["track"])

    payload = read(OUTPUT, {"schema_version": 1, "analysis_engine": "AcousticBrainz", "tracks": {}})
    results = payload.setdefault("tracks", {})
    todo = [mbid for mbid in tracks if mbid not in results or results[mbid].get("source") != "AcousticBrainz low-level"]
    batches = [todo[i:i+BATCH_SIZE] for i in range(0, len(todo), BATCH_SIZE)]
    batches = batches[:MAX_BATCHES]
    found = 0
    for batch_no, batch in enumerate(batches, 1):
        query = urlencode({"recording_ids": ";".join(batch)})
        req = Request(API + "?" + query, headers={"User-Agent": UA, "Accept": "application/json"})
        try:
            with urlopen(req, timeout=45) as response:
                data = json.loads(response.read().decode("utf-8"))
                reset = response.headers.get("X-RateLimit-Reset-In")
        except HTTPError as exc:
            if exc.code == 429:
                wait = int(exc.headers.get("X-RateLimit-Reset-In", "10"))
                print(f"Rate limited; wait {wait}s and rerun to resume.")
                break
            raise
        for mbid in batch:
            docs = data.get(mbid) or data.get(mbid.upper()) or {}
            if not docs:
                continue
            # Most recordings have one submission; use the first available offset.
            doc = docs.get("0") or next(iter(docs.values()), {})
            if not isinstance(doc, dict) or not doc:
                continue
            artist, title = tracks[mbid]
            results[mbid] = extract(doc, artist, title, mbid)
            found += 1
        payload.update({
            "schema_version": 1, "analysis_engine": "AcousticBrainz",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "recording_ids_considered": len(tracks),
            "recordings_with_acousticbrainz_data": sum(1 for x in results.values() if x.get("source") == "AcousticBrainz low-level"),
            "tracks": results
        })
        write(OUTPUT, payload)
        print(f"Batch {batch_no}/{len(batches)}: checked {len(batch)} IDs; found this batch {found}; total profiles {payload['recordings_with_acousticbrainz_data']}")
        if reset and float(reset) > 0:
            time.sleep(min(max(float(reset), SLEEP_SECONDS), 15))
        else:
            time.sleep(SLEEP_SECONDS)
    print(f"AcousticBrainz enrichment complete for this run. Candidate MBIDs: {len(tracks)}; total stored profiles: {len(results)}; batches run: {min(len(batches), batch_no if batches else 0)}")


if __name__ == "__main__":
    main()
