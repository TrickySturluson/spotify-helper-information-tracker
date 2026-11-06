#!/usr/bin/env python3
"""Analyze legally obtained local audio files and build SHIT audio profiles.

Input filenames must be "Artist - Track.ext". Files are analyzed locally; this
tool never downloads or extracts audio from Spotify. Results contain descriptors,
not audio. Requires Essentia and NumPy.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

AUDIO_EXTENSIONS = {".mp3", ".flac", ".wav", ".ogg", ".m4a", ".aiff", ".aif"}


def parse_filename(path: Path) -> tuple[str, str]:
    stem = path.stem.strip()
    if " - " not in stem:
        raise ValueError(f"Expected 'Artist - Track' filename: {path.name}")
    artist, track = stem.split(" - ", 1)
    if not artist.strip() or not track.strip():
        raise ValueError(f"Missing artist or track in filename: {path.name}")
    return artist.strip(), track.strip()


def dbfs(value: float) -> float | None:
    return round(20.0 * math.log10(max(float(value), 1e-12)), 2)


def analyze_file(path: Path, segment_seconds: int = 10) -> dict:
    try:
        import essentia.standard as es
        import numpy as np
    except ImportError as exc:
        raise RuntimeError(
            "Essentia and NumPy are required. Install requirements-audio-analysis.txt."
        ) from exc

    artist, track = parse_filename(path)
    audio, sample_rate, channels, _, _ = es.AudioLoader(filename=str(path))()
    mono = es.MonoMixer()(audio) if len(audio.shape) > 1 else audio
    mono = np.asarray(mono, dtype=np.float32)
    duration = len(mono) / float(sample_rate)
    if duration < 8:
        raise ValueError(f"Audio is too short to analyze reliably: {path.name}")

    bpm, beats, beat_confidence, bpm_estimates, beat_intervals = es.RhythmExtractor2013(
        method="multifeature"
    )(mono)

    integrated_lufs = None
    loudness_range_lu = None
    momentary = []
    short_term = []
    try:
        integrated_lufs, loudness_range_lu, momentary, short_term = es.LoudnessEBUR128()(
            mono
        )
        integrated_lufs = float(integrated_lufs)
        loudness_range_lu = float(loudness_range_lu)
        momentary = [float(x) for x in momentary]
        short_term = [float(x) for x in short_term]
    except Exception:
        pass

    segment_samples = int(segment_seconds * sample_rate)
    segments = []
    for start in range(0, len(mono), segment_samples):
        chunk = mono[start:start + segment_samples]
        if len(chunk) < sample_rate:
            continue
        rms = float(np.sqrt(np.mean(np.square(chunk, dtype=np.float64))))
        peak = float(np.max(np.abs(chunk)))
        segments.append({
            "start_seconds": round(start / sample_rate, 2),
            "end_seconds": round(min(start + len(chunk), len(mono)) / sample_rate, 2),
            "rms_dbfs": dbfs(rms),
            "peak_dbfs": dbfs(peak),
        })

    rms_values = [10 ** (row["rms_dbfs"] / 20) for row in segments]
    dynamic_range = (
        round(max(row["rms_dbfs"] for row in segments) -
              min(row["rms_dbfs"] for row in segments), 2)
        if segments else None
    )
    bpm_estimates = [float(x) for x in bpm_estimates]
    return {
        "artist": artist,
        "track": track,
        "source_file": path.name,
        "analysis_engine": "Essentia RhythmExtractor2013 + LoudnessEBUR128",
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round(duration, 3),
        "sample_rate": int(sample_rate),
        "tempo_bpm": round(float(bpm), 2),
        "tempo_confidence": round(float(beat_confidence), 3),
        "tempo_estimates_bpm": [round(x, 2) for x in bpm_estimates],
        "beat_positions_seconds": [round(float(x), 3) for x in beats],
        "integrated_lufs": round(integrated_lufs, 2) if integrated_lufs is not None else None,
        "loudness_range_lu": round(loudness_range_lu, 2) if loudness_range_lu is not None else None,
        "momentary_loudness_lufs": [round(x, 2) for x in momentary],
        "short_term_loudness_lufs": [round(x, 2) for x in short_term],
        "segment_seconds": segment_seconds,
        "segment_loudness": segments,
        "segment_rms_spread_db": dynamic_range,
        "dynamic_complexity": round(float(np.std(rms_values)), 4) if rms_values else None,
        "analysis_notes": [
            "BPM and beat positions are estimates; tempo can be half/double-time ambiguous.",
            "Segment RMS is a relative level envelope, not calibrated acoustic SPL.",
            "LUFS is program loudness; it is not the playback volume setting on a device.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Audio file or directory of audio files")
    parser.add_argument("--output", type=Path, default=Path("assistant_data/music/audio_profiles.json"))
    parser.add_argument("--segment-seconds", type=int, default=10)
    args = parser.parse_args()
    if args.segment_seconds < 3:
        parser.error("--segment-seconds must be at least 3")
    files = [args.input] if args.input.is_file() else sorted(
        p for p in args.input.rglob("*") if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS
    )
    files = [p for p in files if p.suffix.lower() in AUDIO_EXTENSIONS]
    if not files:
        parser.error("No supported audio files found.")
    existing = {}
    if args.output.exists():
        try:
            existing = json.loads(args.output.read_text(encoding="utf-8")).get("tracks", {})
        except (ValueError, OSError, AttributeError):
            existing = {}
    results = dict(existing)
    failures = []
    for path in files:
        try:
            row = analyze_file(path, args.segment_seconds)
            key = (row["artist"].casefold(), row["track"].casefold())
            results["\u0000".join(key)] = row
            print(f'OK {row["artist"]} — {row["track"]}: {row["tempo_bpm"]} BPM')
        except Exception as exc:
            failures.append(f"{path}: {exc}")
            print(f"SKIP {path}: {exc}")
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "analysis_engine": "Essentia",
        "track_count": len(results),
        "tracks": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(results)} audio profiles to {args.output}; failures: {len(failures)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Measure tempo, beat positions and loudness descriptors from audio
#          files already available locally; it does not acquire music.
# Inputs: One supported audio file or a directory tree of files named
#         "Artist - Track.ext"; supported extensions are defined by
#         AUDIO_EXTENSIONS. Requires the optional Essentia/NumPy dependencies.
# Outputs: Merges successful artist/track profiles into the selected JSON
#          output (default assistant_data/music/audio_profiles.json).
# Side effects/safety: Reads local audio and writes descriptors only; no Spotify
#                      access, downloads, audio uploads or audio-file copies.
#                      Existing profiles are retained. Per-file failures are
#                      reported; successful rows are saved before exit status 1.
# Run: python compat/audio_analysis.py <audio-file-or-folder>
#      [--output PATH] [--segment-seconds N]
# Related: requirements-audio-analysis.txt; docs/AUDIO_ANALYSIS.md;
#          tests/ (local audio-analysis coverage).
# -----------------------------------------------------------------------------
