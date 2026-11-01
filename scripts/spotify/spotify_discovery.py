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

import playlist_intelligence as intelligence

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


def lyric_theme_affinity(analysis, playlist_theme_counts):
    """Measure overlap with this playlist's observed lyric themes (0..1)."""
    candidate_themes = set((analysis or {}).get("themes") or {})
    total = sum(max(0, int(count or 0)) for count in (playlist_theme_counts or {}).values())
    if not candidate_themes or total <= 0:
        return 0.0
    shared = sum(max(0, int(count or 0)) for theme, count in playlist_theme_counts.items()
                 if theme in candidate_themes)
    return round(shared / total, 4)


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
    # A single high Last.fm match is weak evidence on its own. Aggregate
    # independent seed matches so artists related to several parts of the
    # user's taste outrank one-off results. This also prevents a large pile of
    # identical 1.00 scores from silently becoming an alphabetical artist list.
    found = {}
    max_seed_strength = max((math.log1p(int(row.get("plays") or 0)) for row in seeds), default=1.0) or 1.0
    for seed in seeds:
        seed_name = norm(seed["artist"])
        seed_plays = max(0, int(seed.get("plays") or 0))
        seed_strength = math.log1p(seed_plays) / max_seed_strength
        for similar in _lastfm_similar(seed, api_key):
            name = str(similar.get("name") or "").strip()
            if not name:
                continue
            try:
                match = float(similar.get("match") or 0)
            except (TypeError, ValueError):
                match = 0.0
            match = max(0.0, min(1.0, match))
            key = norm(name)
            if not key:
                continue
            evidence = found.setdefault(key, {
                "artist": name, "matches": {}, "seed_strength": 0.0,
            })
            # Count each seed once per similar artist, even if an API payload
            # contains duplicates. Keep the strongest match for that seed.
            previous = evidence["matches"].get(seed_name)
            if previous is None or match > previous:
                evidence["matches"][seed_name] = match
            evidence["seed_strength"] = max(evidence["seed_strength"], seed_strength)
        time.sleep(0.18)

    ranked = []
    for evidence in found.values():
        matches = list(evidence["matches"].values())
        if not matches:
            continue
        best = max(matches)
        mean = sum(matches) / len(matches)
        consensus = min(1.0, math.log1p(len(matches)) / math.log1p(5))
        # Keep this normalized score as the downstream taste-fit signal.
        # Raw best/mean scores remain visible for diagnostics in the preview.
        rank_score = 0.55 * best + 0.20 * mean + 0.15 * consensus + 0.10 * evidence["seed_strength"]
        ranked.append({
            "artist": evidence["artist"],
            "similarity": max(0.0, min(1.0, rank_score)),
            "raw_similarity": best,
            "mean_similarity": mean,
            "supporting_seeds": len(matches),
            "seed_strength": evidence["seed_strength"],
        })
    return sorted(
        ranked,
        key=lambda row: (
            -row["similarity"], -row["supporting_seeds"],
            -row["raw_similarity"], norm(row["artist"]),
        ),
    )[:DISCOVERY_ARTISTS]


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


def load_playlist_feedback(playlist_items, playlist_id, path=Path("playlist_removed_tracks.json")):
    """Build playlist-scoped positive/negative taste evidence.

    A removed track currently present in this same playlist is whitelisted:
    its old removal is ignored and its artist contributes positive evidence.
    """
    current_uris = set()
    current_keys = set()
    positive_artists = defaultdict(int)
    for row in playlist_items:
        if not isinstance(row, dict):
            continue
        uri = row.get("uri")
        if isinstance(uri, str):
            current_uris.add(uri)
        artists = row.get("artists") or []
        artist = artists[0] if artists else row.get("artist", "")
        name = row.get("name") or row.get("track", "")
        if artist and name:
            current_keys.add(track_key(artist, name))
        if artist:
            positive_artists[norm(artist)] += 1

    removed = []
    whitelisted_count = 0
    if path.is_file() and playlist_id:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            records = (payload.get("playlists") or {}).get(playlist_id, {}).get("removed") or []
            for row in records:
                if not isinstance(row, dict):
                    continue
                uri = row.get("uri")
                artists = row.get("artists") or []
                artist = artists[0] if artists else row.get("artist", "")
                name = row.get("name") or row.get("track", "")
                key = track_key(artist, name) if artist and name else ""
                if (uri and uri in current_uris) or (key and key in current_keys):
                    whitelisted_count += 1
                    continue
                if artist or name or uri:
                    removed.append({
                        "uri": uri, "key": key, "artist": norm(artist),
                        "name": norm(name),
                    })
        except (OSError, ValueError, TypeError):
            # Feedback is optional; malformed history must not break discovery.
            removed = []
            whitelisted_count = 0

    daily_evidence = {}
    daily_path = Path("assistant_data/spotify/daily_feedback.json")
    if daily_path.is_file():
        try:
            daily_payload = json.loads(daily_path.read_text(encoding="utf-8"))
            for uri, record in (daily_payload.get("tracks") or {}).items():
                liked_rows = record.get("liked_observations") or []
                playback_rows = record.get("playback_observations") or []
                latest_liked = liked_rows[-1].get("liked") if liked_rows else None
                measured_plays = sum(int(row.get("plays") or 0) for row in playback_rows) if playback_rows else None
                daily_evidence[uri] = {
                    "liked": latest_liked,
                    "liked_at_add": record.get("liked_at_add"),
                    "removal_count": len(record.get("removal_events") or []),
                    "measured_plays": measured_plays,
                    "lastfm_plays": record.get("lastfm_post_add_scrobbles"),
                }
        except (OSError, ValueError, TypeError):
            daily_evidence = {}

    negative_artists = defaultdict(int)
    negative_keys = set()
    negative_uris = set()
    for row in removed:
        if row["artist"]:
            negative_artists[row["artist"]] += 1
        if row["key"]:
            negative_keys.add(row["key"])
        if row["uri"]:
            negative_uris.add(row["uri"])
    return {
        "current_uris": current_uris,
        "current_keys": current_keys,
        "positive_artists": positive_artists,
        "negative_artists": negative_artists,
        "negative_keys": negative_keys,
        "negative_uris": negative_uris,
        "whitelisted_count": whitelisted_count,
        "removed_count": len(removed),
        "daily_evidence": daily_evidence,
    }

def candidate_score(track, similarity, familiarity, liked, today=None, feedback=None):
    today = today or date.today()
    artist = (track.get("artists") or [{}])[0].get("name", "")
    name = track.get("name", "")
    known = familiarity.get(track_key(artist, name), {})
    plays = int(known.get("plays") or 0)
    penalty = familiarity_penalty(plays, known.get("last_scrobble"), today)
    uri = track.get("uri")
    is_liked = track_key(artist, name) in liked or (uri and uri in liked)
    # Playlist-local feedback is deliberately separate from global Last.fm taste.
    # A removed track/artist is a soft negative, never a global blacklist.
    feedback = feedback or {}
    daily = feedback.get("daily_evidence", {}).get(uri, {})
    removed_exact = track_key(artist, name) in feedback.get("negative_keys", set())
    removed_uri = uri in feedback.get("negative_uris", set())
    # A Daily removal is not negative evidence unless meaningful listening exposure was observed.
    if daily and daily.get("removal_count"):
        observed_exposure = daily.get("measured_plays")
        if observed_exposure is None:
            observed_exposure = daily.get("lastfm_plays")
        if observed_exposure is None or observed_exposure == 0:
            removed_exact = False
            removed_uri = False
    removed_artist_count = feedback.get("negative_artists", {}).get(norm(artist), 0)
    positive_artist_count = feedback.get("positive_artists", {}).get(norm(artist), 0)
    weights = intelligence.scoring_config()["weights"]
    feedback_penalty = min(
        weights["negative_cap"],
        (weights["exact_removal"] if removed_exact or removed_uri else 0.0)
        + min(removed_artist_count, weights["artist_removal_cap"]) * weights["artist_removal"],
    )
    feedback_bonus = min(weights["positive_cap"], positive_artist_count * weights["positive_artist"])
    post_add_saved = daily.get("liked") is True and daily.get("liked_at_add") is False
    if post_add_saved:
        feedback_bonus += 0.06
    if daily.get("measured_plays") is not None and daily.get("measured_plays") > 0:
        feedback_bonus += min(0.08, 0.025 * math.log1p(daily["measured_plays"]))
    if daily.get("lastfm_plays") is not None and daily.get("lastfm_plays") > 0:
        feedback_bonus += min(0.025, 0.008 * math.log1p(daily["lastfm_plays"]))
    # Spotify removed the popularity field from some Development Mode API
    # responses in 2026. Do not interpret a missing field as popularity zero.
    score = weights["similarity"] * similarity + weights["familiarity"] * (1.0 - penalty) - feedback_penalty + feedback_bonus
    if is_liked and not post_add_saved:
        score -= weights["liked_penalty"]
    return score, plays, known.get("last_scrobble"), is_liked


def build_discovery_recommendations(
    sp, playlist_items, today=None, profiles_path=PROFILES,
    features_path=FEATURES, api_key=None, target_size=TARGET_SIZE,
    similar_artist_rows=None, liked_keys=None, playlist_id=None,
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
    feedback = load_playlist_feedback(playlist_items, playlist_id)
    # Include manually analyzed songs from the committed theme export and the
    # private local DB, even when they are not part of the Last.fm archive.
    track_metadata = intelligence.track_metadata_index()
    playlist_lyric_profile = intelligence.playlist_track_metadata(playlist_items, track_metadata)
    playlist_theme_counts = {
        row["tag"]: row["track_count"] for row in playlist_lyric_profile.get("lyric_themes", [])
    }
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
                track, artist_row["similarity"], familiarity, liked_keys, today, feedback
            )
            lyric_analysis = (track_metadata.get((intelligence.track_norm(artist), intelligence.track_norm(track["name"])), {}) or {}).get("lyric_analysis") or {}
            theme_affinity = lyric_theme_affinity(lyric_analysis, playlist_theme_counts)
            # Small, explainable tie-break/boost: Last.fm similarity remains the
            # dominant signal, while lyrical fit helps distinguish candidates.
            score += 0.06 * theme_affinity
            row = {
                "uri": uri, "artist": artist, "track": track["name"],
                "plays": plays, "last_scrobble": last, "score": round(score, 6),
                "lyric_theme_affinity": theme_affinity,
                "lyric_themes": sorted((lyric_analysis.get("themes") or {}).keys()),
                "lyric_horror_relevance": lyric_analysis.get("horror_relevance"),
                "lyric_assessment": lyric_analysis.get("assessment"),
                "lyric_source_count": lyric_analysis.get("source_count", 0),
                "similarity": artist_row["similarity"],
                "supporting_seeds": artist_row.get("supporting_seeds", 0),
                "liked": is_liked,
                "tier": "discovery" if plays == 0 else ("rediscovery" if plays <= 2 else "familiar"),
                "popularity": track.get("popularity"),
                "positive_artist_count": feedback.get("positive_artists", {}).get(norm(artist), 0),
                "removed_artist_count": feedback.get("negative_artists", {}).get(norm(artist), 0),
                "removed_exact": key in feedback.get("negative_keys", set()) or uri in feedback.get("negative_uris", set()),
            }
            row["confidence"] = intelligence.recommendation_confidence(
                row["similarity"], row["supporting_seeds"]
            )
            row["why"] = intelligence.recommendation_reasons(row)
            if theme_affinity >= 0.2:
                row["why"].insert(0, "lyrics share themes with this playlist")
                row["why"] = row["why"][:4]
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


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Discovery-first Spotify curator using Last.fm similarity + Spotify catalogue search. The scrobble archive is a taste/familiarity model, never the candidate catalogue. No archive track is hard-excluded: prior plays and recency progressively reduce its rank. Liked tracks receive a strong penalty but remain eligible.
# Location: Maintained implementation in scripts/spotify/spotify_discovery.py.
# Data flow: Uses the canonical archives and/or generated project data; consult
#            this module's configuration and command options for exact paths.
# Run: python compat/spotify_discovery.py (legacy command entry point, when applicable).
# Related: tests/ contains regression coverage; docs/ contains extended guides.
# -----------------------------------------------------------------------------
