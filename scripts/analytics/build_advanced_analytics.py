#!/usr/bin/env python3
"""Build deeper identity-aware listening analytics from the canonical archive.

All timestamps and buckets are UTC. MBIDs are preferred for entity identity;
normalized names are fallbacks where Last.fm did not provide an MBID.
"""
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

SOURCE = Path("data/scrobbles.json")
OUT = Path("assistant_data/advanced")
SESSION_GAP_SECONDS = 30 * 60
REDISCOVERY_GAP_SECONDS = 90 * 86400


def read_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")


def clean(value):
    return str(value or "").strip() or "[Unknown]"


def norm(value):
    return clean(value).casefold()


def identity(mbid, label):
    return "mbid:" + mbid.strip().casefold() if mbid and mbid.strip() else "name:" + norm(label)


def iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).isoformat()


def rank(counter, labels, limit=None):
    rows = []
    for key, count in sorted(counter.items(), key=lambda x: (-x[1], labels.get(x[0], x[0]).casefold())):
        rows.append({"id": key, "name": labels.get(key, key), "plays": count})
    return rows[:limit] if limit else rows


def main():
    if not SOURCE.exists():
        raise FileNotFoundError(SOURCE)
    source = read_json(SOURCE)
    if not source:
        raise RuntimeError("Refusing to build from an empty archive.")

    # Sort defensively; the archive remains untouched.
    source.sort(key=lambda x: int(x["timestamp"]))
    artist_labels, track_labels, album_labels = {}, {}, {}
    artist_counts, track_counts, album_counts = Counter(), Counter(), Counter()
    artist_months = defaultdict(Counter)
    artist_first, artist_last = {}, {}
    artist_gaps = defaultdict(list)
    track_first, track_last = {}, {}
    month_counts = Counter()
    monthly_artist_counts = defaultdict(Counter)
    discoveries = []
    records = []

    for item in source:
        ts = int(item["timestamp"])
        artist, track, album = clean(item.get("artist")), clean(item.get("track")), clean(item.get("album"))
        aid = identity(item.get("artist_mbid"), artist)
        tid = identity(item.get("track_mbid"), aid + " — " + track)
        alid = identity(item.get("album_mbid"), aid + " — " + album)
        month = datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m")
        artist_labels.setdefault(aid, artist)
        track_labels.setdefault(tid, artist + " — " + track)
        album_labels.setdefault(alid, artist + " — " + album)
        artist_counts[aid] += 1
        track_counts[tid] += 1
        album_counts[alid] += 1
        artist_months[aid][month] += 1
        month_counts[month] += 1
        monthly_artist_counts[month][aid] += 1
        if aid in artist_last:
            gap = ts - artist_last[aid]
            if gap >= REDISCOVERY_GAP_SECONDS:
                artist_gaps[aid].append({"returned_at": iso(ts), "gap_days": round(gap / 86400, 1)})
        else:
            artist_first[aid] = ts
            discoveries.append({"artist_id": aid, "artist": artist, "first_scrobble": iso(ts), "month": month})
        artist_last[aid] = ts
        track_first.setdefault(tid, ts)
        track_last[tid] = ts
        records.append((ts, aid, tid, alid))

    total = len(records)
    if sum(artist_counts.values()) != total or sum(track_counts.values()) != total or sum(album_counts.values()) != total or sum(month_counts.values()) != total:
        raise RuntimeError("Advanced analytics reconciliation failed.")
    first_ts, last_ts = records[0][0], records[-1][0]

    # Monthly artist timelines and artist lifecycle metrics.
    timelines = {}
    lifecycle = []
    for aid, counts in artist_months.items():
        timelines[aid] = {
            "artist": artist_labels[aid],
            "monthly_plays": dict(sorted(counts.items())),
            "active_months": len(counts),
            "first_scrobble": iso(artist_first[aid]),
            "last_scrobble": iso(artist_last[aid]),
            "longest_return_gap_days": max((g["gap_days"] for g in artist_gaps[aid]), default=0),
            "rediscoveries": len(artist_gaps[aid]),
        }
        lifecycle.append({
            "artist_id": aid, "artist": artist_labels[aid],
            "plays": artist_counts[aid], "active_months": len(counts),
            "first_scrobble": iso(artist_first[aid]), "last_scrobble": iso(artist_last[aid]),
            "rediscoveries": len(artist_gaps[aid]),
            "longest_return_gap_days": timelines[aid]["longest_return_gap_days"],
        })
    lifecycle.sort(key=lambda x: (-x["active_months"], -x["plays"], x["artist"].casefold()))
    write_json(OUT / "artist_monthly_timelines.json", timelines)
    write_json(OUT / "artist_lifecycle.json", lifecycle)
    write_json(OUT / "artist_rediscoveries.json", [
        {"artist_id": aid, "artist": artist_labels[aid], **gap}
        for aid, gaps in artist_gaps.items() for gap in gaps
    ])

    # Discovery funnel by month.
    new_by_month = Counter(x["month"] for x in discoveries)
    discovery_summary = {
        "new_artists_by_month": dict(sorted(new_by_month.items())),
        "first_time_discoveries": len(discoveries),
        "one_play_artists": sum(1 for n in artist_counts.values() if n == 1),
        "artists_with_2_to_9_plays": sum(1 for n in artist_counts.values() if 2 <= n <= 9),
        "artists_with_10_plus_plays": sum(1 for n in artist_counts.values() if n >= 10),
        "rediscovery_gap_threshold_days": REDISCOVERY_GAP_SECONDS // 86400,
        "rediscoveries_total": sum(len(v) for v in artist_gaps.values()),
        "first_discoveries": discoveries,
    }
    write_json(OUT / "discovery.json", discovery_summary)

    # Rolling windows relative to the newest scrobble, not wall-clock now.
    rolling = {}
    for days in (30, 90):
        start = last_ts - days * 86400
        subset = [r for r in records if start < r[0] <= last_ts]
        ac, tc, alc = Counter(), Counter(), Counter()
        for _, aid, tid, alid in subset:
            ac[aid] += 1
            tc[tid] += 1
            alc[alid] += 1
        rolling[str(days)] = {
            "window_days": days, "start": iso(start), "end": iso(last_ts),
            "scrobbles": len(subset),
            "artists": rank(ac, artist_labels, 100),
            "tracks": rank(tc, track_labels, 100),
            "albums": rank(alc, album_labels, 100),
        }
    write_json(OUT / "rolling_rankings.json", rolling)

    # Session segmentation: a new session begins after a gap >30 minutes.
    sessions = []
    current = []
    for record in records:
        if current and record[0] - current[-1][0] > SESSION_GAP_SECONDS:
            sessions.append(current)
            current = []
        current.append(record)
    if current:
        sessions.append(current)
    if sum(len(s) for s in sessions) != total:
        raise RuntimeError("Session segmentation lost scrobbles.")
    durations = [max(0, s[-1][0] - s[0][0]) for s in sessions]
    per_day = Counter(datetime.fromtimestamp(r[0], timezone.utc).strftime("%Y-%m-%d") for r in records)
    active_dates = sorted(per_day)
    longest_streak = current_streak = 1
    for prev, cur in zip(active_dates, active_dates[1:]):
        delta = (datetime.fromisoformat(cur) - datetime.fromisoformat(prev)).days
        current_streak = current_streak + 1 if delta == 1 else 1
        longest_streak = max(longest_streak, current_streak)
    session_data = {
        "session_gap_minutes": SESSION_GAP_SECONDS // 60,
        "session_count": len(sessions),
        "average_scrobbles_per_session": round(total / len(sessions), 2),
        "median_scrobbles_per_session": sorted(len(s) for s in sessions)[len(sessions)//2],
        "average_session_span_minutes": round(sum(durations) / max(len(durations), 1) / 60, 2),
        "median_session_span_minutes": round(sorted(durations)[len(durations)//2] / 60, 2),
        "longest_session_scrobbles": max(map(len, sessions)),
        "longest_session_span_minutes": round(max(durations) / 60, 2),
        "longest_consecutive_active_days": longest_streak,
        "active_days": len(active_dates),
        "note": "Sessions are inferred from timestamp gaps; span is first-to-last scrobble, not verified playback duration."
    }
    write_json(OUT / "sessions.json", session_data)

    # Monthly concentration/diversity indicators.
    monthly_diversity = {}
    for month, ac in sorted(monthly_artist_counts.items()):
        n = sum(ac.values())
        hhi = sum((v / n) ** 2 for v in ac.values()) if n else 0
        monthly_diversity[month] = {
            "scrobbles": n, "unique_artists": len(ac),
            "top_artist": rank(ac, artist_labels, 1)[0] if ac else None,
            "top_10_artist_share": round(sum(v for _, v in ac.most_common(10)) / n, 6) if n else 0,
            "artist_concentration_hhi": round(hhi, 6),
        }
    write_json(OUT / "monthly_diversity.json", monthly_diversity)

    summary = {
        "schema_version": 1, "source_scrobbles": total,
        "first_scrobble": iso(first_ts), "last_scrobble": iso(last_ts),
        "identity": "MBID when present; otherwise case-folded display name (track fallback includes artist + track; album fallback includes artist + album).",
        "session_gap_minutes": SESSION_GAP_SECONDS // 60,
        "rediscovery_gap_days": REDISCOVERY_GAP_SECONDS // 86400,
        "files": ["artist_monthly_timelines.json", "artist_lifecycle.json", "artist_rediscoveries.json", "discovery.json", "rolling_rankings.json", "sessions.json", "monthly_diversity.json"]
    }
    write_json(OUT / "manifest.json", summary)
    print(f"Built advanced analytics for {total:,} scrobbles, {len(artist_counts):,} MBID-aware artists and {len(sessions):,} inferred sessions.")


if __name__ == "__main__":
    main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Build MBID-aware historical timelines, artist lifecycle, rediscovery, rolling-ranking,
#          listening-session, and monthly-diversity analytics from Last.fm history.
# Input: Reads data/scrobbles.json; sorts a copy in memory and never mutates the archive.
# Identity/time: Prefers artist/track/album MBIDs with normalized-name fallback; all buckets are UTC.
#          Sessions split after a 30-minute gap; artist rediscovery gaps use a 90-day threshold.
# Outputs: Writes assistant_data/advanced/artist_monthly_timelines.json, artist_lifecycle.json,
#          artist_rediscoveries.json, discovery.json, rolling_rankings.json, sessions.json,
#          monthly_diversity.json, and manifest.json.
# Safety: Reconciles aggregate counts against the source archive and refuses empty input.
# Run: python compat/build_advanced_analytics.py.
# Related: docs/REPOSITORY_FILE_INDEX.md and scripts/analytics/build_assistant_data.py.
# -----------------------------------------------------------------------------
