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
RECENT_TOP = Path("assistant_data/music/recent_top_tracks.json")
STATE = Path("assistant_data/music/musicbrainz_id_lookup_state.json")
PLAYLIST_ROOT = Path("assistant_data/spotify/playlists")
API = "https://musicbrainz.org/ws/2/recording/"
ISRC_API = "https://musicbrainz.org/ws/2/isrc/"
UA = "SHIT-MusicBrainz-ID-Enrichment/1.0 (https://github.com/TrickySturluson/spotify-helper-information-tracker)"
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


def recent_priority(path=RECENT_TOP):
    """Map exact normalized artist/title labels to their recent-listening rank."""
    try:
        rows = read(path).get("tracks", [])
    except (OSError, ValueError, AttributeError):
        rows = []
    return {
        (norm(row.get("artist")), norm(row.get("track"))): rank
        for rank, row in enumerate(rows)
        if row.get("artist") and row.get("track")
    }



def spotify_isrc_index(playlist_root=PLAYLIST_ROOT):
    """Read ISRCs already present in accessible Spotify snapshots; no API calls."""
    index = {}
    for path in Path(playlist_root).glob("*.json"):
        try:
            snapshot = read(path)
        except (OSError, ValueError, TypeError):
            continue
        if not isinstance(snapshot, dict) or not snapshot.get("items_accessible"):
            continue
        for item in snapshot.get("items") or []:
            if not isinstance(item, dict) or item.get("type", "track") != "track":
                continue
            external = item.get("external_ids") or {}
            isrc = str(external.get("isrc") or "").strip().upper()
            artists = item.get("artists") or []
            artist = artists[0] if artists else ""
            title = item.get("name") or ""
            if isrc and artist and title:
                index.setdefault((norm(artist), norm(title)), set()).add(isrc)
    return index


def unique_exact_recording(recordings, artist, title):
    """Return one exact MusicBrainz recording match, never a fuzzy guess."""
    candidates = []
    for result in recordings if isinstance(recordings, list) else []:
        credit = result.get("artist-credit-phrase") or ""
        if (norm(result.get("title")) == norm(title)
                and norm(credit) == norm(artist) and result.get("id")):
            candidates.append(result)
    if len(candidates) == 1:
        return candidates[0], "matched"
    return None, "ambiguous" if len(candidates) > 1 else "not_found"


def fetch_json(url):
    request = Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def set_provider_cooldown(state, headers, now):
    """Persist a conservative provider-wide cooldown after a rate-limit response."""
    retry = headers.get("Retry-After") if headers else None
    try:
        wait = max(60, int(float(retry))) if retry else 3600
    except (TypeError, ValueError):
        wait = 3600
    state["provider_retry_after"] = int(now) + wait
    return wait

def main():
    priority = recent_priority()
    provider_state = read(STATE) if STATE.exists() else {}
    now = int(time.time())
    provider_retry_after = int(provider_state.get("provider_retry_after", 0) or 0)
    if provider_retry_after > now:
        print(f"MusicBrainz provider cooldown active for {provider_retry_after - now}s; no request sent.")
        return
    isrc_index = spotify_isrc_index()
    isrc_tracks = sum(1 for values in isrc_index.values() if len(values) == 1)
    ambiguous_isrc_tracks = sum(1 for values in isrc_index.values() if len(values) > 1)
    print(f"Existing Spotify snapshots provide one exact ISRC for {isrc_tracks:,} artist/title pairs; {ambiguous_isrc_tracks:,} pairs have conflicting ISRCs.")
    due = []
    shard_data = {}
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
                rank = priority.get((norm(artist["artist"]), norm(track["track"])), 10**9)
                due.append((i, artist_key, track_key, artist["artist"], track["track"], track, rank))
    due.sort(key=lambda row: (row[6], -int(row[5].get("plays", 0) or 0),
                              norm(row[3]), norm(row[4])))
    recent_due = sum(1 for row in due if row[6] < 10**9)
    print(f"Recent top-200 priority: {min(200, recent_due):,} exact tracks represented in due MusicBrainz ID candidates.")
    looked = matched = ambiguous = 0
    for shard_no, artist_key, track_key, artist, title, track, _rank in due[:LIMIT]:
        candidates = []
        isrc_values = isrc_index.get((norm(artist), norm(title)), set())
        if len(isrc_values) > 1:
            track["musicbrainz_id_checked_at"] = datetime.now(timezone.utc).isoformat()
            track["musicbrainz_id_match"] = "ambiguous_spotify_isrcs"
            track["musicbrainz_id_confidence"] = "unknown"
            track["musicbrainz_id_retry_after"] = now + 180 * 86400
            ambiguous += 1
            continue

        isrc = next(iter(isrc_values)) if len(isrc_values) == 1 else None
        if isrc:
            try:
                isrc_obj = fetch_json(ISRC_API + isrc + "?" + urlencode({"fmt": "json"}))
            except HTTPError as exc:
                if exc.code in (429, 503):
                    wait = set_provider_cooldown(provider_state, exc.headers, now)
                    write(STATE, provider_state)
                    print(f"MusicBrainz rate limited the client; cooldown saved for {wait}s. Stop and resume later.")
                    break
                if exc.code != 404:
                    print(f"ISRC lookup HTTP {exc.code}: {artist} — {title}; falling back to exact title search.")
                isrc_obj = {}
            except (URLError, TimeoutError, ValueError) as exc:
                print(f"Transient ISRC lookup error; stop and resume: {exc}")
                break
            looked += 1
            provider_state["provider_retry_after"] = 0
            isrc_match, isrc_status = unique_exact_recording(isrc_obj.get("recordings", []), artist, title)
            if isrc_match:
                candidates = [isrc_match]
                track["spotify_isrc"] = isrc
                track["musicbrainz_id_match"] = "spotify_isrc_exact_artist_title_unique"
                track["musicbrainz_id_match_source"] = "Spotify snapshot ISRC -> MusicBrainz ISRC lookup"
                track["musicbrainz_id_confidence"] = "high"
            elif isrc_status == "ambiguous":
                track["musicbrainz_id_checked_at"] = datetime.now(timezone.utc).isoformat()
                track["musicbrainz_id_match"] = "ambiguous_musicbrainz_isrc_recordings"
                track["musicbrainz_id_confidence"] = "unknown"
                track["musicbrainz_id_retry_after"] = now + 180 * 86400
                ambiguous += 1
                time.sleep(DELAY)
                continue
            else:
                # ISRC may be absent from MusicBrainz or use a different credit;
                # fall back only to the existing strict exact artist/title query.
                time.sleep(DELAY)

        if not candidates:
            query = 'recording:"' + title.replace('"', '\\"') + '" AND artist:"' + artist.replace('"', '\\"') + '"'
            url = API + "?" + urlencode({"query": query, "fmt": "json", "limit": 5})
            try:
                obj = fetch_json(url)
            except HTTPError as exc:
                if exc.code in (429, 503):
                    wait = set_provider_cooldown(provider_state, exc.headers, now)
                    write(STATE, provider_state)
                    print(f"MusicBrainz rate limited the client; cooldown saved for {wait}s. Stop and resume later.")
                    break
                print(f"HTTP {exc.code}: {artist} — {title}")
                track["musicbrainz_id_retry_after"] = now + 30 * 86400
                looked += 1
                time.sleep(DELAY)
                continue
            except (URLError, TimeoutError, ValueError) as exc:
                print(f"Transient lookup error; stop and resume: {exc}")
                break
            match, match_status = unique_exact_recording(obj.get("recordings", []), artist, title)
            candidates = [match] if match else []
            looked += 1
            provider_state["provider_retry_after"] = 0
            if match_status == "ambiguous":
                ambiguous += 1
                track["musicbrainz_id_match"] = "ambiguous_exact_candidates"
                track["musicbrainz_id_confidence"] = "unknown"

        track["musicbrainz_id_checked_at"] = datetime.now(timezone.utc).isoformat()
        track["musicbrainz_id_retry_after"] = now + 30 * 86400
        if len(candidates) == 1:
            track["track_mbid"] = candidates[0]["id"].lower()
            if track.get("musicbrainz_id_match") != "spotify_isrc_exact_artist_title_unique":
                track["musicbrainz_id_match"] = "exact_artist_title_unique"
                track["musicbrainz_id_match_source"] = "MusicBrainz exact artist/title search"
                track["musicbrainz_id_confidence"] = "medium"
            track["musicbrainz_id_retry_after"] = 0
            matched += 1
        if looked % 50 == 0:
            write(SHARDS / f"shard-{shard_no:02d}.json", shard_data[shard_no])
            print(f"Progress: {looked} lookups; {matched} unique exact IDs; {ambiguous} ambiguous.")
        time.sleep(DELAY)
    for shard_no, data in shard_data.items():
        write(SHARDS / f"shard-{shard_no:02d}.json", data)
    write(STATE, provider_state)
    remaining = sum(
        1 for data in shard_data.values()
        for artist in (data.get("artists") or {}).values()
        for track in (artist.get("tracks") or {}).values()
        if not track.get("track_mbid")
    )
    print(f"MusicBrainz ID resolution: {matched} unique exact matches from {looked} lookups; {ambiguous} ambiguous; {remaining} tracks still lack a recording MBID.")

if __name__ == "__main__":
    main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Resolve missing MusicBrainz recording IDs in legacy artist shards
#          so later acoustic and track-tag enrichment can use exact identities.
# Inputs: assistant_data/music/artists/shard-*.json, recent_top_tracks.json,
#         Spotify playlist reference snapshots for ISRC corroboration, and
#         existing musicbrainz_id_lookup_state.json.
# Outputs: Updates affected artist shards with verified recording MBIDs and
#          checkpoints provider cooldown/lookup state.
# Provider policy: MusicBrainz recording/ISRC endpoints; default cap is
#                  MUSICBRAINZ_ID_LOOKUPS_PER_RUN=1000 with 1.05-second spacing.
# Safety: Exact artist/title matching and corroborating ISRC evidence only;
#         ambiguous candidates remain unresolved. Existing IDs are preserved.
# Run: python compat/enrich_musicbrainz_recording_ids.py (from repository root).
# Related: scripts/music/enrich_acousticbrainz.py;
#          scripts/music/build_track_profiles.py; docs/AUTOMATED_AUDIO_METADATA.md.
# -----------------------------------------------------------------------------
