#!/usr/bin/env python3
"""Evidence-aware, read-only playlist-fit scoring across five independent axes.

Input is normalized track evidence, not human slider ratings. This module does
not call Spotify, write playlists, or read the exploratory human-rating file.
"""
from __future__ import annotations

from collections import Counter
from statistics import mean, pstdev
from typing import Any

MODEL_VERSION = "five-axis-fit-v0.2"
DIMENSIONS = ("genre", "sound", "energy", "mood", "theme")
DEFAULT_WEIGHTS = {
    "genre": 0.15, "sound": 0.25, "energy": 0.20,
    "mood": 0.25, "theme": 0.15,
}
SCOPE_WEIGHT = {"recording": 1.0, "lyrics": 1.0, "audio": 1.0,
                "release": 0.35, "artist": 0.15}
CONFIDENCE_RANK = {"unknown": 0, "low": 1, "medium": 2, "high": 3}


def _identity(track: dict) -> str:
    return str(track.get("uri") or track.get("recording_mbid") or
               f"{track.get('artist', '').casefold()}|{track.get('title', '').casefold()}")


def _observations(track: dict, dimension: str) -> list[dict]:
    dims = track.get("dimensions") or {}
    rows = dims.get(dimension) or []
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict) and row.get("value") not in (None, "", [])]


def _valid_observation(row: dict) -> bool:
    return (row.get("scope") in SCOPE_WEIGHT and
            bool(row.get("source_family")) and
            row.get("identity_confidence", "unknown") in CONFIDENCE_RANK)


def _usable(rows: list[dict], *, allow_context: bool = True) -> list[dict]:
    result = []
    for row in rows:
        if not _valid_observation(row):
            continue
        if not allow_context and row["scope"] not in {"recording", "lyrics", "audio"}:
            continue
        if CONFIDENCE_RANK.get(row.get("identity_confidence", "unknown"), 0) == 0:
            continue
        result.append(row)
    return result


def _tokens(rows: list[dict]) -> set[str]:
    values = set()
    for row in rows:
        raw = row.get("value")
        parts = raw if isinstance(raw, list) else [raw]
        for part in parts:
            value = " ".join(str(part).casefold().strip().split())
            if value:
                values.add(value)
    return values


def _weighted_scope(row: dict) -> float:
    return SCOPE_WEIGHT[row["scope"]]


def build_reference_profile(
    tracks: list[dict],
    *,
    candidate_uri: str | None = None,
    heldout_uris: set[str] | None = None,
) -> dict:
    """Build one target profile, excluding candidate and held-out batch members."""
    heldout = {str(x) for x in (heldout_uris or set())}
    excluded = heldout | ({str(candidate_uri)} if candidate_uri else set())
    included = [t for t in tracks if isinstance(t, dict) and _identity(t) not in excluded]
    dimensions = {}
    for dim in DIMENSIONS:
        if dim == "energy":
            values, families = [], set()
            for track in included:
                rows = _usable(_observations(track, dim), allow_context=False)
                by_family = {}
                for row in rows:
                    try:
                        value = float(row["value"])
                    except (TypeError, ValueError):
                        continue
                    if 0 <= value <= 100:
                        by_family.setdefault(row["source_family"], []).append(value)
                for family, vals in by_family.items():
                    values.append(mean(vals))
                    families.add(family)
            ordered = sorted(values)
            def percentile(fraction):
                if not ordered:
                    return None
                position = (len(ordered) - 1) * fraction
                lower = int(position)
                upper = min(lower + 1, len(ordered) - 1)
                return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)
            dimensions[dim] = {
                "mean": round(mean(values), 3) if values else None,
                "spread": round(pstdev(values), 3) if len(values) > 1 else 0.0 if values else None,
                "min": min(values) if values else None, "max": max(values) if values else None,
                "p10": round(percentile(0.10), 3) if values else None,
                "p90": round(percentile(0.90), 3) if values else None,
                "track_count": len(values), "source_families": sorted(families),
            }
        else:
            counts, families, track_count = Counter(), set(), 0
            for track in included:
                rows = _usable(_observations(track, dim))
                if not rows:
                    continue
                track_count += 1
                per_family = {}
                for row in rows:
                    per_family.setdefault(row["source_family"], set()).update(_tokens([row]))
                for family, tokens in per_family.items():
                    families.add(family)
                    for token in tokens:
                        counts[token] += 1
            dimensions[dim] = {
                "prevalence": {k: round(v / max(1, track_count), 4) for k, v in counts.items()},
                "track_count": track_count, "source_families": sorted(families),
            }
    coverage = sum(bool(dimensions[d]["track_count"]) for d in DIMENSIONS) / len(DIMENSIONS)
    n = len(included)
    profile_confidence = "high" if n >= 20 and coverage >= 0.8 else (
        "medium" if n >= 8 and coverage >= 0.6 else "low" if n else "unknown")
    return {
        "model_version": MODEL_VERSION, "track_count": n,
        "excluded_candidate_and_holdout_count": len(excluded),
        "coverage": round(coverage, 3), "profile_confidence": profile_confidence,
        "dimensions": dimensions,
    }


def _dimension_result(track: dict, dim: str, profile: dict) -> dict:
    rows = _usable(_observations(track, dim), allow_context=(dim != "energy"))
    families = sorted({r["source_family"] for r in rows})
    scopes = sorted({r["scope"] for r in rows})
    if not rows:
        return {"score": None, "confidence": "unknown", "evidence_count": 0,
                "source_families": [], "scopes": [], "reason": "no usable evidence"}
    if dim == "energy":
        direct = []
        by_family = {}
        for row in rows:
            if row["scope"] not in {"recording", "audio"}:
                continue
            try:
                value = float(row["value"])
            except (TypeError, ValueError):
                continue
            if 0 <= value <= 100:
                by_family.setdefault(row["source_family"], []).append(value)
        direct = [mean(v) for v in by_family.values()]
        target = profile.get("mean")
        if not direct or target is None:
            return {"score": None, "confidence": "unknown", "evidence_count": 0,
                    "source_families": families, "scopes": scopes,
                    "reason": "no comparable recording-level energy or target profile"}
        observed = mean(direct)
        low = float(profile.get("p10", target))
        high = float(profile.get("p90", target))
        minimum = float(profile.get("min", target))
        maximum = float(profile.get("max", target))
        # Match the playlist's energy distribution, not just its arithmetic mean.
        if low <= observed <= high:
            score = 100.0
        elif observed < low:
            score = 100.0 * max(0.0, 1.0 - (low - observed) / max(1.0, low - minimum))
        else:
            score = 100.0 * max(0.0, 1.0 - (observed - high) / max(1.0, maximum - high))
    else:
        tokens = _tokens(rows)
        prevalence = profile.get("prevalence") or {}
        if not tokens or not prevalence:
            return {"score": None, "confidence": "unknown", "evidence_count": 0,
                    "source_families": families, "scopes": scopes,
                    "reason": "target profile has no comparable evidence"}
        # Each distinct candidate descriptor contributes its target prevalence.
        score = 100.0 * mean(prevalence.get(token, 0.0) for token in tokens)
        observed = sorted(tokens)
    independent = len(families)
    scope_factor = 1.0 if any(s in {"recording", "lyrics", "audio"} for s in scopes) else 0.35
    identity_rank = min(CONFIDENCE_RANK[r.get("identity_confidence", "unknown")] for r in rows)
    confidence = ("high" if independent >= 2 and identity_rank >= 3 and scope_factor == 1.0
                  else "medium" if independent >= 2 or (identity_rank >= 2 and scope_factor == 1.0)
                  else "low")
    return {"score": round(score, 2), "confidence": confidence,
            "evidence_count": len(rows), "source_families": families,
            "scopes": scopes, "observed_values": observed if dim != "energy" else round(observed, 2),
            "reason": "recording-level evidence" if scope_factor == 1.0 else "context-only evidence"}


def score_track(
    track: dict,
    profile: dict,
    *,
    weights: dict[str, float] | None = None,
) -> dict:
    """Return independent axis scores, normalized fit, and evidence-based confidence."""
    weights = {**DEFAULT_WEIGHTS, **(weights or {})}
    if any(dim not in weights or float(weights[dim]) < 0 for dim in DIMENSIONS):
        raise ValueError("weights must provide non-negative values for all five dimensions")
    axes = {dim: _dimension_result(track, dim, profile["dimensions"].get(dim, {}))
            for dim in DIMENSIONS}
    observed = [(float(axes[d]["score"]), float(weights[d])) for d in DIMENSIONS
                if axes[d]["score"] is not None and float(weights[d]) > 0]
    total_weight = sum(w for _, w in observed)
    fit = sum(score * weight for score, weight in observed) / total_weight if total_weight else None
    coverage = sum(float(weights[d]) for d in DIMENSIONS if axes[d]["score"] is not None) / max(
        1e-9, sum(float(weights[d]) for d in DIMENSIONS))
    supported = sum(axes[d]["score"] is not None for d in DIMENSIONS)
    source_families = {family for axis in axes.values() for family in axis["source_families"]}
    identity_ranks = [CONFIDENCE_RANK.get(row.get("identity_confidence", "unknown"), 0)
                      for dim in DIMENSIONS for row in _observations(track, dim) if _valid_observation(row)]
    identity = min(identity_ranks) if identity_ranks else 0
    profile_tier = profile.get("profile_confidence", "unknown")
    if fit is None or identity == 0:
        confidence = "unknown"
    elif supported >= 4 and len(source_families) >= 2 and identity >= 3 and profile_tier == "high":
        confidence = "high"
    elif supported >= 3 and identity >= 2 and profile_tier in {"medium", "high"}:
        confidence = "medium"
    else:
        confidence = "low"
    reasons = []
    if supported < 5:
        reasons.append(f"{5-supported} of 5 dimensions lack comparable evidence")
    if len(source_families) < 2:
        reasons.append("fewer than two independent source families")
    if identity < 3:
        reasons.append("recording identity confidence is not high")
    if profile_tier in {"low", "unknown"}:
        reasons.append(f"target profile confidence is {profile_tier}")
    if not reasons:
        reasons.append("broad multi-dimensional evidence with a sufficiently sampled target profile")
    return {
        "model_version": MODEL_VERSION, "fit_score": round(fit, 2) if fit is not None else None,
        "confidence_tier": confidence, "dimension_scores": axes,
        "evidence_coverage": round(coverage, 3), "supported_dimensions": supported,
        "identity_confidence": "high" if identity >= 3 else "medium" if identity == 2 else "low" if identity == 1 else "unknown",
        "profile_confidence": profile_tier, "confidence_reasons": reasons,
        "decision": "insufficient_evidence" if confidence in {"low", "unknown"} else
                    "review_candidate" if confidence == "medium" else "scored_candidate",
        "human_ratings_used": False,
    }


# FILE OVERVIEW
# Purpose: Read-only five-axis playlist-fit scorer. It deliberately does not read
#          the exploratory human-rating file or perform Spotify writes.
# Inputs: normalized recording evidence under track["dimensions"] and a profile
#         built from reference tracks with candidate/held-out exclusion.
# Run: import build_reference_profile and score_track from this module.
# Tests: python -m unittest tests.test_playlist_fit_model -v
