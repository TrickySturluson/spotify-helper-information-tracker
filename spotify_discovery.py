#!/usr/bin/env python3
"""Discovery-first Spotify curator using Last.fm similarity + Spotify catalogue search.

The scrobble archive is a taste/familiarity model, never the candidate catalogue.
No archive track is hard-excluded: prior plays and recency progressively reduce
its rank. Liked tracks receive a strong penalty but remain eligible.
"""
import json
import math
import re
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

PROFILES = Path("assistant_data/music/artist_profiles.json")
FEATURES = Path("assistant_data/recommendations/track_features.json")
LASTFM_URL = "https://ws.audioscrobbler.com/2.0/"
TARGET_SIZE = 30
MIN_MATCHES = 20
SEED_ARTISTS = 24
SIMILAR_PER_SEED = 20
DISCOVERY_ARTISTS = 36
TRACKS_PER_ARTIST = 10


def norm(value):
    return re.sub(r"\s+", " ", str(value or "").strip()).casefold()


def track_key(artist, track):
    return norm(artist) + "|" + norm(track)


def parse_date(value):
    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value).date()
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except (TypeError, ValueError, OSError):
        return None


def familiarity_penalty(plays, last_scrobble, today=None):
    """Return a smooth penalty in [0, 0.9]; never excludes a heard track."""
    today = today or date.today()
    plays = max(0, int(plays or 0))
    if not plays:
        return 0.0
    last = parse_date(last_scrobble)
    days_ago = max(0, (today - last).days) if last else 3650
    count_penalty = min(math.log1p(plays) / math.log1p(40), 1.0) * 0.62
    recency_penalty = 0.28 * math.exp(-days_ago / 120.0)
    return min(0.9, count_penalty + recency_penalty)


def build_familiarity_index(tracks):
    return {
        track_key(row.get("artist"), row.get("track")): {
            "plays": int(row.get("plays") or 0),
            "last_scrobble": row.get("last_scrobble"),
        }
        for row in tracks
        if isinstance(row, dict) and row.get("artist") and row.get("track")
    }


def _lastfm_similar(seed, api_key, limit=SIMILAR_PER_SEED):
    params = {
        "method": "artist.getSimilar", "artist": seed["artist"],
        "api_key": api_key, "format": "json", "autocorrect": 0,
        "limit": limit,
    }
    if seed.get("artist_mbid"):
        params.pop("artist")
        params["mbid"] = seed["artist_mbid"]
    request = urllib.request.Request(
        LASTFM_URL + "?" + urllib.parse.urlencode(params),
        headers={"User-Agent": "TrickyLastFM/1.0 (discovery curator)"},
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if "error" in payload:
        raise RuntimeError("Last.fm similar-artist lookup failed: " + str(payload.get("message", payload["error"])))
    rows = (payload.get("similarartists") or {}).get("artist") or []
    if isinstance(rows, dict):
        rows = [rows]
    return rows


def discover_similar_artists(profiles, api_key, today=None, seed_limit=SEED_ARTISTS):
    """Collect similar artists from a rotating, play-weighted sample of taste seeds."""
    today = today or date.today()
    seeds = [
        row for row in profiles.values()
        if row.get("artist") and row.get("status") == "matched"
        and (row.get("genres") or row.get("tags"))
    ]
    # Weight toward artists with substantial listening history, while spreading
    # seeds across the archive rather than using only the top handful.
    seeds.sort(key=lambda row: (-int(row.get("plays") or 0), norm(row["artist"])))
    if len(seeds) > seed_limit:
        stride = max(1, len(seeds) // seed_limit)
        seeds = seeds[::stride][:seed_limit]
    found = {}
    for seed in seeds:
        for similar in _lastfm_similar(seed, api_key):
            name = str(similar.get("name") or "").strip()
            if not name:
                continue
            try:
                match = float(similar.get("match") or 0)
            except (TypeError, ValueError):
                match = 0.0
            key = norm(name)
            if not key:
                continue
            old = found.get(key)
            evidence = {
                "artist": name, "similarity": max(0.0, min(1.0, match)),
                "seed_artist": seed["artist"],
                "seed_plays": int(seed.get("plays") or 0),
            }
            if old is None or evidence["similarity"] > old["similarity"]:
                found[key] = evidence
        time.sleep(0.18)
    return sorted(found.values(), key=lambda row: (-row["similarity"], norm(row["artist"])))[:DISCOVERY_ARTISTS]


def liked_track_keys(sp):
    """Read the complete Spotify Liked Songs library; fail closed if scope is missing."""
    liked = set()
    path = "/me/tracks?limit=50"
    try:
        while path:
            page = sp.call("GET", path)
            for entry in (page or {}).get("items") or []:
                track = entry.get("track") or {}
                artists = track.get("artists") or []
                if track.get("name") and artists:
                    liked.add(track_key(artists[0].get("name"), track["name"]))
                if track.get("uri"):
                    liked.add(track["uri"])
            next_url = (page or {}).get("next")
            path = next_url.replace("https://api.spotify.com/v1", "") if next_url else None
    except Exception as error:
        message = str(error)
        if "403" in message or "scope" in message.casefold():
            raise RuntimeError(
                "Spotify Liked Songs access is not authorized yet. Reauthorize the playlist manager "
                "with the user-library-read scope, then update SPOTIFY_REFRESH_TOKEN in GitHub Actions Secrets. "
                "No playlist changes were made."
            ) from error
        raise
    return liked


def spotify_artist_tracks(sp, artist, limit=TRACKS_PER_ARTIST):
    query = f'artist:"{artist}"'
    endpoint = "/search?" + urllib.parse.urlencode({
        "type": "track", "limit": limit, "q": query,
    })
    response = sp.call("GET", endpoint)
    return ((response or {}).get("tracks") or {}).get("items") or []


def candidate_score(track, similarity, familiarity, liked, today=None):
    today = today or date.today()
    artist = (track.get("artists") or [{}])[0].get("name", "")
    name = track.get("name", "")
    known = familiarity.get(track_key(artist, name), {})
    plays = int(known.get("plays") or 0)
    penalty = familiarity_penalty(plays, known.get("last_scrobble"), today)
    uri = track.get("uri")
    is_liked = track_key(artist, name) in liked or (uri and uri in liked)
    popularity = max(0, min(100, int(track.get("popularity") or 0))) / 100.0
    # Similarity is the taste-fit signal; popularity is a small quality prior,
    # not a popularity contest. Novelty dominates the ranking.
    score = 0.58 * similarity + 0.12 * popularity + 0.30 * (1.0 - penalty)
    if is_liked:
        score -= 0.62
    return score, plays, known.get("last_scrobble"), is_liked


def build_discovery_recommendations(
    sp, playlist_items, today=None, profiles_path=PROFILES,
    features_path=FEATURES, api_key=None, target_size=TARGET_SIZE,
    similar_artist_rows=None, liked_keys=None,
):
    today = today or date.today()
    api_key = api_key or __import__("os").environ.get("LASTFM_API_KEY")
    if not api_key and similar_artist_rows is None:
        raise RuntimeError("LASTFM_API_KEY is required for similar-artist discovery.")
    if not profiles_path.is_file() or not features_path.is_file():
        raise RuntimeError("Music artist profiles or track familiarity features are missing.")
    profiles = json.loads(profiles_path.read_text(encoding="utf-8"))
    archive = json.loads(features_path.read_text(encoding="utf-8"))
    if not isinstance(profiles, dict) or not profiles or not isinstance(archive, list):
        raise RuntimeError("Music taste/familiarity data is empty or invalid.")
    familiarity = build_familiarity_index(archive)
    existing_uris = {row.get("uri") for row in playlist_items if row.get("uri")}
    if liked_keys is None:
        liked_keys = liked_track_keys(sp)
    similar = similar_artist_rows if similar_artist_rows is not None else discover_similar_artists(profiles, api_key, today)
    candidates = {}
    for artist_row in similar:
        artist = artist_row["artist"]
        try:
            items = spotify_artist_tracks(sp, artist)
        except Exception as error:
            # A single unavailable artist should not abort an otherwise healthy
            # discovery pass; Spotify auth/rate-limit errors still propagate.
            if "HTTP 401" in str(error) or "HTTP 403" in str(error) or "HTTP 429" in str(error):
                raise
            continue
        for track in items:
            artists = track.get("artists") or []
            if not track.get("name") or not artists or norm(artists[0].get("name")) != norm(artist):
                continue
            uri = track.get("uri")
            if not isinstance(uri, str) or not uri.startswith("spotify:track:") or uri in existing_uris:
                continue
            key = track_key(artist, track["name"])
            score, plays, last, is_liked = candidate_score(
                track, artist_row["similarity"], familiarity, liked_keys, today
            )
            row = {
                "uri": uri, "artist": artist, "track": track["name"],
                "plays": plays, "last_scrobble": last, "score": round(score, 6),
                "similarity": artist_row["similarity"],
                "liked": is_liked,
                "tier": "discovery" if plays == 0 else ("rediscovery" if plays <= 2 else "familiar"),
                "popularity": track.get("popularity", 0),
            }
            if key not in candidates or row["score"] > candidates[key]["score"]:
                candidates[key] = row
        time.sleep(0.08)
    # Deterministic ordering; cap artists to preserve range across the 30.
    ranked = sorted(candidates.values(), key=lambda row: (-row["score"], norm(row["artist"]), norm(row["track"])))
    selected, artist_counts = [], defaultdict(int)
    for row in ranked:
        if len(selected) >= target_size:
            break
        key = norm(row["artist"])
        if artist_counts[key] >= 2:
            continue
        selected.append(row)
        artist_counts[key] += 1
    if len(selected) < min(MIN_MATCHES, target_size):
        raise RuntimeError(
            f"Only {len(selected)} discovery candidates were found; at least "
            f"{min(MIN_MATCHES, target_size)} are required. Playlist was not changed."
        )
    return selected, []


if __name__ == "__main__":
    raise SystemExit("Run through spotify_playlist_cloud.py using the protected daily_preview command.")
