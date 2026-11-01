#!/usr/bin/env python3
"""Publish complete-history listening-time estimates alongside verified duration data.

The legacy baseline deliberately includes every scrobble. Verified-duration
metrics remain a separate subset and are never filled with guessed durations.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

ARCHIVE = Path("data/scrobbles.json")
ASSISTANT_OVERVIEW = Path("assistant_data/overview.json")
STATS = Path("data/stats.json")
MUSIC_OVERVIEW = Path("assistant_data/music/overview.json")
REC_MONTH = Path("assistant_data/recommendations/monthly_duration_trends.json")
REC_YEAR = Path("assistant_data/recommendations/yearly_duration_trends.json")
OUTPUT = Path("assistant_data/listening_time.json")
BASELINE_MINUTES = 3.5


def read(path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def main():
    rows = read(ARCHIVE, [])
    if not rows:
        raise RuntimeError("Refusing to publish listening-time estimates for an empty archive.")

    total = len(rows)
    legacy_hours = total * BASELINE_MINUTES / 60
    music = read(MUSIC_OVERVIEW, {}) or {}
    known = int(music.get("scrobbles_with_duration", 0) or 0)
    unknown = max(0, total - known)
    coverage = known / total
    verified = {
        "scrobbles_with_duration": known,
        "unknown_duration_scrobbles": unknown,
        "coverage_fraction": round(coverage, 6),
        "coverage_percent": round(coverage * 100, 2),
        "full_track_equivalent_hours": music.get("known_duration_full_track_equivalent_hours"),
        "minimum_qualifying_hours": music.get("known_duration_minimum_qualifying_hours"),
        "note": "Subset only: calculated from matched track durations. It is not actual playback measurement."
    }
    result = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_scrobbles": total,
        "primary_estimate": {
            "method": "legacy_average_duration",
            "average_minutes_per_scrobble": BASELINE_MINUTES,
            "estimated_hours": round(legacy_hours, 1),
            "estimated_days": round(legacy_hours / 24, 2),
            "coverage_scrobbles": total,
            "coverage_percent": 100.0,
            "label": "Estimated listening time (legacy 3.5-minute average)",
            "note": "Includes every archived scrobble, including tracks with unknown duration. An archive-wide estimate, not measured playback."
        },
        "verified_duration_subset": verified,
        "measured_spotify_playback": {
            "status": "prospective_local_tracker",
            "note": "Measured progress intervals are reported separately and cover only periods captured by the local Spotify tracker."
        }
    }
    write(OUTPUT, result)

    overview = read(ASSISTANT_OVERVIEW, {}) or {}
    overview["listening_time"] = result
    overview["estimated_listening_hours"] = round(legacy_hours, 1)
    overview["legacy_3_5_minute_baseline_hours"] = round(legacy_hours, 1)
    overview["listening_time_note"] = result["primary_estimate"]["note"]
    write(ASSISTANT_OVERVIEW, overview)

    stats = read(STATS, {}) or {}
    stats.setdefault("overview", {})
    stats["overview"]["estimated_listening_hours"] = round(legacy_hours, 1)
    stats["overview"]["estimated_listening_days"] = round(legacy_hours / 24, 2)
    stats["overview"]["listening_time_method"] = "legacy 3.5-minute average across all archived scrobbles"
    stats["overview"]["verified_duration_coverage_percent"] = round(coverage * 100, 2)
    write(STATS, stats)

    for path in (REC_MONTH, REC_YEAR):
        buckets = read(path, {}) or {}
        for bucket in buckets.values():
            count = int(bucket.get("scrobbles", 0))
            bucket["legacy_estimated_hours"] = round(count * BASELINE_MINUTES / 60, 3)
            bucket["legacy_estimate_method"] = "3.5 minutes per scrobble; includes all scrobbles"
            bucket["unknown_duration_scrobbles"] = max(0, count - int(bucket.get("known_duration_scrobbles", 0)))
        write(path, buckets)

    print(f"Listening time: {total:,} scrobbles; legacy estimate {legacy_hours:,.1f}h; verified duration coverage {known:,}/{total:,} ({coverage:.1%}).")


if __name__ == "__main__":
    main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Publish complete-history listening-time estimates alongside verified duration data. The legacy baseline deliberately includes every scrobble. Verified-duration metrics remain a separate subset and are never filled with guessed durations.
# Location: Maintained implementation in scripts/analytics/build_listening_time_summary.py.
# Data flow: Reads canonical project inputs and/or existing generated artifacts;
#            writes only the outputs described by this module's implementation.
# Run: python compat/build_listening_time_summary.py (legacy CLI entry point, when this tool has one).
# Related: tests/ (regression coverage for build_listening_time_summary). See docs/ for longer operational and data-contract guides.
# -----------------------------------------------------------------------------
