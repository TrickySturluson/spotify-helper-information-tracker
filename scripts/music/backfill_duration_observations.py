#!/usr/bin/env python3
"""Backfill exact legacy duration-check provenance into canonical song records.

This is a local provenance migration, not an enrichment job: it makes no network
requests and never changes a duration value or song identity. Preview is default;
apply is explicit, backed up, atomic per file, and rolled back if health fails.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MUSIC_ROOT = REPO_ROOT / "assistant_data" / "music"
DEFAULT_LIBRARY_ROOT = DEFAULT_MUSIC_ROOT / "library"
HEALTH_CHECKER = REPO_ROOT / "scripts" / "music" / "library_health.py"


def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return default


def write_json_atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def epoch_iso(value):
    try:
        number = int(value)
        if number <= 0:
            return None
        return datetime.fromtimestamp(number, timezone.utc).isoformat()
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def provider_for_source(value):
    source = str(value or "").casefold()
    if "last.fm" in source or "lastfm" in source:
        return "lastfm"
    if "musicbrainz" in source:
        return "musicbrainz"
    return None


def _resolve_song_id(track, index):
    source_ids = index.get("source_track_ids") or {}
    recording_ids = index.get("recording_mbids") or {}
    songs = index.get("songs") or {}
    candidates = []
    track_id = str(track.get("track_id") or "").strip().casefold()
    track_mbid = str(track.get("track_mbid") or "").strip().casefold()
    if track_id:
        candidates.append(source_ids.get(track_id))
        candidates.append(songs.get(track_id, {}).get("id") if isinstance(songs.get(track_id), dict) else None)
    if track_mbid:
        candidates.extend([
            recording_ids.get(track_mbid),
            recording_ids.get(track_mbid.removeprefix("mbid:")),
            recording_ids.get("mbid:" + track_mbid.removeprefix("mbid:")),
        ])
    found = list(dict.fromkeys(value for value in candidates if value))
    return found[0] if len(found) == 1 else None, len(found) > 1


def _latest_observation(observations, provider, duration_ms, source):
    source_key = str(source or "").strip().casefold()
    rows = [
        row for row in observations
        if isinstance(row, dict)
        and row.get("provider") == provider
        and row.get("checked_at")
        and row.get("duration_ms") == duration_ms
        and str(row.get("source") or "").strip().casefold() == source_key
    ]
    return max(rows, key=lambda row: str(row.get("checked_at") or "")) if rows else None


def build_plan(library_root=DEFAULT_LIBRARY_ROOT, music_root=DEFAULT_MUSIC_ROOT):
    library_root = Path(library_root)
    music_root = Path(music_root)
    index = read_json(library_root / "library_index.json")
    if not isinstance(index, dict) or not isinstance(index.get("songs"), dict):
        raise RuntimeError("Canonical library index is missing or malformed; refusing duration provenance backfill.")

    counts = {
        "legacy_rows": 0, "legacy_with_timestamp": 0, "matched_canonical": 0,
        "candidate_observations": 0, "already_present": 0, "missing_alias": 0,
        "ambiguous_alias": 0, "missing_song_file": 0, "canonical_without_duration": 0,
        "duration_mismatch": 0, "source_mismatch": 0, "not_matched_status": 0,
        "unknown_provider": 0, "invalid_timestamp": 0, "duplicate_legacy_rows": 0,
    }
    song_cache = {}
    candidates = {}
    legacy_seen = {}

    shard_paths = sorted((music_root / "artists").glob("shard-*.json"))
    if not shard_paths:
        raise RuntimeError("No legacy artist shards found; refusing to infer duration provenance.")
    for shard_path in shard_paths:
        shard = read_json(shard_path)
        if not isinstance(shard, dict) or not isinstance(shard.get("artists"), dict):
            raise RuntimeError(f"Malformed legacy shard: {shard_path}")
        for artist_row in shard["artists"].values():
            if not isinstance(artist_row, dict):
                continue
            for track in (artist_row.get("tracks") or {}).values():
                if not isinstance(track, dict):
                    continue
                counts["legacy_rows"] += 1
                source_track_id = str(track.get("track_id") or "").strip().casefold()
                if source_track_id:
                    fingerprint = (
                        track.get("duration_ms"), track.get("duration_source"),
                        track.get("metadata_checked_at"), track.get("metadata_status"),
                    )
                    prior = legacy_seen.get(source_track_id)
                    if prior is not None:
                        if prior != fingerprint:
                            counts["duplicate_legacy_rows"] += 1
                            continue
                        continue
                    legacy_seen[source_track_id] = fingerprint

                provider = provider_for_source(track.get("duration_source"))
                if not provider:
                    counts["unknown_provider"] += 1
                    continue
                checked_at = epoch_iso(
                    track.get("metadata_checked_at") if provider == "lastfm"
                    else track.get("musicbrainz_checked_at")
                )
                if not checked_at:
                    counts["invalid_timestamp"] += 1
                    continue
                counts["legacy_with_timestamp"] += 1
                status = str(
                    track.get("metadata_status") if provider == "lastfm"
                    else track.get("musicbrainz_status") or track.get("metadata_status") or ""
                ).casefold()
                if status != "matched":
                    counts["not_matched_status"] += 1
                    continue
                song_id, ambiguous = _resolve_song_id(track, index)
                if ambiguous:
                    counts["ambiguous_alias"] += 1
                    continue
                if not song_id:
                    counts["missing_alias"] += 1
                    continue
                entry = index["songs"].get(song_id)
                relative = entry.get("path") if isinstance(entry, dict) else None
                if not relative:
                    counts["missing_song_file"] += 1
                    continue
                path = library_root / relative
                if song_id not in song_cache:
                    song_cache[song_id] = read_json(path)
                song = song_cache[song_id]
                if not isinstance(song, dict):
                    counts["missing_song_file"] += 1
                    continue
                metadata = (song.get("evidence") or {}).get("track_metadata") or {}
                if not isinstance(metadata, dict) or metadata.get("duration_ms") is None:
                    counts["canonical_without_duration"] += 1
                    continue
                try:
                    legacy_duration = int(track.get("duration_ms") or 0)
                    canonical_duration = int(metadata.get("duration_ms") or 0)
                except (TypeError, ValueError):
                    counts["duration_mismatch"] += 1
                    continue
                if legacy_duration <= 0 or canonical_duration != legacy_duration:
                    counts["duration_mismatch"] += 1
                    continue
                legacy_source = str(track.get("duration_source") or "").strip().casefold()
                canonical_source = str(metadata.get("duration_source") or "").strip().casefold()
                if not legacy_source or legacy_source != canonical_source:
                    counts["source_mismatch"] += 1
                    continue
                counts["matched_canonical"] += 1
                observation = {
                    "provider": provider,
                    "checked_at": checked_at,
                    "status": status,
                    "duration_ms": legacy_duration,
                    "source": str(track.get("duration_source") or ""),
                    "match_type": track.get("match_type"),
                    "confidence": track.get("confidence"),
                    "retry_after": int(track.get("retry_after") or 0),
                    "provenance": "legacy_music_metadata_shard",
                }
                observations = metadata.get("duration_observations")
                if observations is None:
                    observations = []
                if not isinstance(observations, list):
                    counts["source_mismatch"] += 1
                    continue
                signature = (provider, checked_at, legacy_duration, status, legacy_source)
                existing_signatures = {
                    (row.get("provider"), row.get("checked_at"), row.get("duration_ms"),
                     row.get("status"), str(row.get("source") or "").strip().casefold())
                    for row in observations if isinstance(row, dict)
                }
                if signature in existing_signatures:
                    counts["already_present"] += 1
                    continue
                current = _latest_observation(observations, provider, legacy_duration, legacy_source)
                if current and str(current.get("checked_at") or "") >= checked_at:
                    counts["already_present"] += 1
                    continue
                candidates.setdefault(song_id, {
                    "path": path, "song": song, "observations": list(observations), "new": []
                })["new"].append(observation)

    changes = {}
    selected = []
    for song_id, item in candidates.items():
        signatures = {
            (row.get("provider"), row.get("checked_at"), row.get("duration_ms"))
            for row in item["observations"] if isinstance(row, dict)
        }
        additions = []
        for observation in item["new"]:
            signature = (observation["provider"], observation["checked_at"], observation["duration_ms"])
            if signature not in signatures:
                signatures.add(signature)
                additions.append(observation)
        if not additions:
            continue
        updated = json.loads(json.dumps(item["song"]))
        metadata = updated.setdefault("evidence", {}).setdefault("track_metadata", {})
        metadata["duration_observations"] = sorted(
            item["observations"] + additions, key=lambda row: str(row.get("checked_at") or "")
        )
        changes[item["path"]] = updated
        counts["candidate_observations"] += len(additions)
        selected.append({
            "song_id": song_id,
            "artist": (updated.get("identity") or {}).get("artist"),
            "title": (updated.get("identity") or {}).get("title"),
            "path": str(item["path"].relative_to(library_root)),
            "observations_added": len(additions),
            "provider": additions[-1]["provider"],
            "checked_at": additions[-1]["checked_at"],
        })

    report = {
        "ok": True,
        "mode": "preview",
        "library_root": str(library_root),
        "legacy_shards_scanned": len(shard_paths),
        "canonical_song_count": len(index.get("songs") or {}),
        "counts": counts,
        "songs_to_update": len(changes),
        "safe_to_apply": counts["ambiguous_alias"] == 0 and counts["duplicate_legacy_rows"] == 0,
        "provider_requests": 0,
        "writes": 0,
        "spotify_playlist_writes": 0,
        "selected": selected[:50],
    }
    return report, changes


def apply_plan(changes, library_root=DEFAULT_LIBRARY_ROOT, music_root=DEFAULT_MUSIC_ROOT, health_check=True):
    library_root = Path(library_root)
    music_root = Path(music_root)
    if not changes:
        return {"backup_root": None, "changed_files": 0, "writes": 0}
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = music_root / f"library.backup-duration-observations-{stamp}"
    manifest = {"created_at": datetime.now(timezone.utc).isoformat(), "files": []}
    for path in changes:
        relative = Path(path).relative_to(library_root)
        backup_path = backup_root / relative
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup_path)
        manifest["files"].append({
            "path": str(relative),
            "backup_path": str(backup_path.relative_to(music_root)),
            "sha256_before": sha256(path),
        })
    write_json_atomic(backup_root / "manifest.json", manifest)
    written = []
    try:
        for path, record in changes.items():
            write_json_atomic(path, record)
            written.append(Path(path))
        if health_check:
            completed = subprocess.run(
                [sys.executable, str(HEALTH_CHECKER), "--root", str(library_root), "--json"],
                cwd=REPO_ROOT, capture_output=True, text=True, check=False,
            )
            if completed.returncode != 0:
                raise RuntimeError("Post-backfill health check failed: " + completed.stdout[-2000:] + completed.stderr[-2000:])
            result = json.loads(completed.stdout)
            if result.get("ok") is not True:
                raise RuntimeError("Post-backfill health report is not clean.")
    except Exception:
        for path in written:
            relative = path.relative_to(library_root)
            shutil.copy2(backup_root / relative, path)
        raise
    return {"backup_root": str(backup_root), "changed_files": len(written), "writes": len(written)}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Backfill exact legacy duration-check timestamps into canonical song evidence.")
    parser.add_argument("--root", type=Path, default=DEFAULT_LIBRARY_ROOT)
    parser.add_argument("--music-root", type=Path, default=DEFAULT_MUSIC_ROOT)
    parser.add_argument("--apply", action="store_true", help="Apply exact missing-only provenance updates after backup.")
    parser.add_argument("--yes", action="store_true", help="Confirm the provenance backfill (requires --apply).")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)
    if args.yes and not args.apply:
        parser.error("--yes requires --apply")
    if args.apply and not args.yes:
        parser.error("--apply requires --yes")
    report, changes = build_plan(args.root, args.music_root)
    if args.apply:
        if not report["safe_to_apply"]:
            print(json.dumps(report, indent=2))
            raise SystemExit("Refusing apply: conflicts or ambiguous aliases must be resolved first.")
        result = apply_plan(changes, args.root, args.music_root)
        report["mode"] = "applied"
        report["apply_result"] = result
        report["writes"] = result["changed_files"]
    print(json.dumps(report, indent=2) if args.json else json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# FILE OVERVIEW
# Purpose: Recover exact Last.fm/MusicBrainz duration-check timestamps from legacy shards.
# Inputs: Legacy assistant_data/music/artists/shard-*.json and canonical Library index/song files.
# Output: Adds append-only evidence.track_metadata.duration_observations to existing song records.
# Safety: Exact ID, duration and source match only; preview by default; no provider calls.
# Apply: Requires --apply --yes; timestamped backup, atomic file writes, and post-write health check.
# Related: metadata_freshness.py; library_health.py; music_library.py.
