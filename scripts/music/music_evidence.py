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

# FILE OVERVIEW
# Purpose: Shared confidence rules for identity resolution and individual metadata fields.
# Inputs: Exact lookup method or per-field source-family/value evidence.
# Outputs: Categorical confidence and explicit corroboration/conflict reasons.
# Safety: Community tag counts and contextual album/artist evidence never manufacture track identity or acoustic evidence.
# Related: scripts/music/music_library.py; tests/test_music_evidence.py; docs/ALBUM_METADATA_AND_LOOKUP_CONFIDENCE.md.
