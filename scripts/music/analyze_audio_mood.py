#!/usr/bin/env python3
"""Optional local DEAM valence/arousal inference for legally obtained audio.

This tool does not download music, access Spotify, or change playlist scores.
It requires the official Essentia TensorFlow model files to be placed locally
and an explicit acknowledgement of the model's non-commercial licensing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from scripts.music.audio_analysis import AUDIO_EXTENSIONS, parse_filename

MODEL_DIR = Path("models/essentia/deam")
EMBEDDING_MODEL = "msd-musicnn-1.pb"
MOOD_MODEL = "deam-msd-musicnn-2.pb"
MODEL_METADATA = "deam-msd-musicnn-2.json"
MODEL_VERSION = "2"
EXPECTED_CLASSES = ["valence", "arousal"]


def normalize(value: str) -> str:
    return " ".join(str(value or "").strip().casefold().split())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def aggregate_predictions(predictions) -> dict:
    """Aggregate frame-wise (valence, arousal) outputs without calling them probabilities."""
    rows = [[float(value) for value in row] for row in predictions]
    if not rows or any(len(row) != 2 for row in rows):
        raise ValueError("Expected one or more two-value (valence, arousal) predictions.")
    if any(not math.isfinite(value) or not 1.0 <= value <= 9.0 for row in rows for value in row):
        raise ValueError("DEAM outputs must be finite values on the documented 1–9 scale.")
    means = [sum(row[index] for row in rows) / len(rows) for index in range(2)]
    variances = [
        sum((row[index] - means[index]) ** 2 for row in rows) / len(rows)
        for index in range(2)
    ]
    return {
        "valence_mean": round(means[0], 4),
        "arousal_mean": round(means[1], 4),
        "valence_std": round(math.sqrt(variances[0]), 4),
        "arousal_std": round(math.sqrt(variances[1]), 4),
        "segment_count": len(rows),
        "scale": {"min": 1.0, "max": 9.0},
    }


def validate_model_files(model_dir: Path) -> tuple[Path, Path, dict]:
    embedding_path = model_dir / EMBEDDING_MODEL
    mood_path = model_dir / MOOD_MODEL
    metadata_path = model_dir / MODEL_METADATA
    missing = [path.name for path in (embedding_path, mood_path, metadata_path) if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "Missing official Essentia model files: " + ", ".join(missing)
            + f". See docs/AUDIO_MOOD_MODELS.md for the official source links."
        )
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if metadata.get("name") != "arousal_valence" or metadata.get("classes") != EXPECTED_CLASSES:
        raise ValueError("Unexpected DEAM model metadata; refusing to interpret output columns.")
    if str(metadata.get("version")) != MODEL_VERSION:
        raise ValueError(f"Unsupported DEAM model version: {metadata.get('version')!r}")
    return embedding_path, mood_path, metadata


def analyze_file(path: Path, embedding_path: Path, mood_path: Path, metadata: dict, source_hash: str | None = None) -> dict:
    try:
        import numpy as np
        import essentia.standard as es
    except ImportError as exc:
        raise RuntimeError(
            "Essentia with TensorFlow support and NumPy are required. "
            "See docs/AUDIO_MOOD_MODELS.md; the ordinary essentia package is insufficient."
        ) from exc

    artist, track = parse_filename(path)
    audio = es.MonoLoader(filename=str(path), sampleRate=16000, resampleQuality=4)()
    audio = np.asarray(audio, dtype=np.float32)
    if len(audio) < 16000 * 8:
        raise ValueError(f"Audio is too short to analyze reliably: {path.name}")

    embedder = es.TensorflowPredictMusiCNN(
        graphFilename=str(embedding_path), output="model/dense/BiasAdd"
    )
    embeddings = embedder(audio)
    predictor = es.TensorflowPredict2D(
        graphFilename=str(mood_path),
        input="model/Placeholder",
        output="model/Identity",
    )
    predictions = np.asarray(predictor(embeddings), dtype=np.float64)
    if predictions.ndim == 1:
        predictions = predictions.reshape(1, -1)
    aggregate = aggregate_predictions(predictions.tolist())

    return {
        "artist": artist,
        "track": track,
        "source_file": path.name,
        "source_audio_sha256": source_hash or sha256_file(path),
        "source_sample_rate": 16000,
        "source_family": "essentia_deam_audio_model",
        "evidence_scope": "recording_audio",
        "model_name": metadata.get("name"),
        "model_version": str(metadata.get("version")),
        "model_dataset": metadata.get("dataset", {}).get("name"),
        "model_metrics": metadata.get("dataset", {}).get("metrics", {}),
        "model_output_semantics": "uncalibrated regression output; not a probability or confidence tier",
        "model_license_notice": (
            "Non-commercial use only; verify the current official model license before use or redistribution."
        ),
        "embedding_model_sha256": sha256_file(embedding_path),
        "mood_model_sha256": sha256_file(mood_path),
        "model_metadata_sha256": sha256_file(mood_path.parent / MODEL_METADATA),
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        **aggregate,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="One audio file or a directory of legally obtained audio")
    parser.add_argument("--model-dir", type=Path, default=MODEL_DIR)
    parser.add_argument("--output", type=Path, default=Path("assistant_data/music/audio_mood_profiles.json"))
    parser.add_argument("--max-files", type=int, default=100)
    parser.add_argument(
        "--accept-noncommercial-license",
        action="store_true",
        help="Confirm that you have reviewed and accept the official model's non-commercial terms.",
    )
    args = parser.parse_args()
    if not args.accept_noncommercial_license:
        parser.error("Review docs/AUDIO_MOOD_MODELS.md and pass --accept-noncommercial-license.")
    if args.max_files < 1:
        parser.error("--max-files must be at least 1.")
    files = [args.input] if args.input.is_file() else sorted(
        path for path in args.input.rglob("*")
        if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS
    )
    files = [path for path in files if path.suffix.lower() in AUDIO_EXTENSIONS]
    if not files:
        parser.error("No supported local audio files found.")
    embedding_path, mood_path, metadata = validate_model_files(args.model_dir)

    existing = {}
    if args.output.exists():
        try:
            existing = json.loads(args.output.read_text(encoding="utf-8")).get("tracks", {})
        except (OSError, ValueError, AttributeError):
            existing = {}
    results = dict(existing)
    failures = []
    for path in files[:args.max_files]:
        try:
            artist, track = parse_filename(path)
            key = normalize(artist) + "\0" + normalize(track)
            digest = sha256_file(path)
            prior = results.get(key, {})
            if (
                prior.get("source_audio_sha256") == digest
                and prior.get("model_version") == MODEL_VERSION
                and prior.get("model_name") == metadata.get("name")
            ):
                print(f"SKIP unchanged: {path.name}")
                continue
            row = analyze_file(path, embedding_path, mood_path, metadata, digest)
            results[key] = row
            print(
                f"OK {artist} — {track}: valence={row['valence_mean']:.2f}, "
                f"arousal={row['arousal_mean']:.2f} (raw model outputs)"
            )
        except Exception as exc:
            failures.append(f"{path}: {exc}")
            print(f"SKIP {path}: {exc}")
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_family": "essentia_deam_audio_model",
        "evidence_scope": "recording_audio",
        "model_name": metadata.get("name"),
        "model_version": str(metadata.get("version")),
        "model_dataset": metadata.get("dataset", {}).get("name"),
        "model_metrics": metadata.get("dataset", {}).get("metrics", {}),
        "calibration_status": "uncalibrated; excluded from sorter mood confidence",
        "track_count": len(results),
        "tracks": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(args.output)
    print(f"Wrote {len(results)} audio mood profiles to {args.output}; failures: {len(failures)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Produce optional DEAM valence/arousal predictions from legally obtained local audio.
# Inputs: "Artist - Track.ext" files plus official local Essentia TensorFlow model weights/metadata.
# Outputs: assistant_data/music/audio_mood_profiles.json; no audio is copied or uploaded.
# Provenance: Stores source-file hash, model/version, model hashes, dataset metrics, time and output scope.
# Safety: Never downloads music or accesses Spotify. Requires explicit non-commercial-license acknowledgement.
# Confidence: Raw regression outputs are not probabilities and are excluded from sorter confidence until calibrated.
# Run: python compat/analyze_audio_mood.py <audio-folder> --accept-noncommercial-license
# Related: docs/AUDIO_MOOD_MODELS.md; scripts/music/audio_analysis.py; docs/TRACK_MOOD_EVIDENCE.md.
# -----------------------------------------------------------------------------
