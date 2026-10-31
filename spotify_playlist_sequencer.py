#!/usr/bin/env python3
"""Preview energy-aware sequencing plans for Spotify playlists.

This tool is deliberately preview-only. It reads a playlist through the existing
locked-by-default manager and writes a change plan for spotify_playlist_manager.py
to preview and apply. It never edits Spotify directly.
"""
import argparse
import json
import re
from collections import Counter
from pathlib import Path

import mood_inference
import spotify_playlist_manager as manager

ARTIST_PROFILES = Path("assistant_data/music/artist_profiles.json")
TRACK_PROFILES = Path("assistant_data/music/track_profiles.json")


def norm(value):
    return re.sub(r"\s+", " ", str(value or "").strip()).casefold()


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
        evidence.append(f"Spotify energy={direct_energy:.2f} (42% base weight)")

    tempo = _signal(audio.get("tempo"), 60, 180)
    if tempo is not None:
        components.append(tempo); weights.append(0.23)
        evidence.append(f"tempo={float(audio.get('tempo')):.1f} BPM (23% base weight)")

    loudness = _signal(audio.get("loudness"), -35, -5)
    if loudness is not None:
        components.append(loudness); weights.append(0.15)
        evidence.append(f"loudness={float(audio.get('loudness')):.1f} dB (15% base weight)")

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
        evidence.append(f"track-tag mood={mood_score:.2f} (15% base weight): " + ", ".join(sorted(tag_moods)))
    elif artist_moods:
        mood_score = 0.68 if artist_moods & energetic else 0.32 if artist_moods & gentle else 0.5
        components.append(mood_score); weights.append(0.06)
        evidence.append(f"artist-level mood fallback={mood_score:.2f} (6% base weight): " + ", ".join(sorted(artist_moods)))

    genre_values = []
    for row in track_profile.get("musicbrainz_genres") or []:
        value = row.get("tag", "") if isinstance(row, dict) else row
        if value:
            genre_values.append(norm(value))
    genre_values.extend(norm(value) for value in artist_profile.get("genres") or [] if value)
    genre_text = " ".join(genre_values)
    high_genre = ("metal", "hardcore", "punk", "industrial", "drum and bass", "breakcore", "hardstyle")
    low_genre = ("ambient", "drone", "neoclassical", "slowcore", "dark ambient")
    genre_score = 0.7 if any(x in genre_text for x in high_genre) else 0.3 if any(x in genre_text for x in low_genre) else None
    if genre_score is not None:
        components.append(genre_score); weights.append(0.05 if track_tags else 0.08)
        evidence.append(f"genre-family signal={genre_score:.2f} ({(0.05 if track_tags else 0.08):.0%} base weight)")

    genre_groups = []
    for row in track_profile.get("musicbrainz_genres") or []:
        value = row.get("tag", "") if isinstance(row, dict) else row
        if value and str(value).strip():
            genre_groups.append(str(value).strip())
    genre_groups.extend(str(value).strip() for value in artist_profile.get("genres") or [] if str(value).strip())
    theme_groups = [str(value).strip() for value in artist_profile.get("themes") or [] if str(value).strip()]
    if not components:
        return {"score": 50.0, "confidence": "unknown", "evidence": [],
                "artist": artist, "track": title, "vibe_group": "unclassified",
                "genre_groups": sorted(set(genre_groups)), "theme_groups": sorted(set(theme_groups))}
    score = sum(v * w for v, w in zip(components, weights)) / sum(weights) * 100
    confidence = "high" if direct_energy is not None and (tempo is not None or loudness is not None) else "medium" if len(components) >= 2 else "low"
    group = next(iter(sorted(tag_moods)), "unclassified") if tag_moods else (
        next(iter(sorted(artist_moods)), "artist-level") if artist_moods else "unclassified")
    return {"score": round(score, 2), "confidence": confidence,
            "evidence": evidence, "artist": artist, "track": title,
            "vibe_group": group, "vibe_groups": sorted(tag_moods or artist_moods),
            "genre_groups": sorted(set(genre_groups)), "theme_groups": sorted(set(theme_groups))}


def _set_similarity(left, right):
    a, b = set(left or []), set(right or [])
    return len(a & b) / len(a | b) if a and b else 0.0


def _transition_cost(left, right):
    """Lower is a gentler transition; all inputs are metadata heuristics."""
    energy_gap = abs(float(left["score"]) - float(right["score"])) / 100.0
    mood_similarity = _set_similarity(left.get("vibe_groups"), right.get("vibe_groups"))
    genre_similarity = _set_similarity(left.get("genre_groups"), right.get("genre_groups"))
    same_artist = norm(left.get("artist")) == norm(right.get("artist"))
    return (0.48 * energy_gap + 0.27 * (1.0 - mood_similarity)
            + 0.15 * (1.0 - genre_similarity) + 0.10 * same_artist)


def _transition_order(rows):
    """Greedy local sequencing that favors compatible neighboring tracks."""
    remaining = list(rows)
    if len(remaining) < 3:
        return remaining
    ordered = [remaining.pop(0)]
    while remaining:
        previous = ordered[-1]
        next_row = min(remaining, key=lambda row: (
            _transition_cost(previous, row), row["original_index"]))
        remaining.remove(next_row)
        ordered.append(next_row)
    return ordered


def _narrative_phase(row):
    moods = set(row.get("vibe_groups") or [])
    phases = (
        {"calm", "dreamy", "warm", "romantic", "nostalgic", "wistful"},
        {"introspective", "melancholic", "mysterious", "psychedelic"},
        {"nocturnal", "dark", "eerie", "desolate", "tense"},
        {"aggressive", "chaotic", "rebellious", "energetic", "cathartic"},
        {"hopeful", "uplifting", "upbeat", "playful"},
    )
    for index, phase in enumerate(phases):
        if moods & phase:
            return index
    return 2


def sequence_tracks(items, artist_profiles=None, track_profiles=None,
                    direction="ascending", group_by="none", mode="hybrid"):
    """Sequence tracks by energy, atmosphere, style, narrative or discovery.

    Hybrid mode preserves a broad energy arc and improves local transitions
    within each 10-point band. All non-audio signals remain metadata heuristics.
    """
    if direction not in {"ascending", "descending"}:
        raise ValueError("direction must be ascending or descending")
    if group_by not in {"none", "vibe", "genre", "theme"}:
        raise ValueError("group_by must be none, vibe, genre, or theme")
    if mode not in {"hybrid", "energy", "atmosphere", "style", "narrative", "discovery"}:
        raise ValueError("mode must be hybrid, energy, atmosphere, style, narrative, or discovery")
    artists = artist_profiles or {}
    scored = []
    for index, item in enumerate(items):
        if not isinstance(item, dict) or not item.get("uri"):
            continue
        profile = score_track(item, artists, track_profiles)
        group_field = {"vibe": "vibe_groups", "genre": "genre_groups", "theme": "theme_groups"}.get(group_by)
        groups = profile.get(group_field, []) if group_field else []
        profile["sequence_group"] = groups[0] if groups else "unclassified"
        artist_profile = artists.get(norm(profile["artist"]), {})
        profile["artist_play_count"] = artist_profile.get("play_count")
        profile["narrative_phase"] = _narrative_phase(profile)
        scored.append({"original_index": index, "item": item, **profile})

    reverse = direction == "descending"
    if mode == "atmosphere":
        if group_by == "none":
            for row in scored:
                row["sequence_group"] = (row.get("vibe_groups") or ["unclassified"])[0]
        # Give atmosphere clusters an interpretable emotional progression,
        # rather than arbitrary alphabetical ordering of mood labels.
        scored.sort(key=lambda row: (
            -row["narrative_phase"] if reverse else row["narrative_phase"],
            row["sequence_group"], -row["score"] if reverse else row["score"],
            row["original_index"]))
    elif mode == "style":
        for row in scored:
            if group_by == "none":
                row["sequence_group"] = (row.get("genre_groups") or ["unclassified"])[0]
        scored.sort(key=lambda row: (row["sequence_group"], -row["score"] if reverse else row["score"], row["original_index"]))
    elif mode == "narrative":
        scored.sort(key=lambda row: ((-row["narrative_phase"] if reverse else row["narrative_phase"]),
                                     -row["score"] if reverse else row["score"], row["original_index"]))
        for row in scored:
            row["sequence_group"] = f"act-{row['narrative_phase'] + 1}"
    elif mode == "discovery":
        # Lower-play-count artists surface first; unknown familiarity remains last.
        scored.sort(key=lambda row: (
            row["artist_play_count"] is None,
            row["artist_play_count"] if row["artist_play_count"] is not None else float("inf"),
            -row["score"] if reverse else row["score"], row["original_index"]))
        for row in scored:
            row["sequence_group"] = "less familiar" if row["artist_play_count"] is not None else "familiarity unknown"
    else:
        bands = {}
        for row in scored:
            band = int(row["score"] // 10)
            bands.setdefault(band, []).append(row)
        ordered_bands = sorted(bands, reverse=reverse)
        result = []
        for band in ordered_bands:
            rows = bands[band]
            if mode == "hybrid":
                # Use requested grouping as a soft preference before transition cost.
                if group_by != "none":
                    field = {"vibe": "vibe_groups", "genre": "genre_groups", "theme": "theme_groups"}[group_by]
                    for row in rows:
                        row["sequence_group"] = (row.get(field) or ["unclassified"])[0]
                    rows.sort(key=lambda row: (row["sequence_group"], row["original_index"]))
                rows = _transition_order(rows)
            else:
                rows.sort(key=lambda row: (-row["score"] if reverse else row["score"], row["original_index"]))
            result.extend(rows)
        scored = result
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


def confidence_summary(scored):
    """Count confidence tiers in a sequence preview, including unknown metadata."""
    return {label: sum(1 for row in scored if row.get("confidence") == label)
            for label in ("high", "medium", "low", "unknown")}


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
    parser.add_argument("--mode", choices=("hybrid", "energy", "atmosphere", "style", "narrative", "discovery"), default="hybrid")
    parser.add_argument("--direction", choices=("ascending", "descending"), default="ascending")
    parser.add_argument("--group-by", choices=("none", "vibe", "genre", "theme"), default="none", help="Softly cluster groups within 10-point energy bands.")
    parser.add_argument("--output", type=Path, default=Path("playlist-sequence-plan.json"))
    args = parser.parse_args()
    try:
        sp = manager.Spotify()
        playlist = manager.find(sp, args.playlist_id)
        snap = manager.snapshot(sp, playlist)
        artists = index_artists(read_json(ARTIST_PROFILES, {}))
        tracks = index_tracks(read_json(TRACK_PROFILES, {}))
        scored = sequence_tracks(snap["items"], artists, tracks, args.direction, args.group_by, args.mode)
        plan = make_plan(snap, scored)
        args.output.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f'Preview generated for "{playlist.get("name")}" — {len(scored)} tracks.')
        print(f'Direction: {args.direction}; {len(plan["operations"])} reorder operation(s).')
        confidence_counts = confidence_summary(scored)
        print("Proposed sequence (position | energy | confidence | group | track):")
        print("Confidence: " + ", ".join(f"{label}={count}" for label, count in confidence_counts.items()))
        for position, row in enumerate(scored, 1):
            group = row.get("sequence_group") or row.get("vibe_group") or "unclassified"
            print(f'  {position:3}. {row["score"]:5.1f} [{row["confidence"]:7}] [{group}] {row["artist"]} — {row["track"]}')
            signals = row.get("evidence") or []
            print("       Signals: " + ("; ".join(signals) if signals else "no sourced metadata; neutral placeholder score"))
        print("Plan written to", args.output)
        print("Review the plan, then run: python spotify_playlist_manager.py apply", args.output)
        print("The manager will show its normal preview and require explicit APPLY confirmation.")
    except (manager.ManagerError, OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"ERROR: {exc}\n")


if __name__ == "__main__":
    main()
