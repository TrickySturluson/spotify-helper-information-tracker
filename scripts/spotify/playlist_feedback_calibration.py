#!/usr/bin/env python3
"""Playlist-scoped feedback and conservative calibration for playlist-fit predictions.

This is deliberately separate from the Tricky Daily discovery policy. It records
what the fit model predicted, preserves the evidence available at that moment,
and evaluates only explicit or narrowly inferred playlist outcomes. Spotify
Liked Songs is contextual taste evidence, never a playlist-fit label by itself.

Run: python -m unittest tests.test_playlist_feedback_calibration -v
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_PATH = Path("assistant_data/spotify/playlist_fit_feedback.json")
SCHEMA_VERSION = 1
VALID_OUTCOMES = {"accepted", "rejected", "uncertain"}
VALID_FEEDBACK_SOURCES = {
    "explicit_whitelist", "explicit_blacklist", "manual_removal",
    "manual_addition", "retained_after_review",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _identity(playlist_id: str, track_uri: str) -> str:
    return f"{str(playlist_id).strip()}|{str(track_uri).strip()}"


def _read(path: Path) -> dict:
    if not path.exists():
        return {"schema_version": SCHEMA_VERSION, "predictions": {}, "feedback_events": []}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"Unsupported playlist-fit feedback schema in {path}")
    if not isinstance(payload.get("predictions"), dict) or not isinstance(payload.get("feedback_events"), list):
        raise ValueError(f"Malformed playlist-fit feedback store: {path}")
    return payload


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def record_prediction(
    playlist_id: str,
    track_uri: str,
    fit_score: float,
    confidence: str,
    evidence: dict | None = None,
    *,
    playlist_name: str = "",
    track_name: str = "",
    artist: str = "",
    model_version: str = "unspecified",
    liked_before_prediction: bool | None = None,
    path: Path = DEFAULT_PATH,
    predicted_at: str | None = None,
) -> dict:
    """Persist an immutable prediction snapshot; repeated calls are idempotent."""
    if not playlist_id or not track_uri:
        raise ValueError("playlist_id and track_uri are required")
    score = float(fit_score)
    if not math.isfinite(score) or not 0 <= score <= 100:
        raise ValueError("fit_score must be finite and between 0 and 100")
    if confidence not in {"high", "medium", "low", "unknown"}:
        raise ValueError("confidence must be high, medium, low, or unknown")
    key = _identity(playlist_id, track_uri)
    payload = _read(path)
    # Keep the first prediction for this model version; a changed model creates
    # a distinct immutable record and cannot overwrite the historical forecast.
    prediction_id = hashlib.sha256(f"{key}|{model_version}|{predicted_at or 'first'}".encode()).hexdigest()[:20]
    existing = payload["predictions"].get(prediction_id)
    if existing:
        return existing
    row = {
        "prediction_id": prediction_id,
        "playlist_id": str(playlist_id),
        "playlist_name": str(playlist_name),
        "track_uri": str(track_uri),
        "track_name": str(track_name),
        "artist": str(artist),
        "fit_score": round(score, 3),
        "confidence": confidence,
        "evidence": dict(evidence or {}),
        "model_version": str(model_version),
        "liked_before_prediction": liked_before_prediction,
        "predicted_at": predicted_at or _now(),
        "outcome": None,
    }
    payload["predictions"][prediction_id] = row
    _write(path, payload)
    return row


def record_feedback(
    prediction_id: str,
    outcome: str,
    source: str,
    *,
    reason: str = "",
    weight: float | None = None,
    observed_at: str | None = None,
    path: Path = DEFAULT_PATH,
) -> dict:
    """Attach a traceable outcome to a prediction without rewriting its forecast."""
    if outcome not in VALID_OUTCOMES:
        raise ValueError(f"outcome must be one of {sorted(VALID_OUTCOMES)}")
    if source not in VALID_FEEDBACK_SOURCES:
        raise ValueError(f"source must be one of {sorted(VALID_FEEDBACK_SOURCES)}")
    payload = _read(path)
    prediction = payload["predictions"].get(prediction_id)
    if prediction is None:
        raise KeyError(f"Unknown prediction_id: {prediction_id}")
    default_weight = {
        "explicit_whitelist": 1.0, "explicit_blacklist": 1.0,
        "manual_removal": 0.85, "manual_addition": 0.65,
        "retained_after_review": 0.5,
    }[source]
    effective_weight = default_weight if weight is None else float(weight)
    if not math.isfinite(effective_weight) or not 0 < effective_weight <= 1:
        raise ValueError("weight must be greater than 0 and at most 1")
    # An identical event is idempotent; contradictory later feedback is retained
    # as a new event so the history exposes reversals rather than hiding them.
    event = {
        "prediction_id": prediction_id,
        "playlist_id": prediction["playlist_id"],
        "track_uri": prediction["track_uri"],
        "outcome": outcome,
        "source": source,
        "reason": str(reason),
        "weight": effective_weight,
        "observed_at": observed_at or _now(),
    }
    if event not in payload["feedback_events"]:
        payload["feedback_events"].append(event)
    prediction["outcome"] = outcome
    _write(path, payload)
    return event


def record_liked_observation(
    prediction_id: str,
    liked: bool,
    *,
    observed_at: str | None = None,
    path: Path = DEFAULT_PATH,
) -> dict:
    """Record a global-like state change as context, never as accept/reject."""
    payload = _read(path)
    prediction = payload["predictions"].get(prediction_id)
    if prediction is None:
        raise KeyError(f"Unknown prediction_id: {prediction_id}")
    observations = prediction.setdefault("liked_observations", [])
    event = {"liked": bool(liked), "observed_at": observed_at or _now()}
    if not observations or observations[-1] != event:
        observations.append(event)
        _write(path, payload)
    return event


def _holdout(prediction_id: str) -> bool:
    """Stable 20% holdout, independent of score and outcome."""
    return int(hashlib.sha256(prediction_id.encode()).hexdigest()[:8], 16) % 5 == 0


def calibration_report(path: Path = DEFAULT_PATH, *, min_bin_samples: int = 8) -> dict:
    """Report weighted observed acceptance by score band; never auto-tunes weights."""
    payload = _read(path)
    latest = {}
    for event in payload["feedback_events"]:
        latest[event["prediction_id"]] = event
    rows = []
    for prediction_id, event in latest.items():
        prediction = payload["predictions"].get(prediction_id)
        if not prediction or event["outcome"] == "uncertain":
            continue
        rows.append({
            "prediction_id": prediction_id,
            "score": float(prediction["fit_score"]),
            "confidence": prediction["confidence"],
            "accepted": 1.0 if event["outcome"] == "accepted" else 0.0,
            "weight": float(event["weight"]),
            "holdout": _holdout(prediction_id),
            "source": event["source"],
            "playlist_id": prediction["playlist_id"],
            "model_version": prediction["model_version"],
        })
    bins = []
    for lower in range(0, 100, 20):
        upper = lower + 20
        for split in ("train", "holdout"):
            group = [r for r in rows if lower <= r["score"] < upper
                     and r["holdout"] == (split == "holdout")]
            total_weight = sum(r["weight"] for r in group)
            observed = (sum(r["accepted"] * r["weight"] for r in group) / total_weight
                        if total_weight else None)
            bins.append({
                "range": [lower, upper], "split": split,
                "sample_count": len(group), "effective_weight": round(total_weight, 3),
                "observed_acceptance": round(observed, 4) if observed is not None else None,
                "status": ("eligible_for_review" if len(group) >= min_bin_samples
                           else "provisional_insufficient_samples"),
            })
    scored = [r for r in rows if not r["holdout"]]
    total_weight = sum(r["weight"] for r in scored)
    mae = (sum(abs(r["score"] / 100 - r["accepted"]) * r["weight"] for r in scored) / total_weight
           if total_weight else None)
    return {
        "schema_version": SCHEMA_VERSION,
        "labelled_predictions": len(rows),
        "training_predictions": len(scored),
        "holdout_predictions": sum(r["holdout"] for r in rows),
        "training_mean_absolute_error": round(mae, 4) if mae is not None else None,
        "minimum_bin_samples": min_bin_samples,
        "bins": bins,
        "calibration_status": (
            "provisional" if len(scored) < min_bin_samples * 2
            else "reviewable_not_automatically_applied"
        ),
        "guardrails": [
            "Tricky Daily discovery/familiarity scoring is a separate policy.",
            "Liked Songs observations are context, never playlist-fit labels.",
            "Uncertain outcomes and ignored recommendations are not negative labels.",
            "Holdout rows are excluded from training summaries.",
            "No scoring weights are changed automatically.",
        ],
    }


def ingest_manual_removals(
    predictions: dict[str, str],
    *,
    removal_path: Path = Path("playlist_removed_tracks.json"),
    feedback_path: Path = DEFAULT_PATH,
) -> int:
    """Link existing playlist-specific manual removals to known predictions.

    predictions maps 'playlist_id|track_uri' to prediction_id. Historical rows
    without a URI cannot be joined safely and are intentionally skipped.
    """
    if not removal_path.is_file():
        return 0
    payload = json.loads(removal_path.read_text(encoding="utf-8"))
    count = 0
    for playlist_id, playlist in (payload.get("playlists") or {}).items():
        for row in playlist.get("removed") or []:
            uri = row.get("uri")
            if not uri:
                continue
            prediction_id = predictions.get(_identity(playlist_id, uri))
            if not prediction_id:
                continue
            source = str(row.get("source") or "").casefold()
            if "manual" not in source and "user-confirmed" not in source:
                continue
            record_feedback(
                prediction_id, "rejected", "manual_removal",
                reason="Imported from playlist-specific removal history",
                path=feedback_path,
            )
            count += 1
    return count


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Keep immutable playlist-fit predictions and playlist-scoped feedback,
#          then report conservative calibration diagnostics without changing
#          production scoring automatically.
# Data flow: Sequencer/recommender records a prediction with record_prediction;
#            explicit user decisions are attached with record_feedback;
#            liked-state changes are contextual observations only. Existing
#            manual removal history can be joined when exact Spotify URIs exist.
# Safety: This is independent of Tricky Daily's discovery-first scoring. Unknown,
#        ignored, and uncertain outcomes never become negative training labels.
# Run: python -m unittest tests.test_playlist_feedback_calibration -v
# Related: docs/PLAYLIST_FEEDBACK_CALIBRATION.md
# -----------------------------------------------------------------------------
