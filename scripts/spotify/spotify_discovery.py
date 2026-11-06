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
# Prefer the maintained source module over its same-named compat launcher.
import sys
from pathlib import Path as _Path
_SOURCE_DIR = str(_Path.cwd() / "scripts" / "spotify")
if _SOURCE_DIR not in sys.path:
    sys.path.insert(0, _SOURCE_DIR)
import spotify_listening_trends as listening_trends

PROFILES = Path("assistant_data/music/artist_profiles.json")
FEATURES = Path("assistant_data/recommendations/track_features.json")
LASTFM_URL = "https://ws.audioscrobbler.com/2.0/"
TARGET_SIZE = 30
MIN_MATCHES = 20
SEED_ARTISTS = 24
SIMILAR_PER_SEED = 20
DISCOVERY_ARTISTS = 300
TRACKS_PER_ARTIST = 10


def norm(value):
    return re.sub(r"\s+", " ", str(value or "").strip()).casefold()


def track_key(artist, track):
    return norm(artist) + "|" + norm(track)


def is_playlist_candidate_blocked(artist, title, uri, feedback):
    """Block exact playlist removals unless explicitly whitelisted.

    Current membership is not approval: automation may have re-added a rejected
    candidate. Artist-level removals remain soft ranking evidence.
    """
    feedback = feedback or {}
    return (
        track_key(artist, title) in feedback.get("negative_keys", set())
        or (uri and uri in feedback.get("negative_uris", set()))
    )


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


def spotify_artist_tracks(sp, artist, limit=TRACKS_PER_ARTIST, offset=0):
    """Search Spotify with bounded retries for transient transport/server errors.

    Authentication, permission and rate-limit responses are not retried here:
    the manager owns token refresh and Spotify's Retry-After cooldown policy.
    """
    query = f'artist:"{artist}"'
    endpoint = "/search?" + urllib.parse.urlencode({
        "type": "track", "limit": limit, "offset": offset, "q": query,
    })
    for attempt in range(3):
        try:
            response = sp.call("GET", endpoint)
            return ((response or {}).get("tracks") or {}).get("items") or []
        except Exception as error:
            message = str(error)
            if any(code in message for code in ("HTTP 401", "HTTP 403", "HTTP 429")):
                raise
            transient = (
                any(code in message for code in ("HTTP 500", "HTTP 502", "HTTP 503", "HTTP 504"))
                or isinstance(error, (TimeoutError, ConnectionError, urllib.error.URLError))
            )
            if not transient or attempt == 2:
                raise
            time.sleep(2 ** attempt)
    return []


DAILY_PLAYLIST_ID = "4yUVHSMQySfWeEowfIMcx7"


def reconcile_daily_manual_removals(
    playlist_items,
    cycle_marker,
    baseline_path=Path("playlist_removal_baseline.json"),
    blacklist_path=Path("playlist_removed_tracks.json"),
    detected_at=None,
):
    """Persist exact manual removals since the last accepted Daily cycle.

    The baseline is trusted only when its marker matches the last accepted
    cycle. This prevents stale historical snapshots from being mistaken for
    current user removals after a failed or interrupted rotation.
    """
    if not cycle_marker or not baseline_path.is_file():
        return {"status": "skipped", "reason": "missing_cycle_marker_or_baseline", "newly_removed": 0}
    try:
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        if not isinstance(baseline, dict) or not isinstance(baseline.get("playlists"), dict):
            raise ValueError("invalid playlist removal baseline schema")
        if baseline.get("daily_cycle_marker") != cycle_marker:
            return {"status": "skipped", "reason": "baseline_not_aligned", "newly_removed": 0}
        previous = baseline["playlists"].get(DAILY_PLAYLIST_ID)
        if not isinstance(previous, list):
            raise ValueError("Daily removal baseline is missing or invalid")
        blacklist = json.loads(blacklist_path.read_text(encoding="utf-8")) if blacklist_path.is_file() else {"version": 1, "playlists": {}}
        if not isinstance(blacklist, dict) or not isinstance(blacklist.get("playlists", {}), dict):
            raise ValueError("invalid playlist removal blacklist schema")
        daily = blacklist.setdefault("playlists", {}).setdefault(
            DAILY_PLAYLIST_ID, {"name": "Tricky Daily", "removed": [], "whitelisted": []}
        )
        if not isinstance(daily, dict):
            raise ValueError("invalid Tricky Daily blacklist entry")
        removed_rows = daily.setdefault("removed", [])
        whitelist_rows = daily.setdefault("whitelisted", [])
        if not isinstance(removed_rows, list) or not isinstance(whitelist_rows, list):
            raise ValueError("Daily removed/whitelisted values must be lists")
        current_uris = {
            row.get("uri") for row in playlist_items
            if isinstance(row, dict) and isinstance(row.get("uri"), str)
        }
        whitelist_uris = {
            row.get("uri") for row in whitelist_rows
            if isinstance(row, dict) and row.get("uri")
        }
        whitelist_keys = set()
        for row in whitelist_rows:
            if not isinstance(row, dict):
                continue
            artists = row.get("artists") or []
            artist = artists[0] if artists else row.get("artist", "")
            name = row.get("name") or row.get("track", "")
            if artist and name:
                whitelist_keys.add(track_key(artist, name))
        existing_uris = {row.get("uri") for row in removed_rows if isinstance(row, dict)}
        existing_keys = set()
        for row in removed_rows:
            if not isinstance(row, dict):
                continue
            artists = row.get("artists") or []
            artist = artists[0] if artists else row.get("artist", "")
            name = row.get("name") or row.get("track", "")
            if artist and name:
                existing_keys.add(track_key(artist, name))
        detected_at = detected_at or datetime.now().astimezone().isoformat()
        newly_removed = []
        for row in previous:
            if not isinstance(row, dict):
                raise ValueError("invalid row in Daily removal baseline")
            uri = row.get("uri")
            if not isinstance(uri, str) or not uri.startswith("spotify:track:") or uri in current_uris:
                continue
            artists = row.get("artists") or []
            artist = artists[0] if artists else row.get("artist", "")
            name = row.get("name") or row.get("track", "")
            key = track_key(artist, name) if artist and name else ""
            if uri in whitelist_uris or (key and key in whitelist_keys):
                continue
            if uri in existing_uris or (key and key in existing_keys):
                continue
            entry = {
                "uri": uri, "name": name, "artists": artists or ([artist] if artist else []),
                "album": row.get("album") or "",
                "source": "manual removal detected by Tricky Daily live reconciliation",
                "detected_at": detected_at, "last_present_cycle": cycle_marker,
            }
            removed_rows.append(entry)
            newly_removed.append(entry)
            existing_uris.add(uri)
            if key:
                existing_keys.add(key)
        if newly_removed:
            temp = blacklist_path.with_suffix(blacklist_path.suffix + ".tmp")
            temp.write_text(json.dumps(blacklist, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            temp.replace(blacklist_path)
        return {
            "status": "checked", "reason": "baseline_aligned",
            "newly_removed": len(newly_removed), "removed_total": len(removed_rows),
            "whitelist_count": len(whitelist_rows),
        }
    except (OSError, ValueError, TypeError) as error:
        raise RuntimeError(
            "Tricky Daily removal reconciliation failed closed; refusing to generate "
            "recommendations from an unreadable baseline or blacklist."
        ) from error


def write_daily_removal_baseline(
    playlist_items,
    cycle_marker,
    baseline_path=Path("playlist_removal_baseline.json"),
):
    """Save the exact accepted Daily contents as the next removal-detection baseline."""
    if not cycle_marker:
        raise ValueError("A Daily cycle marker is required for the removal baseline.")
    baseline = json.loads(baseline_path.read_text(encoding="utf-8")) if baseline_path.is_file() else {"version": 1, "playlists": {}}
    if not isinstance(baseline, dict) or not isinstance(baseline.get("playlists", {}), dict):
        raise ValueError("Daily playlist removal baseline is malformed.")
    baseline.setdefault("playlists", {})[DAILY_PLAYLIST_ID] = [
        {
            "uri": row.get("uri"), "name": row.get("name") or row.get("track"),
            "artists": row.get("artists") or ([row.get("artist")] if row.get("artist") else []),
            "album": row.get("album") or "",
        }
        for row in playlist_items
        if isinstance(row, dict) and isinstance(row.get("uri"), str)
    ]
    baseline["daily_cycle_marker"] = cycle_marker
    baseline["daily_cycle_playlist_id"] = DAILY_PLAYLIST_ID
    temp = baseline_path.with_suffix(baseline_path.suffix + ".tmp")
    temp.write_text(json.dumps(baseline, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.replace(baseline_path)
    return len(baseline["playlists"][DAILY_PLAYLIST_ID])


def load_playlist_feedback(playlist_items, playlist_id, path=Path("playlist_removed_tracks.json")):
    """Build playlist-scoped evidence; only explicit whitelist records clear removals.

    Presence in the playlist is deliberately not treated as approval because
    automated workflows can re-add their own previously rejected candidates.
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
            playlist_feedback = (payload.get("playlists") or {}).get(playlist_id, {})
            if not isinstance(payload, dict) or not isinstance(payload.get("playlists", {}), dict):
                raise ValueError("invalid playlist removal feedback schema")
            if not isinstance(playlist_feedback, dict):
                raise ValueError("invalid playlist feedback entry")
            whitelist_rows = playlist_feedback.get("whitelisted") or []
            records = playlist_feedback.get("removed") or []
            if not isinstance(whitelist_rows, list) or not isinstance(records, list):
                raise ValueError("removed/whitelisted feedback must be lists")
            # An explicit whitelist is positive, playlist-local evidence. It is
            # stronger than mere artist representation and can clear only the
            # matching removal identity.
            whitelist_uris = {
                row.get("uri") for row in whitelist_rows
                if isinstance(row, dict) and row.get("uri")
            }
            whitelist_keys = set()
            for row in whitelist_rows:
                if not isinstance(row, dict):
                    continue
                artists = row.get("artists") or []
                artist = artists[0] if artists else row.get("artist", "")
                name = row.get("name") or row.get("track", "")
                if artist and name:
                    whitelist_keys.add(track_key(artist, name))
            for row in records:
                if not isinstance(row, dict):
                    continue
                uri = row.get("uri")
                artists = row.get("artists") or []
                artist = artists[0] if artists else row.get("artist", "")
                name = row.get("name") or row.get("track", "")
                key = track_key(artist, name) if artist and name else ""
                if (uri and uri in whitelist_uris) or (key and key in whitelist_keys):
                    whitelisted_count += 1
                    continue
                if artist or name or uri:
                    removed.append({
                        "uri": uri, "key": key, "artist": norm(artist),
                        "name": norm(name),
                    })
        except (OSError, ValueError, TypeError) as error:
            # Never silently disable the blacklist because its source is corrupt.
            raise RuntimeError(
                f"Playlist removal feedback is unreadable or invalid ({path}); "
                "recommendation generation stopped rather than ignoring exclusions."
            ) from error

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
        "positive_keys": whitelist_keys if path.is_file() and playlist_id else set(),
        "positive_uris": whitelist_uris if path.is_file() and playlist_id else set(),
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
    explicit_positive = (
        track_key(artist, name) in feedback.get("positive_keys", set())
        or (uri and uri in feedback.get("positive_uris", set()))
    )
    feedback_bonus = min(weights["positive_cap"], positive_artist_count * weights["positive_artist"])
    if explicit_positive:
        feedback_bonus += weights.get("exact_whitelist", 0.10)
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


def select_unique_artist_candidates(candidates, target_size=TARGET_SIZE, max_per_artist=1):
    """Select highest-ranked tracks with a configurable per-artist ceiling."""
    ranked = sorted(
        candidates,
        key=lambda row: (-row.get("score", 0), norm(row.get("artist")), norm(row.get("track"))),
    )
    selected, artist_counts = [], defaultdict(int)
    for row in ranked:
        if len(selected) >= target_size:
            break
        artist_key = norm(row.get("artist"))
        if not artist_key or artist_counts[artist_key] >= max_per_artist:
            continue
        selected.append(row)
        artist_counts[artist_key] += 1
    return selected


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
    # Daily receives user-wide momentum as a soft signal, never a fixed mood target.
    trends_report = {}
    trends_path = Path("assistant_data/spotify/listening_trends.json")
    is_daily = playlist_id == "4yUVHSMQySfWeEowfIMcx7"
    if is_daily and trends_path.is_file():
        try:
            trends_report = json.loads(trends_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            trends_report = {}
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

    def collect_artist_candidates(artist_rows, offset=0):
        """Search one Spotify catalogue page per artist and merge scored tracks."""
        for artist_row in artist_rows:
            artist = artist_row["artist"]
            try:
                items = spotify_artist_tracks(sp, artist, offset=offset)
            except Exception as error:
                if any(code in str(error) for code in ("HTTP 401", "HTTP 403", "HTTP 429")):
                    raise
                continue
            for track in items:
                artists = track.get("artists") or []
                if not track.get("name") or not artists or norm(artists[0].get("name")) != norm(artist):
                    continue
                uri = track.get("uri")
                if not isinstance(uri, str) or not uri.startswith("spotify:track:") or uri in existing_uris:
                    continue
                if is_playlist_candidate_blocked(artist, track["name"], uri, feedback):
                    continue
                key = track_key(artist, track["name"])
                score, plays, last, is_liked = candidate_score(
                    track, artist_row["similarity"], familiarity, liked_keys, today, feedback
                )
                lyric_analysis = (track_metadata.get((intelligence.track_norm(artist), intelligence.track_norm(track["name"])), {}) or {}).get("lyric_analysis") or {}
                theme_affinity = lyric_theme_affinity(lyric_analysis, playlist_theme_counts)
                trend_affinity, trend_confidence, trend_reasons = (
                    listening_trends.candidate_affinity(
                        artist, trends_report,
                        next((listening_trends.tags_of(profile) for profile in profiles.values()
                              if isinstance(profile, dict)
                              and norm(profile.get("artist") or profile.get("name")) == norm(artist)), []),
                    )
                    if is_daily and trends_report.get("coverage", {}).get("status") == "available"
                    else (0.0, "low", [])
                )
                if is_daily:
                    if trend_confidence in ("medium", "high"):
                        score += 0.03 * trend_affinity
                else:
                    score += 0.06 * theme_affinity
                row = {
                    "uri": uri, "artist": artist, "track": track["name"],
                    "plays": plays, "last_scrobble": last, "score": round(score, 6),
                    "lyric_theme_affinity": None if is_daily else theme_affinity,
                    "daily_trend_affinity": trend_affinity if is_daily else None,
                    "daily_trend_confidence": trend_confidence if is_daily else None,
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
                    "removed_exact": False,
                    "whitelisted": key in feedback.get("positive_keys", set()) or uri in feedback.get("positive_uris", set()),
                    "positive_exact": key in feedback.get("positive_keys", set()) or uri in feedback.get("positive_uris", set()),
                }
                row["confidence"] = intelligence.recommendation_confidence(
                    row["similarity"], row["supporting_seeds"]
                )
                row["why"] = intelligence.recommendation_reasons(row)
                if is_daily and trend_reasons:
                    row["why"].insert(0, trend_reasons[0])
                    row["why"] = row["why"][:4]
                elif not is_daily and theme_affinity >= 0.2:
                    row["why"].insert(0, "lyrics share themes with this playlist")
                    row["why"] = row["why"][:4]
                if uri not in candidates or row["score"] > candidates[uri]["score"]:
                    candidates[uri] = row
            time.sleep(0.08)

    collect_artist_candidates(similar, offset=0)
    fallback_used = False
    if is_daily:
        # Search progressively deeper Spotify result pages before relaxing
        # diversity. Each page is searched across the expanded artist pool.
        selected = select_unique_artist_candidates(candidates.values(), target_size)
        offset = TRACKS_PER_ARTIST
        while len(selected) < target_size and offset < 100:
            collect_artist_candidates(similar, offset=offset)
            selected = select_unique_artist_candidates(candidates.values(), target_size)
            offset += TRACKS_PER_ARTIST

        # If 60 distinct artists still cannot be found, keep the 60-track
        # rotation viable by relaxing the artist ceiling one step at a time.
        # Track URIs remain deduplicated and removed tracks remain blocked.
        if len(selected) < target_size:
            fallback_used = True
            max_per_artist = 2
            while len(selected) < target_size and max_per_artist <= target_size:
                selected = select_unique_artist_candidates(
                    candidates.values(), target_size, max_per_artist=max_per_artist
                )
                max_per_artist += 1
        required = target_size
    else:
        # Preserve the established general-discovery behavior for other playlists.
        selected = select_unique_artist_candidates(candidates.values(), target_size, max_per_artist=2)
        required = min(MIN_MATCHES, target_size)

    if len(selected) < required:
        raise RuntimeError(
            f"Only {len(selected)} discovery candidates were found; {required} are required. "
            "Playlist was not changed."
        )
    if fallback_used:
        for row in selected:
            row["artist_diversity_fallback"] = True
    return selected, []



if __name__ == "__main__":
    raise SystemExit("Run through spotify_playlist_cloud.py using the protected daily_preview command.")


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Build discovery-first Spotify candidates using Last.fm artist similarity and catalogue search.
# Inputs: Canonical Last.fm scrobbles, artist/track profiles, recommendation features,
#         Spotify saved-track/reference feedback and LASTFM_API_KEY.
# Outputs: Ranked candidate tracks with identity, score and seed evidence for protected
#          preview/cycle callers; updates local discovery baseline/blacklist state where required.
# Semantics: The scrobble archive models familiarity/taste, not the candidate catalogue.
#            Prior plays and recency reduce rank progressively; liked tracks receive a strong
#            penalty but remain eligible. Default target is 30; Tricky Daily passes 60 explicitly.
# Safety: Candidate/search logic only; live playlist writes belong to spotify_daily_cycle.py
#         or the separately confirmed playlist manager flow.
# Run: Invoked by spotify_daily_cycle.py and the protected spotify_playlist_cloud.py preview;
#      direct execution intentionally exits with guidance.
# Related: scripts/music/discovery_ingestion.py; spotify_daily_cycle.py;
#          docs/TRICKY_DAILY_CYCLE.md.
# -----------------------------------------------------------------------------
