#!/usr/bin/env python3
"""Rank archive tracks and resolve exact Spotify matches for Tricky Daily.

The archive is a source of listening history, not proof of preference. This
curator favors tracks with a long gap since their last scrobble, balances
familiarity with rediscovery, caps artist concentration, and only accepts
exact title + primary-artist matches from Spotify search.
"""
import hashlib
import json
import math
import re
import urllib.parse
from datetime import date, datetime, timezone
from pathlib import Path

FEATURES = Path("assistant_data/recommendations/track_features.json")
TARGET_SIZE = 30
MIN_MATCHES = 20
RECENT_EXCLUSION_DAYS = 14


def norm(value):
    return re.sub(r"\\s+", " ", str(value or "").strip()).casefold()


def parse_date(value):
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except (AttributeError, TypeError, ValueError):
        return None


def score_track(track, today=None):
    """A transparent, bounded score; never treats scrobbles as a like signal."""
    today = today or date.today()
    last = parse_date(track.get("last_scrobble"))
    days_since = max(0, (today - last).days) if last else 365
    plays = max(1, int(track.get("plays") or 1))
    freshness = min(days_since / 180.0, 1.0)
    familiarity = min(math.log1p(plays) / math.log1p(25), 1.0)
    # Familiarity is deliberately a small anchor, not the dominant signal.
    return round(0.72 * freshness + 0.18 * (1.0 - familiarity) + 0.10 * familiarity, 8)


def rank_candidates(tracks, today=None, limit=TARGET_SIZE):
    """Return a deterministic, diverse set of previously scrobbled tracks."""
    today = today or date.today()
    valid = []
    for track in tracks:
        if not isinstance(track, dict) or not track.get("artist") or not track.get("track"):
            continue
        last = parse_date(track.get("last_scrobble"))
        days_since = (today - last).days if last else 365
        if days_since < RECENT_EXCLUSION_DAYS:
            continue
        row = dict(track)
        row["_score"] = score_track(row, today)
        # Daily deterministic variation without non-reproducible random state.
        seed = f"{today.isoformat()}:{row.get('track_id', row['artist'] + '|' + row['track'])}"
        row["_tie"] = hashlib.sha256(seed.encode("utf-8")).hexdigest()
        valid.append(row)

    valid.sort(key=lambda x: (-x["_score"], x["_tie"], norm(x["artist"]), norm(x["track"])))
    selected, artist_counts = [], {}
    # Two passes: first enforce a strict artist cap, then relax only if needed.
    for cap in (2, 3):
        for row in valid:
            artist = norm(row["artist"])
            if row in selected or artist_counts.get(artist, 0) >= cap:
                continue
            selected.append(row)
            artist_counts[artist] = artist_counts.get(artist, 0) + 1
            if len(selected) >= limit:
                break
        if len(selected) >= limit:
            break
    for row in selected:
        row.pop("_tie", None)
    return selected


def spotify_search_query(track):
    query = f'track:"{track["track"]}" artist:"{track["artist"]}"'
    return "/search?" + urllib.parse.urlencode({"type": "track", "limit": 5, "q": query})


def resolve_exact_tracks(sp, candidates, existing_uris=None, limit=TARGET_SIZE):
    """Resolve only exact title + primary artist matches; skip ambiguous misses."""
    existing = set(existing_uris or [])
    resolved, skipped = [], []
    for candidate in candidates:
        if len(resolved) >= limit:
            break
        try:
            response = sp.call("GET", spotify_search_query(candidate))
        except Exception as error:
            raise RuntimeError(f"Spotify search failed while resolving {candidate['artist']} — {candidate['track']}: {error}") from error
        items = ((response or {}).get("tracks") or {}).get("items") or []
        match = next((
            item for item in items
            if norm(item.get("name")) == norm(candidate["track"])
            and (item.get("artists") or [])
            and norm(item["artists"][0].get("name")) == norm(candidate["artist"])
            and isinstance(item.get("uri"), str)
            and item["uri"].startswith("spotify:track:")
        ), None)
        if not match:
            skipped.append({"artist": candidate["artist"], "track": candidate["track"], "reason": "no exact Spotify match"})
            continue
        if match["uri"] in existing:
            skipped.append({"artist": candidate["artist"], "track": candidate["track"], "reason": "already in Tricky Daily"})
            continue
        existing.add(match["uri"])
        resolved.append({
            "uri": match["uri"], "artist": candidate["artist"], "track": candidate["track"],
            "plays": candidate.get("plays", 0), "last_scrobble": candidate.get("last_scrobble"),
            "score": candidate.get("_score", score_track(candidate))
        })
    return resolved, skipped


def build_daily_recommendations(sp, playlist_items, today=None, feature_path=FEATURES, target_size=TARGET_SIZE):
    if not feature_path.is_file():
        raise RuntimeError(f"Missing recommendation features: {feature_path}")
    tracks = json.loads(feature_path.read_text(encoding="utf-8"))
    if not isinstance(tracks, list) or not tracks:
        raise RuntimeError("Recommendation feature file is empty or invalid.")
    candidates = rank_candidates(tracks, today=today, limit=max(target_size * 5, target_size))
    existing = {item.get("uri") for item in playlist_items if item.get("uri")}
    resolved, skipped = resolve_exact_tracks(sp, candidates, existing, target_size)
    if len(resolved) < min(MIN_MATCHES, target_size):
        raise RuntimeError(
            f"Only {len(resolved)} exact, non-duplicate Spotify matches were found; "
            f"at least {min(MIN_MATCHES, target_size)} are required. Playlist was not changed."
        )
    return resolved, skipped


if __name__ == "__main__":
    raise SystemExit("Run through spotify_playlist_cloud.py using the protected daily_preview command.")
