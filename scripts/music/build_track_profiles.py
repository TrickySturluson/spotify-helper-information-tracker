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
PLAYLIST_ROOT = Path("assistant_data/spotify/playlists")
PRIORITY_PLAYLIST_IDS = tuple(x.strip() for x in os.environ.get("TRACK_PROFILE_PRIORITY_PLAYLISTS", "").split(",") if x.strip())
LASTFM_URL = "https://ws.audioscrobbler.com/2.0/"
MUSICBRAINZ_URL = "https://musicbrainz.org/ws/2/recording/"
API_KEY = os.environ.get("LASTFM_API_KEY")
LIMIT = int(os.environ.get("TRACK_PROFILE_LOOKUPS_PER_RUN", "120"))
RECENT_WINDOW_DAYS = max(1, int(os.environ.get("TRACK_PROFILE_RECENT_WINDOW_DAYS", "90")))
RECENT_TOP_N = max(1, int(os.environ.get("TRACK_PROFILE_RECENT_TOP_N", "200")))
RECENT_TOP_OUT = ROOT / "recent_top_tracks.json"
RETRY_DAYS = 30
SHARDS = 32
UA = "TrickyLastFM/1.2 (track profile enrichment; https://github.com/TrickySturluson/spotify-helper-information-tracker)"


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
    base = {"method": "track.getTopTags", "api_key": API_KEY, "format": "json", "autocorrect": 0}
    has_mbid = bool(item.get("track_mbid"))
    params = dict(base)
    if has_mbid:
        params["mbid"] = item["track_mbid"]
    else:
        params.update({"artist": item["artist"], "track": item["track"]})

    used_name_fallback = False
    try:
        payload = request_json(LASTFM_URL, params)
    except HTTPError as exc:
        # Last.fm documents MBID and artist/title as alternative identifiers.
        # Some valid recording MBIDs nevertheless produce HTTP 400/404, so
        # retry once using the exact scrobble identity before classifying it.
        if not has_mbid or exc.code not in {400, 404}:
            raise
        detail = ""
        try:
            detail = exc.read(300).decode("utf-8", errors="replace").replace(chr(10), " ").strip()
        except Exception:
            pass
        print(f"Last.fm MBID lookup HTTP {exc.code} for {item['artist']} — {item['track']}; retrying exact artist/title ({detail[:120]})")
        fallback = dict(base, artist=item["artist"], track=item["track"])
        payload = request_json(LASTFM_URL, fallback)
        used_name_fallback = True
    if "error" in payload:
        code = str(payload.get("error"))
        if code in {"11", "16", "29"}:
            raise RuntimeError("Temporary Last.fm API error " + code)
        # Invalid-parameter responses on an MBID lookup get the same exact
        # artist/title fallback as HTTP 400/404 responses.
        if has_mbid and code == "6":
            payload = request_json(LASTFM_URL, dict(base, artist=item["artist"], track=item["track"]))
            used_name_fallback = True
            if "error" in payload:
                code = str(payload.get("error"))
                if code in {"11", "16", "29"}:
                    raise RuntimeError("Temporary Last.fm API error " + code)
                return [], "not_found" if code == "6" else "api_error_" + code
        else:
            return [], "not_found" if code == "6" else "api_error_" + code

    top = payload.get("toptags") or {}
    # Always verify the response against the exact artist/title from the archive,
    # including responses obtained through the MBID route.
    returned_artist = clean(top.get("@attr", {}).get("artist"))
    returned_track = clean(top.get("@attr", {}).get("track"))
    if used_name_fallback or not has_mbid:
        if returned_artist == "[Unknown]" or returned_track == "[Unknown]":
            return [], "identity_unverified"
        if norm(returned_artist) != norm(item["artist"]) or norm(returned_track) != norm(item["track"]):
            return [], "identity_mismatch"
    elif returned_artist != "[Unknown]" and (
        norm(returned_artist) != norm(item["artist"]) or norm(returned_track) != norm(item["track"])
    ):
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


def should_retry_lastfm(old, now):
    """Retry previously failed MBID HTTP lookups immediately after fallback is added."""
    if old.get("lastfm_status") in {"matched", "no_tags", "not_found"}:
        return False
    return int(old.get("retry_after", 0) or 0) <= now


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



def build_catalogue(rows, priority_playlist_ids=(), playlist_root=PLAYLIST_ROOT, recent_since=None, metadata_root=ROOT):
    """Build the scrobbled catalogue and add exact tracks from priority playlists.

    Playlist-only tracks are eligible for Last.fm track.getTopTags lookups even
    when they have never been scrobbled. Spotify artist/title strings are kept
    as-is and Last.fm response identity checks still gate every accepted tag.
    """
    catalogue = {}
    by_name = {}
    # Use only unique exact artist/title matches from the canonical metadata shards.
    # Keep the archive-derived track_id stable even when a recording MBID is added.
    verified_mbids = {}
    for shard_no in range(SHARDS):
        shard = read(Path(metadata_root) / "artists" / f"shard-{shard_no:02d}.json", {})
        for artist_row in (shard.get("artists") or {}).values():
            artist_name = clean(artist_row.get("artist"))
            for track_row in (artist_row.get("tracks") or {}).values():
                mbid = str(track_row.get("track_mbid") or "").strip()
                title = clean(track_row.get("track"))
                if mbid and artist_name != "[Unknown]" and title != "[Unknown]":
                    verified_mbids.setdefault((norm(artist_name), norm(title)), set()).add(mbid)
    for row in rows:
        aid = artist_id(row)
        tid = track_id(row, aid)
        key = (norm(row.get("artist")), norm(row.get("track")))
        rec = catalogue.setdefault(tid, {
            "track_id": tid, "artist_id": aid,
            "artist": clean(row.get("artist")), "track": clean(row.get("track")),
            "track_mbid": row.get("track_mbid") or None, "plays": 0,
            "recent_plays": 0, "priority_playlist_ids": []
        })
        rec["plays"] += 1
        try:
            played_at = int(row.get("timestamp") or row.get("uts") or 0)
        except (TypeError, ValueError):
            played_at = 0
        if recent_since is not None and played_at >= int(recent_since):
            rec["recent_plays"] += 1
        shard_matches = verified_mbids.get(key, set())
        if row.get("track_mbid"):
            rec["track_mbid"] = row["track_mbid"]
        elif len(shard_matches) == 1:
            rec["track_mbid"] = next(iter(shard_matches))
        by_name.setdefault(key, []).append(tid)

    for playlist_id in priority_playlist_ids:
        playlist = read(Path(playlist_root) / f"{playlist_id}.json", {})
        if (not isinstance(playlist, dict) or playlist.get("id") != playlist_id
                or not playlist.get("items_accessible")):
            continue
        for item in playlist.get("items") or []:
            if not isinstance(item, dict) or item.get("type", "track") != "track":
                continue
            artists = item.get("artists") or []
            artist = clean(artists[0] if artists else "")
            title = clean(item.get("name"))
            if artist == "[Unknown]" or title == "[Unknown]":
                continue
            key = (norm(artist), norm(title))
            matches = by_name.get(key, [])
            # Reuse an archive identity only when artist/title resolves to one
            # catalogue record. If several recordings share that label, retain
            # a separate exact-name lookup rather than guessing an MBID.
            if len(matches) == 1:
                tid = matches[0]
                rec = catalogue[tid]
            else:
                row = {"artist": artist, "track": title}
                aid = artist_id(row)
                tid = track_id(row, aid)
                rec = catalogue.setdefault(tid, {
                    "track_id": tid, "artist_id": aid, "artist": artist,
                    "track": title, "track_mbid": None, "plays": 0,
                    "recent_plays": 0, "priority_playlist_ids": []
                })
                by_name.setdefault(key, []).append(tid)
            rec.setdefault("priority_playlist_ids", [])
            if playlist_id not in rec["priority_playlist_ids"]:
                rec["priority_playlist_ids"].append(playlist_id)
    # Add a shard-resolved ID to playlist-only tracks only when the exact
    # artist/title maps to one recording.
    for key, tids in by_name.items():
        matches = verified_mbids.get(key, set())
        if len(matches) == 1:
            for tid in tids:
                if not catalogue[tid].get("track_mbid"):
                    catalogue[tid]["track_mbid"] = next(iter(matches))
    return catalogue

def recent_top_tracks(catalogue, limit=RECENT_TOP_N, window_days=RECENT_WINDOW_DAYS):
    """Return a deterministic rolling-window ranking from Last.fm scrobbles."""
    eligible = [item for item in catalogue.values() if int(item.get("recent_plays", 0) or 0) > 0]
    eligible.sort(key=lambda row: (
        -int(row.get("recent_plays", 0) or 0),
        -int(row.get("plays", 0) or 0),
        row["artist"].casefold(), row["track"].casefold(),
    ))
    return {
        "schema_version": 1,
        "source": "Last.fm scrobble archive",
        "window_days": int(window_days),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidate_tracks": len(eligible),
        "tracks": [
            {"track_id": row["track_id"], "artist_id": row["artist_id"],
             "artist": row["artist"], "track": row["track"],
             "track_mbid": row.get("track_mbid"), "recent_plays": int(row["recent_plays"]),
             "all_time_plays": int(row["plays"])}
            for row in eligible[:max(1, int(limit))]
        ],
    }


def main():
    if not API_KEY:
        raise RuntimeError("LASTFM_API_KEY is required.")
    rows = read(SOURCE, [])
    if not rows:
        raise RuntimeError("Refusing to enrich an empty archive.")

    now = int(time.time())
    recent_since = now - RECENT_WINDOW_DAYS * 86400
    catalogue = build_catalogue(rows, PRIORITY_PLAYLIST_IDS, recent_since=recent_since)
    recent_ranking = recent_top_tracks(catalogue)
    write(RECENT_TOP_OUT, recent_ranking)
    recent_top_ids = {row["track_id"] for row in recent_ranking["tracks"]}
    print(f"Recent top-track cohort: {len(recent_top_ids):,} tracks from the last {RECENT_WINDOW_DAYS} days; ranked from {recent_ranking['candidate_tracks']:,} recently played unique tracks.")
    if PRIORITY_PLAYLIST_IDS:
        prioritized = sum(1 for item in catalogue.values() if item.get("priority_playlist_ids"))
        print(f"Priority playlist coverage: {prioritized:,} exact tracks across {len(PRIORITY_PLAYLIST_IDS)} configured playlist(s).")

    profiles = read(OUT, {})
    due = []
    for tid, item in catalogue.items():
        old = profiles.get(tid, {})
        lastfm_due = should_retry_lastfm(old, now)
        mb_due = bool(item.get("track_mbid")) and not old.get("musicbrainz_checked_at") and int(old.get("musicbrainz_retry_after", 0) or 0) <= now
        if lastfm_due or mb_due:
            due.append(item)
    due.sort(key=lambda row: (
        row["track_id"] not in recent_top_ids,
        not bool(row.get("priority_playlist_ids")),
        -int(row.get("recent_plays", 0) or 0),
        -row["plays"], row["artist"].casefold(), row["track"].casefold()
    ))

    looked = found = mb_looked = mb_found = 0
    for item in due[:LIMIT]:
        tid = item["track_id"]
        old = profiles.get(tid, {})
        if should_retry_lastfm(old, now):
            try:
                tags, status = lastfm_tags(item)
            except HTTPError as exc:
                try:
                    body = exc.read(500).decode("utf-8", errors="replace").replace("\n", " ").strip()
                except Exception:
                    body = ""
                headers = {}
                for key in ("Content-Type", "Content-Length", "Retry-After", "Server", "Date"):
                    value = exc.headers.get(key) if exc.headers else None
                    if value:
                        headers[key.lower()] = value
                detail = json.dumps({"reason": str(exc.reason), "headers": headers, "body": body}, ensure_ascii=False)
                if exc.code in {400, 404}:
                    status = "http_" + str(exc.code)
                    old.update({"track_id": tid, "artist_id": item["artist_id"], "artist": item["artist"],
                        "track": item["track"], "track_mbid": item.get("track_mbid"),
                        "lastfm_tags": [], "lastfm_status": status, "lastfm_error": detail[:900],
                        "lastfm_checked_at": datetime.now(timezone.utc).isoformat(),
                        "retry_after": now + RETRY_DAYS * 86400})
                    profiles[tid] = old
                    looked += 1
                    print(f"Skipping Last.fm HTTP {exc.code} for {item['artist']} — {item['track']}: {detail[:240]}")
                else:
                    old["retry_after"] = now + 6 * 3600
                    profiles[tid] = old
                    print(f"Last.fm transient HTTP {exc.code} at {item['artist']} — {item['track']}: {detail[:240]}")
                    break
            except (URLError, TimeoutError, ValueError, RuntimeError) as exc:
                old["retry_after"] = now + 6 * 3600
                profiles[tid] = old
                print(f"Last.fm track-tag lookup interrupted at {item['artist']} — {item['track']}: {exc}")
                break
            else:
                looked += 1
                old.update({"track_id": tid, "artist_id": item["artist_id"], "artist": item["artist"],
                    "track": item["track"], "track_mbid": item.get("track_mbid"),
                    "lastfm_tags": tags, "lastfm_status": status,
                    "lastfm_checked_at": datetime.now(timezone.utc).isoformat(),
                    "retry_after": 0 if status in {"matched", "no_tags", "not_found"} else now + RETRY_DAYS * 86400})
                if tags:
                    found += 1
                time.sleep(0.25)

        # MusicBrainz retries are independent of Last.fm. A Last.fm no-tags
        # response must not suppress an unattempted recording lookup.
        if item.get("track_mbid") and not old.get("musicbrainz_checked_at") and int(old.get("musicbrainz_retry_after", 0) or 0) <= now:
            try:
                mb_tags, mb_genres, mb_status = musicbrainz_tags(item)
            except HTTPError as exc:
                if exc.code == 404:
                    mb_tags, mb_genres, mb_status = [], [], "not_found"
                else:
                    retry = 6 * 3600
                    try:
                        retry = max(60, min(7 * 86400, int(exc.headers.get("Retry-After", retry))))
                    except (TypeError, ValueError, AttributeError):
                        pass
                    old["musicbrainz_retry_after"] = now + retry
                    profiles[tid] = old
                    print(f"MusicBrainz temporary HTTP {exc.code} at {item['artist']} — {item['track']}; retry in {retry}s.")
                    continue
            except (URLError, TimeoutError, ValueError) as exc:
                old["musicbrainz_retry_after"] = now + 6 * 3600
                profiles[tid] = old
                print(f"MusicBrainz lookup interrupted at {item['artist']} — {item['track']}: {exc}")
                continue
            mb_looked += 1
            old.update({"musicbrainz_tags": mb_tags, "musicbrainz_genres": mb_genres,
                "musicbrainz_status": mb_status,
                "musicbrainz_checked_at": datetime.now(timezone.utc).isoformat(),
                "musicbrainz_retry_after": 0})
            if mb_tags or mb_genres:
                mb_found += 1
            time.sleep(1.05)
        profiles[tid] = old

    write(OUT, profiles)

    # Persist every scraped track profile into the canonical per-recording
    # library. Existing catalogue evidence and mood assessments are merged.
    from scripts.music.music_library import MusicLibrary
    library_rows = []
    for tid, item in catalogue.items():
        profile = profiles.get(tid, {})
        library_rows.append({
            "track_id": tid,
            "track_mbid": item.get("track_mbid") or profile.get("track_mbid"),
            "artist_id": item.get("artist_id"),
            "artist": item.get("artist"),
            "track": item.get("track"),
            "lastfm_tags": profile.get("lastfm_tags") or [],
            "musicbrainz_tags": profile.get("musicbrainz_tags") or [],
            "musicbrainz_genres": profile.get("musicbrainz_genres") or [],
            "lastfm_status": profile.get("lastfm_status"),
            "musicbrainz_status": profile.get("musicbrainz_status"),
            "lastfm_checked_at": profile.get("lastfm_checked_at"),
            "musicbrainz_checked_at": profile.get("musicbrainz_checked_at"),
            "priority_playlist_ids": item.get("priority_playlist_ids") or [],
            "listening_context": {
                "source": "Last.fm scrobble archive and configured Spotify playlists",
                "all_time_plays": item.get("plays", 0),
                "recent_plays": item.get("recent_plays", 0),
                "priority_playlist_ids": item.get("priority_playlist_ids") or [],
            },
        })
    library_result = MusicLibrary().put_catalogue(library_rows)
    print("Canonical music library updated from track enrichment: "
          f"{library_result['songs']:,} songs, "
          f"{library_result['artists']:,} artists, "
          f"{library_result['albums']:,} albums.")

    matched = sum(1 for row in profiles.values() if row.get("lastfm_tags") or row.get("musicbrainz_tags") or row.get("musicbrainz_genres"))
    pending = sum(1 for item in catalogue.values() if should_retry_lastfm(profiles.get(item["track_id"], {}), now) or
                  (item.get("track_mbid") and not profiles.get(item["track_id"], {}).get("musicbrainz_checked_at") and
                   int(profiles.get(item["track_id"], {}).get("musicbrainz_retry_after", 0) or 0) <= now))
    print(f"Track profiles: {matched:,} with sourced tags; {looked:,} Last.fm lookups ({found:,} tagged); "
          f"{mb_looked:,} MusicBrainz lookups ({mb_found:,} tagged); {pending:,} pending.")


if __name__ == "__main__":
    main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Build track-level sourced tags and a rolling recent-top-track enrichment cohort.
# Inputs: Last.fm scrobbles, exact priority-playlist snapshots, existing track-profile cache,
#         LASTFM_API_KEY, TRACK_PROFILE_LOOKUPS_PER_RUN, TRACK_PROFILE_RECENT_WINDOW_DAYS,
#         TRACK_PROFILE_RECENT_TOP_N and TRACK_PROFILE_PRIORITY_PLAYLISTS.
# Outputs: assistant_data/music/track_profiles.json, durable lookup state,
#          recent_top_tracks.json, and canonical MusicLibrary song/artist/album evidence
#          written through MusicLibrary.put_catalogue().
# Selection: Includes archive tracks, exact priority-playlist tracks and a configurable
#            recent top-N cohort ranked by Last.fm plays within the configured window.
# Identity: Uses existing verified recording evidence; fuzzy MusicBrainz ID search is not run here.
# Safety: Bounded provider requests; no archive mutation or Spotify playlist writes.
# Run: python compat/build_track_profiles.py (repository root; LASTFM_API_KEY required).
# Related: docs/RECENT_TRACK_ENRICHMENT.md; docs/TRACK_MOOD_EVIDENCE.md;
#          tests/test_track_profiles.py.
# -----------------------------------------------------------------------------
