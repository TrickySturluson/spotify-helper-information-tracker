"""Conservative mood inference from artist-level Last.fm tags."""
import math
import re

def _norm(value):
    return re.sub(r'\s+', ' ', str(value or '').strip()).casefold()

# Explicit mood/affect descriptors only; genre and scene labels are intentionally excluded.
MOOD_LEXICON = {
    'dark': {'dark','darkwave','gloomy','bleak','ominous','brooding','sinister','macabre','noir','dystopian','occult','witch house'},
    'eerie': {'eerie','haunting','spooky','creepy','ghostly','horror','halloween','unsettling','uncanny','surreal','creepypasta'},
    'aggressive': {'aggressive','angry','rage','abrasive','violent','brutal','ferocious','hostile','intense','confrontational'},
    'energetic': {'energetic','high energy','danceable','uptempo','fast paced','driving','powerful','exhilarating','adrenaline'},
    'dreamy': {'dreamy','ethereal','hazy','floaty','atmospheric','ambient','hypnotic','ethereal wave','shoegaze'},
    'melancholic': {'melancholic','melancholy','sad','depressing','depressed','lonely','heartbroken','mournful','bittersweet','wistful'},
    'calm': {'calm','peaceful','relaxing','relaxed','chill','soothing','meditative','serene','tranquil','laid back'},
    'upbeat': {'happy','cheerful','joyful','uplifting','optimistic','feel good','fun','playful','bouncy','carefree'},
    'romantic': {'romantic','sensual','intimate','tender','passionate','love','seductive','sultry'},
    'psychedelic': {'psychedelic','trippy','mind bending','kaleidoscopic','hypnotic','surreal'},
    'nostalgic': {'nostalgic','retro','nostalgia','vintage','oldies','throwback','wistful'},
}

def _tag_moods(tag):
    value = _norm(tag)
    matches = []
    for mood, terms in MOOD_LEXICON.items():
        if value in terms or any(len(term) > 5 and term in value for term in terms):
            matches.append(mood)
    return matches

def infer_mood_profile(items, artist_profiles):
    """Aggregate conservative mood evidence, weighted by playlist artist presence.
    A tag contributes at most once per artist and mood; Last.fm tag counts scale
    confidence but cannot let one prolific tag dominate the entire playlist.
    """
    artist_tracks = {}
    for item in items or []:
        if not isinstance(item, dict):
            continue
        names = item.get('artists') or ([item.get('artist')] if item.get('artist') else [])
        if names and names[0]:
            key = _norm(names[0])
            artist_tracks[key] = artist_tracks.get(key, 0) + 1
    totals = {mood: 0.0 for mood in MOOD_LEXICON}
    supporters = {mood: set() for mood in MOOD_LEXICON}
    evidence = {mood: [] for mood in MOOD_LEXICON}
    for artist, track_count in artist_tracks.items():
        profile = artist_profiles.get(artist, {}) or {}
        tags = profile.get('tags') or []
        per_artist = {}
        for row in tags:
            if isinstance(row, dict):
                tag, raw_count = row.get('tag', ''), row.get('count', 1)
            else:
                tag, raw_count = row, 1
            try:
                strength = min(1.0, max(0.15, math.log1p(max(0, float(raw_count))) / math.log(101)))
            except (TypeError, ValueError):
                strength = 0.25
            for mood in _tag_moods(tag):
                per_artist[mood] = max(per_artist.get(mood, 0.0), strength)
                evidence[mood].append((artist, str(tag)))
        # Each artist's playlist presence matters, but repeated tracks are capped.
        presence = 1.0 + min(track_count - 1, 4) * 0.15
        for mood, strength in per_artist.items():
            totals[mood] += strength * presence
            supporters[mood].add(artist)
    track_total = max(1, len(items or []))
    ranked = []
    for mood, score in totals.items():
        if not supporters[mood]:
            continue
        artist_share = len(supporters[mood]) / max(1, len(artist_tracks))
        track_support = sum(count for artist, count in artist_tracks.items() if artist in supporters[mood]) / track_total
        # Confidence rewards multiple independent artists and broad playlist coverage.
        confidence = min(1.0, 0.65 * artist_share + 0.35 * track_support)
        ranked.append({
            'mood': mood, 'score': round(score, 3),
            'artist_support': len(supporters[mood]),
            'artist_share': round(artist_share, 3),
            'track_support': round(track_support, 3),
            'confidence': round(confidence, 3),
            'evidence': sorted({tag for _, tag in evidence[mood]}, key=str.casefold)[:8],
        })
    ranked.sort(key=lambda row: (-row['score'], -row['artist_support'], row['mood']))
    return {
        'method': 'artist Last.fm tags mapped through conservative mood lexicon',
        'artist_count': len(artist_tracks),
        'artists_with_tag_evidence': len({artist for rows in evidence.values() for artist, _ in rows}),
        'moods': ranked[:8],
    }
