#!/usr/bin/env python3
"""Build read-only five-target playlist-fit previews from canonical SHIT data.

No Spotify API calls, human-rating reads, playlist writes, or title/artist-only
identity joins are performed. Candidate input is an identity-only JSON file.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.spotify.playlist_fit_model import (
    MODEL_VERSION, build_reference_profile, score_track, track_from_library_record,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LIBRARY = REPO_ROOT / "assistant_data/music/library"
DEFAULT_MUSIC = REPO_ROOT / "assistant_data/music"
DEFAULT_SPOTIFY = REPO_ROOT / "assistant_data/spotify"
DEFAULT_OUTPUT = DEFAULT_SPOTIFY / "playlist_fit_preview.json"


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def spotify_uri(value: Any) -> str | None:
    raw = str(value or "").strip()
    if raw.startswith("spotify:track:"):
        return raw
    if raw.startswith("https://open.spotify.com/track/"):
        return "spotify:track:" + raw.split("/track/", 1)[1].split("?", 1)[0]
    if len(raw) == 22 and raw.isalnum():
        return "spotify:track:" + raw
    return None


def load_candidate_identities(path: Path) -> list[dict]:
    """Accept a list or {tracks:[...]}; intentionally extract IDs only."""
    payload = read_json(path)
    rows = payload if isinstance(payload, list) else payload.get("tracks") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise ValueError("candidate file must be a JSON list or an object with a tracks list")
    candidates, seen = [], set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        uri = spotify_uri(row.get("uri") or row.get("spotify_uri") or row.get("track_uri")
                          or row.get("spotify_id") or row.get("id"))
        if not uri or uri in seen:
            continue
        seen.add(uri)
        candidates.append({"uri": uri, "title": str(row.get("title") or row.get("name") or ""),
                           "artist": str(row.get("artist") or "")})
    if not candidates:
        raise ValueError("candidate file contains no valid Spotify track IDs")
    return candidates


def load_library_records(root: Path, music_root: Path) -> tuple[dict, dict]:
    """Read canonical songs and stable-ID keyed track-profile cache."""
    records = {}
    for path in sorted((root / "songs").rglob("song.json")):
        record = read_json(path)
        if not isinstance(record, dict):
            continue
        identity = record.get("identity") if isinstance(record.get("identity"), dict) else {}
        spotify_id = str(identity.get("spotify_id") or "").strip()
        uri = spotify_uri(spotify_id)
        if uri:
            records[uri] = record
    cache = read_json(music_root / "track_profiles.json")
    if not isinstance(cache, dict):
        raise ValueError("track_profiles.json must contain an object")
    return records, index_track_profiles(cache)


def index_track_profiles(cache: dict) -> dict:
    """Index cache rows once by their stable recording/source ID."""
    indexed = {}
    for key, row in cache.items():
        if isinstance(row, dict):
            stable_id = str(row.get("track_id") or key).casefold()
            if stable_id:
                indexed[stable_id] = row
    return indexed


def profile_for_record(record: dict, cache: dict) -> dict | None:
    identity = record.get("identity") if isinstance(record.get("identity"), dict) else {}
    candidates = []
    if identity.get("source_track_id"):
        candidates.append(str(identity["source_track_id"]).casefold())
    if identity.get("recording_mbid"):
        candidates.append("mbid:" + str(identity["recording_mbid"]).casefold().removeprefix("mbid:"))
    if identity.get("spotify_id"):
        candidates.append("spotify:track:" + str(identity["spotify_id"]).casefold().rsplit(":", 1)[-1])
    for stable in candidates:
        row = cache.get(stable)
        if isinstance(row, dict) and str(row.get("track_id") or stable).casefold() == stable:
            return row
    return None


def load_reference_targets(spotify_root: Path) -> dict:
    roles = read_json(spotify_root / "playlist_roles.json")
    if not isinstance(roles, dict) or not isinstance(roles.get("playlists"), dict):
        raise ValueError("playlist_roles.json has an invalid schema")
    targets = {}
    for playlist_id, role in roles["playlists"].items():
        if not isinstance(role, dict) or role.get("role") != "sorter_calibration_target":
            continue
        relative = role.get("snapshot_record")
        expected_name = f"{playlist_id}.json"
        if not relative or Path(str(relative)).name != expected_name:
            raise ValueError(f"target {playlist_id} has an invalid snapshot path")
        path = spotify_root / "playlists" / expected_name
        snapshot = read_json(path)
        if str(snapshot.get("id") or "") != playlist_id:
            raise ValueError(f"snapshot identity mismatch for target {playlist_id}")
        items = snapshot.get("items") if isinstance(snapshot, dict) else None
        reported = snapshot.get("total_items_reported")
        fetched = snapshot.get("item_count_fetched")
        if snapshot.get("items_accessible") is not True or not isinstance(items, list):
            raise ValueError(f"target {playlist_id} is inaccessible; refusing to treat it as empty")
        if reported is not None and int(reported) != len(items):
            raise ValueError(f"target {playlist_id} count mismatch: reported={reported}, fetched={len(items)}")
        if fetched is not None and int(fetched) != len(items):
            raise ValueError(f"target {playlist_id} fetched-count mismatch")
        targets[playlist_id] = {
            "name": role.get("name") or snapshot.get("name") or playlist_id,
            "snapshot_id": snapshot.get("snapshot_id"),
            "captured_at": snapshot.get("captured_at"),
            "items": [item for item in items if isinstance(item, dict)
                      and item.get("type", "track") == "track" and spotify_uri(item.get("uri") or item.get("id"))],
        }
    if len(targets) != 5:
        raise ValueError(f"expected exactly five registered calibration targets, found {len(targets)}")
    return targets


def build_preview(candidates: list[dict], targets: dict, records: dict, cache: dict) -> dict:
    heldout = {candidate["uri"] for candidate in candidates}
    reference_tracks = {}
    for playlist_id, target in targets.items():
        tracks = []
        for item in target["items"]:
            uri = spotify_uri(item.get("uri") or item.get("id"))
            record = records.get(uri)
            if record is None:
                continue
            tracks.append(track_from_library_record(record, profile_for_record(record, cache)))
        reference_tracks[playlist_id] = tracks

    target_profiles = {}
    for playlist_id, target in targets.items():
        profile = build_reference_profile(reference_tracks[playlist_id], heldout_uris=heldout)
        target_profiles[playlist_id] = {
            "name": target["name"], "snapshot_id": target["snapshot_id"],
            "captured_at": target["captured_at"], "snapshot_track_count": len(target["items"]),
            "library_matched_count": len(reference_tracks[playlist_id]),
            "profile_track_count": profile["track_count"],
            "excluded_candidate_count": profile["excluded_candidate_and_holdout_count"],
            "coverage": profile["coverage"], "profile_confidence": profile["profile_confidence"],
            "dimension_coverage": {dim: profile["dimensions"][dim]["track_count"]
                                   for dim in profile["dimensions"]},
            "profile": profile,
        }

    results = []
    for candidate in candidates:
        record = records.get(candidate["uri"])
        track = (track_from_library_record(record, profile_for_record(record, cache))
                 if record else {"uri": candidate["uri"], "title": candidate["title"],
                                 "artist": candidate["artist"], "dimensions": {}})
        scores = {}
        for playlist_id, target in targets.items():
            scored = score_track(track, target_profiles[playlist_id]["profile"])
            scores[target["name"]] = {
                "fit_score": scored["fit_score"], "confidence": scored["confidence_tier"],
                "decision": scored["decision"], "evidence_coverage": scored["evidence_coverage"],
                "supported_dimensions": scored["supported_dimensions"],
                "dimension_scores": scored["dimension_scores"],
                "confidence_reasons": scored["confidence_reasons"],
                "human_ratings_used": False,
            }
        results.append({
            "uri": candidate["uri"], "title": track.get("title") or candidate["title"],
            "artist": track.get("artist") or candidate["artist"],
            "library_record_found": record is not None, "scores_by_target": scores,
        })
    return {
        "schema_version": 1, "model_version": MODEL_VERSION,
        "status": "read_only_preview_not_for_sorting",
        "human_ratings_read": False, "spotify_api_calls": 0, "playlist_writes": 0,
        "candidate_count": len(candidates), "heldout_batch_excluded_from_all_profiles": True,
        "targets": target_profiles, "results": results,
        "limitations": [
            "Only canonical recording-scoped evidence and exact stable-ID track-profile cache rows are used.",
            "No artist/title-only joins are allowed; unmatched recordings remain unscored.",
            "AcousticBrainz loudness/complexity and tempo are not converted into perceived energy or sound labels.",
            "A missing dimension remains unknown, never a zero or a negative fit.",
            "Scores and confidence are evidence summaries, not calibrated probabilities or production decisions.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, required=True,
                        help="identity-only JSON list or {tracks:[...]}; no human scores are read")
    parser.add_argument("--library", type=Path, default=DEFAULT_LIBRARY)
    parser.add_argument("--music-data", type=Path, default=DEFAULT_MUSIC)
    parser.add_argument("--spotify-data", type=Path, default=DEFAULT_SPOTIFY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    candidates = load_candidate_identities(args.candidates)
    records, cache = load_library_records(args.library, args.music_data)
    targets = load_reference_targets(args.spotify_data)
    result = build_preview(candidates, targets, records, cache)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output), "candidate_count": result["candidate_count"],
        "target_count": len(result["targets"]),
        "library_matched_candidates": sum(row["library_record_found"] for row in result["results"]),
        "target_profile_counts": {name: row["profile_track_count"] for name, row in result["targets"].items()},
        "human_ratings_read": False, "spotify_api_calls": 0, "playlist_writes": 0,
    }, indent=2))


if __name__ == "__main__":
    main()

# FILE OVERVIEW
# Purpose: Read-only integration of canonical Library evidence with five reference playlist profiles.
# Inputs: five accessible playlist snapshots, canonical song records, exact-ID track cache, identity-only candidates.
# Outputs: auditable per-target profiles and candidate scores; never writes to Spotify.
# Safety: no human rating input, no artist/title joins, no API calls, and no playlist mutations.
# Run: python scripts/spotify/playlist_fit_preview.py --candidates path/to/candidate-identities.json
