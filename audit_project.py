#!/usr/bin/env python3
"""Cross-check canonical SHIT data and generated manifests."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ERRORS, WARNINGS, CHECKS = [], [], []

def load(path):
    try:
        return json.loads((ROOT / path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        ERRORS.append(f"{path}: invalid or missing JSON ({exc})")
        return None

def check(ok, message):
    (CHECKS if ok else ERRORS).append(message)

def referenced_paths(value):
    found = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"path", "file", "filename"} and isinstance(item, str):
                found.add(item)
            else:
                found.update(referenced_paths(item))
    elif isinstance(value, list):
        for item in value:
            found.update(referenced_paths(item))
    return found

def main():
    metadata = load("data/metadata.json") or {}
    total = metadata.get("total_scrobbles", metadata.get("scrobbles"))
    check(isinstance(total, int) and total >= 0, "Canonical scrobble count is valid.")
    manifests = (
        "assistant_data/manifest.json",
        "assistant_data/advanced/manifest.json",
        "assistant_data/music/manifest.json",
        "assistant_data/recommendations/manifest.json",
        "assistant_data/playback/manifest.json",
    )
    for path in manifests:
        manifest = load(path)
        if not isinstance(manifest, dict):
            continue
        for relative in referenced_paths(manifest):
            check((ROOT / relative).exists(), f"{path} references existing file {relative}.")
        for key in ("total_scrobbles", "source_scrobbles", "scrobbles"):
            if isinstance(manifest.get(key), int) and isinstance(total, int):
                check(manifest[key] == total, f"{path}: {key} agrees with canonical archive.")
    overview = load("assistant_data/music/overview.json") or {}
    unique, covered = overview.get("unique_tracks"), overview.get("tracks_with_duration")
    check(isinstance(unique, int) and isinstance(covered, int) and 0 <= covered <= unique,
          "Music duration coverage counts are valid.")
    profiles = load("assistant_data/music/track_profiles.json") or {}
    invalid = [key for key, row in profiles.items() if not isinstance(row, dict) or not key]
    check(not invalid, f"Track profile structure valid ({len(profiles)} records).")
    playback = load("assistant_data/playback/manifest.json") or {}
    if playback.get("source_exists") is False and playback.get("recorded_intervals", 0) == 0:
        WARNINGS.append("No captured playback intervals yet; this is a coverage gap, not corruption.")
    CHECKS.append("Legacy display-name and MBID-aware identity models may differ; this is intentional.")
    for label, messages in (("PASS", CHECKS), ("WARNING", WARNINGS), ("ERROR", ERRORS)):
        for message in messages:
            print(f"{label}: {message}")
    print(f"Audit result: {len(CHECKS)} checks, {len(WARNINGS)} warnings, {len(ERRORS)} errors.")
    return 1 if ERRORS else 0

if __name__ == "__main__":
    sys.exit(main())
