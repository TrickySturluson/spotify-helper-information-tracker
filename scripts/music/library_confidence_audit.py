#!/usr/bin/env python3
"""Read-only confidence and evidence coverage audit for the canonical music Library."""
import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from scripts.music.music_evidence import identity_confidence, track_metadata_confidence

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROOT = REPO_ROOT / "assistant_data" / "music" / "library"
MUSIC_ROOT = REPO_ROOT / "assistant_data" / "music"
sys.path.insert(0, str(REPO_ROOT))


def _read(path):
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return None, f"{type(error).__name__}: {error}"


def _norm(value):
    return " ".join(str(value or "").casefold().split())


def _matched_by(song_id):
    value = str(song_id or "").casefold()
    if value.startswith("mbid:"):
        return "musicbrainz_recording_mbid"
    if value.startswith("spotify:"):
        return "spotify_track_id"
    if value.startswith("source:"):
        return "source_track_id"
    if value.startswith("fallback:"):
        return "fallback_identity"
    return None


def inspect_confidence(root=DEFAULT_ROOT, music_root=MUSIC_ROOT):
    """Recompute categorical confidence from canonical IDs and field evidence; never write."""
    root, music_root = Path(root), Path(music_root)
    errors = []
    identity_tiers = Counter()
    identity_methods = Counter()
    identity_quality = Counter()
    identity_drift = []
    metadata_tiers = {}
    metadata_drift = []
    coverage = Counter()
    provenance_missing = Counter()
    songs_seen = 0
    candidate_aliases = 0
    alias_index, alias_problem = _read(root / "library_index.json")
    if alias_problem or not isinstance(alias_index, dict):
        errors.append(f"Library index unreadable: {alias_problem or 'not an object'}")
        alias_index = {}

    for path in sorted((root / "songs").rglob("song.json")):
        record, problem = _read(path)
        if problem or not isinstance(record, dict):
            errors.append(f"Invalid song record {path}: {problem or 'not an object'}")
            continue
        songs_seen += 1
        song_id = record.get("id")
        identity = record.get("identity") if isinstance(record.get("identity"), dict) else {}
        stored_confidence = record.get("confidence") if isinstance(record.get("confidence"), dict) else {}
        stored_identity = stored_confidence.get("identity", "unknown")
        method = _matched_by(song_id)
        recomputed_identity = identity_confidence(
            method,
            {"identity_quality": "fallback_artist_title"} if method == "fallback_identity" else identity,
        )
        identity_tiers[str(stored_identity or "unknown")] += 1
        identity_methods[str(method or "unclassified")] += 1
        identity_quality[str(identity.get("identity_quality") or "unspecified")] += 1
        if stored_identity != recomputed_identity:
            identity_drift.append({
                "song_id": song_id,
                "stored": stored_identity,
                "recomputed": recomputed_identity,
                "method": method,
                "identity_quality": identity.get("identity_quality"),
            })

        evidence = record.get("evidence") if isinstance(record.get("evidence"), dict) else {}
        track_metadata = evidence.get("track_metadata") if isinstance(evidence.get("track_metadata"), dict) else {}
        stored_metadata = stored_confidence.get("metadata") if isinstance(stored_confidence.get("metadata"), dict) else {}
        recomputed_metadata = track_metadata_confidence(track_metadata)
        for field, detail in stored_metadata.items():
            if field == "track_tags" and isinstance(detail, dict):
                for tag, value in detail.items():
                    tier = value.get("confidence", "unknown") if isinstance(value, dict) else "unknown"
                    metadata_tiers.setdefault("track_tags", Counter())[tier] += 1
            elif isinstance(detail, dict):
                metadata_tiers.setdefault(field, Counter())[detail.get("confidence", "unknown")] += 1
        for field, detail in recomputed_metadata.items():
            if stored_metadata.get(field) != detail:
                metadata_drift.append({
                    "song_id": song_id, "field": field,
                    "stored": stored_metadata.get(field), "recomputed": detail,
                })

        if track_metadata.get("duration_ms") or track_metadata.get("duration"):
            coverage["duration"] += 1
            if not (track_metadata.get("duration_source") or track_metadata.get("duration_provider")):
                provenance_missing["duration"] += 1
        if track_metadata.get("lastfm_tags") or track_metadata.get("musicbrainz_tags") or track_metadata.get("musicbrainz_genres"):
            coverage["track_tags"] += 1
        audio = evidence.get("audio")
        if isinstance(audio, dict) and audio:
            coverage["audio_features"] += 1
        mood = record.get("mood") if isinstance(record.get("mood"), dict) else {}
        recording_mood = mood.get("recording_level") if isinstance(mood.get("recording_level"), dict) else {}
        if recording_mood.get("confidence") not in (None, "", "none", "unknown"):
            coverage["recording_mood"] += 1
        if evidence.get("lyrics") not in (None, "", [], {}):
            coverage["lyric_features"] += 1
        playability = evidence.get("spotify_playability")
        if isinstance(playability, dict) and playability.get("observations"):
            coverage["spotify_playability"] += 1

    candidates = alias_index.get("name_candidates", {})
    if isinstance(candidates, dict):
        candidate_aliases = sum(1 for rows in candidates.values() if isinstance(rows, list) and len(rows) > 1)

    source_tracks, track_problem = _read(music_root / "indexes" / "tracks.json")
    source_artists, artist_problem = _read(music_root / "indexes" / "artists.json")
    source_track_count = len(source_tracks) if isinstance(source_tracks, dict) else 0
    source_artist_count = len(source_artists) if isinstance(source_artists, dict) else 0
    library_source_ids = alias_index.get("source_track_ids", {})
    library_mbids = alias_index.get("recording_mbids", {})
    track_hits = 0
    if isinstance(source_tracks, dict):
        for source_id in source_tracks:
            if str(source_id).casefold().startswith("mbid:"):
                found = source_id in library_mbids or str(source_id)[5:] in library_mbids
            else:
                found = source_id in library_source_ids
            track_hits += int(bool(found))
    library_artist_names = {
        _norm(row.get("name") or row.get("artist"))
        for row in (alias_index.get("artists") or {}).values() if isinstance(row, dict)
    }
    artist_hits = 0
    if isinstance(source_artists, dict):
        for artist_id, row in source_artists.items():
            name = _norm(row.get("artist")) if isinstance(row, dict) else ""
            artist_hits += int(artist_id in (alias_index.get("artists") or {}) or bool(name and name in library_artist_names))

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ok": not errors,
        "songs_scanned": songs_seen,
        "identity_confidence": dict(identity_tiers),
        "identity_resolution_methods": dict(identity_methods),
        "identity_quality": dict(identity_quality),
        "identity_confidence_drift_count": len(identity_drift),
        "identity_confidence_drift_examples": identity_drift[:25],
        "metadata_confidence": {field: dict(counts) for field, counts in metadata_tiers.items()},
        "metadata_confidence_drift_count": len(metadata_drift),
        "metadata_confidence_drift_examples": metadata_drift[:25],
        "field_coverage": dict(coverage),
        "missing_provenance_counts": dict(provenance_missing),
        "ambiguous_name_aliases": candidate_aliases,
        "legacy_source_coverage": {
            "track_index_total": source_track_count,
            "track_index_resolved": track_hits,
            "track_index_unresolved": source_track_count - track_hits,
            "artist_index_total": source_artist_count,
            "artist_index_represented": artist_hits,
            "artist_index_unrepresented": source_artist_count - artist_hits,
            "track_index_error": track_problem,
            "artist_index_error": artist_problem,
        },
        "errors": errors,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--music-root", type=Path, default=MUSIC_ROOT)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON only")
    args = parser.parse_args(argv)
    report = inspect_confidence(args.root, args.music_root)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print("SHIT Library confidence audit")
        print(f"Status: {'OK' if report['ok'] else 'ERRORS'}")
        print(f"Songs scanned: {report['songs_scanned']:,}")
        print(f"Identity confidence: {report['identity_confidence']}")
        print(f"Identity confidence drift: {report['identity_confidence_drift_count']}")
        print(f"Metadata confidence drift: {report['metadata_confidence_drift_count']}")
        print(f"Legacy track coverage: {report['legacy_source_coverage']['track_index_resolved']:,}/{report['legacy_source_coverage']['track_index_total']:,}")
        print(f"Errors: {len(report['errors'])}")
        for error in report["errors"]:
            print(f"ERROR: {error}")
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())


# FILE OVERVIEW
# Purpose: Read-only confidence and field-evidence audit across canonical song records.
# Checks: Stored vs recomputed identity/metadata confidence, source-index coverage, field coverage and provenance.
# Safety: Never writes records, recalibrates scores, makes provider calls, or edits Spotify playlists.
# Run: python scripts/music/library_confidence_audit.py [--json] [--root PATH].
# Related: scripts/music/music_evidence.py, music_library.py, project/goals/library-confidence-verification/.
