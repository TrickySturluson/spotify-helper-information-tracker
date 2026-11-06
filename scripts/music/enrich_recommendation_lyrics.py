#!/usr/bin/env python3
"""Merge local lyric-analysis evidence into recommendation track features.

Run after build_music_analytics.py. If the local lyrics database is absent,
the command exits cleanly without changing generated recommendation data.
"""
import json
import re
import sqlite3
from pathlib import Path

DB = Path("data/lyrics/library.sqlite3")
FEATURES = Path("assistant_data/recommendations/track_features.json")


def norm(value):
    return " ".join(re.findall(r"[a-z0-9']+", str(value or "").casefold()))


def main():
    if not DB.exists():
        print("No local lyrics database; recommendation lyric enrichment skipped.")
        return
    if not FEATURES.exists():
        raise FileNotFoundError(f"Missing {FEATURES}; run build_music_analytics.py first.")
    connection = sqlite3.connect(DB)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute("""
            SELECT s.normalized_title, s.normalized_artist, a.themes_json,
                   a.relevance, a.assessment, a.word_count, a.analyzed_at
            FROM songs s LEFT JOIN analyses a ON a.song_id=s.id
        """).fetchall()
    finally:
        connection.close()
    index = {(row["normalized_title"], row["normalized_artist"]): row for row in rows}
    features = json.loads(FEATURES.read_text(encoding="utf-8"))
    enriched = 0
    for track in features:
        row = index.get((norm(track.get("track")), norm(track.get("artist"))))
        if not row:
            track["lyric_analysis"] = None
            continue
        analysis = json.loads(row["themes_json"] or "{}")
        track["lyric_analysis"] = {
            "schema_version": analysis.get("schema_version", 1),
            "themes": analysis.get("themes", analysis),
            "source_count": analysis.get("source_count", 1),
            "sources": analysis.get("sources", []),
            "method": analysis.get("method", "legacy_lexical_analysis"),
            "horror_relevance": row["relevance"],
            "assessment": row["assessment"],
            "word_count": row["word_count"],
            "analyzed_at": row["analyzed_at"],
            "evidence_type": "lyrics_keyword_analysis",
            "full_lyrics_stored": False
        }
        enriched += 1
    temp = FEATURES.with_suffix(".json.tmp")
    temp.write_text(json.dumps(features, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    temp.replace(FEATURES)
    print(f"Added lyric-analysis metadata to {enriched:,} of {len(features):,} recommendation tracks.")


if __name__ == "__main__":
    main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Merge locally stored lyric-analysis features into recommendation
#          track rows after the main music-analytics build.
# Inputs: Optional data/lyrics/library.sqlite3 and required
#         assistant_data/recommendations/track_features.json.
# Outputs: Atomically replaces track_features.json with lyric-analysis fields
#          joined by normalized artist/title identity.
# Behavior: If the local lyrics database is absent, exits successfully without
#           changing recommendation data; if features are absent, fails with
#           an instruction to run build_music_analytics.py first.
# Side effects: Local SQLite/JSON reads and temporary-file replacement only;
#               no lyrics are fetched and no Spotify playlist writes occur.
# Run: python compat/enrich_recommendation_lyrics.py (from repository root).
# Related: scripts/music/lyrics_library.py; scripts/analytics/build_music_analytics.py;
#          docs/LYRICS_LIBRARY.md.
# -----------------------------------------------------------------------------
