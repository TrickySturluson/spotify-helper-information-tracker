#!/usr/bin/env python3
"""Build duration trends and recommendation-ready library features from existing data."""
import hashlib
import json
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import mood_inference

SOURCE = Path("data/scrobbles.json")
MUSIC = Path("assistant_data/music")
OUT = Path("assistant_data/recommendations")
LYRICS_DB = Path("data/lyrics/library.sqlite3")
SHARD_COUNT = 32


def read(path, default=None):
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")
    tmp.replace(path)


def clean(v):
    return str(v or "").strip() or "[Unknown]"


def norm(v):
    return re.sub(r"\s+", " ", clean(v)).casefold()


def track_norm(v):
    return " ".join(re.findall(r"[a-z0-9]+", clean(v).casefold()))

def stable_id(prefix, value):
    return prefix + ":" + hashlib.sha1(value.encode("utf-8")).hexdigest()[:16]


def artist_id(row):
    mbid = str(row.get("artist_mbid") or "").strip().casefold()
    return "mbid:" + mbid if mbid else stable_id("name", norm(row.get("artist")))


def track_id(row, aid):
    mbid = str(row.get("track_mbid") or "").strip().casefold()
    return "mbid:" + mbid if mbid else stable_id("track", aid + "\0" + norm(row.get("track")))


def iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).isoformat()


def load_lyric_analyses():
    """Load exported and private lyric metadata without requiring a cloud DB."""
    index = {}
    exported = read(OUT / "lyric_features.json", [])
    for row in exported if isinstance(exported, list) else []:
        if not isinstance(row, dict) or not row.get("artist") or not row.get("track"):
            continue
        index[(track_norm(row["track"]), track_norm(row["artist"]))] = {
            "schema_version": row.get("schema_version", 1),
            "themes": row.get("themes", {}),
            "source_count": row.get("source_count", 1),
            "sources": row.get("sources", []),
            "method": row.get("method", "legacy_lexical_analysis"),
            "horror_relevance": row.get("horror_relevance", 0.0),
            "assessment": row.get("assessment", "unavailable"),
            "word_count": row.get("word_count", 0),
            "analyzed_at": row.get("analyzed_at"),
            "evidence_type": "lyrics_keyword_analysis",
            "full_lyrics_stored": False,
        }
    db = LYRICS_DB
    if not db.exists():
        return index
    connection = sqlite3.connect(db)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute("""
            SELECT s.normalized_title, s.normalized_artist, a.themes_json,
                   a.relevance, a.assessment, a.word_count, a.analyzed_at
            FROM songs s JOIN analyses a ON a.song_id=s.id
        """).fetchall()
    finally:
        connection.close()
    for row in rows:
        analysis = json.loads(row["themes_json"] or "{}")
        index[(track_norm(row["normalized_title"]), track_norm(row["normalized_artist"]))] = {
            "schema_version": analysis.get("schema_version", 1),
            "themes": analysis.get("themes", {}),
            "source_count": analysis.get("source_count", 1),
            "sources": analysis.get("sources", []),
            "method": analysis.get("method", "legacy_lexical_analysis"),
            "horror_relevance": row["relevance"],
            "assessment": row["assessment"],
            "word_count": row["word_count"],
            "analyzed_at": row["analyzed_at"],
            "evidence_type": "lyrics_keyword_analysis",
            "full_lyrics_stored": False,
        }
    return index

def main():
    scrobbles = read(SOURCE, [])
    if not scrobbles:
        raise RuntimeError("Refusing to build music analytics from an empty archive.")

    durations = {}
    for shard in range(SHARD_COUNT):
        data = read(MUSIC / "artists" / f"shard-{shard:02d}.json", {"artists": {}})
        for aid, artist in data.get("artists", {}).items():
            for tid, track in artist.get("tracks", {}).items():
                if track.get("duration_ms"):
                    durations[tid] = track

    profiles = read(MUSIC / "artist_profiles.json", {})
    track_profiles = read(MUSIC / "track_profiles.json", {})
    tracks, artists = {}, {}
    monthly = defaultdict(lambda: {"scrobbles": 0, "known_duration_scrobbles": 0, "full_track_equivalent_ms": 0, "minimum_qualifying_ms": 0, "unique_tracks": set(), "unique_artists": set()})
    yearly = defaultdict(lambda: {"scrobbles": 0, "known_duration_scrobbles": 0, "full_track_equivalent_ms": 0, "minimum_qualifying_ms": 0, "unique_tracks": set(), "unique_artists": set()})
    for row in sorted(scrobbles, key=lambda r: int(r["timestamp"])):
        ts = int(row["timestamp"])
        aid = artist_id(row)
        tid = track_id(row, aid)
        artist = clean(row.get("artist"))
        title = clean(row.get("track"))
        album = clean(row.get("album"))
        month = datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m")
        year = str(datetime.fromtimestamp(ts, timezone.utc).year)
        t = tracks.setdefault(tid, {"track_id": tid, "artist_id": aid, "artist": artist, "track": title, "albums": Counter(), "plays": 0, "first_scrobble_ts": ts, "last_scrobble_ts": ts})
        t["plays"] += 1
        t["first_scrobble_ts"] = min(t["first_scrobble_ts"], ts)
        t["last_scrobble_ts"] = max(t["last_scrobble_ts"], ts)
        if album != "[Unknown]":
            t["albums"][album] += 1
        a = artists.setdefault(aid, {"artist_id": aid, "artist": artist, "plays": 0, "tracks": set(), "first_scrobble_ts": ts, "last_scrobble_ts": ts})
        a["plays"] += 1
        a["tracks"].add(tid)
        a["first_scrobble_ts"] = min(a["first_scrobble_ts"], ts)
        a["last_scrobble_ts"] = max(a["last_scrobble_ts"], ts)
        for key in (month, year):
            bucket = monthly[key] if len(key) == 7 else yearly[key]
            bucket["scrobbles"] += 1
            bucket["unique_tracks"].add(tid)
            bucket["unique_artists"].add(aid)
        meta = durations.get(tid)
        if meta:
            duration = int(meta["duration_ms"])
            for bucket in (monthly[month], yearly[year]):
                bucket["known_duration_scrobbles"] += 1
                bucket["full_track_equivalent_ms"] += duration
                if duration > 30000:
                    bucket["minimum_qualifying_ms"] += min(duration // 2, 240000)

    def finalize_buckets(source):
        result = {}
        for key, b in sorted(source.items()):
            result[key] = {
                "scrobbles": b["scrobbles"],
                "known_duration_scrobbles": b["known_duration_scrobbles"],
                "duration_coverage": round(b["known_duration_scrobbles"] / b["scrobbles"], 6) if b["scrobbles"] else 0,
                "known_duration_full_track_equivalent_hours": round(b["full_track_equivalent_ms"] / 3600000, 3),
                "known_duration_minimum_qualifying_hours": round(b["minimum_qualifying_ms"] / 3600000, 3),
                "unique_tracks": len(b["unique_tracks"]),
                "unique_artists": len(b["unique_artists"]),
                "note": "Duration estimates include only scrobbles with known track durations; these are not measured playback."
            }
        return result

    artist_output = []
    for aid, a in artists.items():
        p = profiles.get(aid, {})
        artist_output.append({
            "artist_id": aid, "artist": a["artist"], "plays": a["plays"], "unique_tracks": len(a["tracks"]),
            "first_scrobble": iso(a["first_scrobble_ts"]), "last_scrobble": iso(a["last_scrobble_ts"]),
            "genres": p.get("genres", []), "moods": p.get("moods", []), "themes": p.get("themes", []),
            "community_tags": [x.get("tag") for x in p.get("tags", [])[:15]],
            "profile_status": p.get("status", "not_enriched"),
            "recommendation_role": "familiar_anchor" if a["plays"] >= 25 else "lightly_explored_artist"
        })
    artist_output.sort(key=lambda a: (-a["plays"], a["artist"].casefold()))

    lyric_index = load_lyric_analyses()
    track_output = []
    for tid, t in tracks.items():
        meta = durations.get(tid, {})
        profile = profiles.get(t["artist_id"], {})
        track_profile = track_profiles.get(tid, {})
        lastfm_tags = track_profile.get("lastfm_tags", [])
        musicbrainz_tags = track_profile.get("musicbrainz_tags", [])
        musicbrainz_genres = track_profile.get("musicbrainz_genres", [])
        sourced_tags = lastfm_tags + musicbrainz_tags + musicbrainz_genres
        tag_names = list(dict.fromkeys(row.get("tag", "") for row in sourced_tags if row.get("tag")))
        track_moods = sorted({mood for tag in tag_names for mood in mood_inference._tag_moods(tag)})
        track_output.append({
            "track_id": tid, "artist_id": t["artist_id"], "artist": t["artist"], "track": t["track"],
            "albums": [name for name, _ in t["albums"].most_common(5)], "plays": t["plays"],
            "first_scrobble": iso(t["first_scrobble_ts"]), "last_scrobble": iso(t["last_scrobble_ts"]),
            "duration_ms": meta.get("duration_ms"), "duration_source": meta.get("duration_source"),
            "duration_confidence": meta.get("confidence"),
            "genres": [row.get("tag") for row in musicbrainz_genres if row.get("tag")],
            "moods": track_moods, "themes": [],
            "track_tags": tag_names,
            "track_tag_sources": sorted({row.get("source", "unknown") for row in sourced_tags}),
            "track_metadata_status": track_profile.get("lastfm_status", "not_enriched"),
            "artist_genres": profile.get("genres", []),
            "artist_moods": profile.get("moods", []),
            "artist_themes": profile.get("themes", []),
            "lyric_analysis": lyric_index.get((track_norm(t["track"]), track_norm(t["artist"]))),
            "familiarity": "frequent" if t["plays"] >= 25 else "known" if t["plays"] >= 2 else "single_scrobble"
        })
    track_output.sort(key=lambda t: (-t["plays"], t["artist"].casefold(), t["track"].casefold()))

    write(OUT / "monthly_duration_trends.json", finalize_buckets(monthly))
    write(OUT / "yearly_duration_trends.json", finalize_buckets(yearly))
    write(OUT / "artist_features.json", artist_output)
    write(OUT / "track_features.json", track_output)
    summary = {
        "schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_scrobbles": len(scrobbles), "unique_artists": len(artists), "unique_tracks": len(tracks),
        "tracks_with_duration": sum(1 for t in tracks if t in durations),
        "tracks_with_artist_profiles": sum(1 for aid in artists if profiles.get(aid, {}).get("status") == "matched"),
        "tracks_with_track_tags": sum(1 for tid in tracks if track_profiles.get(tid, {}).get("lastfm_tags") or track_profiles.get(tid, {}).get("musicbrainz_tags") or track_profiles.get(tid, {}).get("musicbrainz_genres")),
        "tracks_with_lyric_analysis": sum(1 for t in track_output if t.get("lyric_analysis")),
        "tracks_with_track_moods": sum(1 for tid in tracks if any(mood_inference._tag_moods(row.get("tag", "")) for row in (track_profiles.get(tid, {}).get("lastfm_tags", []) + track_profiles.get(tid, {}).get("musicbrainz_tags", [])))),
        "files": {
            "monthly_duration_trends": "monthly_duration_trends.json",
            "yearly_duration_trends": "yearly_duration_trends.json",
            "artist_features": "artist_features.json",
            "track_features": "track_features.json"
        },
        "recommendation_notes": [
            "Familiarity is based on scrobble counts, not a claim that the user likes every track.",
            "Tracks with one scrobble are still previously heard in the archive; external discovery requires a separate catalogue/search step.",
            "Artist genres, moods and themes remain separate from track-level tags; track moods are conservative mappings from track-sourced tags only.",
            "Track-level community tags are descriptive evidence, not objective audio analysis; source and identity provenance are retained.",
            "Lyric themes come from the compact committed export and optional local database; neither stores full lyric text in recommendation features.",
            "Duration trends include only scrobbles whose track duration is known."
        ]
    }
    write(OUT / "manifest.json", summary)
    print(f"Music analytics: {len(tracks):,} tracks; {len(artists):,} artists; {summary['tracks_with_duration']:,} tracks with durations; wrote monthly/yearly duration trends and recommendation features.")


if __name__ == "__main__":
    main()
