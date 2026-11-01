#!/usr/bin/env python3
"""Record recommended/discovered tracks and sync them into the canonical SHIT Library.

Input is a JSON list (or {"tracks": [...]}) of track candidates. This tool stores
candidate provenance separately from listening evidence, then rebuilds the canonical
Library using the normal identity resolver. It never writes to Spotify playlists.
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.music.music_library import MusicLibrary, norm, read_json, write_json

MUSIC = ROOT / "assistant_data" / "music"
CANDIDATES = MUSIC / "discovery_candidates.json"
EVENTS = MUSIC / "discovery_events.json"


def load_tracks(path):
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(value, dict):
        value = value.get("tracks", [])
    if not isinstance(value, list):
        raise ValueError("Input must be a JSON list or an object with a tracks list.")
    return value


def candidate_key(row):
    for field in ("spotify_id", "spotify_track_id", "track_mbid", "recording_mbid", "isrc", "isrc_code"):
        value = str(row.get(field) or "").strip().casefold()
        if value:
            return field + ":" + value
    return "name:" + norm(row.get("artist")) + "\0" + norm(row.get("track") or row.get("name")) + "\0" + norm(row.get("album"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="JSON file containing recommended/discovered track candidates")
    parser.add_argument("--source", default="SHIT recommendation", help="Discovery source/provenance label")
    parser.add_argument("--context", default="", help="Seed, playlist, prompt, or recommendation context")
    parser.add_argument("--action", choices=("unknown", "accepted", "added_to_playlist", "saved", "rejected", "skipped"), default="unknown",
                        help="Observed user response, if known; does not imply a play or scrobble")
    parser.add_argument("--no-sync", action="store_true", help="Store discovery ledger only; do not update canonical Library yet")
    args = parser.parse_args(argv)

    incoming = load_tracks(args.input)
    existing = read_json(CANDIDATES) or {}
    if not isinstance(existing, dict):
        existing = {}
    events = read_json(EVENTS) or []
    if not isinstance(events, list):
        events = []
    now = datetime.now(timezone.utc).isoformat()
    accepted = skipped = 0
    library = MusicLibrary()

    for raw in incoming:
        if not isinstance(raw, dict):
            skipped += 1
            continue
        artist = str(raw.get("artist") or "").strip()
        title = str(raw.get("track") or raw.get("name") or "").strip()
        if not artist or not title:
            skipped += 1
            continue
        row = dict(raw)
        row["artist"], row["track"] = artist, title
        row.pop("listening_context", None)  # discovery is never fabricated listening evidence
        key = candidate_key(row)
        prior = existing.get(key, {})
        sources = list(prior.get("discovery_sources") or [])
        source_event = {"source": args.source, "context": args.context or None, "first_seen_at": prior.get("first_seen_at") or now}
        if source_event not in sources:
            sources.append(source_event)
        row["discovery_context"] = {
            "kind": "recommendation_or_discovery",
            "first_seen_at": prior.get("first_seen_at") or now,
            "last_seen_at": now,
            "discovery_sources": sources,
            "observed_user_action": args.action if args.action != "unknown" else prior.get("observed_user_action", "unknown"),
            "listening_evidence": "not_inferred_from_discovery",
        }
        existing[key] = row
        events.append({
            "event_id": str(len(events) + 1) + ":" + key,
            "occurred_at": now,
            "song_key": key,
            "artist": artist,
            "track": title,
            "album": row.get("album") or row.get("album_name") or None,
            "source": args.source,
            "context": args.context or None,
            "observed_user_action": args.action,
            "action_is_observation_not_inference": True,
        })
        accepted += 1

    write_json(CANDIDATES, existing)
    write_json(EVENTS, events)
    result = {"received": len(incoming), "stored_or_updated": accepted, "skipped_invalid": skipped,
              "unique_discovery_candidates": len(existing), "event_count": len(events),
              "canonical_sync": "skipped"}
    if not args.no_sync:
        profiles_path = MUSIC / "track_profiles.json"
        profiles = read_json(profiles_path) or {}
        if not isinstance(profiles, dict):
            raise SystemExit("Refusing to sync: track_profiles.json is not a JSON object.")
        # Keep provider profile rows and discovery-only rows distinct by stable keys.
        for key, row in existing.items():
            row_key = "discovery:" + key
            profiles[row_key] = {**row, "track_id": row.get("track_id") or row_key}
        write_json(profiles_path, profiles)
        proc = subprocess.run([sys.executable, str(ROOT / "scripts/music/sync_music_library.py")], cwd=ROOT, check=False)
        result["canonical_sync"] = "success" if proc.returncode == 0 else "failed"
        if proc.returncode:
            return proc.returncode
        # Verify that each candidate is retrievable through at least one supported identity.
        refreshed = MusicLibrary()
        verified = 0
        for row in existing.values():
            audit = refreshed.lookup_song(
                spotify_id=row.get("spotify_id") or row.get("spotify_track_id"),
                recording_mbid=row.get("track_mbid") or row.get("recording_mbid"),
                isrc=row.get("isrc") or row.get("isrc_code"),
                source_track_id=row.get("track_id"),
                artist=row.get("artist"), track=row.get("track") or row.get("name"), album=row.get("album") or row.get("album_name"),
            )
            if audit.get("status") == "matched":
                verified += 1
        result["canonical_candidates_retrievable"] = verified
        result["library_audit"] = refreshed.audit()
        if not result["library_audit"].get("ok"):
            return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# FILE OVERVIEW
# Purpose: Capture SHIT recommendations and externally surfaced song candidates as durable Library inputs.
# Inputs: JSON track rows with artist/title and optional Spotify ID, ISRC, MBID, album, and metadata.
# Outputs: discovery_candidates.json (current deduplicated candidates), discovery_events.json (event history),
#          and, by default, canonical Library records via the normal sync path.
# Evidence rule: recommendation provenance and observed response stay separate from plays/scrobbles.
# Safety: no Spotify playlist writes; invalid rows are skipped; canonical identity resolver and audit are reused.
