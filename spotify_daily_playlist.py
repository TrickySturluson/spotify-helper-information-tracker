#!/usr/bin/env python3
"""Build a balanced daily mix of proven favorites, rediscoveries and deep cuts.

Last.fm scrobbles are evidence of repeated listening, not a guarantee of liking.
The curator uses that history as a useful signal, while preserving room for
less-played tracks and enforcing artist diversity.
"""
import hashlib
import json
import math
import re
import urllib.parse
from datetime import date, datetime
from pathlib import Path

FEATURES = Path("assistant_data/recommendations/track_features.json")
TARGET_SIZE = 30
MIN_MATCHES = 20
RECENT_EXCLUSION_DAYS = 14
FAVORITE_MIN_PLAYS = 5
KNOWN_MIN_PLAYS = 2


def norm(value):
    return re.sub(r"\s+", " ", str(value or "").strip()).casefold()


def parse_date(value):
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except (AttributeError, TypeError, ValueError):
        return None


def track_tier(track):
    """Classify by archive evidence; these are listening-history tiers, not ratings."""
    plays = max(1, int(track.get("plays") or 1))
    if plays >= FAVORITE_MIN_PLAYS:
        return "favorite"
    if plays >= KNOWN_MIN_PLAYS:
        return "rediscovery"
    return "deep_cut"


def score_track(track, today=None):
    """Balance recency, repeat-listening evidence, and room for discovery."""
    today = today or date.today()
    last = parse_date(track.get("last_scrobble"))
    days_since = max(0, (today - last).days) if last else 365
    plays = max(1, int(track.get("plays") or 1))

    # Recency saturates after a year. Repeated listening is a stronger positive
    # signal than before, but is bounded so one mega-hit cannot dominate.
    freshness = min(days_since / 365.0, 1.0)
    replay_signal = min(math.log1p(plays) / math.log1p(20), 1.0)

    # Give lightly explored tracks a modest discovery bonus without treating a
    # single scrobble as equal evidence to a repeatedly played favorite.
    if plays == 1:
        discovery = 1.0
    elif plays <= 4:
        discovery = 0.9
    elif plays <= 12:
        discovery = 0.75
    else:
        discovery = 0.6

    return round(0.38 * freshness + 0.47 * replay_signal + 0.15 * discovery, 8)


def _ranked_rows(tracks, today):
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
        row["_tier"] = track_tier(row)
        seed = f"{today.isoformat()}:{row.get('track_id', row['artist'] + '|' + row['track'])}"
        row["_tie"] = hashlib.sha256(seed.encode("utf-8")).hexdigest()
        valid.append(row)
    valid.sort(key=lambda x: (-x["_score"], x["_tie"], norm(x["artist"]), norm(x["track"])))
    return valid


def rank_candidates(tracks, today=None, limit=TARGET_SIZE):
    """Return a balanced, deterministic mix with a strict two-track artist cap."""
    today = today or date.today()
    ranked = _ranked_rows(tracks, today)
    if limit <= 0:
        return []

    quotas = {
        "favorite": int(limit * 0.40),
        "rediscovery": int(limit * 0.40),
    }
    quotas["deep_cut"] = limit - sum(quotas.values())

    selected, artist_counts, tier_counts = [], {}, {key: 0 for key in ("favorite", "rediscovery", "deep_cut")}

    def take(rows, tier=None):
        for row in rows:
            if len(selected) >= limit:
                break
            artist = norm(row["artist"])
            row_tier = row["_tier"]
            if row in selected or artist_counts.get(artist, 0) >= 2:
                continue
            if tier and tier_counts[row_tier] >= quotas[tier]:
                continue
            selected.append(row)
            artist_counts[artist] = artist_counts.get(artist, 0) + 1
            tier_counts[row_tier] += 1

    for tier in ("favorite", "rediscovery", "deep_cut"):
        take((row for row in ranked if row["_tier"] == tier), tier=tier)

    # If a tier is sparse or artist diversity prevents filling its quota, use
    # the strongest remaining candidates from any tier to complete the pool.
    take(ranked)

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
            "score": candidate.get("_score", score_track(candidate)),
            "tier": candidate.get("_tier", track_tier(candidate)),
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
