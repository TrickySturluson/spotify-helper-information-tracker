#!/usr/bin/env python3
"""Persist discovered/recommended tracks as discovery evidence, never listening evidence."""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PATH = ROOT / "assistant_data" / "recommendations" / "discovery_candidates.json"


def append_candidates(rows, *, source="shit_discovery", context=None, observed_at=None, path=DEFAULT_PATH):
    """Append normalized candidates idempotently by source + Spotify ID.

    Existing records and observation history are preserved. A candidate does not
    imply a play, scrobble, save, acceptance, or preference.
    """
    path = Path(path)
    try:
        existing = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        existing = []
    if isinstance(existing, dict):
        existing = existing.get("tracks", [])
    if not isinstance(existing, list):
        existing = []
    by_key = {}
    for row in existing:
        if isinstance(row, dict):
            key = str(row.get("spotify_id") or "").strip()
            if key:
                by_key[key] = row

    stamp = observed_at or datetime.now(timezone.utc).isoformat()
    added = 0
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        uri = str(row.get("uri") or row.get("spotify_uri") or "").strip()
        spotify_id = str(row.get("spotify_id") or (uri.rsplit(":", 1)[-1] if uri.startswith("spotify:track:") else "")).strip()
        artist = str(row.get("artist") or row.get("artist_name") or "").strip()
        title = str(row.get("track") or row.get("name") or row.get("title") or "").strip()
        if not spotify_id or not artist or not title:
            continue
        current = by_key.get(spotify_id)
        if current is None:
            current = {
                "spotify_id": spotify_id,
                "spotify_uri": "spotify:track:" + spotify_id,
                "artist": artist,
                "track": title,
                "album": row.get("album") or row.get("album_name"),
                "duration_ms": row.get("duration_ms"),
                "isrc": row.get("isrc") or row.get("external_ids", {}).get("isrc") if isinstance(row.get("external_ids"), dict) else row.get("isrc"),
                "track_mbid": row.get("track_mbid") or row.get("recording_mbid"),
                "discovery_evidence": [],
                "listening_evidence": {"plays": None, "scrobbles": None, "saved": None},
            }
            by_key[spotify_id] = current
            added += 1
        evidence = current.setdefault("discovery_evidence", [])
        event = {
            "source": source,
            "observed_at": stamp,
            "context": context or {},
        }
        # Retry-safe dedupe ignores observation timestamp but retains distinct
        # contexts (for example, different daily cycles or source surfaces).
        event_key = (str(source), json.dumps(context or {}, sort_keys=True, ensure_ascii=False))
        seen = {
            (str(item.get("source", "")), json.dumps(item.get("context") or {}, sort_keys=True, ensure_ascii=False))
            for item in evidence if isinstance(item, dict)
        }
        if event_key not in seen:
            evidence.append(event)
        # Fill blanks only; do not overwrite richer/verified identity metadata.
        for field, value in (
            ("artist", artist), ("track", title),
            ("album", row.get("album") or row.get("album_name")),
            ("duration_ms", row.get("duration_ms")),
            ("isrc", row.get("isrc")),
            ("track_mbid", row.get("track_mbid") or row.get("recording_mbid")),
        ):
            if value not in (None, "") and not current.get(field):
                current[field] = value
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(sorted(by_key.values(), key=lambda x: (x.get("artist", "").casefold(), x.get("track", "").casefold(), x.get("spotify_id", ""))), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
    return {"input_rows": len(rows or []), "unique_candidates": len(by_key), "new_candidates": added, "path": str(path)}


# FILE OVERVIEW
# Purpose: Durable, idempotent intake for songs surfaced by SHIT discovery workflows.
# Evidence boundary: Discovery events are stored separately from plays, Last.fm
# scrobbles, liked status, and explicit user feedback; unknown listening stays unknown.
# Identity: Spotify track ID is the stable intake key; richer identifiers are retained
# when available and canonical identity resolution remains the Library's responsibility.
# Storage: assistant_data/recommendations/discovery_candidates.json (compact metadata only).
# Related: scripts/music/sync_music_library.py; scripts/spotify/spotify_daily_cycle.py.
