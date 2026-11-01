#!/usr/bin/env python3
"""Resolve missing MusicBrainz recording IDs in SHIT's artist shards.

Uses strict exact artist + recording-title matching and the MusicBrainz
one-request-per-second policy. Results are checkpointed to the original shard
and can be resumed on the next run. Ambiguous/unmatched titles are not guessed.
"""
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

SHARDS = Path("assistant_data/music/artists")
API = "https://musicbrainz.org/ws/2/recording/"
UA = "SHIT-MusicBrainz-ID-Enrichment/1.0 (https://github.com/TrickySturluson/tricky-lastfm)"
LIMIT = int(os.environ.get("MUSICBRAINZ_ID_LOOKUPS_PER_RUN", "1000"))
DELAY = 1.05


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    tmp.replace(path)


def norm(value):
    import re
    return re.sub(r"\s+", " ", str(value or "").strip()).casefold()


def main():
    due = []
    shard_data = {}
    now = int(time.time())
    for i in range(32):
        path = SHARDS / f"shard-{i:02d}.json"
        if not path.exists():
            continue
        data = read(path)
        shard_data[i] = data
        for artist_key, artist in (data.get("artists") or {}).items():
            for track_key, track in (artist.get("tracks") or {}).items():
                if track.get("track_mbid") or int(track.get("musicbrainz_id_retry_after", 0) or 0) > now:
                    continue
                if not track.get("track") or not artist.get("artist"):
                    continue
                due.append((i, artist_key, track_key, artist["artist"], track["track"], track))
    due.sort(key=lambda row: -int(row[5].get("plays", 0) or 0))
    looked = matched = ambiguous = 0
    for shard_no, artist_key, track_key, artist, title, track in due[:LIMIT]:
        query = 'recording:"' + title.replace('"', '\\"') + '" AND artist:"' + artist.replace('"', '\\"') + '"'
        url = API + "?" + urlencode({"query": query, "fmt": "json", "limit": 5})
        request = Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
        try:
            with urlopen(request, timeout=30) as response:
                obj = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code == 503:
                print("MusicBrainz rate limited the client; stop and resume next run.")
                break
            print(f"HTTP {exc.code}: {artist} — {title}")
            track["musicbrainz_id_retry_after"] = now + 30 * 86400
            looked += 1
            time.sleep(DELAY)
            continue
        except (URLError, TimeoutError, ValueError) as exc:
            print(f"Transient lookup error; stop and resume: {exc}")
            break
        candidates = []
        for result in obj.get("recordings", []):
            credit = result.get("artist-credit-phrase") or ""
            if norm(result.get("title")) == norm(title) and norm(credit) == norm(artist) and result.get("id"):
                candidates.append(result)
        looked += 1
        track["musicbrainz_id_checked_at"] = datetime.now(timezone.utc).isoformat()
        track["musicbrainz_id_retry_after"] = now + 30 * 86400
        if len(candidates) == 1:
            track["track_mbid"] = candidates[0]["id"].lower()
            track["musicbrainz_id_match"] = "exact_artist_title_unique"
            track["musicbrainz_id_retry_after"] = 0
            matched += 1
        elif len(candidates) > 1:
            # Do not guess between different recordings with the same display title/credit.
            ambiguous += 1
            track["musicbrainz_id_match"] = "ambiguous_exact_candidates"
        if looked % 50 == 0:
            write(SHARDS / f"shard-{shard_no:02d}.json", shard_data[shard_no])
            print(f"Progress: {looked} lookups; {matched} unique exact IDs; {ambiguous} ambiguous.")
        time.sleep(DELAY)
    for shard_no, data in shard_data.items():
        write(SHARDS / f"shard-{shard_no:02d}.json", data)
    remaining = sum(
        1 for data in shard_data.values()
        for artist in (data.get("artists") or {}).values()
        for track in (artist.get("tracks") or {}).values()
        if not track.get("track_mbid")
    )
    print(f"MusicBrainz ID resolution: {matched} unique exact matches from {looked} lookups; {ambiguous} ambiguous; {remaining} tracks still lack a recording MBID.")


if __name__ == "__main__":
    main()
