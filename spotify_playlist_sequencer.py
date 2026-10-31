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


def _transition_cost(left, right, genre_strength=0.0, theme_strength=0.0):
    """Metadata-only edge cost; genre affinity is deliberately a soft bonus."""
    energy_gap = abs(float(left["score"]) - float(right["score"])) / 100.0
    mood = _set_similarity(left.get("vibe_groups"), right.get("vibe_groups"))
    genre = _set_similarity(left.get("genre_groups"), right.get("genre_groups"))
    theme = _set_similarity(left.get("theme_groups"), right.get("theme_groups"))
    section = _set_similarity(left.get("section_groups"), right.get("section_groups"))
    same_artist = bool(norm(left.get("artist")) and norm(left.get("artist")) == norm(right.get("artist")))
    return (0.34 * energy_gap + 0.25 * (1.0 - mood) + 0.08 * (1.0 - genre)
            + 0.08 * (1.0 - theme) + 0.10 * same_artist
            - 0.12 * max(0.0, min(1.0, genre_strength)) * genre
            - 0.12 * max(0.0, min(1.0, theme_strength)) * theme - 0.08 * section)


def transition_report(left, right):
    gap = abs(float(left["score"]) - float(right["score"])) / 100.0
    moods = sorted(set(left.get("vibe_groups") or []) & set(right.get("vibe_groups") or []))
    genres = sorted(set(left.get("genre_groups") or []) & set(right.get("genre_groups") or []))
    themes = sorted(set(left.get("theme_groups") or []) & set(right.get("theme_groups") or []))
    same = bool(norm(left.get("artist")) and norm(left.get("artist")) == norm(right.get("artist")))
    cost = _transition_cost(left, right)
    reasons = []
    if moods: reasons.append("shared track mood: " + ", ".join(moods))
    if genres: reasons.append("shared genre: " + ", ".join(genres))
    if themes: reasons.append("shared theme: " + ", ".join(themes))
    if gap <= 0.12: reasons.append("similar estimated energy")
    elif gap >= 0.35: reasons.append("large estimated energy change")
    if same: reasons.append("same primary artist")
    if not reasons: reasons.append("limited matching metadata; uncertain handoff")
    return {"cost": round(cost, 4), "label": "gentle" if cost < 0.34 else "moderate" if cost < 0.52 else "potential jump",
            "confidence": "supported" if left.get("confidence") in ("high", "medium") and right.get("confidence") in ("high", "medium") else "limited",
            "energy_gap": round(gap, 3), "shared_moods": moods, "shared_genres": genres,
            "shared_themes": themes, "same_artist": same, "reasons": reasons}


def target_energy(position, count, journey="rising", peak_position=85, peak_shape="gradual"):
    """Soft target curve; the track catalogue, not the curve, determines the peak."""
    if count <= 1: return 0.55
    x = position / (count - 1)
    peak = max(0.05, min(0.98, peak_position / 100))
    if journey == "steady": return 0.52
    if journey == "falling": return 0.90 - 0.68 * x
    if journey == "wave":
        import math
        return 0.42 + 0.34 * (0.5 - 0.5 * math.cos(2 * math.pi * x))
    if x <= peak:
        t = x / peak
        if peak_shape == "sharp": t = t ** 1.8
        elif peak_shape == "sustained": t = min(1.0, t * 1.35)
        return 0.18 + 0.78 * t
    t = (x - peak) / (1 - peak)
    if peak_shape == "sharp": t = t ** 0.65
    elif peak_shape == "sustained": t = max(0.0, (t - 0.18) / 0.82)
    return 0.96 - 0.72 * t


def transition_summary(scored):
    from collections import Counter
    pairs = [transition_report(a, b) for a, b in zip(scored, scored[1:])]
    counts = Counter(row["label"] for row in pairs)
    return {"pairs": pairs, "gentle": counts["gentle"], "moderate": counts["moderate"],
            "potential_jumps": counts["potential jump"],
            "limited_evidence": sum(row["confidence"] == "limited" for row in pairs)}


def _sequence_objective(rows, journey, peak_position, peak_shape, genre_strength, theme_strength):
    total = 0.0
    for index, row in enumerate(rows):
        # Curve fit is intentionally low-weight: continuity beats a mathematically perfect arc.
        total += 0.10 * abs(float(row["score"]) / 100 - target_energy(
            index, len(rows), journey, peak_position, peak_shape))
        if index:
            previous = rows[index - 1]
            total += _transition_cost(previous, row, genre_strength, theme_strength)
            left_section, right_section = previous.get("section_index"), row.get("section_index")
            if left_section is not None and right_section is not None and right_section < left_section:
                total += 0.10
    return total


def _smooth_order(rows, journey="rising", peak_position=85, peak_shape="gradual",
                  genre_strength=0.0, theme_strength=0.0, fixed_positions=None):
    """Multi-start nearest-neighbor followed by whole-sequence swap/relocation refinement."""
    rows = list(rows)
    if len(rows) < 2: return rows
    fixed_positions = fixed_positions or {}
    fixed = {}
    for row in rows:
        uri = row["item"]["uri"]
        if uri in fixed_positions:
            position = max(0, min(len(rows) - 1, int(fixed_positions[uri])))
            if position in fixed and fixed[position] is not row:
                raise ValueError("Conflicting opener, closer, or pinned-track anchors at position " + str(position))
            fixed[position] = row
    locked = {id(row) for row in fixed.values()}
    movable = [row for row in rows if id(row) not in locked]
    if not movable:
        return [fixed.get(i, rows[i]) for i in range(len(rows))]
    seeds = sorted(movable, key=lambda row: row["original_index"])[:min(8, len(movable))]
    candidates = []
    for seed in seeds or movable[:1]:
        remaining = [row for row in movable if row is not seed]
        order = [seed]
        while remaining:
            nxt = min(remaining, key=lambda row: (
                _transition_cost(order[-1], row, genre_strength, theme_strength),
                abs(row["score"] - order[-1]["score"]) * 0.001, row["original_index"]))
            order.append(nxt)
            remaining.remove(nxt)
        iterator = iter(order)
        candidates.append([fixed[i] if i in fixed else next(iterator) for i in range(len(rows))])
    best = min(candidates, key=lambda seq: _sequence_objective(
        seq, journey, peak_position, peak_shape, genre_strength, theme_strength))
    best_cost = _sequence_objective(best, journey, peak_position, peak_shape, genre_strength, theme_strength)
    for _ in range(4):
        changed = False
        for i in range(len(best)):
            if i in fixed: continue
            for j in range(i + 1, len(best)):
                if j in fixed: continue
                trial = list(best)
                trial[i], trial[j] = trial[j], trial[i]
                cost = _sequence_objective(trial, journey, peak_position, peak_shape, genre_strength, theme_strength)
                if cost + 1e-9 < best_cost:
                    best, best_cost, changed = trial, cost, True
        for i in range(len(best)):
            if i in fixed: continue
            for j in range(len(best)):
                if j in fixed or i == j: continue
                trial = list(best)
                moved = trial.pop(i)
                trial.insert(j, moved)
                if any(trial[pos] is not row for pos, row in fixed.items()): continue
                cost = _sequence_objective(trial, journey, peak_position, peak_shape, genre_strength, theme_strength)
                if cost + 1e-9 < best_cost:
                    best, best_cost, changed = trial, cost, True
        if not changed: break
    return best


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
                    direction="ascending", group_by="none", mode="smooth",
                    journey="rising", peak_position=85, peak_shape="gradual",
                    genre_strength=0.0, theme_strength=0.0, opener_uri=None,
                    closer_uri=None, pinned_uris=None, sections=None):
    """Smooth Flow is the default; journey and section preferences are soft."""
    if direction not in {"ascending", "descending"}: raise ValueError("direction must be ascending or descending")
    if group_by not in {"none", "vibe", "genre", "theme"}: raise ValueError("invalid group_by")
    if mode not in {"smooth", "hybrid", "energy", "atmosphere", "style", "narrative", "discovery"}:
        raise ValueError("invalid mode")
    if journey not in {"rising", "falling", "wave", "steady"}: raise ValueError("invalid journey")
    if peak_shape not in {"gradual", "sharp", "sustained"}: raise ValueError("invalid peak shape")
    if not 10 <= int(peak_position) <= 100: raise ValueError("peak_position must be between 10 and 100")
    artists = artist_profiles or {}
    section_lookup = {}
    for section_index, (name, uris) in enumerate((sections or {}).items()):
        if not isinstance(uris, list): raise ValueError("each section must map to a URI list")
        for uri in uris: section_lookup[uri] = (section_index, name)
    scored = []
    for index, item in enumerate(items):
        if not isinstance(item, dict) or not item.get("uri"): continue
        profile = score_track(item, artists, track_profiles)
        group_field = {"vibe": "vibe_groups", "genre": "genre_groups", "theme": "theme_groups"}.get(group_by)
        artist_profile = artists.get(norm(profile["artist"]), {})
        section = section_lookup.get(item["uri"], (None, "unassigned"))
        profile["sequence_group"] = (profile.get(group_field) or [section[1]])[0] if group_field else section[1]
        profile["artist_play_count"] = artist_profile.get("play_count")
        profile["narrative_phase"] = _narrative_phase(profile)
        profile["section_index"], profile["section_name"] = section
        profile["section_groups"] = [f"section:{section[0]}"] if section[0] is not None else []
        scored.append({"original_index": index, "item": item, **profile})
    if mode in {"smooth", "hybrid"}:
        fixed = {}
        uri_counts = Counter(row["item"]["uri"] for row in scored)
        requested = set(pinned_uris or []) | {uri for uri in (opener_uri, closer_uri) if uri}
        ambiguous = [uri for uri in requested if uri_counts[uri] > 1]
        if ambiguous:
            raise ValueError("Anchor URI occurs more than once; pinning is ambiguous: " + ", ".join(ambiguous))
        if opener_uri: fixed[opener_uri] = 0
        if closer_uri: fixed[closer_uri] = len(scored) - 1
        for row in scored:
            if row["item"]["uri"] in set(pinned_uris or []):
                fixed[row["item"]["uri"]] = row["original_index"]
        # hybrid remains a backwards-compatible alias; it no longer partitions energy bands.
        result = _smooth_order(scored, journey, peak_position, peak_shape, genre_strength, theme_strength, fixed)
    elif mode == "energy":
        result = sorted(scored, key=lambda row: (row["score"], row["original_index"]), reverse=direction == "descending")
    elif mode == "atmosphere":
        if group_by == "none":
            for row in scored:
                row["sequence_group"] = (row.get("vibe_groups") or ["unclassified"])[0]
        result = sorted(scored, key=lambda row: (row["narrative_phase"], row["score"], row["original_index"]), reverse=direction == "descending")
    elif mode == "style":
        if group_by == "none":
            for row in scored:
                row["sequence_group"] = (row.get("genre_groups") or ["unclassified"])[0]
        result = sorted(scored, key=lambda row: (row["sequence_group"], row["score"], row["original_index"]), reverse=direction == "descending")
    elif mode == "narrative":
        result = sorted(scored, key=lambda row: (row["narrative_phase"], row["score"], row["original_index"]), reverse=direction == "descending")
        for row in result:
            row["sequence_group"] = f"act-{row['narrative_phase'] + 1}"
    else:
        result = sorted(scored, key=lambda row: (row["artist_play_count"] is None,
            row["artist_play_count"] if row["artist_play_count"] is not None else float("inf"),
            row["score"], row["original_index"]))
    return result

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
    parser.add_argument("--mode", choices=("smooth", "hybrid", "energy", "atmosphere", "style", "narrative", "discovery"), default="smooth")
    parser.add_argument("--journey", choices=("rising", "falling", "wave", "steady"), default="rising")
    parser.add_argument("--peak-position", type=int, default=85, help="Target climax position as percent of playlist length.")
    parser.add_argument("--peak-shape", choices=("gradual", "sharp", "sustained"), default="gradual")
    parser.add_argument("--genre-strength", type=float, default=0.0, help="Soft genre affinity from 0 to 1.")
    parser.add_argument("--theme-strength", type=float, default=0.0, help="Soft theme affinity from 0 to 1.")
    parser.add_argument("--opener-uri")
    parser.add_argument("--closer-uri")
    parser.add_argument("--pin-uri", action="append", default=[], help="Keep this track at its current position; repeatable.")
    parser.add_argument("--sections", type=Path, help="JSON object mapping ordered section names to URI lists.")
    parser.add_argument("--compare", action="store_true", help="Generate alternative 70/85/95 percent peak plans.")
    parser.add_argument("--direction", choices=("ascending", "descending"), default="ascending")
    parser.add_argument("--group-by", choices=("none", "vibe", "genre", "theme"), default="none", help="Soft grouping preference; does not create rigid genre blocks.")
    parser.add_argument("--output", type=Path, default=Path("playlist-sequence-plan.json"))
    args = parser.parse_args()
    try:
        sp = manager.Spotify()
        playlist = manager.find(sp, args.playlist_id)
        snap = manager.snapshot(sp, playlist)
        artists = index_artists(read_json(ARTIST_PROFILES, {}))
        tracks = index_tracks(read_json(TRACK_PROFILES, {}))
        sections = read_json(args.sections, {}) if args.sections else {}
        if not isinstance(sections, dict):
            raise ValueError("--sections must be a JSON object mapping section names to URI lists.")
        def arrange(peak):
            return sequence_tracks(snap["items"], artists, tracks, args.direction, args.group_by, args.mode,
                args.journey, peak, args.peak_shape, args.genre_strength, args.theme_strength,
                args.opener_uri, args.closer_uri, args.pin_uri, sections)
        scored = arrange(args.peak_position)
        plan = make_plan(snap, scored)
        args.output.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f'Preview generated for "{playlist.get("name")}" — {len(scored)} tracks.')
        print(f'Direction: {args.direction}; {len(plan["operations"])} reorder operation(s).')
        summary = transition_summary(scored)
        print("Journey: " + args.journey + "; peak target: " + str(args.peak_position) + "% (" + args.peak_shape + ").")
        print("Transitions: " + str(summary["gentle"]) + " gentle, " + str(summary["moderate"]) + " moderate, " + str(summary["potential_jumps"]) + " potential jumps; limited evidence=" + str(summary["limited_evidence"]) + ".")
        confidence_counts = confidence_summary(scored)
        print("Proposed sequence (position | energy | confidence | group | track):")
        print("Confidence: " + ", ".join(f"{label}={count}" for label, count in confidence_counts.items()))
        for position, row in enumerate(scored, 1):
            group = row.get("sequence_group") or row.get("vibe_group") or "unclassified"
            print(f'  {position:3}. {row["score"]:5.1f} [{row["confidence"]:7}] [{group}] {row["artist"]} — {row["track"]}')
            signals = row.get("evidence") or []
            print("       Signals: " + ("; ".join(signals) if signals else "no sourced metadata; neutral placeholder score"))
        if args.compare and args.mode in ("smooth", "hybrid"):
            for peak in (70, 85, 95):
                if peak == args.peak_position: continue
                variant = arrange(peak)
                variant_path = args.output.with_name(f"{args.output.stem}-peak{peak}{args.output.suffix}")
                variant_path.write_text(json.dumps(make_plan(snap, variant), indent=2) + "\n", encoding="utf-8")
                print("Alternative preview:", variant_path)
        print("Plan written to", args.output)
        print("Review the plan, then run: python spotify_playlist_manager.py apply", args.output)
        print("The manager will show its normal preview and require explicit APPLY confirmation.")
    except (manager.ManagerError, OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"ERROR: {exc}\n")


if __name__ == "__main__":
    main()
