#!/usr/bin/env python3
"""Preview energy-aware sequencing plans for Spotify playlists.

This tool is deliberately preview-only. It reads a playlist through the existing
locked-by-default manager and writes a change plan for spotify_playlist_manager.py
to preview and apply. It never edits Spotify directly.
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

import mood_inference
import spotify_playlist_manager as manager

try:
    from music_library import MusicLibrary
except ImportError:
    _music_path = Path(__file__).resolve().parents[1] / "music"
    if str(_music_path) not in sys.path:
        sys.path.insert(0, str(_music_path))
    try:
        from music_library import MusicLibrary
    except ImportError:
        MusicLibrary = None

ARTIST_PROFILES = Path("assistant_data/music/artist_profiles.json")
TRACK_PROFILES = Path("assistant_data/music/track_profiles.json")
LYRIC_FEATURES = Path("assistant_data/recommendations/lyric_features.json")
AUDIO_PROFILES = Path("assistant_data/music/audio_profiles.json")
ALBUM_PROFILES = Path("assistant_data/music/album_profiles.json")


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
            if isinstance(row, dict) and row.get("artist") and row.get("track")}


def index_audio_profiles(rows):
    """Merge audio providers by recording identity without discarding provenance."""
    indexed = {}
    for row in rows.values() if isinstance(rows, dict) else []:
        if not isinstance(row, dict) or not row.get("artist") or not row.get("track"):
            continue
        key = (norm(row["artist"]), norm(row["track"]))
        merged = indexed.setdefault(key, {"source_profiles": {}})
        engine = str(row.get("analysis_engine") or "").casefold()
        source = str(row.get("source") or "").casefold()
        if "essentia" in engine:
            merged["source_profiles"]["essentia"] = row
        elif "acousticbrainz" in source or row.get("recording_mbid"):
            acoustic_row = dict(row)
            # GetSongBPM may fill a previously empty flat tempo_bpm field on an
            # AcousticBrainz profile. Keep that catalog value out of the AB slot.
            if str(row.get("tempo_source") or "").casefold().startswith("getsongbpm"):
                acoustic_row["tempo_bpm"] = None
            merged["source_profiles"]["acousticbrainz"] = acoustic_row
        elif row.get("getsongbpm") or "getsongbpm" in source:
            merged["source_profiles"]["getsongbpm"] = row.get("getsongbpm") or row
        # Preserve useful scalar metadata, but never erase a populated value
        # with a later null/empty field from another provider.
        for field, value in row.items():
            if value not in (None, "", [], {}):
                merged[field] = value
        if isinstance(row.get("getsongbpm"), dict):
            merged["source_profiles"]["getsongbpm"] = row["getsongbpm"]
    return indexed

def load_library_profiles(items, root=Path("assistant_data/music/library")):
    """Load only profiles referenced by this playlist; fall back per missing record."""
    if MusicLibrary is None or not (Path(root) / "library_index.json").exists():
        return None
    library = MusicLibrary(root)
    artists, tracks, audio, albums = {}, {}, {}, {}
    for item in items:
        names = item.get("artists") or ([item.get("artist")] if item.get("artist") else [])
        artist = str(names[0]) if names else ""
        title = str(item.get("name") or item.get("track") or "")
        album = str(item.get("album") or item.get("album_name") or "")
        uri = str(item.get("uri") or "")
        spotify_id = uri.rsplit(":", 1)[-1] if uri.startswith("spotify:track:") else None
        found = library.get_song(spotify_id=spotify_id, recording_mbid=item.get("recording_mbid"),
                                      artist=artist, track=title, album=album)
        if not found:
            continue
        record = found["song"]
        key = (norm(artist), norm(title))
        tracks[key] = dict(record.get("evidence", {}).get("track_metadata") or {})
        tracks[key]["derived"] = record.get("derived") or {}
        tracks[key]["coverage"] = record.get("coverage") or {}
        if record.get("evidence", {}).get("lyrics"):
            tracks[key]["lyric_analysis"] = record["evidence"]["lyrics"]
        audio[key] = record.get("evidence", {}).get("audio") or {}
        artist_record = found.get("artist") or {}
        artists[norm(artist)] = artist_record.get("evidence") or {}
        album_record = found.get("album") or {}
        if album:
            albums[(norm(artist), norm(album))] = album_record.get("evidence") or {}
    return artists, tracks, audio, albums


def merge_lyric_features(track_profiles, rows):
    """Attach exported lyric themes to track metadata for transition matching."""
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict) or not row.get("artist") or not row.get("track"):
            continue
        key = (norm(row["artist"]), norm(row["track"]))
        profile = track_profiles.setdefault(key, {"artist": row["artist"], "track": row["track"]})
        profile["lyric_analysis"] = row
    return track_profiles


def _tag_rows(profile):
    rows = []
    for field in ("lastfm_tags", "tags", "musicbrainz_tags", "musicbrainz_genres"):
        rows.extend(profile.get(field) or [])
    return [str(row.get("tag", "") if isinstance(row, dict) else row).strip()
            for row in rows if (row.get("tag") if isinstance(row, dict) else row)]


def _track_mood_evidence(profile):
    """Return track-level mood tags, polarity, and calibrated descriptive confidence.

    Distinct descriptors and independent track-tag source families determine
    confidence; raw tag counts are not treated as independent confirmations.
    Artist-level tags are intentionally excluded.
    """
    source_fields = {
        "lastfm_track": ("lastfm_tags", "tags"),
        "musicbrainz_recording": ("musicbrainz_tags",),
    }
    moods = set()
    descriptors = set()
    source_families = set()
    for family, fields in source_fields.items():
        family_moods = set()
        for field in fields:
            for row in profile.get(field) or []:
                tag = row.get("tag", "") if isinstance(row, dict) else row
                if not tag:
                    continue
                label = str(tag).strip()
                key = norm(label)
                if not key:
                    continue
                matches = mood_inference._tag_moods(label)
                if not matches:
                    continue
                family_moods.update(matches)
                descriptors.add(key)
                moods.update(matches)
        if family_moods:
            source_families.add(family)
    energetic = {"aggressive", "energetic", "chaotic", "tense", "rebellious", "cathartic"}
    gentle = {"calm", "dreamy", "melancholic", "introspective", "wistful", "warm", "romantic"}
    has_energetic = bool(moods & energetic)
    has_gentle = bool(moods & gentle)
    conflict = has_energetic and has_gentle
    if not moods:
        confidence = "unknown"
    elif len(source_families) >= 2 and len(descriptors) >= 2 and not conflict:
        confidence = "high"
    elif (len(descriptors) >= 2 or len(source_families) >= 2) and not conflict:
        confidence = "medium"
    else:
        confidence = "low"
    if conflict:
        confidence = "low"
    return {
        "moods": sorted(moods),
        "confidence": confidence,
        "source_families": sorted(source_families),
        "tag_count": len(descriptors),
        "conflict": conflict,
    }


def _signal(value, low, high):
    if value is None:
        return None
    try:
        return max(0.0, min(1.0, (float(value) - low) / (high - low)))
    except (TypeError, ValueError):
        return None


def _tempo_compatible(a, b, tolerance=0.08):
    """Compare tempo estimates while allowing half/double-time equivalence."""
    try:
        a, b = float(a), float(b)
    except (TypeError, ValueError):
        return False
    if not (40 <= a <= 300 and 40 <= b <= 300):
        return False
    ratio = max(a, b) / min(a, b)
    return min(abs(ratio - 1.0), abs(ratio - 2.0)) <= tolerance


def score_track(item, artist_profiles=None, track_profiles=None, audio_profiles=None, album_profiles=None):
    """Score perceived energy while keeping acoustic and semantic confidence separate.

    Genre, mood, lyrics, and artist tags can influence the display score, but
    they can never promote acoustic confidence or make energy comparable.
    """
    artist_profiles = artist_profiles or {}
    track_profiles = track_profiles or {}
    album_profiles = album_profiles or {}
    names = item.get("artists") or ([item.get("artist")] if item.get("artist") else [])
    artist = str(names[0]) if names else ""
    title = str(item.get("name") or item.get("track") or "")
    artist_profile = artist_profiles.get(norm(artist), {})
    album_name = str(item.get("album") or item.get("album_name") or "")
    album_profile = album_profiles.get((norm(artist), norm(album_name)), {})
    track_profile = track_profiles.get((norm(artist), norm(title)), {})
    measured_audio = (audio_profiles or {}).get((norm(artist), norm(title)), {})
    sources = measured_audio.get("source_profiles") or {}
    essentia = sources.get("essentia") or (
        measured_audio if (
            "essentia" in str(measured_audio.get("analysis_engine", "")).casefold()
            or any(measured_audio.get(field) is not None
                   for field in ("integrated_lufs", "loudness_range_lu", "tempo_confidence"))
        ) else {}
    )
    acousticbrainz = sources.get("acousticbrainz") or (measured_audio if "acousticbrainz" in str(measured_audio.get("source", "")).casefold() else {})
    getsongbpm = sources.get("getsongbpm") or measured_audio.get("getsongbpm") or {}
    spotify = item.get("audio_features") or {}

    components, weights, evidence, evidence_sources = [], [], [], []
    acoustic_components, acoustic_weights = [], []
    semantic_components, semantic_weights = [], []
    direct_energy = _signal(spotify.get("energy"), 0, 1)
    if direct_energy is not None:
        components.append(direct_energy); weights.append(0.42)
        acoustic_components.append(direct_energy); acoustic_weights.append(0.42)
        evidence.append(f"Spotify audio-feature energy={direct_energy:.2f}")
        evidence_sources.append("spotify_audio_features")

    # Prefer independent local analysis, then Spotify-provided tempo, then the
    # historical AcousticBrainz estimate, and finally catalog-only GetSongBPM.
    tempo_candidates = []
    for source_name, row, field in (
        ("Essentia", essentia, "tempo_bpm"),
        ("Spotify audio features", spotify, "tempo"),
        ("AcousticBrainz", acousticbrainz, "tempo_bpm"),
        ("GetSongBPM catalog", getsongbpm, "tempo_bpm"),
    ):
        value = row.get(field) if isinstance(row, dict) else None
        try:
            value = float(value) if value is not None else None
        except (TypeError, ValueError):
            value = None
        if value is not None and 40 <= value <= 300:
            tempo_candidates.append((source_name, value))
    tempo_source, tempo_value = tempo_candidates[0] if tempo_candidates else ("unknown", None)
    tempo = _signal(tempo_value, 60, 180)
    if tempo is not None:
        tempo_weight = 0.23 if tempo_source != "GetSongBPM catalog" else 0.08
        components.append(tempo); weights.append(tempo_weight)
        if tempo_source != "GetSongBPM catalog":
            acoustic_components.append(tempo); acoustic_weights.append(tempo_weight)
        evidence.append(f"{tempo_source} tempo={tempo_value:.1f} BPM")
        evidence_sources.append(tempo_source.casefold().replace(" ", "_"))
    tempo_agreement = (
        len(tempo_candidates) >= 2 and
        all(_tempo_compatible(tempo_candidates[0][1], candidate[1])
            for candidate in tempo_candidates[1:])
    )
    if len(tempo_candidates) >= 2:
        evidence.append("independent tempo estimates agree" if tempo_agreement
                        else "tempo estimates disagree; half/double-time ambiguity or version mismatch possible")

    # Only actual LUFS measurements are treated as integrated program loudness.
    loudness = None
    local_lufs = essentia.get("integrated_lufs")
    try:
        local_lufs = float(local_lufs) if local_lufs is not None else None
    except (TypeError, ValueError):
        local_lufs = None
    if local_lufs is not None:
        loudness = _signal(local_lufs, -35, -5)
        components.append(loudness); weights.append(0.15)
        acoustic_components.append(loudness); acoustic_weights.append(0.15)
        evidence.append(f"Essentia integrated loudness={local_lufs:.1f} LUFS")
        evidence_sources.append("essentia_lufs")
    elif spotify.get("loudness") is not None:
        # Spotify's loudness is a dB value, not LUFS. Keep its provenance clear.
        loudness = _signal(spotify.get("loudness"), -35, -5)
        if loudness is not None:
            components.append(loudness); weights.append(0.10)
            acoustic_components.append(loudness); acoustic_weights.append(0.10)
            evidence.append(f"Spotify loudness={float(spotify['loudness']):.1f} dB (not LUFS)")
            evidence_sources.append("spotify_loudness")

    track_mood = _track_mood_evidence(track_profile)
    tag_moods = set(track_mood["moods"])
    artist_tags = _tag_rows(artist_profile)
    artist_moods = set()
    # Artist and album tags are context, never recording-level mood evidence.
    for tag in artist_profile.get("moods") or []:
        artist_moods.update(mood_inference._tag_moods(tag))
    for tag in artist_tags:
        artist_moods.update(mood_inference._tag_moods(tag))
    album_moods = set()
    for row in _tag_rows(album_profile):
        album_moods.update(mood_inference._tag_moods(row))
    energetic = {"aggressive", "energetic", "chaotic", "tense", "rebellious", "cathartic", "uplifting"}
    gentle = {"calm", "dreamy", "melancholic", "introspective", "wistful", "warm", "romantic", "desolate"}
    if tag_moods:
        # Conflicting affect directions are retained as evidence but neutralized
        # for energy blending rather than arbitrarily choosing the first mood.
        mood_score = (0.5 if track_mood["conflict"] else
                      0.72 if tag_moods & energetic else
                      0.28 if tag_moods & gentle else 0.5)
        mood_weight = {"high": 0.15, "medium": 0.10, "low": 0.05}.get(track_mood["confidence"], 0.0)
        components.append(mood_score); weights.append(mood_weight)
        semantic_components.append(mood_score); semantic_weights.append(mood_weight)
        evidence.append("track-tag mood=" + ", ".join(sorted(tag_moods)))
        evidence.append("track mood confidence=" + track_mood["confidence"])
        evidence.append(f"track mood contribution weight={mood_weight:.2f}")
        if track_mood["conflict"]:
            evidence.append("conflicting track mood directions; neutral energy contribution")
    elif album_moods:
        mood_score = 0.68 if album_moods & energetic else 0.32 if album_moods & gentle else 0.5
        mood_weight = 0.04
        components.append(mood_score); weights.append(mood_weight)
        semantic_components.append(mood_score); semantic_weights.append(mood_weight)
        evidence.append("album-level mood context (not track-specific)=" + ", ".join(sorted(album_moods)))
        evidence.append(f"album mood contribution weight={mood_weight:.2f}")
    elif artist_moods:
        mood_score = 0.68 if artist_moods & energetic else 0.32 if artist_moods & gentle else 0.5
        mood_weight = 0.03
        components.append(mood_score); weights.append(mood_weight)
        semantic_components.append(mood_score); semantic_weights.append(mood_weight)
        evidence.append("artist-level mood fallback=" + ", ".join(sorted(artist_moods)))
        evidence.append(f"artist mood contribution weight={mood_weight:.2f}")

    genre_values = []
    for row in track_profile.get("musicbrainz_genres") or []:
        value = row.get("tag", "") if isinstance(row, dict) else row
        if value:
            genre_values.append(norm(value))
    genre_values.extend(norm(value) for value in artist_profile.get("genres") or [] if value)
    genre_values.extend(norm(value) for value in track_profile.get("discogs_styles") or [] if value)
    genre_values.extend(norm(value) for value in track_profile.get("discogs_genres") or [] if value)
    genre_text = " ".join(genre_values)
    high_genre = ("metal", "hardcore", "punk", "industrial", "drum and bass", "breakcore", "hardstyle", "psychobilly", "hard rock", "nu metal", "heavy metal", "metalcore", "horror punk")
    dance_genre = ("electronic", "synthwave", "synthpop", "electropop", "electroclash", "techno", "house", "rave", "ebm", "dark electro", "industrial dance")
    mid_genre = ("rockabilly", "surf rock", "horror surf", "garage rock", "rock and roll", "post-punk", "gothic rock", "deathrock", "darkwave", "alternative rock", "indie rock", "rock")
    low_genre = ("ambient", "drone", "neoclassical", "slowcore", "dark ambient", "shoegaze")
    if any(x in genre_text for x in high_genre): genre_score = 0.78
    elif any(x in genre_text for x in dance_genre): genre_score = 0.72
    elif any(x in genre_text for x in mid_genre): genre_score = 0.62
    elif any(x in genre_text for x in low_genre): genre_score = 0.30
    else: genre_score = None
    if genre_score is not None:
        components.append(genre_score); weights.append(0.05 if tag_moods else 0.08)
        semantic_components.append(genre_score); semantic_weights.append(0.05 if tag_moods else 0.08)
        evidence.append(f"genre-family signal={genre_score:.2f}")

    genre_groups = []
    for row in track_profile.get("musicbrainz_genres") or []:
        value = row.get("tag", "") if isinstance(row, dict) else row
        if value and str(value).strip(): genre_groups.append(str(value).strip())
    genre_groups.extend(str(value).strip() for value in artist_profile.get("genres") or [] if str(value).strip())
    genre_groups.extend(str(value).strip() for value in track_profile.get("discogs_styles") or [] if str(value).strip())
    genre_groups.extend(str(value).strip() for value in track_profile.get("discogs_genres") or [] if str(value).strip())
    theme_groups = [str(value).strip() for value in artist_profile.get("themes") or [] if str(value).strip()]
    theme_groups.extend(str(value).strip() for value in track_profile.get("theme_groups") or [] if str(value).strip())
    lyric_analysis = track_profile.get("lyric_analysis") or {}
    lyric_themes = lyric_analysis.get("themes") or {}
    theme_groups.extend(str(value).strip() for value in lyric_themes if str(value).strip())
    if lyric_themes: evidence.append("lyric-theme evidence: " + ", ".join(sorted(lyric_themes)))
    if essentia.get("loudness_range_lu") is not None:
        evidence.append(f"loudness range={float(essentia['loudness_range_lu']):.1f} LU")
    if acousticbrainz.get("dynamic_complexity") is not None:
        evidence.append(f"AcousticBrainz dynamic complexity={float(acousticbrainz['dynamic_complexity']):.2f}")
    if acousticbrainz.get("tempo_spread_bpm") is not None:
        evidence.append(
            f"AcousticBrainz submission tempo spread={float(acousticbrainz['tempo_spread_bpm']):.1f} BPM "
            f"across {int(acousticbrainz.get('tempo_submission_count') or acousticbrainz.get('submission_count') or 0)} submission(s)"
        )

    if not components:
        score = 50.0
    else:
        score = sum(v * w for v, w in zip(components, weights)) / sum(weights) * 100
    acoustic_score = (
        sum(v * w for v, w in zip(acoustic_components, acoustic_weights)) /
        sum(acoustic_weights) * 100 if acoustic_weights else None
    )
    semantic_score = (
        sum(v * w for v, w in zip(semantic_components, semantic_weights)) /
        sum(semantic_weights) * 100 if semantic_weights else None
    )

    # Acoustic confidence is deliberately independent of genre/mood/lyric counts.
    local_tempo_conf = essentia.get("tempo_confidence")
    try: local_tempo_conf = float(local_tempo_conf) if local_tempo_conf is not None else None
    except (TypeError, ValueError): local_tempo_conf = None
    if direct_energy is not None and (tempo_source in {"Essentia", "Spotify audio features"} and tempo is not None or loudness is not None):
        acoustic_confidence = "high"
    elif local_lufs is not None or (tempo_source == "Essentia" and (local_tempo_conf or 0) >= 0.55) or direct_energy is not None:
        acoustic_confidence = "medium"
    elif tempo_source == "AcousticBrainz":
        acoustic_confidence = "low"
    elif tempo_source == "GetSongBPM catalog":
        acoustic_confidence = "low"
    else:
        acoustic_confidence = "unknown" if not components else "low"

    semantic_source_families = set()
    if track_profile.get("lastfm_tags") or track_profile.get("tags") or artist_tags or artist_profile.get("genres") or album_profile.get("lastfm_tags"):
        semantic_source_families.add("lastfm_community")
    if track_profile.get("musicbrainz_tags") or track_profile.get("musicbrainz_genres"):
        semantic_source_families.add("musicbrainz")
    if track_profile.get("discogs_styles") or track_profile.get("discogs_genres"):
        semantic_source_families.add("discogs_release_context")
    if lyric_themes:
        semantic_source_families.add("lyric_analysis")
    semantic_sources = len(semantic_source_families)
    semantic_confidence = ("high" if semantic_sources >= 3 else
                           "medium" if semantic_sources == 2 else
                           "low" if semantic_sources == 1 else "unknown")
    group_moods = tag_moods or album_moods or artist_moods
    group = next(iter(sorted(group_moods)), "unclassified") if group_moods else "unclassified"
    return {
        "score": round(score, 2),
        "acoustic_score": round(acoustic_score, 2) if acoustic_score is not None else None,
        "semantic_score": round(semantic_score, 2) if semantic_score is not None else None,
        "confidence": acoustic_confidence,  # backwards-compatible acoustic-only alias
        "acoustic_confidence": acoustic_confidence,
        "semantic_confidence": semantic_confidence,
        "mood_confidence": track_mood["confidence"] if tag_moods else ("low" if album_moods or artist_moods else "unknown"),
        "mood_weight": mood_weight if tag_moods or album_moods or artist_moods else 0.0,
        "mood_evidence_scope": "track" if tag_moods else ("album" if album_moods else ("artist" if artist_moods else "unknown")),
        "mood_source_families": track_mood["source_families"] if tag_moods else (["lastfm_album"] if album_moods else (["lastfm_artist"] if artist_moods else [])),
        "mood_tag_count": track_mood["tag_count"],
        "mood_conflict": track_mood["conflict"],
        "semantic_source_families": sorted(semantic_source_families),
        "tempo_bpm": tempo_value,
        "tempo_source": tempo_source,
        "tempo_agreement": tempo_agreement if len(tempo_candidates) >= 2 else None,
        "tempo_sources": [{"source": name, "bpm": value} for name, value in tempo_candidates],
        "evidence_sources": sorted(set(evidence_sources)),
        "evidence": evidence, "artist": artist, "track": title,
        "vibe_group": group, "vibe_groups": sorted(tag_moods or album_moods or artist_moods),
        "genre_groups": sorted(set(genre_groups)), "theme_groups": sorted(set(theme_groups)),
    }

def _set_similarity(left, right):
    """Jaccard affinity; callers decide whether both sides have evidence."""
    a, b = set(left or []), set(right or [])
    return len(a & b) / len(a | b) if a and b else None


def _tempo_relationship(left, right):
    """Return a bounded mismatch that treats half/double-time as compatible."""
    try:
        a = float(left.get("tempo_bpm"))
        b = float(right.get("tempo_bpm"))
    except (TypeError, ValueError):
        return None
    if not (40 <= a <= 300 and 40 <= b <= 300):
        return None
    ratios = (b / a, a / b)
    ratio = min(ratios)
    # A 2:1 or 1:2 tempo relationship is a natural rhythmic bridge.
    distance = min(abs(ratio - 1.0), abs(ratio - 0.5) * 0.65)
    return max(0.0, min(1.0, distance / 0.5))


def _energy_score(row):
    """Return an acoustic-only energy estimate, never a semantic blend."""
    if "acoustic_score" in row:
        return row.get("acoustic_score")
    # Hand-authored rows may supply an explicit acoustic tier without the
    # newer split score; ordinary legacy rows are not trusted as measured.
    return row.get("score") if row.get("acoustic_confidence") in {"medium", "high"} else None


def _has_reliable_energy(row):
    """Only medium/high estimates are reliable enough to drive transition scoring."""
    return row.get("acoustic_confidence") in {"medium", "high"}


def _transition_cost(left, right, genre_strength=0.0, theme_strength=0.0, artist_penalty=True):
    """Evidence-aware edge cost: absent or weak metadata is omitted, not treated as fact."""
    terms = []
    # Low-confidence genre/artist estimates can guide discovery, but should not
    # dominate handoff quality as if they were measured track energy.
    if _has_reliable_energy(left) and _has_reliable_energy(right):
        left_energy, right_energy = _energy_score(left), _energy_score(right)
        if left_energy is not None and right_energy is not None:
            terms.append((0.34, abs(float(left_energy) - float(right_energy)) / 100.0))
    mood_tiers = {"high": 0.25, "medium": 0.17, "low": 0.08, "unknown": 0.0}
    left_mood_conf = left.get("mood_confidence", "low")
    right_mood_conf = right.get("mood_confidence", "low")
    mood_weight = min(mood_tiers.get(left_mood_conf, 0.0),
                      mood_tiers.get(right_mood_conf, 0.0))
    for field, weight in (("vibe_groups", mood_weight),
                          ("genre_groups", 0.08), ("theme_groups", 0.08)):
        affinity = _set_similarity(left.get(field), right.get(field))
        if affinity is not None and weight > 0:
            terms.append((weight, 1.0 - affinity))
    tempo_gap = _tempo_relationship(left, right)
    if tempo_gap is not None:
        terms.append((0.12, tempo_gap))
    section = _set_similarity(left.get("section_groups"), right.get("section_groups"))
    if section is not None:
        terms.append((0.08, 1.0 - section))
    same_artist = bool(norm(left.get("artist")) and norm(left.get("artist")) == norm(right.get("artist")))
    numerator = sum(weight * value for weight, value in terms)
    denominator = sum(weight for weight, _ in terms)
    cost = numerator / denominator if denominator else 0.5
    # Repetition is a genuine sequencing issue, but cap its impact so it cannot
    # overwhelm musical compatibility or make an otherwise strong transition fail.
    if same_artist and artist_penalty:
        # A repeated artist is a sequencing/diversity issue, not a sonic mismatch.
        # Make it strong enough to break up long artist runs when alternatives exist.
        cost += 0.65
    genre_affinity = _set_similarity(left.get("genre_groups"), right.get("genre_groups"))
    theme_affinity = _set_similarity(left.get("theme_groups"), right.get("theme_groups"))
    if genre_affinity is not None:
        cost -= 0.08 * max(0.0, min(1.0, genre_strength)) * genre_affinity
    if theme_affinity is not None:
        cost -= 0.08 * max(0.0, min(1.0, theme_strength)) * theme_affinity
    return max(0.0, min(1.0, cost))


def transition_report(left, right):
    energy_known = (
        _has_reliable_energy(left) and _has_reliable_energy(right)
        and _energy_score(left) is not None and _energy_score(right) is not None
    )
    gap = abs(float(_energy_score(left)) - float(_energy_score(right))) / 100.0 if energy_known else None
    moods = sorted(set(left.get("vibe_groups") or []) & set(right.get("vibe_groups") or []))
    genres = sorted(set(left.get("genre_groups") or []) & set(right.get("genre_groups") or []))
    themes = sorted(set(left.get("theme_groups") or []) & set(right.get("theme_groups") or []))
    same = bool(norm(left.get("artist")) and norm(left.get("artist")) == norm(right.get("artist")))
    tempo_gap = _tempo_relationship(left, right)
    # Reports describe musical compatibility; the optimizer separately applies
    # a stronger artist-diversity penalty to avoid long consecutive runs.
    cost = _transition_cost(left, right, artist_penalty=False)
    reasons = []
    if moods: reasons.append("shared track mood: " + ", ".join(moods))
    if genres: reasons.append("shared genre: " + ", ".join(genres))
    if themes: reasons.append("shared theme: " + ", ".join(themes))
    if tempo_gap is not None:
        reasons.append("compatible tempo relationship (including half/double-time)")
    if energy_known:
        if gap <= 0.12: reasons.append("similar estimated energy")
        elif gap >= 0.35: reasons.append("large estimated energy change")
    if same: reasons.append("same primary artist")
    if not reasons: reasons.append("insufficient shared metadata; transition remains uncertain")
    mood_supported = (
        left.get("mood_confidence") in {"medium", "high"}
        and right.get("mood_confidence") in {"medium", "high"}
        and bool(left.get("vibe_groups")) and bool(right.get("vibe_groups"))
    )
    evidence_count = int(mood_supported)
    evidence_count += sum(bool(left.get(field)) and bool(right.get(field))
                          for field in ("genre_groups", "theme_groups"))
    evidence_count += int(tempo_gap is not None)
    evidence_count += int(energy_known)
    confidence = "supported" if evidence_count >= 2 and energy_known else "limited"
    label = ("uncertain" if evidence_count == 0 else
             "provisional" if confidence == "limited" else
             "provisional" if confidence == "limited" else "gentle" if cost < 0.34 else "moderate" if cost < 0.52 else "potential jump")
    return {"cost": round(cost, 4), "label": label,
            "confidence": confidence, "evidence_count": evidence_count,
            "energy_gap": round(gap, 3) if gap is not None else None,
            "tempo_relationship": round(tempo_gap, 3) if tempo_gap is not None else None,
            "shared_moods": moods, "shared_genres": genres,
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
    if journey == "rising":
        return 0.96
    t = (x - peak) / (1 - peak)
    if peak_shape == "sharp": t = t ** 0.65
    elif peak_shape == "sustained": t = max(0.0, (t - 0.18) / 0.82)
    return 0.96 - 0.72 * t


def transition_summary(scored):
    from collections import Counter
    pairs = [transition_report(a, b) for a, b in zip(scored, scored[1:])]
    counts = Counter(row["label"] for row in pairs)
    return {"pairs": pairs, "gentle": counts["gentle"], "moderate": counts["moderate"],
            "potential_jumps": counts["potential jump"], "provisional": counts["provisional"],
            "uncertain": counts["uncertain"],
            "limited_evidence": sum(row["confidence"] == "limited" for row in pairs)}


def _sequence_objective(rows, journey, peak_position, peak_shape, genre_strength, theme_strength, position_offset=0, total_count=None):
    total = 0.0
    for index, row in enumerate(rows):
        # Curve fit is intentionally low-weight: continuity beats a mathematically perfect arc.
        # Unknown scores use 50 only as a display placeholder. They must not be
        # pulled toward or away from a journey curve as if 50 were measured data.
        energy_value = _energy_score(row)
        if energy_value is not None and row.get("acoustic_confidence") != "unknown":
            curve_weight = 0.10 if row.get("acoustic_confidence") in {"high", "medium"} else 0.04
            total += curve_weight * abs(float(energy_value) / 100 - target_energy(
                index + position_offset, total_count or len(rows), journey, peak_position, peak_shape))
        if index:
            previous = rows[index - 1]
            total += _transition_cost(previous, row, genre_strength, theme_strength)
            if index >= 2:
                artist = norm(row.get("artist"))
                previous_artist = norm(previous.get("artist"))
                before_previous_artist = norm(rows[index - 2].get("artist"))
                if artist and artist == previous_artist == before_previous_artist:
                    # Strongly discourage a third consecutive track by the same artist.
                    total += 1.25
            left_section, right_section = previous.get("section_index"), row.get("section_index")
            if left_section is not None and right_section is not None and right_section < left_section:
                total += 2.0
    return total


def _smooth_order(rows, journey="rising", peak_position=85, peak_shape="gradual",
                  genre_strength=0.0, theme_strength=0.0, fixed_positions=None,
                  position_offset=0, total_count=None):
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
    ordered_movable = sorted(movable, key=lambda row: row["original_index"])
    seed_count = min(4, len(ordered_movable))
    seed_indices = ([0] if seed_count == 1 else
                    [round(i * (len(ordered_movable) - 1) / (seed_count - 1))
                     for i in range(seed_count)])
    seeds = [ordered_movable[index] for index in seed_indices]
    candidates = []
    for seed in seeds or movable[:1]:
        remaining = [row for row in movable if row is not seed]
        order = [seed]
        while remaining:
            # Avoid creating runs of three or more by the same primary artist
            # whenever another artist is still available.
            last_artist = norm(order[-1].get("artist"))
            previous_artist = norm(order[-2].get("artist")) if len(order) > 1 else ""
            pool = remaining
            if last_artist and last_artist == previous_artist:
                alternatives = [row for row in remaining
                                if norm(row.get("artist")) != last_artist]
                if alternatives:
                    pool = alternatives
            nxt = min(pool, key=lambda row: (
                _transition_cost(order[-1], row, genre_strength, theme_strength),
                (abs(float(_energy_score(row)) - float(_energy_score(order[-1]))) * 0.001
                 if _has_reliable_energy(row) and _has_reliable_energy(order[-1]) and _energy_score(row) is not None and _energy_score(order[-1]) is not None else 0.0),
                row["original_index"]))
            order.append(nxt)
            remaining.remove(nxt)
        iterator = iter(order)
        candidates.append([fixed[i] if i in fixed else next(iterator) for i in range(len(rows))])
    best = min(candidates, key=lambda seq: _sequence_objective(
        seq, journey, peak_position, peak_shape, genre_strength, theme_strength,
        position_offset, total_count))
    best_cost = _sequence_objective(best, journey, peak_position, peak_shape, genre_strength, theme_strength,
        position_offset, total_count)
    # Local refinement avoids the cubic full-objective scan across every possible
    # swap/relocation. Diverse seeds plus a 12-track neighborhood keep previews
    # responsive on ordinary playlists while preserving exact anchor positions.
    neighborhood = 12
    for _ in range(2):
        changed = False
        for i in range(len(best)):
            if i in fixed: continue
            for j in range(i + 1, min(len(best), i + neighborhood + 1)):
                if j in fixed: continue
                trial = list(best)
                trial[i], trial[j] = trial[j], trial[i]
                cost = _sequence_objective(trial, journey, peak_position, peak_shape, genre_strength, theme_strength,
                    position_offset, total_count)
                if cost + 1e-9 < best_cost:
                    best, best_cost, changed = trial, cost, True
        for i in range(len(best)):
            if i in fixed: continue
            for j in range(max(0, i - neighborhood), min(len(best), i + neighborhood + 1)):
                if j in fixed or i == j: continue
                trial = list(best)
                moved = trial.pop(i)
                trial.insert(j, moved)
                if any(trial[pos] is not row for pos, row in fixed.items()): continue
                cost = _sequence_objective(trial, journey, peak_position, peak_shape, genre_strength, theme_strength,
                    position_offset, total_count)
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
                    closer_uri=None, pinned_uris=None, sections=None, audio_profiles=None, album_profiles=None):
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
        profile = score_track(item, artists, track_profiles, audio_profiles, album_profiles)
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
        available_uris = {row["item"]["uri"] for row in scored}
        requested = set(pinned_uris or []) | {uri for uri in (opener_uri, closer_uri) if uri}
        missing = sorted(requested - available_uris)
        if missing:
            raise ValueError("Requested anchor URI is not in this playlist: " + ", ".join(missing))
        if group_by == "genre": genre_strength = max(genre_strength, 0.35)
        if group_by == "theme": theme_strength = max(theme_strength, 0.35)
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
        # When explicit narrative sections are supplied, preserve their declared
        # order and optimize transitions/artist variety inside each act. This
        # prevents a smooth local handoff from moving the dance-floor or finale
        # ahead of the requested opening. Anchored generic sorts retain the
        # global optimizer so absolute pin positions remain meaningful.
        if sections and not (opener_uri or closer_uri or pinned_uris):
            grouped = {}
            for row in scored:
                grouped.setdefault(row.get("section_index"), []).append(row)
            result = []
            position_offset = 0
            ordered_sections = sorted(index for index in grouped if index is not None)
            for section_index in ordered_sections:
                ordered_group = _smooth_order(
                    grouped[section_index], journey, peak_position, peak_shape,
                    genre_strength, theme_strength,
                    position_offset=position_offset, total_count=len(scored),
                )
                result.extend(ordered_group)
                position_offset += len(ordered_group)
            if None in grouped:
                result.extend(_smooth_order(
                    grouped[None], journey, peak_position, peak_shape,
                    genre_strength, theme_strength,
                    position_offset=position_offset, total_count=len(scored),
                ))
        else:
            # hybrid remains a backwards-compatible alias; it no longer partitions energy bands.
            result = _smooth_order(scored, journey, peak_position, peak_shape, genre_strength, theme_strength, fixed)
    elif mode == "energy":
        known_energy = [row for row in scored if row.get("acoustic_score") is not None]
        unknown_energy = [row for row in scored if row.get("acoustic_score") is None]
        result = sorted(
            known_energy,
            key=lambda row: (row["acoustic_score"], row["original_index"]),
            reverse=direction == "descending",
        ) + sorted(unknown_energy, key=lambda row: row["original_index"])
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


def evidence_coverage_summary(scored):
    """Summarize confidence and independent tempo-source coverage for a preview."""
    from collections import Counter
    acoustic = Counter(row.get("acoustic_confidence", row.get("confidence", "unknown"))
                       for row in scored)
    semantic = Counter(row.get("semantic_confidence", "unknown") for row in scored)
    mood = Counter(row.get("mood_confidence", "unknown") for row in scored)
    mood_source_coverage = Counter(
        source for row in scored for source in row.get("mood_source_families", [])
    )
    semantic_source_coverage = Counter(
        source for row in scored for source in row.get("semantic_source_families", [])
    )
    acoustic_source_coverage = Counter(
        source for row in scored for source in row.get("evidence_sources", [])
    )
    tempo_sources = Counter(row.get("tempo_source", "unknown") for row in scored
                            if row.get("tempo_bpm") is not None)
    return {
        "acoustic_confidence": {key: acoustic.get(key, 0) for key in ("high", "medium", "low", "unknown")},
        "semantic_confidence": {key: semantic.get(key, 0) for key in ("high", "medium", "low", "unknown")},
        "mood_confidence": {key: mood.get(key, 0) for key in ("high", "medium", "low", "unknown")},
        "mood_source_coverage": dict(sorted(mood_source_coverage.items())),
        "tempo_sources": dict(sorted(tempo_sources.items())),
        "acoustic_source_coverage": dict(sorted(acoustic_source_coverage.items())),
        "semantic_source_coverage": dict(sorted(semantic_source_coverage.items())),
        "tempo_agreements": sum(row.get("tempo_agreement") is True for row in scored),
        "tempo_disagreements": sum(row.get("tempo_agreement") is False for row in scored),
    }


def alternative_preview_message(path, summary):
    """Format the comparison-plan summary without mixing output and string building."""
    return (
        f"Alternative preview: {path} | gentle: {summary['gentle']} "
        f"| moderate: {summary['moderate']} "
        f"| potential jumps: {summary['potential_jumps']} "
        f"| provisional: {summary.get('provisional', 0)} "
        f"| uncertain: {summary.get('uncertain', 0)}"
    )


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
        library_profiles = load_library_profiles(snap["items"])
        if library_profiles is not None:
            artists, tracks, audio_profiles, album_profiles = library_profiles
            # Missing library records remain eligible for the legacy cache during
            # incremental migration; existing records are loaded on demand only.
            legacy_tracks = index_tracks(read_json(TRACK_PROFILES, {}))
            for item in snap["items"]:
                names = item.get("artists") or ([item.get("artist")] if item.get("artist") else [])
                key = (norm(names[0]) if names else "", norm(item.get("name") or item.get("track")))
                if key not in tracks and key in legacy_tracks:
                    tracks[key] = legacy_tracks[key]
        else:
            artists = index_artists(read_json(ARTIST_PROFILES, {}))
            tracks = index_tracks(read_json(TRACK_PROFILES, {}))
            tracks = merge_lyric_features(tracks, read_json(LYRIC_FEATURES, []))
            audio_rows = read_json(AUDIO_PROFILES, {})
            audio_profiles = index_audio_profiles(audio_rows.get("tracks", audio_rows) if isinstance(audio_rows, dict) else {})
            album_rows = read_json(ALBUM_PROFILES, {})
            album_profiles = {(norm(row.get("artist")), norm(row.get("album"))): row
                              for row in album_rows.values() if isinstance(row, dict) and row.get("artist") and row.get("album")}
        sections = read_json(args.sections, {}) if args.sections else {}
        if not isinstance(sections, dict):
            raise ValueError("--sections must be a JSON object mapping section names to URI lists.")
        def arrange(peak):
            return sequence_tracks(snap["items"], artists, tracks, args.direction, args.group_by, args.mode,
                args.journey, peak, args.peak_shape, args.genre_strength, args.theme_strength,
                args.opener_uri, args.closer_uri, args.pin_uri, sections, audio_profiles, album_profiles)
        scored = arrange(args.peak_position)
        plan = make_plan(snap, scored)
        args.output.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f'Preview generated for "{playlist.get("name")}" — {len(scored)} tracks.')
        print(f'Direction: {args.direction}; {len(plan["operations"])} reorder operation(s).')
        summary = transition_summary(scored)
        print("Journey: " + args.journey + "; peak target: " + str(args.peak_position) + "% (" + args.peak_shape + ").")
        print("Transitions: " + str(summary["gentle"]) + " gentle, " + str(summary["moderate"]) + " moderate, " + str(summary["potential_jumps"]) + " supported potential jumps, " + str(summary["provisional"]) + " provisional (limited evidence), " + str(summary["uncertain"]) + " uncertain (no evidence).")
        confidence_counts = confidence_summary(scored)
        print("Merged audio profiles loaded: " + str(len(audio_profiles)))
        print("Album profiles loaded: " + str(len(album_profiles)))
        print("Proposed sequence (position | perceived energy | acoustic energy | confidence | group | track):")
        print("Acoustic confidence: " + ", ".join(f"{label}={count}" for label, count in confidence_counts.items()))
        coverage = evidence_coverage_summary(scored)
        print("Semantic confidence: " + ", ".join(f"{label}={count}" for label, count in coverage["semantic_confidence"].items()))
        print("Track mood confidence: " + ", ".join(f"{label}={count}" for label, count in coverage["mood_confidence"].items()))
        print("Track mood sources: " + (", ".join(f"{name}={count}" for name, count in coverage["mood_source_coverage"].items()) or "none"))
        print("Acoustic sources: " + (", ".join(f"{name}={count}" for name, count in coverage["acoustic_source_coverage"].items()) or "none"))
        print("Semantic sources: " + (", ".join(f"{name}={count}" for name, count in coverage["semantic_source_coverage"].items()) or "none"))
        print("Tempo sources: " + (", ".join(f"{name}={count}" for name, count in coverage["tempo_sources"].items()) or "none") + f"; agreement={coverage['tempo_agreements']}; disagreement={coverage['tempo_disagreements']}")
        for position, row in enumerate(scored, 1):
            group = row.get("sequence_group") or row.get("vibe_group") or "unclassified"
            acoustic_display = f"{row['acoustic_score']:.1f}" if row.get("acoustic_score") is not None else "n/a"
            print(f'  {position:3}. {row["score"]:5.1f} / {acoustic_display:>5} [{row["confidence"]:7}] [{group}] {row["artist"]} — {row["track"]}')
            signals = row.get("evidence") or []
            print("       Signals: " + ("; ".join(signals) if signals else "no sourced metadata; neutral placeholder score"))
            if position < len(scored):
                pair = summary["pairs"][position - 1]
                print("       Next transition: " + pair["label"] + " (" + pair["confidence"] + " evidence): " + "; ".join(pair["reasons"]))
        if args.compare and args.mode in ("smooth", "hybrid"):
            for peak in (70, 85, 95):
                if peak == args.peak_position: continue
                variant = arrange(peak)
                variant_path = args.output.with_name(f"{args.output.stem}-peak{peak}{args.output.suffix}")
                variant_path.write_text(json.dumps(make_plan(snap, variant), indent=2) + "\n", encoding="utf-8")
                alt_summary = transition_summary(variant)
                print(alternative_preview_message(variant_path, alt_summary))
        print("Plan written to", args.output)
        print("Review the plan, then run: python spotify_playlist_manager.py apply", args.output)
        print("The manager will show its normal preview and require explicit APPLY confirmation.")
    except (manager.ManagerError, OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"ERROR: {exc}\n")


if __name__ == "__main__":
    main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Preview energy-aware Spotify playlist sequences and write reorder plans for review. The sequencer never edits Spotify directly; the locked-by-default playlist manager performs the separate preview and confirmation-gated apply.
# Inputs: Reads the selected Spotify playlist plus artist, track-tag, lyric-theme, and acoustic-profile caches under assistant_data/. Missing metadata remains unknown rather than being treated as a measured neutral value.
# Outputs: Writes a JSON reorder plan; --compare also writes alternative peak-position plans and prints their transition summaries.
# Run: python compat/spotify_playlist_sequencer.py PLAYLIST_ID [--journey rising|falling|wave|steady] [--peak-position 85] [--compare].
# Safety: Refuses incomplete playlist membership and invalid or ambiguous anchors. Apply plans only through spotify_playlist_manager.py after reviewing its preview.
# Related: tests/test_spotify_playlist_sequencer.py; docs/TRANSITION_SCORING.md; scripts/spotify/spotify_playlist_manager.py.
# -----------------------------------------------------------------------------
