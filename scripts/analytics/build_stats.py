import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone


SCROBBLES_FILE = "data/scrobbles.json"
STATS_FILE = "data/stats.json"


def load_scrobbles():
    with open(SCROBBLES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def safe_name(value):
    return value if value else "[Unknown]"


def main():
    print("Loading scrobble history...")

    scrobbles = load_scrobbles()

    if not scrobbles:
        raise RuntimeError("No scrobbles found.")

    print(f"Loaded {len(scrobbles):,} scrobbles.")

    # --------------------------------------------------------
    # Basic counters
    # --------------------------------------------------------

    artist_counts = Counter()
    album_counts = Counter()
    track_counts = Counter()

    artist_tracks = defaultdict(set)
    artist_albums = defaultdict(set)

    year_counts = Counter()
    month_counts = Counter()
    weekday_counts = Counter()
    hour_counts = Counter()

    year_artist_counts = defaultdict(Counter)
    year_track_counts = defaultdict(Counter)
    year_album_counts = defaultdict(Counter)

    month_artist_counts = defaultdict(Counter)

    artist_first_seen = {}
    artist_last_seen = {}

    track_first_seen = {}
    track_last_seen = {}

    album_first_seen = {}
    album_last_seen = {}

    # --------------------------------------------------------
    # Process scrobbles
    # --------------------------------------------------------

    for i, scrobble in enumerate(scrobbles, 1):

        timestamp = int(scrobble["timestamp"])

        dt = datetime.fromtimestamp(
            timestamp,
            tz=timezone.utc
        )

        artist = safe_name(scrobble.get("artist"))
        album = safe_name(scrobble.get("album"))
        track = safe_name(scrobble.get("track"))

        year = str(dt.year)
        month = f"{dt.year}-{dt.month:02d}"

        weekday = dt.strftime("%A")
        hour = dt.hour

        # Basic counts
        artist_counts[artist] += 1
        album_counts[album] += 1
        track_counts[(artist, track)] += 1

        # Artist relationships
        artist_tracks[artist].add(track)
        artist_albums[artist].add(album)

        # Time
        year_counts[year] += 1
        month_counts[month] += 1
        weekday_counts[weekday] += 1
        hour_counts[str(hour)] += 1

        # Yearly breakdowns
        year_artist_counts[year][artist] += 1
        year_track_counts[year][(artist, track)] += 1
        year_album_counts[year][(artist, album)] += 1

        # Monthly artist breakdown
        month_artist_counts[month][artist] += 1

        # First / last seen
        artist_first_seen[artist] = min(
            timestamp,
            artist_first_seen.get(artist, timestamp)
        )

        artist_last_seen[artist] = max(
            timestamp,
            artist_last_seen.get(artist, timestamp)
        )

        track_key = f"{artist} — {track}"
        track_first_seen[track_key] = min(
            timestamp,
            track_first_seen.get(track_key, timestamp)
        )

        track_last_seen[track_key] = max(
            timestamp,
            track_last_seen.get(track_key, timestamp)
        )

        album_key = f"{artist} — {album}"
        album_first_seen[album_key] = min(
            timestamp,
            album_first_seen.get(album_key, timestamp)
        )

        album_last_seen[album_key] = max(
            timestamp,
            album_last_seen.get(album_key, timestamp)
        )

        if i % 25000 == 0:
            print(f"Processed {i:,} scrobbles...")

    # --------------------------------------------------------
    # Date range
    # --------------------------------------------------------

    timestamps = [
        int(s["timestamp"])
        for s in scrobbles
        if s.get("timestamp")
    ]

    first_timestamp = min(timestamps)
    last_timestamp = max(timestamps)

    first_dt = datetime.fromtimestamp(
        first_timestamp,
        tz=timezone.utc
    )

    last_dt = datetime.fromtimestamp(
        last_timestamp,
        tz=timezone.utc
    )

    listening_days = max(
        1,
        (last_dt - first_dt).total_seconds() / 86400
    )

    # --------------------------------------------------------
    # Estimated listening time
    # --------------------------------------------------------
    #
    # Last.fm doesn't give us exact track duration here.
    # We use a conservative 3.5 minute estimate for the
    # high-level estimate.
    #

    estimated_minutes = len(scrobbles) * 3.5
    estimated_hours = estimated_minutes / 60
    estimated_days = estimated_hours / 24

    # --------------------------------------------------------
    # Replay metrics
    # --------------------------------------------------------

    total_scrobbles = len(scrobbles)
    unique_artists = len(artist_counts)
    unique_albums = len(album_counts)
    unique_tracks = len(track_counts)

    top_artist_count = (
        artist_counts.most_common(1)[0][1]
        if artist_counts
        else 0
    )

    top_track_count = (
        track_counts.most_common(1)[0][1]
        if track_counts
        else 0
    )

    top_10_artist_plays = sum(
        count
        for _, count in artist_counts.most_common(10)
    )

    top_10_track_plays = sum(
        count
        for _, count in track_counts.most_common(10)
    )

    # --------------------------------------------------------
    # Chaos metrics
    # --------------------------------------------------------

    replay_concentration = (
        top_10_track_plays / total_scrobbles
        if total_scrobbles
        else 0
    )

    artist_concentration = (
        top_10_artist_plays / total_scrobbles
        if total_scrobbles
        else 0
    )

    tracks_per_artist = (
        unique_tracks / unique_artists
        if unique_artists
        else 0
    )

    albums_per_artist = (
        unique_albums / unique_artists
        if unique_artists
        else 0
    )

    # Artists with only one scrobble
    one_play_artists = sum(
        1
        for count in artist_counts.values()
        if count == 1
    )

    one_play_artist_percentage = (
        one_play_artists / unique_artists
        if unique_artists
        else 0
    )

    # Artists with 100+ plays
    heavy_rotation_artists = sum(
        1
        for count in artist_counts.values()
        if count >= 100
    )

    # --------------------------------------------------------
    # Format helpers
    # --------------------------------------------------------

    def top_artist_list(limit=100):
        result = []

        for artist, count in artist_counts.most_common(limit):
            result.append({
                "artist": artist,
                "plays": count,
                "unique_tracks": len(artist_tracks[artist]),
                "unique_albums": len(artist_albums[artist]),
                "share": round(
                    count / total_scrobbles,
                    6
                )
            })

        return result

    def top_track_list(limit=100):
        result = []

        for (artist, track), count in track_counts.most_common(limit):
            result.append({
                "artist": artist,
                "track": track,
                "plays": count,
                "share": round(
                    count / total_scrobbles,
                    6
                )
            })

        return result

    def top_album_list(limit=100):
        result = []

        album_counter = Counter()

        for scrobble in scrobbles:
            artist = safe_name(scrobble.get("artist"))
            album = safe_name(scrobble.get("album"))

            album_counter[(artist, album)] += 1

        for (artist, album), count in album_counter.most_common(limit):
            result.append({
                "artist": artist,
                "album": album,
                "plays": count
            })

        return result

    def counter_to_dict(counter):
        return {
            str(key): value
            for key, value in counter.items()
        }

    def yearly_top_artists():
        result = {}

        for year in sorted(year_artist_counts):
            result[year] = [
                {
                    "artist": artist,
                    "plays": count
                }
                for artist, count
                in year_artist_counts[year].most_common(25)
            ]

        return result

    def yearly_top_tracks():
        result = {}

        for year in sorted(year_track_counts):
            result[year] = [
                {
                    "artist": artist,
                    "track": track,
                    "plays": count
                }
                for (artist, track), count
                in year_track_counts[year].most_common(25)
            ]

        return result

    def monthly_top_artists():
        result = {}

        for month in sorted(month_artist_counts):
            result[month] = [
                {
                    "artist": artist,
                    "plays": count
                }
                for artist, count
                in month_artist_counts[month].most_common(10)
            ]

        return result

    # --------------------------------------------------------
    # Build final stats object
    # --------------------------------------------------------

    stats = {
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),

        "username": "TrickySturluson",

        "overview": {
            "total_scrobbles": total_scrobbles,
            "unique_artists": unique_artists,
            "unique_albums": unique_albums,
            "unique_tracks": unique_tracks,

            "first_scrobble": first_dt.isoformat(),
            "last_scrobble": last_dt.isoformat(),

            "history_days": round(
                listening_days,
                2
            ),

            "average_scrobbles_per_day": round(
                total_scrobbles / listening_days,
                2
            ),

            "estimated_listening_hours": round(
                estimated_hours,
                1
            ),

            "estimated_listening_days": round(
                estimated_days,
                2
            )
        },

        "replay": {
            "top_artist": (
                artist_counts.most_common(1)[0][0]
                if artist_counts
                else None
            ),

            "top_artist_plays": top_artist_count,

            "top_track": (
                {
                    "artist": track_counts.most_common(1)[0][0][0],
                    "track": track_counts.most_common(1)[0][0][1]
                }
                if track_counts
                else None
            ),

            "top_track_plays": top_track_count,

            "top_10_artist_share": round(
                artist_concentration,
                4
            ),

            "top_10_track_share": round(
                replay_concentration,
                4
            ),

            "tracks_per_artist": round(
                tracks_per_artist,
                2
            ),

            "albums_per_artist": round(
                albums_per_artist,
                2
            ),

            "one_play_artists": one_play_artists,

            "one_play_artist_percentage": round(
                one_play_artist_percentage,
                4
            ),

            "artists_with_100_plus_plays":
                heavy_rotation_artists
        },

        "time": {
            "by_year": counter_to_dict(
                year_counts
            ),

            "by_month": counter_to_dict(
                month_counts
            ),

            "by_weekday": counter_to_dict(
                weekday_counts
            ),

            "by_hour_utc": counter_to_dict(
                hour_counts
            )
        },

        "top_artists": top_artist_list(100),

        "top_tracks": top_track_list(100),

        "top_albums": top_album_list(100),

        "yearly_top_artists":
            yearly_top_artists(),

        "yearly_top_tracks":
            yearly_top_tracks(),

        "monthly_top_artists":
            monthly_top_artists()
    }

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    with open(
        STATS_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            stats,
            f,
            indent=2,
            ensure_ascii=False
        )

    print()
    print("=" * 60)
    print("STATS BUILT SUCCESSFULLY")
    print("=" * 60)
    print(
        f"Scrobbles:       {total_scrobbles:,}"
    )
    print(
        f"Artists:         {unique_artists:,}"
    )
    print(
        f"Albums:          {unique_albums:,}"
    )
    print(
        f"Tracks:          {unique_tracks:,}"
    )
    print(
        f"Estimated hours: {estimated_hours:,.1f}"
    )
    print(
        f"Top artist:      "
        f"{artist_counts.most_common(1)[0][0]}"
    )
    print(
        f"Top artist plays:"
        f" {top_artist_count:,}"
    )
    print(
        f"One-play artists:"
        f" {one_play_artists:,}"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Build the compact top-level listening statistics snapshot from the
#          canonical Last.fm scrobble archive.
# Inputs: data/scrobbles.json; each record supplies a Unix timestamp, artist,
#         album and track fields.
# Outputs: Replaces data/stats.json with totals, rankings, first/last-seen dates,
#          UTC time buckets and replay/concentration metrics.
# Semantics: The listening-time figure is a rough 3.5-minute-per-scrobble
#            estimate, not measured playback or duration-verified time.
# Side effects: Local JSON read/write only; no provider requests and no changes
#               to the canonical scrobble archive.
# Run: python compat/build_stats.py (from the repository root).
# Related: scripts/analytics/build_assistant_data.py; data/README.md;
#          tests/ (analytics regression coverage).
# -----------------------------------------------------------------------------
