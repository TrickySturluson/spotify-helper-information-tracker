# Track mood evidence and coverage

This document defines how SHIT gathers, stores, and interprets mood-related metadata. The central rule is that **evidence scope is not interchangeable**: a recording tag, album tag, artist tag, lyric theme, and audio-model prediction describe different things.

## Evidence hierarchy

| Evidence | Scope | Current use | Confidence treatment |
|---|---|---|---|
| Last.fm `track.getTopTags` | Recording / track | Track mood descriptors | Track-level evidence; popularity counts do not equal independent confirmations |
| MusicBrainz recording tags | Recording / track | Track mood descriptors | Independent track-tag source family when recording MBID is verified |
| Last.fm `album.getTopTags` | Album / release | Context when track tags are absent | Low-confidence album context; never increases track mood confidence |
| Discogs styles / genres | Release | Style and genre context | Release context only; not track mood or acoustics |
| Last.fm artist tags | Artist | Fallback context | Low-confidence artist context; never promoted to track mood evidence |
| Lyrics analysis | Lyric text | Narrative / subject themes | Separate lyrical evidence; not evidence of how the recording sounds |
| AcousticBrainz / Essentia / GetSongBPM | Recording audio or catalog | Tempo, dynamics, loudness and other audio features | Acoustic confidence is independent from semantic mood confidence |
| Essentia DEAM valence/arousal model | Local audio | Continuous valence and arousal regression estimates | Optional local analysis only; uncalibrated for this library, excluded from sorter confidence pending validation and license review |
| Essentia MTG-Jamendo mood/theme model | Local audio | Potential 56-label mood/theme predictions | Not integrated; requires local audio, optional TensorFlow support, model-license review and calibration |

## Stored data and provenance

- `assistant_data/music/track_profiles.json`: track-level Last.fm and verified MusicBrainz recording tags. Each provider has a separate status and checked timestamp.
- `assistant_data/music/album_profiles.json`: exact Last.fm artist + album lookups. Each row stores the raw tag labels/counts, `source`, `identity_verified`, `status`, `checked_at`, `retry_after`, recent/all-time play priority, and unique track count.
- `assistant_data/music/album_profile_state.json`: provider-wide cooldown and last-run state. A cooldown prevents additional requests until the provider's retry time.
- `assistant_data/music/artist_profiles.json`: Last.fm artist tags, separated into genres, moods and themes.
- `assistant_data/music/audio_profiles.json`: acoustic provider records, with provenance kept separate.
- `assistant_data/recommendations/lyric_features.json`: compact derived lyric themes; full lyric text is not exported.

The album enrichment pipeline deduplicates by normalized artist + album, prioritizes configured playlist snapshots and recent scrobbles, caps each run at 100 unique albums, sends requests sequentially with a 0.4-second minimum delay, verifies the response artist and album exactly, caches empty results for 30 days, checkpoints after each album, and stops on provider cooldowns. It does not call Spotify or modify playlists.

## Normalized per-recording storage

The Library dataset lives under `assistant_data/music/library/`.
Each artist, album, and recording has its own JSON record; `library_index.json`
contains only stable-ID paths and lookup aliases. Recording files preserve raw
track-provider observations, audio observations, lyric features, derived data,
coverage, source statuses, and explicit artist/album relations. Artist and album
evidence remains contextual rather than being copied into track-level evidence.

The migration reads existing aggregate JSON locally and makes no network calls.
It does not delete or rewrite the aggregates. See
[PER_RECORDING_MUSIC_LIBRARY.md](PER_RECORDING_MUSIC_LIBRARY.md) for identity
precedence, fallback identity caveats, layout, and lookup behavior.

## Mood confidence rules

The sorter reports track mood confidence separately from acoustic and general semantic confidence.

- **High**: at least two independent track-tag source families, at least two distinct mood descriptors, and no opposing affect-direction conflict.
- **Medium**: at least two distinct track mood descriptors, or corroboration across two track-tag sources, without an opposing-direction conflict.
- **Low**: one track mood descriptor, conflicting affect directions, or album/artist fallback context.
- **Unknown**: no usable track, album or artist mood descriptor.

Album and artist fallback labels remain low confidence and have an explicit `mood_evidence_scope` (`album` or `artist`). They never increase `mood_tag_count` or the confidence of track-specific tags. Raw community tag counts do not increase confidence. A conflict between energetic and gentle affect directions is retained and neutralized in the perceived-energy blend.

Mood contribution to perceived energy is confidence-scaled: track-level high 0.15, medium 0.10, low 0.05; album context 0.04; artist context 0.03. These are blend weights, not probabilities. Mood continuity in sequencing is separately confidence-weighted. Only medium/high track-level mood evidence can count as mood support in a transition-confidence assessment.

## Coverage reporting

The sequencer's preview reports:

- Track mood confidence counts (high / medium / low / unknown).
- Track mood source-family coverage (for example `lastfm_track`, `musicbrainz_recording`, `lastfm_album`, `lastfm_artist`).
- Acoustic confidence and source coverage separately.
- Tempo provider agreement and disagreement separately.

The saved-playlist integration test also reports track-tag and album-tag coverage for **Booze or Boos!**. An empty provider response is a measured coverage gap, not negative evidence and not a reason to invent a mood label.

## Future audio-model path

The first optional implementation is Essentia's DEAM valence/arousal regression model. Its published metadata reports a 1–9 scale, trained on 1,802 songs, with valence CCC 0.778 / Pearson 0.738 and arousal CCC 0.647 / Pearson 0.773. The local-only script stores mean and variability across model frames, audio/model hashes and model version, but deliberately does not feed the sorter yet. It requires legally obtained local audio and Essentia TensorFlow support.

Essentia also publishes a 56-label MTG-Jamendo mood/theme classifier. Its metadata reports test ROC-AUC 0.76 and PR-AUC 0.14, so raw scores must not be treated as calibrated probabilities. Essentia's documentation identifies non-commercial model licensing; the model catalogue and general licensing page differ on the exact Creative Commons suffix. Before wider use, confirm the applicable license, retain model/version provenance, and calibrate against a human-reviewed sample. These predictions must remain a separate audio-model evidence family until validation demonstrates how much weight they deserve. See [AUDIO_MOOD_MODELS.md](AUDIO_MOOD_MODELS.md).

## References

- Last.fm album top tags: https://www.last.fm/api/show/album.getTopTags
- MusicBrainz API and rate limiting: https://musicbrainz.org/doc/MusicBrainz_API
- MTG-Jamendo dataset: https://github.com/MTG/mtg-jamendo-dataset
- Essentia pretrained models: https://essentia.upf.edu/models.html
- DEAM model metadata: https://essentia.upf.edu/models/classification-heads/deam/deam-msd-musicnn-2.json
- Essentia model licensing: https://essentia.upf.edu/licensing_information.html
- DEAM valence/arousal dataset: https://cvml.unige.ch/databases/DEAM/

