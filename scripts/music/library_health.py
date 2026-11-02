#!/usr/bin/env python3
"""Read-only structural and referential health report for the canonical music Library.

Run: python scripts/music/library_health.py [--root assistant_data/music/library]
This checker never repairs files, rebuilds indexes, calls providers, or edits playlists.
"""
import argparse
import json
import re
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
        return "mbid-" + re.sub(r"[^a-z0-9-]", "", value[5:])
    if value.startswith("spotify:"):
        return "spotify-" + re.sub(r"[^a-z0-9]", "", value.split(":")[-1])
    return re.sub(r"[^a-z0-9_-]", "-", value).strip("-") or "unknown"


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


PLAYABILITY_STATUSES = {"playable", "unplayable", "restricted", "unknown", "not_found"}


def _spotify_track_id(value):
    return str(value or "").strip().rsplit(":", 1)[-1].casefold()


def _parse_observation_time(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def _validate_playability(song_id, song, errors, warnings):
    """Validate optional market-scoped playability evidence without changing it."""
    evidence = song.get("evidence") if isinstance(song.get("evidence"), dict) else {}
    playability = evidence.get("spotify_playability")
    if playability is None:
        return
    if not isinstance(playability, dict):
        errors.append(f"song Spotify playability evidence must be an object: {song_id}")
        return

    observations = playability.get("observations")
    latest_by_market = playability.get("latest_by_market")
    if not isinstance(observations, list):
        errors.append(f"song Spotify playability observations must be a list: {song_id}")
        return
    if not isinstance(latest_by_market, dict):
        errors.append(f"song Spotify playability latest_by_market must be an object: {song_id}")
        return

    identity = song.get("identity") if isinstance(song.get("identity"), dict) else {}
    canonical_spotify_id = _spotify_track_id(identity.get("spotify_id"))
    expected_latest = {}
    seen = set()
    for position, observation in enumerate(observations):
        label = f"{song_id} observation[{position}]"
        if not isinstance(observation, dict):
            errors.append(f"Spotify playability observation must be an object: {label}")
            continue
        encoded = json.dumps(observation, sort_keys=True, ensure_ascii=False)
        if encoded in seen:
            warnings.append(f"duplicate Spotify playability observation: {label}")
        seen.add(encoded)

        market = observation.get("market")
        if not isinstance(market, str) or not market.strip():
            errors.append(f"Spotify playability observation has no market: {label}")
            continue
        market_key = market.upper()
        status = observation.get("status")
        if status not in PLAYABILITY_STATUSES:
            errors.append(f"Spotify playability observation has invalid status {status!r}: {label}")
        playable = observation.get("is_playable")
        if playable is not None and not isinstance(playable, bool):
            errors.append(f"Spotify playability is_playable must be boolean or null: {label}")
        if status == "playable" and playable is not True:
            errors.append(f"playable observation does not have is_playable=true: {label}")
        elif status == "unplayable" and playable is not False:
            errors.append(f"unplayable observation does not have is_playable=false: {label}")
        elif status == "restricted" and not (
            observation.get("restrictions_reason") or observation.get("restrictions")
        ):
            errors.append(f"restricted observation has no restriction evidence: {label}")
        elif status in {"unknown", "not_found"} and playable is not None:
            errors.append(f"indeterminate playability observation has a boolean is_playable: {label}")

        checked_at = observation.get("checked_at")
        parsed_time = _parse_observation_time(checked_at)
        if parsed_time is None:
            errors.append(f"Spotify playability observation has missing/invalid checked_at: {label}")

        requested_id = _spotify_track_id(observation.get("requested_spotify_id"))
        returned_id = _spotify_track_id(observation.get("returned_spotify_id"))
        linked_id = _spotify_track_id(observation.get("linked_from_spotify_id"))
        if not requested_id:
            errors.append(f"Spotify playability observation has no requested Spotify ID: {label}")
        if canonical_spotify_id and requested_id and requested_id != canonical_spotify_id:
            errors.append(f"Spotify playability requested ID does not match song identity: {label}")
        if returned_id and requested_id and returned_id != requested_id and linked_id != requested_id:
            errors.append(f"Spotify relinked ID lacks matching linked_from identity: {label}")

        prior = expected_latest.get(market_key)
        if prior is None or str(checked_at or "") >= str(prior.get("checked_at") or ""):
            expected_latest[market_key] = observation

    if set(latest_by_market) != set(expected_latest):
        errors.append(f"Spotify playability latest_by_market keys do not match observations: {song_id}")
    for market_key, expected in expected_latest.items():
        actual = latest_by_market.get(market_key)
        if not isinstance(actual, dict):
            errors.append(f"Spotify playability latest market entry is missing/malformed: {song_id} [{market_key}]")
        elif actual != expected:
            errors.append(f"Spotify playability latest market entry is stale or inconsistent: {song_id} [{market_key}]")


def _validate_duration_observations(song_id, song, errors, warnings):
    """Validate optional field-level duration provenance history without rewriting it."""
    evidence = song.get("evidence") if isinstance(song.get("evidence"), dict) else {}
    metadata = evidence.get("track_metadata") if isinstance(evidence.get("track_metadata"), dict) else {}
    observations = metadata.get("duration_observations")
    if observations is None:
        return
    if not isinstance(observations, list):
        errors.append(f"song duration_observations must be a list: {song_id}")
        return

    seen = set()
    for position, observation in enumerate(observations):
        label = f"{song_id} duration_observations[{position}]"
        if not isinstance(observation, dict):
            errors.append(f"duration observation must be an object: {label}")
            continue
        encoded = json.dumps(observation, sort_keys=True, ensure_ascii=False)
        if encoded in seen:
            warnings.append(f"duplicate duration observation: {label}")
        seen.add(encoded)

        provider = observation.get("provider")
        if provider not in {"lastfm", "musicbrainz"}:
            errors.append(f"duration observation has unsupported provider {provider!r}: {label}")
        checked_at = observation.get("checked_at")
        if _parse_observation_time(checked_at) is None:
            errors.append(f"duration observation has missing/invalid checked_at: {label}")
        status = observation.get("status")
        if not isinstance(status, str) or not status.strip():
            errors.append(f"duration observation has no status: {label}")
        source = str(observation.get("source") or "").strip()
        if not source:
            errors.append(f"duration observation has no source: {label}")
        elif provider == "lastfm" and "last.fm" not in source.casefold() and "lastfm" not in source.casefold():
            errors.append(f"Last.fm duration observation source/provider mismatch: {label}")
        elif provider == "musicbrainz" and "musicbrainz" not in source.casefold():
            errors.append(f"MusicBrainz duration observation source/provider mismatch: {label}")
        try:
            duration_ms = int(observation.get("duration_ms") or 0)
            if duration_ms <= 0:
                raise ValueError
        except (TypeError, ValueError):
            errors.append(f"duration observation has invalid duration_ms: {label}")
        retry_after = observation.get("retry_after")
        if retry_after is not None:
            try:
                if int(retry_after) < 0:
                    raise ValueError
            except (TypeError, ValueError):
                errors.append(f"duration observation has invalid retry_after: {label}")


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
        _validate_playability(song_id, song, errors, warnings)
        _validate_duration_observations(song_id, song, errors, warnings)
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
