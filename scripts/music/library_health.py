#!/usr/bin/env python3
"""Read-only structural and referential health report for the canonical music Library.

Run: python scripts/music/library_health.py [--root assistant_data/music/library]
This checker never repairs files, rebuilds indexes, calls providers, or edits playlists.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROOT = REPO_ROOT / "assistant_data" / "music" / "library"
COLLECTIONS = {
    "songs": "song.json",
    "artists": "artist.json",
    "albums": "album.json",
}


def _safe_id(value):
    value = str(value or "").strip().casefold()
    if value.startswith("mbid:"):
        return "mbid-" + "".join(c for c in value[5:] if c.isalnum() or c == "-")
    if value.startswith("spotify:"):
        return "spotify-" + "".join(c for c in value.split(":")[-1] if c.isalnum())
    return "".join(c if c.isalnum() or c in "_-" else "-" for c in value).strip("-") or "unknown"


def _read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except FileNotFoundError:
        return None, "missing"
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return None, f"{type(error).__name__}: {error}"


def _inside_root(root, path):
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (OSError, ValueError):
        return False


def inspect_library(root=DEFAULT_ROOT):
    """Return a read-only health report; never instantiate the mutating lazy resolver."""
    root = Path(root)
    errors, warnings = [], []
    records = {kind: {} for kind in COLLECTIONS}
    paths = {kind: {} for kind in COLLECTIONS}
    indexed_paths = {kind: set() for kind in COLLECTIONS}

    if not root.is_dir():
        return {
            "schema_version": 1,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "root": str(root),
            "ok": False,
            "counts": {"songs": 0, "artists": 0, "albums": 0},
            "errors": [f"Library root is missing or not a directory: {root}"],
            "warnings": [],
        }

    for kind, filename in COLLECTIONS.items():
        directory = root / kind
        if not directory.exists():
            warnings.append(f"Collection directory is missing: {kind}/")
            continue
        for path in sorted(directory.rglob(filename)):
            if not _inside_root(root, path):
                errors.append(f"{kind} record resolves outside Library root: {path}")
                continue
            record, problem = _read_json(path)
            if problem:
                errors.append(f"{kind} record is unreadable ({problem}): {path.relative_to(root)}")
                continue
            if not isinstance(record, dict):
                errors.append(f"{kind} record must be a JSON object: {path.relative_to(root)}")
                continue
            record_id = record.get("id")
            if not isinstance(record_id, str) or not record_id.strip():
                errors.append(f"{kind} record has no stable id: {path.relative_to(root)}")
                continue
            if record_id in records[kind]:
                errors.append(f"duplicate {kind} record id {record_id!r}: {paths[kind][record_id]} and {path.relative_to(root)}")
                continue
            records[kind][record_id] = record
            relative = path.relative_to(root).as_posix()
            paths[kind][record_id] = relative
            expected = Path(kind) / _safe_id(record_id)[:2] / _safe_id(record_id) / filename
            if Path(relative) != expected:
                warnings.append(f"{kind} record path does not match stable-id shard convention: {relative} (expected {expected.as_posix()})")

    index_path = root / "library_index.json"
    index, problem = _read_json(index_path)
    if problem:
        errors.append(f"Library index is unreadable ({problem}): library_index.json")
        index = {}
    elif not isinstance(index, dict):
        errors.append("Library index must be a JSON object.")
        index = {}

    index_collections = {
        "songs": index.get("songs", index.get("recordings", {})),
        "artists": index.get("artists", {}),
        "albums": index.get("albums", {}),
    }
    for kind, entries in index_collections.items():
        if not isinstance(entries, dict):
            errors.append(f"Library index collection must be an object: {kind}")
            continue
        for record_id, entry in entries.items():
            if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
                errors.append(f"{kind} index entry is malformed: {record_id}")
                continue
            relative = Path(entry["path"])
            target = root / relative
            if not _inside_root(root, target):
                errors.append(f"{kind} index path escapes Library root: {record_id} -> {entry['path']}")
                continue
            indexed_paths[kind].add(relative.as_posix())
            record, read_problem = _read_json(target)
            if read_problem or not isinstance(record, dict):
                errors.append(f"{kind} index target is missing or invalid: {record_id} -> {entry['path']}")
                continue
            if record.get("id") != record_id:
                errors.append(f"{kind} index/record ID mismatch: {record_id} -> {entry['path']}")
            if record_id not in records[kind]:
                errors.append(f"{kind} index target is not present in the scanned canonical collection: {record_id}")

    for kind in COLLECTIONS:
        for record_id, relative in paths[kind].items():
            if relative not in indexed_paths[kind]:
                warnings.append(f"canonical {kind} record is not referenced by the index: {record_id} ({relative})")

    song_ids = set(records["songs"])
    artist_ids = set(records["artists"])
    album_ids = set(records["albums"])

    for alias_map in ("spotify_ids", "recording_mbids", "isrcs", "source_track_ids"):
        aliases = index.get(alias_map, {})
        if not isinstance(aliases, dict):
            errors.append(f"Alias map must be an object: {alias_map}")
            continue
        for alias, target in aliases.items():
            if target not in song_ids:
                errors.append(f"{alias_map} alias references missing song: {alias} -> {target}")

    candidates = index.get("name_candidates", {})
    if not isinstance(candidates, dict):
        errors.append("name_candidates must be an object")
    else:
        for alias, targets in candidates.items():
            if not isinstance(targets, list) or not targets:
                errors.append(f"name candidate alias has no candidate list: {alias!r}")
                continue
            if len(targets) != len(set(targets)):
                warnings.append(f"name candidate alias contains duplicate candidate IDs: {alias!r}")
            for target in targets:
                if target not in song_ids:
                    errors.append(f"name candidate alias references missing song: {alias!r} -> {target}")

    for song_id, song in records["songs"].items():
        identity = song.get("identity") if isinstance(song.get("identity"), dict) else {}
        if not identity.get("artist") or not identity.get("title"):
            errors.append(f"song identity is missing artist/title: {song_id}")
        relations = song.get("relations") if isinstance(song.get("relations"), dict) else {}
        artist_id = identity.get("artist_id")
        album_id = identity.get("album_id")
        artist_path = relations.get("artist_path")
        if artist_id and artist_id not in artist_ids:
            errors.append(f"song references missing artist identity: {song_id} -> {artist_id}")
        if artist_path:
            target = root / artist_path
            if not _inside_root(root, target):
                errors.append(f"song artist relation escapes Library root: {song_id} -> {artist_path}")
            else:
                related, related_problem = _read_json(target)
                if related_problem or not isinstance(related, dict):
                    errors.append(f"song related artist record is missing or invalid: {song_id}")
                elif artist_id and related.get("id") != artist_id:
                    errors.append(f"song related artist identity mismatch: {song_id}")
        elif artist_id:
            errors.append(f"song has artist_id but no artist_path: {song_id}")
        if album_id and album_id not in album_ids:
            errors.append(f"song references missing album identity: {song_id} -> {album_id}")
        album_path = relations.get("album_path")
        if album_path:
            target = root / album_path
            if not _inside_root(root, target):
                errors.append(f"song album relation escapes Library root: {song_id} -> {album_path}")
            else:
                related, related_problem = _read_json(target)
                if related_problem or not isinstance(related, dict):
                    errors.append(f"song related album record is missing or invalid: {song_id}")
                elif album_id and related.get("id") != album_id:
                    errors.append(f"song related album identity mismatch: {song_id}")
        elif album_id:
            errors.append(f"song has album_id but no album_path: {song_id}")

    for album_id, album in records["albums"].items():
        artist_id = album.get("artist_id")
        if artist_id and artist_id not in artist_ids:
            errors.append(f"album references missing artist: {album_id} -> {artist_id}")
        for song_id in album.get("song_ids") or []:
            if song_id not in song_ids:
                errors.append(f"album references missing song: {album_id} -> {song_id}")

    for artist_id, artist in records["artists"].items():
        for album_id in artist.get("album_ids") or []:
            if album_id not in album_ids:
                errors.append(f"artist references missing album: {artist_id} -> {album_id}")

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "ok": not errors,
        "counts": {kind: len(records[kind]) for kind in COLLECTIONS},
        "index_counts": {kind: len(entries) if isinstance(entries, dict) else 0 for kind, entries in index_collections.items()},
        "alias_counts": {
            name: len(index.get(name, {})) if isinstance(index.get(name, {}), dict) else 0
            for name in ("spotify_ids", "recording_mbids", "isrcs", "source_track_ids", "name_candidates")
        },
        "errors": errors,
        "warnings": warnings,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON only")
    args = parser.parse_args(argv)
    report = inspect_library(args.root)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print("SHIT canonical Library health")
        print(f"Status: {'OK' if report['ok'] else 'ERRORS'}")
        print("Records: " + ", ".join(f"{kind}={count:,}" for kind, count in report["counts"].items()))
        print(f"Errors: {len(report['errors'])}; warnings: {len(report['warnings'])}")
        for issue in report["errors"]:
            print(f"ERROR: {issue}")
        for issue in report["warnings"]:
            print(f"WARNING: {issue}")
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())


# FILE OVERVIEW
# Purpose: Comprehensive read-only structural and referential health check for The Library.
# Checks: JSON validity, stable IDs, sharded paths, index targets, aliases, and entity relations.
# Safety: Never instantiates the lazy resolver, rebuilds indexes, makes provider calls, or writes files.
# Run: python scripts/music/library_health.py [--json] [--root PATH].
# Related: scripts/music/music_library.py, library_cli.py, project/goals/library-health-maintenance/.
