#!/usr/bin/env python3
"""Build a read-only, prioritized metadata coverage report for the canonical SHIT Library.

This tool never calls providers and never modifies Library records. It reads canonical
song/artist/album JSON, classifies missing fields and provider outcomes, and emits a
bounded work queue that later enrichment jobs can consume safely.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LIBRARY = ROOT / "assistant_data" / "music" / "library"


def read_json(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except (OSError, ValueError, TypeError):
        return None


def present(value):
    return value not in (None, "", [], {})


def classify_provider(status, retry_after):
    status = str(status or "").strip().casefold()
    if status in {"matched", "success", "ok"}:
        return "matched"
    if status in {"not_found", "no_tags", "negative", "no_match"}:
        return "negative_cached"
    if status in {"rate_limited", "http_429", "http_503", "temporary_error", "error", "failed"}:
        return "transient_or_error"
    if retry_after:
        return "cooldown"
    return "not_checked"


def build_report(library_root, limit=200):
    root = Path(library_root)
    counts = Counter()
    provider = Counter()
    queue = []
    errors = []
    song_paths = sorted((root / "songs").glob("**/song.json"))
    counts["songs_seen"] = len(song_paths)

    for path in song_paths:
        record = read_json(path)
        if not record:
            counts["invalid_song_records"] += 1
            errors.append({"path": str(path.relative_to(root)), "issue": "invalid_or_unreadable_json"})
            continue
        identity = record.get("identity") or {}
        evidence = record.get("evidence") or {}
        track_meta = evidence.get("track_metadata") or {}
        audio = evidence.get("audio") or {}
        lyrics = evidence.get("lyrics")
        mood = record.get("mood") or {}
        missing = []

        if not present(identity.get("recording_mbid")):
            missing.append("recording_mbid")
        if not present(identity.get("isrc")):
            missing.append("isrc")
        if not present(identity.get("spotify_id")):
            missing.append("spotify_id")
        if not present(track_meta.get("duration_ms")):
            missing.append("duration")
        if not present(audio):
            missing.append("audio_features")
        if not present(lyrics):
            missing.append("lyrics")
        recording_mood = mood.get("recording_level") or {}
        if not present(recording_mood.get("moods")):
            missing.append("track_mood")

        lastfm_state = classify_provider(
            track_meta.get("lastfm_status") or (record.get("sources") or {}).get("lastfm_status", {}).get("status"),
            track_meta.get("retry_after"),
        )
        provider["lastfm_" + lastfm_state] += 1

        artist_path = record.get("relations", {}).get("artist_path")
        album_path = record.get("relations", {}).get("album_path")
        if artist_path and not (root / artist_path).is_file():
            missing.append("artist_record_missing")
        if album_path and not (root / album_path).is_file():
            missing.append("album_record_missing")

        for field in missing:
            counts["missing_" + field] += 1
        if missing:
            plays = (record.get("listening_context") or {}).get("all_time_plays") or 0
            recent = (record.get("listening_context") or {}).get("recent_plays") or 0
            # Priority is a deterministic score, not a confidence claim.
            score = min(int(plays or 0), 1000) + min(int(recent or 0), 500) * 3
            queue.append({
                "song_id": record.get("id"),
                "artist": identity.get("artist"),
                "track": identity.get("title"),
                "missing": missing,
                "priority_score": score,
                "lastfm_state": lastfm_state,
                "path": str(path.relative_to(root)),
            })

    for kind, folder, filename in (
        ("artists", "artists", "artist.json"),
        ("albums", "albums", "album.json"),
    ):
        paths = sorted((root / folder).glob("**/" + filename))
        counts[kind + "_seen"] = len(paths)
        for path in paths:
            record = read_json(path)
            if not record:
                counts["invalid_" + kind] += 1
                continue
            evidence = record.get("evidence") or {}
            if kind == "artists":
                fields = ("biography", "genres", "tags", "images")
            else:
                fields = ("tracklist", "description", "artwork", "release_date")
            absent = [field for field in fields if not present(evidence.get(field))]
            counts[kind + "_with_gaps"] += bool(absent)
            for field in absent:
                counts[kind + "_missing_" + field] += 1

    queue.sort(key=lambda item: (-item["priority_score"], item["artist"] or "", item["track"] or "", item["song_id"] or ""))
    counts["songs_with_gaps"] = len(queue)
    return {
        "schema_version": 1,
        "mode": "read_only_no_provider_calls",
        "library_root": str(root),
        "counts": dict(sorted(counts.items())),
        "provider_outcomes": dict(sorted(provider.items())),
        "priority_queue": queue[:max(0, int(limit))],
        "queue_total": len(queue),
        "errors": errors[:100],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library-root", type=Path, default=DEFAULT_LIBRARY)
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--output", type=Path, help="optional report destination; never writes into the Library")
    args = parser.parse_args(argv)
    report = build_report(args.library_root, args.limit)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    if args.json or args.output:
        print(rendered, end="")
    else:
        print("SHIT Library metadata coverage (read-only)")
        print("Songs: {songs_seen}; with gaps: {songs_with_gaps}".format(**report["counts"]))
        for key, value in report["counts"].items():
            if key.startswith("missing_") or key.startswith("artists_missing_") or key.startswith("albums_missing_"):
                print(f"  {key}: {value}")
        print("Provider outcomes:")
        for key, value in report["provider_outcomes"].items():
            print(f"  {key}: {value}")
        print(f"Priority queue: {report['queue_total']} songs; showing {len(report['priority_queue'])}")
        for row in report["priority_queue"][:20]:
            print(f"  {row['priority_score']:>5}  {row['artist']} — {row['track']} [{', '.join(row['missing'])}]")


if __name__ == "__main__":
    main()


# FILE OVERVIEW
# Purpose: Quantify canonical Library metadata gaps and generate a deterministic
#          priority queue for later bounded enrichment passes.
# Safety: Read-only; makes no provider requests and does not edit Library records.
# Priority: Uses existing listening evidence only; recommendations/discovery events
#           are not used as plays or preference signals.
# Output: Console summary or JSON via --json / --output; reports may be stored outside
#         assistant_data/music/library to avoid mixing reports with canonical records.
# Run: python scripts/music/library_coverage_report.py
# Related: scripts/music/music_library.py; scripts/music/prepare_music_library.py.
