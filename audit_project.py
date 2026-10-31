#!/usr/bin/env python3
"""Cross-check canonical SHIT data and generated manifests."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ERRORS, WARNINGS, CHECKS = [], [], []

def load(path):
    try:
        return json.loads((ROOT / path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        ERRORS.append(f"{path}: invalid or missing JSON ({exc})")
        return None

def check(ok, message):
    (CHECKS if ok else ERRORS).append(message)

def referenced_paths(value):
    found = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"path", "file", "filename"} and isinstance(item, str):
                found.add(item)
            else:
                found.update(referenced_paths(item))
    elif isinstance(value, list):
        for item in value:
            found.update(referenced_paths(item))
    return found


def audit_spotify_reference(root=ROOT):
    """Validate the optional Spotify reference catalog/index without treating 403s as empty data."""
    catalog_path = root / "assistant_data/spotify/playlists.json"
    index_path = root / "assistant_data/spotify/reference_index.json"
    if not catalog_path.exists():
        return [], ["Spotify reference library has not been synced yet; reference audit skipped."]
    errors, warnings = [], []
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"Spotify reference catalog is invalid: {exc}"], []
    rows = catalog.get("playlists") if isinstance(catalog, dict) else None
    if not isinstance(rows, list):
        return ["Spotify reference catalog must contain a playlists list."], []
    ids = [row.get("id") for row in rows if isinstance(row, dict)]
    if len(ids) != len(rows) or any(not isinstance(pid, str) or not pid for pid in ids):
        errors.append("Spotify reference catalog contains malformed playlist records.")
    if len(set(ids)) != len(ids):
        errors.append("Spotify reference catalog contains duplicate playlist IDs.")
    if catalog.get("playlist_count") != len(rows):
        errors.append("Spotify reference catalog playlist_count does not match its records.")
    inaccessible = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        pid = row.get("id")
        accessible = row.get("items_accessible", True)
        inaccessible += int(not accessible)
        relative = row.get("record_path") or f"assistant_data/spotify/playlists/{pid}.json"
        path = root / relative
        if not path.exists():
            errors.append(f"Spotify catalog record {pid} references missing file {relative}.")
            continue
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            errors.append(f"Spotify playlist record {pid} is invalid JSON: {exc}")
            continue
        if record.get("id") != pid:
            errors.append(f"Spotify playlist record identity mismatch for {pid}.")
        # The catalog is a summary of this record; catch drift rather than silently
        # trusting whichever copy happens to be read by a downstream consumer.
        if "items_accessible" in record and record.get("items_accessible") != accessible:
            errors.append(f"Spotify catalog/record accessibility mismatch for {pid}.")
        if row.get("snapshot_id") is not None and record.get("snapshot_id") is not None and row.get("snapshot_id") != record.get("snapshot_id"):
            errors.append(f"Spotify catalog/record snapshot mismatch for {pid}.")
        if row.get("item_count") is not None and record.get("item_count_fetched") is not None and row.get("item_count") != record.get("item_count_fetched"):
            errors.append(f"Spotify catalog/record fetched-item count mismatch for {pid}.")
        # Unavailable item contents are an access limitation, not evidence of an empty playlist.
        if accessible and not isinstance(record.get("items"), list):
            errors.append(f"Accessible Spotify playlist {pid} has no items list.")
        elif accessible and isinstance(record.get("items"), list):
            fetched = record.get("item_count_fetched")
            if isinstance(fetched, int) and fetched != len(record["items"]):
                errors.append(f"Accessible Spotify playlist {pid} item_count_fetched does not match its items list.")
        if not accessible:
            warnings.append(f"Spotify playlist item contents inaccessible for {pid}; preserved data may be stale.")
    if not index_path.exists():
        errors.append("Spotify reference index is missing.")
    else:
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
            track_map = index.get("track_playlists", {})
            artist_map = index.get("artist_playlists", {})
            if not isinstance(track_map, dict) or not isinstance(artist_map, dict):
                errors.append("Spotify reference index maps must be JSON objects.")
            else:
                known = set(ids)
                dangling = set()
                malformed_values = []
                duplicate_references = []
                for map_name, mapping in (("track_playlists", track_map), ("artist_playlists", artist_map)):
                    for key, values in mapping.items():
                        if not isinstance(values, list) or any(not isinstance(pid, str) or not pid for pid in values):
                            malformed_values.append(f"{map_name}:{key}")
                            continue
                        if len(values) != len(set(values)):
                            duplicate_references.append(f"{map_name}:{key}")
                        dangling.update(pid for pid in values if pid not in known)
                if malformed_values:
                    errors.append(f"Spotify reference index contains {len(malformed_values)} malformed playlist-reference list(s).")
                if duplicate_references:
                    errors.append(f"Spotify reference index contains duplicate playlist references in {len(duplicate_references)} entr(y/ies).")
                if dangling:
                    errors.append(f"Spotify reference index contains {len(dangling)} unknown playlist ID(s).")
        except (OSError, ValueError, AttributeError) as exc:
            errors.append(f"Spotify reference index is invalid: {exc}")
    if inaccessible:
        warnings.append(f"{inaccessible} Spotify playlist(s) have inaccessible item contents; this is not counted as an empty-list success.")
    return errors, warnings

def main():
    metadata = load("data/metadata.json") or {}
    total = metadata.get("total_scrobbles", metadata.get("scrobbles"))
    check(isinstance(total, int) and total >= 0, "Canonical scrobble count is valid.")
    manifests = (
        "assistant_data/manifest.json",
        "assistant_data/advanced/manifest.json",
        "assistant_data/music/manifest.json",
        "assistant_data/recommendations/manifest.json",
        "assistant_data/playback/manifest.json",
    )
    for path in manifests:
        manifest = load(path)
        if not isinstance(manifest, dict):
            continue
        for relative in referenced_paths(manifest):
            check((ROOT / relative).exists(), f"{path} references existing file {relative}.")
        for key in ("total_scrobbles", "source_scrobbles", "scrobbles"):
            if isinstance(manifest.get(key), int) and isinstance(total, int):
                check(manifest[key] == total, f"{path}: {key} agrees with canonical archive.")
    overview = load("assistant_data/music/overview.json") or {}
    unique, covered = overview.get("unique_tracks"), overview.get("tracks_with_duration")
    check(isinstance(unique, int) and isinstance(covered, int) and 0 <= covered <= unique,
          "Music duration coverage counts are valid.")
    profiles = load("assistant_data/music/track_profiles.json") or {}
    invalid = [key for key, row in profiles.items() if not isinstance(row, dict) or not key]
    check(not invalid, f"Track profile structure valid ({len(profiles)} records).")
    playback = load("assistant_data/playback/manifest.json") or {}
    if playback.get("source_exists") is False and playback.get("recorded_intervals", 0) == 0:
        WARNINGS.append("No captured playback intervals yet; this is a coverage gap, not corruption.")
    spotify_errors, spotify_warnings = audit_spotify_reference()
    ERRORS.extend(spotify_errors)
    WARNINGS.extend(spotify_warnings)
    if not spotify_errors and not any("not been synced" in warning for warning in spotify_warnings):
        CHECKS.append("Spotify reference catalog, playlist records, and cross-playlist index are structurally consistent.")
    CHECKS.append("Legacy display-name and MBID-aware identity models may differ; this is intentional.")
    for label, messages in (("PASS", CHECKS), ("WARNING", WARNINGS), ("ERROR", ERRORS)):
        for message in messages:
            print(f"{label}: {message}")
    print(f"Audit result: {len(CHECKS)} checks, {len(WARNINGS)} warnings, {len(ERRORS)} errors.")
    return 1 if ERRORS else 0

if __name__ == "__main__":
    sys.exit(main())
