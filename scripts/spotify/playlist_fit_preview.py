#!/usr/bin/env python3
"""Build read-only five-target playlist-fit previews from canonical SHIT data.

No Spotify API calls, human-rating reads, playlist writes, or title/artist-only
identity joins are performed. Candidate input is an identity-only JSON file.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.spotify.playlist_fit_model import (
    MODEL_VERSION, build_reference_profile, score_track, track_from_library_record,
)
from scripts.music.music_library import norm as library_norm

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
        candidates.append({
            "uri": uri, "title": str(row.get("title") or row.get("name") or ""),
            "artist": str(row.get("artist") or ""), "album": str(row.get("album") or ""),
            "duration_ms": row.get("duration_ms"), "isrc": str(row.get("isrc") or ""),
        })
    if not candidates:
        raise ValueError("candidate file contains no valid Spotify track IDs")
    return candidates


def name_album_key(artist: Any, title: Any, album: Any) -> tuple[str, str, str]:
    return (library_norm(artist), library_norm(title), library_norm(album))


def load_library_records(root: Path, music_root: Path) -> tuple[dict, dict, dict]:
    """Read canonical songs, exact Spotify aliases, and exact name/album candidates."""
    records, name_album_index = {}, {}
    for path in sorted((root / "songs").rglob("song.json")):
        record = read_json(path)
        if not isinstance(record, dict):
            continue
        identity = record.get("identity") if isinstance(record.get("identity"), dict) else {}
        spotify_id = str(identity.get("spotify_id") or "").strip()
        uri = spotify_uri(spotify_id)
        if uri:
            records[uri] = record
        if identity.get("artist") and identity.get("title") and identity.get("album"):
            key = name_album_key(identity["artist"], identity["title"], identity["album"])
            name_album_index.setdefault(key, []).append(record)
    cache = read_json(music_root / "track_profiles.json")
    if not isinstance(cache, dict):
        raise ValueError("track_profiles.json must contain an object")
    library_index = read_json(root / "library_index.json")
    if not isinstance(library_index, dict):
        raise ValueError("library_index.json must contain an object")
    return records, index_profiles_by_song(cache, library_index), name_album_index


def index_profiles_by_song(cache: dict, library_index: dict) -> dict:
    """Resolve legacy cache rows to canonical song IDs through exact Library aliases."""
    recording_aliases = library_index.get("recording_mbids") if isinstance(library_index.get("recording_mbids"), dict) else {}
    source_aliases = library_index.get("source_track_ids") if isinstance(library_index.get("source_track_ids"), dict) else {}
    spotify_aliases = library_index.get("spotify_ids") if isinstance(library_index.get("spotify_ids"), dict) else {}
    indexed = {}
    for profile_key, profile in cache.items():
        if not isinstance(profile, dict):
            continue
        song_id = None
        mbid = str(profile.get("track_mbid") or "").strip().casefold()
        if mbid:
            song_id = recording_aliases.get(mbid) or recording_aliases.get("mbid:" + mbid)
        track_id = str(profile.get("track_id") or profile_key).strip().casefold()
        if not song_id and track_id.startswith("mbid:"):
            song_id = recording_aliases.get(track_id) or recording_aliases.get(track_id[5:])
        if not song_id and track_id.startswith("track:"):
            song_id = source_aliases.get(track_id)
        if not song_id and track_id.startswith("spotify:track:"):
            song_id = spotify_aliases.get(track_id.rsplit(":", 1)[-1])
        if not song_id:
            continue
        prior = indexed.get(song_id)
        if prior is None or str(profile.get("lastfm_checked_at") or "") >= str(prior.get("lastfm_checked_at") or ""):
            indexed[song_id] = profile
    return indexed


def profile_for_record(record: dict, cache_by_song: dict) -> dict | None:
    """Return only the cache row whose exact alias resolves to this canonical song ID."""
    song_id = str(record.get("id") or "")
    row = cache_by_song.get(song_id)
    return row if isinstance(row, dict) else None


def has_recording_fit_evidence(record: dict, profile: dict | None = None) -> bool:
    evidence = record.get("evidence") if isinstance(record.get("evidence"), dict) else {}
    metadata = evidence.get("track_metadata") if isinstance(evidence.get("track_metadata"), dict) else {}
    metadata = {**(profile or {}), **metadata}
    tag_fields = ("musicbrainz_genres", "musicbrainz_tags", "lastfm_tags", "discogs_styles", "discogs_genres")
    if any(metadata.get(field) for field in tag_fields):
        return True
    audio = evidence.get("audio") if isinstance(evidence.get("audio"), dict) else {}
    if any(audio.get(field) is not None for field in ("energy_score", "perceived_energy", "spotify_energy", "energy")):
        return True
    if any(audio.get(field) for field in ("sound_descriptors", "timbre_tags", "instrumentation", "production_tags")):
        return True
    lyrics = evidence.get("lyrics")
    if isinstance(lyrics, dict) and any(lyrics.get(field) for field in ("themes", "theme_tags", "topics")):
        return True
    mood = record.get("mood") if isinstance(record.get("mood"), dict) else {}
    recording = mood.get("recording_level") if isinstance(mood.get("recording_level"), dict) else {}
    return bool(recording.get("moods"))


def resolve_item_record(item: dict, records: dict, cache_by_song: dict, name_album_index: dict | None = None):
    """Resolve by Spotify ID first; fallback requires exact artist/title/album plus duration."""
    uri = spotify_uri(item.get("uri") or item.get("id"))
    exact = records.get(uri) if uri else None
    if exact and has_recording_fit_evidence(exact, profile_for_record(exact, cache_by_song)):
        return exact, "spotify_track_id"

    artists = item.get("artists") or []
    artist = artists[0] if isinstance(artists, list) and artists else item.get("artist")
    title = item.get("name") or item.get("title")
    album = item.get("album")
    spotify_duration = item.get("duration_ms")
    if name_album_index is not None and artist and title and album and spotify_duration not in (None, ""):
        candidates = name_album_index.get(name_album_key(artist, title, album), [])
        matches = []
        for record in candidates:
            if exact and str(record.get("id") or "") == str(exact.get("id") or ""):
                continue
            evidence = record.get("evidence") if isinstance(record.get("evidence"), dict) else {}
            metadata = evidence.get("track_metadata") if isinstance(evidence.get("track_metadata"), dict) else {}
            source_duration = metadata.get("duration_ms")
            try:
                duration_match = source_duration is not None and abs(int(source_duration) - int(spotify_duration)) <= 2000
            except (TypeError, ValueError):
                duration_match = False
            if duration_match:
                matches.append(record)
        if len(matches) == 1:
            copied = dict(matches[0])
            confidence = dict(copied.get("confidence") or {})
            confidence["identity"] = "medium"
            copied["confidence"] = confidence
            return copied, "exact_artist_title_album_duration"
    return (exact, "spotify_track_id") if exact else (None, "unmatched")


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


def build_preview(candidates: list[dict], targets: dict, records: dict, cache: dict, name_album_index: dict | None = None) -> dict:
    heldout = {candidate["uri"] for candidate in candidates}
    candidate_resolutions = []
    heldout_record_ids = set()
    for candidate in candidates:
        item = {
            "uri": candidate["uri"], "name": candidate.get("title"), "artist": candidate.get("artist"),
            "artists": [candidate.get("artist")] if candidate.get("artist") else [],
            "album": candidate.get("album"), "duration_ms": candidate.get("duration_ms"),
        }
        record, method = resolve_item_record(item, records, cache, name_album_index)
        candidate_resolutions.append((candidate, record, method))
        if record and record.get("id"):
            heldout_record_ids.add(str(record["id"]))

    reference_tracks = {}
    reference_resolution_counts = {}
    for playlist_id, target in targets.items():
        tracks, seen_record_ids = [], set()
        resolution_counts = {}
        for item in target["items"]:
            uri = spotify_uri(item.get("uri") or item.get("id"))
            record, method = resolve_item_record(item, records, cache, name_album_index)
            if record is None:
                continue
            record_id = str(record.get("id") or "")
            if record_id and (record_id in heldout_record_ids or record_id in seen_record_ids):
                continue
            if record_id:
                seen_record_ids.add(record_id)
            adapted = track_from_library_record(record, profile_for_record(record, cache))
            adapted["uri"] = uri
            tracks.append(adapted)
            resolution_counts[method] = resolution_counts.get(method, 0) + 1
        reference_tracks[playlist_id] = tracks
        reference_resolution_counts[playlist_id] = resolution_counts

    target_profiles = {}
    for playlist_id, target in targets.items():
        profile = build_reference_profile(reference_tracks[playlist_id], heldout_uris=heldout)
        target_profiles[playlist_id] = {
            "name": target["name"], "snapshot_id": target["snapshot_id"],
            "captured_at": target["captured_at"], "snapshot_track_count": len(target["items"]),
            "library_matched_count": len(reference_tracks[playlist_id]),
            "identity_resolution_counts": reference_resolution_counts[playlist_id],
            "profile_track_count": profile["track_count"],
            "excluded_candidate_count": profile["excluded_candidate_and_holdout_count"],
            "coverage": profile["coverage"], "profile_confidence": profile["profile_confidence"],
            "dimension_coverage": {dim: profile["dimensions"][dim]["track_count"]
                                   for dim in profile["dimensions"]},
            "profile": profile,
        }

    results = []
    for candidate, record, method in candidate_resolutions:
        track = (track_from_library_record(record, profile_for_record(record, cache))
                 if record else {"uri": candidate["uri"], "title": candidate["title"],
                                 "artist": candidate["artist"], "dimensions": {}})
        track["uri"] = candidate["uri"]
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
            "library_record_found": record is not None, "identity_resolution": method,
            "scores_by_target": scores,
        })
    usable_profiles = sum(1 for target in target_profiles.values() if target["coverage"] > 0)
    block_reasons = [] if usable_profiles else [
        "No target profile has usable evidence in any dimension; all candidate fit scores are withheld."
    ]
    return {
        "schema_version": 1, "model_version": MODEL_VERSION,
        "status": "read_only_preview_not_for_sorting" if usable_profiles else "blocked_insufficient_reference_evidence",
        "human_ratings_read": False, "spotify_api_calls": 0, "playlist_writes": 0,
        "candidate_count": len(candidates), "heldout_batch_excluded_from_all_profiles": True,
        "usable_target_profile_count": usable_profiles, "block_reasons": block_reasons,
        "targets": target_profiles, "results": results,
        "limitations": [
            "Stable Spotify/MBID/source IDs are preferred. A fallback is accepted only for exact artist + title + album and duration within 2 seconds; it is marked medium identity confidence.",
            "No fuzzy or artist/title-only joins are allowed; ambiguous or duration-mismatched recordings remain unscored.",
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
    records, cache, name_album_index = load_library_records(args.library, args.music_data)
    targets = load_reference_targets(args.spotify_data)
    result = build_preview(candidates, targets, records, cache, name_album_index=name_album_index)
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
