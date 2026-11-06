#!/usr/bin/env python3
"""Optionally enrich track profiles with conservative Discogs release styles.

Discogs styles describe a release, not an individual recording's acoustics.
The resolver therefore requires an exact artist and track title on one unique
Discogs master/release, records release-level provenance, and never contributes
to acoustic confidence. Requires DISCOGS_USER_TOKEN.
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

ROOT = Path("assistant_data/music")
PROFILES = ROOT / "track_profiles.json"
STATE = ROOT / "discogs_lookup_state.json"
API = "https://api.discogs.com"
TOKEN = os.environ.get("DISCOGS_USER_TOKEN", "").strip()
LIMIT = max(1, int(os.environ.get("DISCOGS_LOOKUPS_PER_RUN", "30")))
DELAY = max(1.05, float(os.environ.get("DISCOGS_DELAY_SECONDS", "1.15")))
MISS_RETRY_DAYS = max(30, int(os.environ.get("DISCOGS_MISS_RETRY_DAYS", "180")))
UA = "SHIT-Discogs-Enrichment/1.0 (https://github.com/TrickySturluson/spotify-helper-information-tracker)"


def read(path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return fallback


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n",
                   encoding="utf-8")
    tmp.replace(path)


def norm(value):
    return re.sub(r"\s+", " ", str(value or "").strip()).casefold()


def cache_key(artist, track):
    return hashlib.sha256((norm(artist) + "\0" + norm(track)).encode("utf-8")).hexdigest()


def request_json(path, params=None):
    url = API + path
    if params:
        url += "?" + urlencode(params)
    req = Request(url, headers={
        "User-Agent": UA,
        "Accept": "application/json",
        "Authorization": "Discogs token=" + TOKEN,
    })
    with urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8")), response.headers


def unique_release_candidate(results):
    """Return one unambiguous master/release candidate, otherwise None."""
    rows = [row for row in results if isinstance(row, dict) and row.get("id")]
    if not rows:
        return None, "not_found"
    identities = {}
    for row in rows:
        identity = ("master", str(row.get("master_id"))) if row.get("master_id") else ("release", str(row["id"]))
        identities.setdefault(identity, row)
    if len(identities) != 1:
        return None, "ambiguous_release"
    return next(iter(identities.values())), "candidate"


def exact_release_track(release, artist, track):
    """Require exact artist credit and exact track title in the selected release."""
    artists = release.get("artists") or []
    artist_names = [row.get("name", "") for row in artists if isinstance(row, dict)]
    if not any(norm(name) == norm(artist) for name in artist_names):
        return None
    matches = [row for row in release.get("tracklist") or []
               if isinstance(row, dict) and norm(row.get("title")) == norm(track)]
    if len(matches) != 1:
        return None
    return matches[0]


def lookup_track(artist, track, fetch=request_json):
    """Resolve one exact track through a unique Discogs release context."""
    search, _ = fetch("/database/search", {
        "artist": artist, "track": track, "type": "release", "per_page": 20,
    })
    candidate, status = unique_release_candidate(search.get("results") or [])
    if not candidate:
        return None, status
    release_id = candidate.get("id")
    release, _ = fetch("/releases/" + str(release_id))
    matched_track = exact_release_track(release, artist, track)
    if not matched_track:
        return None, "release_track_or_artist_mismatch"
    styles = sorted({str(value).strip() for value in release.get("styles") or [] if str(value).strip()})
    genres = sorted({str(value).strip() for value in release.get("genres") or [] if str(value).strip()})
    return {
        "discogs_release_id": release_id,
        "discogs_master_id": release.get("master_id") or candidate.get("master_id"),
        "discogs_release_title": release.get("title"),
        "discogs_release_year": release.get("year"),
        "discogs_track_position": matched_track.get("position"),
        "discogs_styles": styles,
        "discogs_genres": genres,
        "discogs_source": "Discogs release database",
        "discogs_scope": "release-level context; not track-specific acoustic evidence",
        "discogs_url": release.get("uri"),
        "discogs_checked_at": datetime.now(timezone.utc).isoformat(),
    }, "matched"


def main():
    if not TOKEN:
        print("DISCOGS_USER_TOKEN is not configured; optional Discogs enrichment skipped.")
        return
    profiles = read(PROFILES, {})
    state = read(STATE, {"checked": {}})
    checked = state.setdefault("checked", {})
    now = int(time.time())
    provider_retry_after = int(state.get("provider_retry_after", 0) or 0)
    if provider_retry_after > now:
        print(f"Discogs provider cooldown active for {provider_retry_after - now}s; no request sent.")
        return
    by_name = {}
    for key, row in profiles.items():
        if isinstance(row, dict) and row.get("artist") and row.get("track"):
            by_name.setdefault((norm(row["artist"]), norm(row["track"])), []).append((key, row))
    candidates = []
    for name, rows in by_name.items():
        if len(rows) != 1:
            continue
        key, row = rows[0]
        if row.get("discogs_status") == "matched":
            continue
        cache = checked.get(cache_key(*name)) or {}
        if int(cache.get("retry_after", 0) or 0) > now:
            continue
        candidates.append((name, key, row))
    candidates.sort(key=lambda item: (item[0][0], item[0][1]))
    looked = matched = misses = 0
    for (artist_norm, track_norm), profile_key, profile in candidates[:LIMIT]:
        artist, track = profile["artist"], profile["track"]
        key = cache_key(artist, track)
        try:
            result, status = lookup_track(artist, track)
        except HTTPError as exc:
            if exc.code in (429, 503):
                retry = exc.headers.get("Retry-After") if exc.headers else None
                try:
                    wait = max(60, int(float(retry))) if retry else 3600
                except (TypeError, ValueError):
                    wait = 3600
                state["provider_retry_after"] = now + wait
                write(STATE, state)
                print(f"Discogs HTTP {exc.code}; provider cooldown saved for {wait}s; stopping safely.")
                break
            print(f"Discogs HTTP {exc.code}; stopping to retry on a later run.")
            break
        except (URLError, TimeoutError, ValueError) as exc:
            print(f"Transient Discogs error; stopping to retry: {exc}")
            break
        looked += 1
        state["provider_retry_after"] = 0
        retry_after = now + (365 if status == "matched" else MISS_RETRY_DAYS) * 86400
        checked[key] = {
            "artist": artist, "track": track,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "retry_after": retry_after, "status": status,
        }
        profile["discogs_status"] = status
        if result:
            profile.update(result)
            matched += 1
        else:
            misses += 1
        if looked % 10 == 0:
            write(PROFILES, profiles)
            write(STATE, state)
            print(f"Progress: {looked} lookups; {matched} exact release matches; {misses} misses/ambiguous.")
        if looked < min(LIMIT, len(candidates)):
            time.sleep(DELAY)
    write(PROFILES, profiles)
    write(STATE, state)
    print(f"Discogs enrichment: {matched} exact release matches from {looked} lookups; "
          f"{misses} misses/ambiguous; {len(candidates)} candidates due.")


if __name__ == "__main__":
    main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Add optional Discogs release-style context to exact track-profile matches.
# Inputs: Existing track_profiles.json rows and DISCOGS_USER_TOKEN; bounded lookup limit
#         is controlled by DISCOGS_LOOKUPS_PER_RUN.
# Outputs: Release-context evidence and durable lookup state in assistant_data/music/.
# Matching: Requires exact artist/title tracklist validation and one unambiguous release;
#           ambiguous releases and misses remain explicit rather than guessed.
# Safety: Rate-limited and cached; does not overwrite primary BPM or acoustic evidence.
# Run: python compat/enrich_discogs.py (requires DISCOGS_USER_TOKEN).
# Related: docs/AUTOMATED_AUDIO_METADATA.md; tests/test_enrich_discogs.py.
# -----------------------------------------------------------------------------
