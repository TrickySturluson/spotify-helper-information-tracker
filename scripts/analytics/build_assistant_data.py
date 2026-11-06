#!/usr/bin/env python3
"""Build compact, queryable analytics from the canonical Last.fm archive.

The raw data/scrobbles.json remains the source of truth. This script creates
assistant_data/ JSON files that can be fetched individually without loading
the full archive.
"""
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

SOURCE = Path("data/scrobbles.json")
OUTPUT = Path("assistant_data")
USERNAME = "TrickySturluson"


def read_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, separators=(",", ":"))
        handle.write("\n")


def name(value):
    return str(value).strip() if value else "[Unknown]"


def iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).isoformat()


def ranked(counter, key_name, total=None):
    rows = []
    for key, plays in sorted(counter.items(), key=lambda item: (-item[1], str(item[0]).casefold())):
        row = dict(key) if isinstance(key, dict) else {key_name: key}
        row["plays"] = plays
        if total:
            row["share"] = round(plays / total, 8)
        rows.append(row)
    return rows


def main():
    if not SOURCE.exists():
        raise FileNotFoundError(f"Missing canonical archive: {SOURCE}")
    scrobbles = read_json(SOURCE)
    if not scrobbles:
        raise RuntimeError("Refusing to build analytics from an empty archive.")

    records = []
    artists, tracks, albums = Counter(), Counter(), Counter()
    artist_tracks, artist_albums = defaultdict(set), defaultdict(set)
    artist_first, artist_last = {}, {}
    track_first, track_last = {}, {}
    album_first, album_last = {}, {}
    by_year, by_month, by_day = Counter(), Counter(), Counter()
    by_weekday, by_hour = Counter(), Counter()
    monthly = defaultdict(lambda: {"artists": Counter(), "tracks": Counter(), "albums": Counter(), "days": Counter(), "new_artists": set()})
    yearly = defaultdict(lambda: {"artists": Counter(), "tracks": Counter(), "albums": Counter(), "days": Counter(), "new_artists": set()})
    all_artist_first = {}

    for item in scrobbles:
        ts = int(item["timestamp"])
        dt = datetime.fromtimestamp(ts, timezone.utc)
        artist, track, album = name(item.get("artist")), name(item.get("track")), name(item.get("album"))
        month, year, day = dt.strftime("%Y-%m"), str(dt.year), dt.strftime("%Y-%m-%d")
        track_key, album_key = (artist, track), (artist, album)
        artists[artist] += 1
        tracks[track_key] += 1
        albums[album_key] += 1
        artist_tracks[artist].add(track_key)
        artist_albums[artist].add(album_key)
        artist_first[artist] = min(ts, artist_first.get(artist, ts))
        artist_last[artist] = max(ts, artist_last.get(artist, ts))
        track_first[track_key] = min(ts, track_first.get(track_key, ts))
        track_last[track_key] = max(ts, track_last.get(track_key, ts))
        album_first[album_key] = min(ts, album_first.get(album_key, ts))
        album_last[album_key] = max(ts, album_last.get(album_key, ts))
        all_artist_first[artist] = min(ts, all_artist_first.get(artist, ts))
        by_year[year] += 1
        by_month[month] += 1
        by_day[day] += 1
        by_weekday[dt.strftime("%A")] += 1
        by_hour[str(dt.hour)] += 1
        for bucket in (monthly[month], yearly[year]):
            bucket["artists"][artist] += 1
            bucket["tracks"][track_key] += 1
            bucket["albums"][album_key] += 1
            bucket["days"][day] += 1
        records.append((ts, artist, track, album, month, year, day))

    total = len(records)
    first_ts, last_ts = records[0][0], records[-1][0]
    first_dt, last_dt = iso(first_ts), iso(last_ts)
    months = sorted(monthly)
    years = sorted(yearly)

    artist_rows = []
    for artist, plays in sorted(artists.items(), key=lambda x: (-x[1], x[0].casefold())):
        artist_rows.append({
            "artist": artist, "plays": plays,
            "unique_tracks": len(artist_tracks[artist]),
            "unique_albums": len(artist_albums[artist]),
            "first_scrobble": iso(artist_first[artist]),
            "last_scrobble": iso(artist_last[artist]),
            "active_months": sum(1 for m in months if monthly[m]["artists"].get(artist)),
            "share": round(plays / total, 8)
        })

    track_rows = []
    for (artist, track), plays in sorted(tracks.items(), key=lambda x: (-x[1], x[0][0].casefold(), x[0][1].casefold())):
        track_rows.append({"artist": artist, "track": track, "plays": plays,
                           "first_scrobble": iso(track_first[(artist, track)]),
                           "last_scrobble": iso(track_last[(artist, track)]),
                           "share": round(plays / total, 8)})
    album_rows = []
    for (artist, album), plays in sorted(albums.items(), key=lambda x: (-x[1], x[0][0].casefold(), x[0][1].casefold())):
        album_rows.append({"artist": artist, "album": album, "plays": plays,
                           "first_scrobble": iso(album_first[(artist, album)]),
                           "last_scrobble": iso(album_last[(artist, album)]),
                           "share": round(plays / total, 8)})

    top_artist = artist_rows[0]
    top_track = track_rows[0]
    music_duration = {}
    music_overview_path = OUTPUT / "music" / "overview.json"
    if music_overview_path.exists():
        music_overview = read_json(music_overview_path)
        music_duration = {
            "duration_coverage": music_overview.get("scrobble_duration_coverage"),
            "scrobbles_with_duration": music_overview.get("scrobbles_with_duration"),
            "unknown_duration_scrobbles": music_overview.get("unknown_duration_scrobbles"),
            "known_duration_minimum_qualifying_hours": music_overview.get("known_duration_minimum_qualifying_hours"),
            "known_duration_full_track_equivalent_hours": music_overview.get("known_duration_full_track_equivalent_hours"),
            "note": "Duration-based figures cover only scrobbles whose track duration is known; they are not actual playback measurements."
        }
    overview = {
        "username": USERNAME, "total_scrobbles": total,
        "unique_artists": len(artists), "unique_tracks": len(tracks), "unique_albums": len(albums),
        "first_scrobble": first_dt, "last_scrobble": last_dt,
        "history_days": round((last_ts - first_ts) / 86400, 2),
        "average_scrobbles_per_day": round(total / max((last_ts - first_ts) / 86400, 1), 2),
        "estimated_listening_hours": round(total * 3.5 / 60, 1),
        "legacy_3_5_minute_baseline_hours": round(total * 3.5 / 60, 1),
        "listening_time_note": "Legacy baseline only: 3.5 minutes per scrobble. Prefer duration_estimates when present; Last.fm scrobbles do not reveal actual played duration.",
        "duration_estimates": music_duration,
        "top_artist": top_artist, "top_track": top_track,
        "top_10_artist_share": round(sum(x["plays"] for x in artist_rows[:10]) / total, 6),
        "top_10_track_share": round(sum(x["plays"] for x in track_rows[:10]) / total, 6)
    }
    write_json(OUTPUT / "overview.json", overview)
    write_json(OUTPUT / "rankings" / "artists.json", artist_rows)
    write_json(OUTPUT / "rankings" / "tracks.json", track_rows)
    write_json(OUTPUT / "rankings" / "albums.json", album_rows)

    artist_index = {row["artist"]: {k: row[k] for k in ("plays", "unique_tracks", "unique_albums", "first_scrobble", "last_scrobble", "active_months")} for row in artist_rows}
    write_json(OUTPUT / "indexes" / "artists.json", artist_index)

    weekday_days = Counter()
    weekday_plays = Counter()
    for day, plays in by_day.items():
        weekday = datetime.strptime(day, "%Y-%m-%d").strftime("%A")
        weekday_days[weekday] += 1
        weekday_plays[weekday] += plays

    pattern = {
        "timezone": "UTC",
        "daily_scrobbles": dict(sorted(by_day.items())),
        "monthly_scrobbles": dict(sorted(by_month.items())),
        "yearly_scrobbles": dict(sorted(by_year.items())),
        "weekday_scrobbles": dict(by_weekday),
        "hour_utc_scrobbles": {str(h): by_hour.get(str(h), 0) for h in range(24)},
        "average_scrobbles_per_occurrence_of_weekday": {d: round(weekday_plays[d] / weekday_days[d], 2) if weekday_days[d] else 0 for d in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")}
    }
    write_json(OUTPUT / "listening_patterns.json", pattern)

    for year in years:
        b = yearly[year]
        year_total = sum(b["artists"].values())
        write_json(OUTPUT / "years" / f"{year}.json", {
            "year": year, "scrobbles": year_total,
            "unique_artists": len(b["artists"]), "unique_tracks": len(b["tracks"]), "unique_albums": len(b["albums"]),
            "daily_scrobbles": dict(sorted(b["days"].items())),
            "top_artists": ranked(b["artists"], "artist")[:100],
            "top_tracks": ranked(b["tracks"], "track")[:200],
            "top_albums": ranked(b["albums"], "album")[:100]
        })
    for month in months:
        b = monthly[month]
        month_total = sum(b["artists"].values())
        newly_seen = sorted(a for a in b["artists"] if all_artist_first[a] // 86400 >= 0 and datetime.fromtimestamp(all_artist_first[a], timezone.utc).strftime("%Y-%m") == month)
        write_json(OUTPUT / "months" / f"{month}.json", {
            "month": month, "scrobbles": month_total,
            "unique_artists": len(b["artists"]), "unique_tracks": len(b["tracks"]), "unique_albums": len(b["albums"]),
            "daily_scrobbles": dict(sorted(b["days"].items())),
            "new_artists": newly_seen,
            "top_artists": ranked(b["artists"], "artist"),
            "top_tracks": ranked(b["tracks"], "track")[:200],
            "top_albums": ranked(b["albums"], "album")[:100]
        })

    # Integrity checks: every source scrobble must land in exactly one year and month.
    if sum(by_year.values()) != total or sum(by_month.values()) != total or sum(by_day.values()) != total:
        raise RuntimeError("Time-series reconciliation failed.")
    if sum(row["plays"] for row in artist_rows) != total or sum(row["plays"] for row in track_rows) != total or sum(row["plays"] for row in album_rows) != total:
        raise RuntimeError("Ranking reconciliation failed.")

    manifest = {
        "schema_version": 1, "username": USERNAME,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "data/scrobbles.json",
        "source_scrobbles": total,
        "first_scrobble": first_dt, "last_scrobble": last_dt,
        "timezone": "UTC",
        "files": {
            "overview": "overview.json",
            "patterns": "listening_patterns.json",
            "artist_ranking": "rankings/artists.json",
            "track_ranking": "rankings/tracks.json",
            "album_ranking": "rankings/albums.json",
            "artist_index": "indexes/artists.json",
            "years": [f"years/{y}.json" for y in years],
            "months": [f"months/{m}.json" for m in months]
        },
        "identity_rules": "Artist+track and artist+album pairs are the ranking identities; names are display labels. MBIDs remain in the canonical raw archive.",
        "duration_note": "Listening duration is estimated at 3.5 minutes per scrobble, not measured playback time.",
        "validation": {"year_total": sum(by_year.values()), "month_total": sum(by_month.values()), "day_total": sum(by_day.values()), "ranked_artist_total": sum(x["plays"] for x in artist_rows), "ranked_track_total": sum(x["plays"] for x in track_rows), "ranked_album_total": sum(x["plays"] for x in album_rows)}
    }
    write_json(OUTPUT / "manifest.json", manifest)
    print(f"Built assistant_data for {total:,} scrobbles ({len(artists):,} artists, {len(tracks):,} tracks, {len(albums):,} artist/album pairs).")


if __name__ == "__main__":
    main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Build compact assistant-queryable indexes and summaries from Last.fm history.
# Source of truth: data/scrobbles.json; this script never rewrites the raw scrobble archive.
# Outputs: assistant_data overview/manifest, time buckets, rankings, entity indexes and
#          other compact JSON summaries consumed by ChatGPT and project analytics.
# Semantics: Preserves UTC timestamps and explicit unknown artist/album/track labels;
#            output is derived and can be regenerated from the canonical archive.
# Safety: Local aggregation only; no provider requests or Spotify playlist writes.
# Run: python compat/build_assistant_data.py (repository root).
# Related: tests/; assistant_data/README.md; docs/REPOSITORY_FILE_INDEX.md.
# -----------------------------------------------------------------------------
