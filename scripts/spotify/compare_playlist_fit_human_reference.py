#!/usr/bin/env python3
"""Compare a frozen read-only preview with human labels as diagnostic references only.

This script is deliberately separate from playlist_fit_model.py and
playlist_fit_preview.py. Human ratings never enter model scoring, profile
construction, confidence estimation, training, or playlist decisions.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def norm(value) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).casefold()


def pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2:
        return None
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    dx, dy = [x - mx for x in xs], [y - my for y in ys]
    denom = math.sqrt(sum(x * x for x in dx) * sum(y * y for y in dy))
    return round(sum(x * y for x, y in zip(dx, dy)) / denom, 4) if denom else None


def ranks(values: list[float]) -> list[float]:
    ordered = sorted(enumerate(values), key=lambda pair: pair[1])
    result = [0.0] * len(values)
    cursor = 0
    while cursor < len(ordered):
        end = cursor + 1
        while end < len(ordered) and ordered[end][1] == ordered[cursor][1]:
            end += 1
        average_rank = ((cursor + 1) + end) / 2
        for position in range(cursor, end):
            result[ordered[position][0]] = average_rank
        cursor = end
    return result


def metrics(pairs: list[dict]) -> dict:
    if not pairs:
        return {"n": 0, "mae": None, "mean_bias_model_minus_human": None,
                "pearson_r": None, "spearman_r": None, "mean_human": None, "mean_model": None}
    human = [float(row["human_score"]) for row in pairs]
    model = [float(row["model_score"]) for row in pairs]
    errors = [m - h for m, h in zip(model, human)]
    return {
        "n": len(pairs),
        "mae": round(sum(abs(x) for x in errors) / len(errors), 2),
        "mean_bias_model_minus_human": round(sum(errors) / len(errors), 2),
        "pearson_r": pearson(model, human),
        "spearman_r": pearson(ranks(model), ranks(human)),
        "mean_human": round(sum(human) / len(human), 2),
        "mean_model": round(sum(model) / len(model), 2),
    }


def compare(preview: dict, ratings_doc: dict) -> dict:
    targets = preview.get("targets") if isinstance(preview.get("targets"), dict) else {}
    target_names = {playlist_id: target.get("name", playlist_id)
                    for playlist_id, target in targets.items()}
    results = preview.get("results") if isinstance(preview.get("results"), list) else []
    by_uri = {str(row.get("uri")): row for row in results if row.get("uri")}
    by_display = {}
    for row in results:
        key = (norm(row.get("title")), norm(row.get("artist")))
        by_display.setdefault(key, []).append(row)

    pairs_by_target = {name: [] for name in target_names.values()}
    human_pairs_by_target = {name: 0 for name in target_names.values()}
    matched_ratings = unmatched = ambiguous = unknown = 0
    match_methods = {"spotify_uri": 0, "unique_exact_title_artist_display_join": 0}
    confidence_counts = {"low": 0, "medium": 0, "high": 0, "unknown": 0}

    ratings = ratings_doc.get("ratings") if isinstance(ratings_doc.get("ratings"), list) else []
    for rating in ratings:
        track = rating.get("track") if isinstance(rating.get("track"), dict) else {}
        uri = str(track.get("uri") or "")
        candidate = by_uri.get(uri) if uri else None
        if candidate:
            match_methods["spotify_uri"] += 1
        else:
            matches = by_display.get((norm(track.get("name")), norm(track.get("artist"))), [])
            if len(matches) == 1:
                candidate = matches[0]
                match_methods["unique_exact_title_artist_display_join"] += 1
            elif len(matches) > 1:
                ambiguous += 1
                continue
        if candidate is None:
            unmatched += 1
            continue
        matched_ratings += 1
        score_rows = candidate.get("scores_by_target") if isinstance(candidate.get("scores_by_target"), dict) else {}
        for human_row in rating.get("human_fit_ratings") or []:
            playlist_id = human_row.get("playlist_id")
            target_name = target_names.get(playlist_id)
            if not target_name:
                continue
            human_pairs_by_target[target_name] += 1
            model_row = score_rows.get(target_name) if isinstance(score_rows.get(target_name), dict) else {}
            model_score = model_row.get("fit_score")
            if model_score is None:
                unknown += 1
                confidence_counts["unknown"] += 1
                continue
            tier = model_row.get("confidence", "unknown")
            confidence_counts[tier if tier in confidence_counts else "unknown"] += 1
            pairs_by_target[target_name].append({
                "title": candidate.get("title"), "artist": candidate.get("artist"),
                "human_score": float(human_row.get("score")),
                "model_score": float(model_score), "signed_error": round(float(model_score) - float(human_row.get("score")), 2),
                "confidence": tier, "supported_dimensions": model_row.get("supported_dimensions"),
                "directly_supported_dimensions": model_row.get("directly_supported_dimensions"),
                "identity_confidence": model_row.get("identity_confidence"),
                "profile_confidence": model_row.get("profile_confidence"),
            })

    target_reports = {}
    all_pairs = []
    for name, pairs in pairs_by_target.items():
        all_pairs.extend(pairs)
        human_pair_count = human_pairs_by_target[name]
        target_reports[name] = {
            **metrics(pairs), "human_rating_pairs": human_pair_count,
            "scored_pairs": len(pairs), "unknown_pairs": human_pair_count - len(pairs),
            "score_coverage": round(len(pairs) / human_pair_count, 3) if human_pair_count else 0.0,
            "pairs": pairs,
        }

    return {
        "schema_version": 1,
        "status": "diagnostic_reference_comparison_only",
        "model_version": preview.get("model_version"),
        "preview_status": preview.get("status"),
        "human_ratings_used_by_model_scorer": False,
        "human_ratings_used_for_training": False,
        "playlist_writes": 0,
        "human_rating_tracks": len(ratings),
        "matched_human_rating_tracks": matched_ratings,
        "unmatched_human_rating_tracks": unmatched,
        "ambiguous_human_rating_tracks": ambiguous,
        "unknown_model_score_pairs": unknown,
        "match_methods": match_methods,
        "confidence_counts_on_scored_pairs": confidence_counts,
        "overall": metrics(all_pairs),
        "targets": target_reports,
        "interpretation": [
            "Human sliders are exploratory reference observations, not ground truth, model training data, listening events, or playlist membership decisions.",
            "The comparison is descriptive only. It must not tune scoring weights or enable sorting.",
            "Low-confidence and context-only predictions are included but remain visibly stratified; unknown model scores are not imputed as zero.",
            "The current reference set is small and the model may have sparse evidence coverage; correlations and errors are not production validation.",
            "Where a human track lacks a Spotify URI, matching uses a unique exact normalized title+artist display key only for joining the separate evaluation records; it is not used as model identity evidence.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", type=Path, required=True)
    parser.add_argument("--ratings", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    preview = read_json(args.preview)
    ratings = read_json(args.ratings)
    result = compare(preview, ratings)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output), "status": result["status"],
        "model_version": result["model_version"], "overall": result["overall"],
        "unknown_model_score_pairs": result["unknown_model_score_pairs"],
        "human_ratings_used_by_model_scorer": False,
    }, indent=2))


if __name__ == "__main__":
    main()

# FILE OVERVIEW
# Purpose: Post-hoc comparison of frozen model previews against exploratory human slider labels.
# Boundary: Not imported by the scorer or preview builder; never used for training, sorting, or playlist actions.
# Run: python scripts/spotify/compare_playlist_fit_human_reference.py --preview <preview.json> --ratings assistant_data/spotify/playlist_human_fit_ratings.json --output <comparison.json>
