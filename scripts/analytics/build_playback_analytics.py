#!/usr/bin/env python3
"""Aggregate measured Spotify playback intervals into queryable analytics."""
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

SOURCE = Path("playback_data/segments.jsonl")
OUT = Path("assistant_data/playback")
OUT.mkdir(parents=True, exist_ok=True)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")


def main():
    artist_ms, track_ms, month_ms, day_ms = Counter(), Counter(), Counter(), Counter()
    total_ms = 0
    rows = 0
    first = last = None
    if SOURCE.exists():
        with SOURCE.open(encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                    played = int(item["played_ms"])
                    if played <= 0:
                        continue
                    sampled = datetime.fromisoformat(item["sampled_at"].replace("Z", "+00:00")).astimezone(timezone.utc)
                    artist = item.get("artist") or "[Unknown]"
                    track = item.get("track") or "[Unknown]"
                    key = (artist, track)
                    artist_ms[artist] += played
                    track_ms[key] += played
                    month_ms[sampled.strftime("%Y-%m")] += played
                    day_ms[sampled.strftime("%Y-%m-%d")] += played
                    total_ms += played
                    rows += 1
                    first = sampled if first is None or sampled < first else first
                    last = sampled if last is None or sampled > last else last
                except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                    raise RuntimeError(f"Invalid playback segment at {SOURCE}:{line_no}: {exc}") from exc

    artist_rows = [{"artist": a, "listened_ms": ms, "listened_hours": round(ms / 3_600_000, 3)}
                   for a, ms in artist_ms.most_common()]
    track_rows = [{"artist": a, "track": t, "listened_ms": ms, "listened_hours": round(ms / 3_600_000, 3)}
                  for (a, t), ms in track_ms.most_common()]
    overview = {
        "source": str(SOURCE), "measurement": "Spotify playback progress deltas sampled locally",
        "measured_listening_ms": total_ms, "measured_listening_hours": round(total_ms / 3_600_000, 3),
        "recorded_intervals": rows, "unique_artists": len(artist_ms), "unique_tracks": len(track_ms),
        "first_sample": first.isoformat() if first else None, "last_sample": last.isoformat() if last else None,
        "note": "Measured only while the local tracker is running and Spotify playback state is accessible. Short gaps at track changes, polling gaps, unsupported content and seeks are not reconstructed. This is a measured lower-bound estimate, not a complete account-wide history."
    }
    write(OUT / "overview.json", overview)
    write(OUT / "artists.json", artist_rows)
    write(OUT / "tracks.json", track_rows)
    write(OUT / "monthly.json", dict(sorted(month_ms.items())))
    write(OUT / "daily.json", dict(sorted(day_ms.items())))
    write(OUT / "manifest.json", {
        "schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": str(SOURCE), "source_exists": SOURCE.exists(), "recorded_intervals": rows,
        "measured_listening_ms": total_ms,
        "files": ["overview.json", "artists.json", "tracks.json", "monthly.json", "daily.json"]
    })
    print(f"Built measured playback analytics: {total_ms / 3_600_000:.3f} hours across {rows:,} intervals.")


if __name__ == "__main__":
    main()


# -----------------------------------------------------------------------------
# # FILE OVERVIEW
# # Purpose: Aggregate locally measured Spotify playback intervals into separate analytics.
# # Inputs: playback_data/segments.jsonl; each valid row contributes its measured played_ms
# #         and sampled_at timestamp.
# # Outputs: artist, track, month, day and overall summaries under assistant_data/playback/.
# # Semantics: Counts only recorded positive playback intervals; this is prospective tracker
# #            evidence, not a reconstruction of Last.fm scrobbles or complete listening history.
# # Safety: Offline aggregation only; an absent/sparse input is not interpreted as no listening.
# # Run: python compat/build_playback_analytics.py (repository root).
# # Related: scripts/spotify/spotify_playback_tracker.py; playback_data/README.md.
# # -----------------------------------------------------------------------------
