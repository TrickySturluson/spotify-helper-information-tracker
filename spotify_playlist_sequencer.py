#!/usr/bin/env python3
"""Preview energy-aware sequencing plans for Spotify playlists.

This tool is deliberately preview-only. It reads a playlist through the existing
locked-by-default manager and writes a change plan for spotify_playlist_manager.py
to preview and apply. It never edits Spotify directly.
"""
import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path

import mood_inference
import spotify_playlist_manager as manager

ARTIST_PROFILES = Path("assistant_data/music/artist_profiles.json")
TRACK_PROFILES = Path("assistant_data/music/track_profiles.json")


def norm(value):
    return re.sub(r"\\s+", " ", str(value or "").strip()).casefold()


def read_json(path, fallback):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return fallback


def index_artists(rows):
    return {norm(row["artist"]): row for row in rows.values()
            if isinstance(row, dict) and row.get("artist")} if isinstance(rows, dict) else {}


def index_tracks(rows):
    return {(norm(row["artist"]), norm(row["track"])): row for row in rows.values()
            if isinstance(row, dict) and row.get("artist") and row.get("track")} if isinstance(rows, dict) else {}


def _tag_rows(profile):
    rows = []
    for field in ("lastfm_tags", "musicbrainz_tags", "musicbrainz_genres"):
        rows.extend(profile.get(field) or [])
    return [str(row.get("tag", "") if isinstance(row, dict) else row).strip()
            for row in rows if (row.get("tag") if isinstance(row, dict) else row)]


def _signal(value, low, high):
    if value is None:
        return None
    try:
        return max(0.0, min(1.0, (float(value) - low) / (high - low)))
    except (TypeError, ValueError):
        return None


def score_track(item, artist_profiles=None, track_profiles=None):
    """Return a conservative 0..100 perceived-energy score and its evidence.

    Spotify audio features, when already present in a playlist export, are the
    strongest signals. Sourced track tags come next; artist metadata is a weak
    fallback and is never presented as track-level fact.
    """
    artist_profiles = artist_profiles or {}
    track_profiles = track_profiles or {}
    names = item.get("artists") or ([item.get("artist")] if item.get("artist") else [])
    artist = str(names[0]) if names else ""
    title = str(item.get("name") or item.get("track") or "")
    artist_profile = artist_profiles.get(norm(artist), {})
    track_profile = track_profiles.get((norm(artist), norm(title)), {})
    audio = item.get("audio_features") or {}
    components = []
    evidence = []
    weights = []

    # Spotify's 0..1 energy is the most direct available signal.
    direct_energy = _signal(audio.get("energy"), 0, 1)
    if direct_energy is not None:
        components.append(direct_energy); weights.append(0.42)
        evidence.append("Spotify energy")

    tempo = _signal(audio.get("tempo"), 60, 180)
    if tempo is not None:
        components.append(tempo); weights.append(0.23)
        evidence.append("tempo")

    loudness = _signal(audio.get("loudness"), -35, -5)
    if loudness is not None:
        components.append(loudness); weights.append(0.15)
        evidence.append("loudness")

    track_tags = _tag_rows(track_profile)
    artist_tags = _tag_rows(artist_profile)
    tag_moods = set()
    for tag in track_tags:
        tag_moods.update(mood_inference._tag_moods(tag))
    artist_moods = set()
    for tag in artist_tags:
        artist_moods.update(mood_inference._tag_moods(tag))
    energetic = {"aggressive", "energetic", "chaotic", "tense", "rebellious", "cathartic"}
    gentle = {"calm", "dreamy", "melancholic", "introspective", "wistful", "warm", "romantic"}
    if tag_moods:
        mood_score = 0.72 if tag_moods & energetic else 0.28 if tag_moods & gentle else 0.5
        components.append(mood_score); weights.append(0.15)
        evidence.append("track tags: " + ", ".join(sorted(tag_moods)))
    elif artist_moods:
        mood_score = 0.68 if artist_moods & energetic else 0.32 if artist_moods & gentle else 0.5
        components.append(mood_score); weights.append(0.06)
        evidence.append("artist-level mood fallback: " + ", ".join(sorted(artist_moods)))

    genres = [norm(x) for x in (track_profile.get("musicbrainz_genres") or [])]
    genres += [norm(x) for x in (artist_profile.get("genres") or [])]
    genre_text = " ".join(g.get("tag", "") if isinstance(g, dict) else g for g in genres)
    high_genre = ("metal", "hardcore", "punk", "industrial", "drum and bass", "breakcore", "hardstyle")
    low_genre = ("ambient", "drone", "neoclassical", "slowcore", "dark ambient")
    genre_score = 0.7 if any(x in genre_text for x in high_genre) else 0.3 if any(x in genre_text for x in low_genre) else None
    if genre_score is not None:
        components.append(genre_score); weights.append(0.05 if track_tags else 0.08)
        evidence.append("genre family")

    if not components:
        return {"score": 50.0, "confidence": "unknown", "evidence": [],
                "artist": artist, "track": title, "vibe_group": "unclassified"}
    score = sum(v * w for v, w in zip(components, weights)) / sum(weights) * 100
    confidence = "high" if direct_energy is not None and (tempo is not None or loudness is not None) else "medium" if len(components) >= 2 else "low"
    group = next(iter(sorted(tag_moods)), "unclassified") if tag_moods else (
        next(iter(sorted(artist_moods)), "artist-level") if artist_moods else "unclassified")
    return {"score": round(score, 2), "confidence": confidence,
            "evidence": evidence, "artist": artist, "track": title,
            "vibe_group": group}


def sequence_tracks(items, artist_profiles=None, track_profiles=None, direction="ascending"):
    if direction not in {"ascending", "descending"}:
        raise ValueError("direction must be ascending or descending")
    scored = []
    for index, item in enumerate(items):
        if not isinstance(item, dict) or not item.get("uri"):
            continue
        profile = score_track(item, artist_profiles, track_profiles)
        scored.append({"original_index": index, "item": item, **profile})
    reverse = direction == "descending"
    scored.sort(key=lambda row: ((-row["score"] if reverse else row["score"]),
                                 row["vibe_group"], row["artist"].casefold(),
                                 row["track"].casefold(), row["original_index"]))
    return scored


def build_reorder_operations(current_uris, ordered_uris):
    """Create Spotify single-item moves that transform current order exactly."""
    if len(current_uris) != len(ordered_uris) or Counter(current_uris) != Counter(ordered_uris):
        raise ValueError("Current and desired playlist contents must contain the same URIs.")
    working = list(current_uris)
    operations = []
    for target_index, wanted in enumerate(ordered_uris):
        if working[target_index] == wanted:
            continue
        source_index = working.index(wanted, target_index + 1)
        operations.append({"action": "reorder", "range_start": source_index,
                           "insert_before": target_index, "range_length": 1})
        moved = working.pop(source_index)
        working.insert(target_index, moved)
    return operations


def make_plan(snapshot, scored):
    items = snapshot["items"]
    current = [row.get("uri") for row in items]
    ordered = [row["item"]["uri"] for row in scored]
    if len(ordered) != len(current):
        raise ValueError("Some playlist items are unavailable or do not have track URIs; refusing a partial reorder.")
    return {"playlist_id": snapshot["playlist"]["id"],
            "operations": build_reorder_operations(current, ordered)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("playlist_id")
    parser.add_argument("--direction", choices=("ascending", "descending"), default="ascending")
    parser.add_argument("--output", type=Path, default=Path("playlist-sequence-plan.json"))
    args = parser.parse_args()
    try:
        sp = manager.Spotify()
        playlist = manager.find(sp, args.playlist_id)
        snap = manager.snapshot(sp, playlist)
        artists = index_artists(read_json(ARTIST_PROFILES, {}))
        tracks = index_tracks(read_json(TRACK_PROFILES, {}))
        scored = sequence_tracks(snap["items"], artists, tracks, args.direction)
        plan = make_plan(snap, scored)
        args.output.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f'Preview generated for "{playlist.get("name")}" — {len(scored)} tracks.')
        print(f'Direction: {args.direction}; {len(plan["operations"])} reorder operation(s).')
        print("Lowest-energy opening:")
        for row in scored[:5]:
            print(f'  {row["score"]:5.1f} [{row["confidence"]}] {row["artist"]} — {row["track"]}')
        print("Highest-energy ending:")
        for row in scored[-5:]:
            print(f'  {row["score"]:5.1f} [{row["confidence"]}] {row["artist"]} — {row["track"]}')
        print("Plan written to", args.output)
        print("Review the plan, then run: python spotify_playlist_manager.py apply", args.output)
        print("The manager will show its normal preview and require explicit APPLY confirmation.")
    except (manager.ManagerError, OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"ERROR: {exc}\n")


if __name__ == "__main__":
    main()
