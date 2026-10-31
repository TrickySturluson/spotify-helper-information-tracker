#!/usr/bin/env python3
"""Playlist-specific taste profiles, recommendation diagnostics, and health checks.

All outputs are derived from a single playlist snapshot plus public/local music
metadata. This module is intentionally read-only: it never edits Spotify.
"""
import json
from functools import lru_cache
import math
import mood_inference
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

SCORING_CONFIG = Path("assistant_data/recommendations/playlist_scoring.json")
ARTIST_PROFILES = Path("assistant_data/music/artist_profiles.json")
TRACK_PROFILES = Path("assistant_data/music/track_profiles.json")
SCHEMA_VERSION = 1

DEFAULT_SCORING = {
    "version": 1,
    "weights": {
        "similarity": 0.58,
        "familiarity": 0.30,
        "exact_removal": 0.18,
        "artist_removal": 0.035,
        "artist_removal_cap": 4,
        "negative_cap": 0.32,
        "positive_artist": 0.015,
        "positive_cap": 0.12,
        "liked_penalty": 0.62
    },
    "confidence": {
        "strong_similarity": 0.78,
        "strong_seed_support": 3,
        "promising_similarity": 0.62,
        "promising_seed_support": 2
    }
}


def norm(value):
    return re.sub(r"\\s+", " ", str(value or "").strip()).casefold()


def read_json(path, fallback):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return fallback


@lru_cache(maxsize=8)
def scoring_config(path=SCORING_CONFIG):
    data = read_json(path, {})
    if not isinstance(data, dict) or not isinstance(data.get("weights"), dict):
        return DEFAULT_SCORING
    merged = json.loads(json.dumps(DEFAULT_SCORING))
    merged["version"] = int(data.get("version") or 1)
    merged["weights"].update(data["weights"])
    if isinstance(data.get("confidence"), dict):
        merged["confidence"].update(data["confidence"])
    return merged


def artist_metadata_index(path=ARTIST_PROFILES):
    rows = read_json(path, {})
    result = {}
    if isinstance(rows, dict):
        for row in rows.values():
            if isinstance(row, dict) and row.get("artist"):
                result[norm(row["artist"])] = row
    return result


def track_metadata_index(path=TRACK_PROFILES):
    """Index sourced track profiles by exact normalized primary-artist/title pair."""
    rows = read_json(path, {})
    result = {}
    if isinstance(rows, dict):
        for row in rows.values():
            if isinstance(row, dict) and row.get("artist") and row.get("track"):
                result[(norm(row["artist"]), norm(row["track"]))] = row
    return result


def playlist_track_metadata(items, track_profiles):
    """Aggregate only exact track-level metadata; never substitute artist tags."""
    moods, genres, tags = Counter(), Counter(), Counter()
    matched = 0
    for item in items or []:
        if not isinstance(item, dict):
            continue
        names = item.get("artists") or ([item.get("artist")] if item.get("artist") else [])
        title = item.get("name") or item.get("track")
        if not names or not names[0] or not title:
            continue
        profile = track_profiles.get((norm(names[0]), norm(title)))
        if not profile:
            continue
        matched += 1
        names_seen = set()
        for row in (profile.get("lastfm_tags", []) + profile.get("musicbrainz_tags", []) + profile.get("musicbrainz_genres", [])):
            tag = row.get("tag", "") if isinstance(row, dict) else str(row)
            if tag:
                tags[tag] += 1
                for mood in mood_inference._tag_moods(tag):
                    names_seen.add(mood)
        for mood in names_seen:
            moods[mood] += 1
        for row in profile.get("musicbrainz_genres", []):
            if row.get("tag"):
                genres[norm(row["tag"])] += 1
    total = len(items or [])
    return {
        "matched_tracks": matched,
        "total_tracks": total,
        "coverage": round(matched / max(1, total), 4),
        "moods": [{"tag": key, "track_count": count} for key, count in moods.most_common(12)],
        "genres": [{"tag": key, "track_count": count} for key, count in genres.most_common(12)],
        "tags": [{"tag": key, "track_count": count} for key, count in tags.most_common(20)],
        "method": "exact normalized primary-artist + track-title match; track-sourced tags only",
    }


def artist_metadata_coverage(items, artist_profiles):
    """Track-weighted artist-profile coverage with explicit missing/empty distinctions."""
    counts = {"tagged": 0, "profile_without_tags": 0, "missing_profile": 0}
    for item in items or []:
        if not isinstance(item, dict):
            counts["missing_profile"] += 1
            continue
        names = item.get("artists") or ([item.get("artist")] if item.get("artist") else [])
        if not names or not names[0]:
            counts["missing_profile"] += 1
            continue
        profile = artist_profiles.get(norm(names[0]))
        if not profile:
            counts["missing_profile"] += 1
        elif profile.get("tags"):
            counts["tagged"] += 1
        else:
            counts["profile_without_tags"] += 1
    total = sum(counts.values())
    return {
        **counts,
        "total_items": total,
        "tagged_item_coverage": round(counts["tagged"] / max(1, total), 4),
        "any_profile_item_coverage": round((counts["tagged"] + counts["profile_without_tags"]) / max(1, total), 4),
    }


def build_playlist_profile(items, feedback=None, artist_profiles=None, track_profiles=None):
    """Summarize a playlist's identity using current membership, not global taste."""
    feedback = feedback or {}
    artist_profiles = artist_profiles if artist_profiles is not None else artist_metadata_index()
    track_profiles = track_profiles if track_profiles is not None else track_metadata_index()
    track_metadata = playlist_track_metadata(items, track_profiles)
    artists = Counter()
    artist_labels = {}
    genres, moods, themes = Counter(), Counter(), Counter()
    for item in items or []:
        if not isinstance(item, dict):
            continue
        names = item.get("artists") or ([item.get("artist")] if item.get("artist") else [])
        if not names:
            continue
        primary = names[0]
        artist_key = norm(primary)
        artists[artist_key] += 1
        artist_labels.setdefault(artist_key, str(primary))
        metadata = artist_profiles.get(artist_key, {})
        for field, counter in (("genres", genres), ("moods", moods), ("themes", themes)):
            counter.update(norm(value) for value in metadata.get(field, []) if value)
    total = sum(artists.values())
    inferred_moods = mood_inference.infer_mood_profile(items, artist_profiles)
    sound_tags = mood_inference.infer_sound_tag_profile(items, artist_profiles)
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "track_count": len(items or []),
        "artist_count": len(artists),
        "top_artists": [{"artist": artist_labels[key], "tracks": count, "share": round(count / total, 4) if total else 0}
                        for key, count in artists.most_common(10)],
        "genres": [{"tag": key, "count": count} for key, count in genres.most_common(12)],
        "moods": [
            {"tag": row["mood"], "count": row["artist_support"],
             "confidence": row["confidence"], "evidence": row["evidence"]}
            for row in inferred_moods["moods"]
        ],
        "mood_inference": inferred_moods,
        "artist_moods": [{"tag": row["mood"], "artist_count": row["artist_support"], "confidence": row["confidence"]} for row in inferred_moods["moods"]],
        "track_metadata": track_metadata,
        "track_moods": track_metadata["moods"],
        "sound_tags": sound_tags,
        "themes": [{"tag": key, "count": count} for key, count in themes.most_common(10)],
        "positive_artist_evidence": sum((feedback.get("positive_artists") or {}).values()),
        "negative_track_evidence": feedback.get("removed_count", 0),
        "whitelisted_tracks": feedback.get("whitelisted_count", 0),
        "metadata_coverage": artist_metadata_coverage(items, artist_profiles)["tagged_item_coverage"],
        "metadata_coverage_detail": artist_metadata_coverage(items, artist_profiles)
    }


def recommendation_confidence(similarity, supporting_seeds=0, wildcard=False, config=None):
    cfg = (config or scoring_config())["confidence"]
    if wildcard or (similarity < cfg["promising_similarity"] and supporting_seeds < cfg["promising_seed_support"]):
        return "wildcard"
    if similarity >= cfg["strong_similarity"] and supporting_seeds >= cfg["strong_seed_support"]:
        return "strong fit"
    return "promising"


def recommendation_reasons(row):
    reasons = []
    if row.get("supporting_seeds"):
        reasons.append(f"similarity supported by {row['supporting_seeds']} seed artist(s)")
    if row.get("positive_artist_count"):
        reasons.append("artist already represented in this playlist")
    if row.get("removed_artist_count"):
        reasons.append("artist has appeared in this playlist's removal history")
    if row.get("removed_exact"):
        reasons.append("this exact track was previously removed")
    if row.get("whitelisted"):
        reasons.append("re-added track is whitelisted by current membership")
    if row.get("plays", 0) == 0:
        reasons.append("unheard in the Last.fm archive")
    elif row.get("plays", 0) <= 2:
        reasons.append("lightly heard in the Last.fm archive")
    else:
        reasons.append("familiarity penalty applied using play count and recency")
    if row.get("liked"):
        reasons.append("already Liked; strong ranking penalty applied")
    return reasons[:4]


def playlist_health(items, feedback=None, artist_profiles=None, track_profiles=None):
    feedback = feedback or {}
    artist_profiles = artist_profiles if artist_profiles is not None else artist_metadata_index()
    track_profiles = track_profiles if track_profiles is not None else track_metadata_index()
    track_metadata = playlist_track_metadata(items, track_profiles)
    uris, artist_counts = Counter(), Counter()
    missing_uri, non_track = 0, 0
    for item in items or []:
        if not isinstance(item, dict):
            continue
        uri = item.get("uri")
        if not uri:
            missing_uri += 1
        elif uri.startswith("spotify:track:"):
            uris[uri] += 1
        else:
            non_track += 1
        names = item.get("artists") or ([item.get("artist")] if item.get("artist") else [])
        if names and names[0]:
            artist_counts[norm(names[0])] += 1
    duplicates = [{"uri": uri, "count": count, "surplus": count - 1}
                  for uri, count in uris.items() if count > 1]
    total = len(items or [])
    top = artist_counts.most_common(5)
    return {
        "track_count": total,
        "unique_track_uris": len(uris),
        "duplicate_uri_groups": duplicates,
        "surplus_duplicates": sum(row["surplus"] for row in duplicates),
        "missing_uri_items": missing_uri,
        "non_track_items": non_track,
        "unique_primary_artists": len(artist_counts),
        "top_artists": [{"artist": artist, "tracks": count,
                         "share": round(count / max(1, total), 4)} for artist, count in top],
        "top_artist_share": round(top[0][1] / max(1, total), 4) if top else 0,
        "artist_metadata_coverage": artist_metadata_coverage(items, artist_profiles)["tagged_item_coverage"],
        "artist_metadata_coverage_detail": artist_metadata_coverage(items, artist_profiles),
        "track_metadata_coverage": track_metadata["coverage"],
        "track_metadata_matched": track_metadata["matched_tracks"],
        "removal_feedback_count": feedback.get("removed_count", 0),
        "whitelisted_count": feedback.get("whitelisted_count", 0),
    }
