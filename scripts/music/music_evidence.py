#!/usr/bin/env python3
"""Explainable identity and field-level metadata confidence for The Library."""
import re

def _normal(value):
    return re.sub(r"\s+", " ", str(value or "").strip()).casefold()

def identity_confidence(matched_by, identity=None, ambiguous=False):
    """Return a conservative category, never a probability."""
    if ambiguous or not matched_by: return "unknown"
    if matched_by in {"spotify_track_id", "musicbrainz_recording_mbid", "isrc", "verified_release_track_position"}:
        return "high"
    if matched_by in {"exact_artist_title_album", "unique_exact_artist_title"}: return "medium"
    if matched_by == "source_track_id": return "low"
    quality = (identity or {}).get("identity_quality", "")
    return "low" if quality in {"source_track_id", "fallback_artist_title", "fallback_release_context"} else "unknown"

def metadata_confidence(evidence, conflicts=None):
    """Assess one metadata field; duplicate observations from one family count once.

    Each item needs source_family and value. authoritative=True is reserved for
    a source authoritative for that particular field, not merely a well-known API.
    """
    rows = [row for row in (evidence or []) if isinstance(row, dict)
        and row.get("source_family") and row.get("value") not in (None, "", [], {})]
    if conflicts:
        return {"confidence": "low", "source_families": sorted({str(x) for x in conflicts}), "reason": "conflicting values were retained"}
    if not rows:
        return {"confidence": "unknown", "source_families": [], "reason": "no field evidence"}
    families = sorted({str(row["source_family"]) for row in rows})
    values = {_normal(row.get("value")) for row in rows}
    if len(values) > 1:
        return {"confidence": "low", "source_families": families, "reason": "independent sources disagree"}
    if any(row.get("authoritative") for row in rows):
        return {"confidence": "high", "source_families": families, "reason": "supported by an authoritative field source"}
    if len(families) >= 2:
        return {"confidence": "high", "source_families": families, "reason": "corroborated by independent source families"}
    return {"confidence": "low", "source_families": families, "reason": "single source family; corroboration unavailable"}

def _tag_label(value):
    if isinstance(value, dict):
        return str(value.get("tag") or value.get("name") or "").strip()
    return str(value or "").strip()


def _source_family(label):
    value = str(label or "").casefold()
    if "musicbrainz" in value: return "musicbrainz_catalog"
    if "last.fm" in value or "lastfm" in value: return "lastfm_catalog"
    if "discogs" in value: return "discogs_catalog"
    if "spotify" in value: return "spotify_catalog"
    if "acousticbrainz" in value: return "acousticbrainz"
    if "essentia" in value: return "essentia"
    return ""


def track_metadata_confidence(row):
    """Build per-field confidence from source-attributed track metadata."""
    row = row if isinstance(row, dict) else {}
    by_tag = {}
    for field, family in (
        ("lastfm_tags", "lastfm_community"),
        ("musicbrainz_tags", "musicbrainz_community"),
        ("musicbrainz_genres", "musicbrainz_community"),
    ):
        values = row.get(field) or []
        if isinstance(values, (str, dict)):
            values = [values]
        for value in values:
            label = _tag_label(value)
            if label:
                by_tag.setdefault(label.casefold(), {"label": label, "evidence": []})
                by_tag[label.casefold()]["evidence"].append({"source_family": family, "value": label})
    result = {"track_tags": {
        item["label"]: metadata_confidence(item["evidence"])
        for item in by_tag.values()
    }}
    duration = row.get("duration_ms") or row.get("duration")
    family = _source_family(row.get("duration_source") or row.get("duration_provider"))
    if duration not in (None, "", 0) and family:
        result["duration"] = metadata_confidence([{"source_family": family, "value": duration}])
    release_date = row.get("release_date") or row.get("first_release_date")
    family = _source_family(row.get("release_date_source") or row.get("release_source"))
    if release_date and family:
        result["release_date"] = metadata_confidence([{"source_family": family, "value": release_date}])
    return result


def album_metadata_confidence(profile):
    """Assess release fields independently; album context never upgrades track confidence."""
    profile = profile if isinstance(profile, dict) else {}
    fields = {
        "tracklist": "lastfm_tracklist",
        "summary": "lastfm_summary",
        "artwork": "lastfm_artwork_url",
        "tags": "lastfm_tags",
    }
    result = {}
    for field, source_key in fields.items():
        value = profile.get(source_key)
        if value not in (None, "", [], {}):
            result[field] = metadata_confidence([{"source_family": "lastfm_catalog", "value": value}])
    return result

# FILE OVERVIEW
# Purpose: Shared confidence rules for identity resolution and individual metadata fields.
# Inputs: Exact lookup method or per-field source-family/value evidence.
# Outputs: Categorical confidence and explicit corroboration/conflict reasons.
# Safety: Community tag counts and contextual album/artist evidence never manufacture track identity or acoustic evidence.
# Related: scripts/music/music_library.py; tests/test_music_evidence.py; docs/ALBUM_METADATA_AND_LOOKUP_CONFIDENCE.md.

