# Automated acoustic metadata enrichment

SHIT combines acoustic measurements and catalog context, but keeps those evidence classes separate. AcousticBrainz is queried in batches using verified MusicBrainz recording MBIDs; local Essentia analysis is the strongest independent acoustic source when legally obtained audio is available. MusicBrainz, Last.fm, Discogs, lyrics, and GetSongBPM add identity or descriptive context rather than pretending to be acoustic measurements.

The AcousticBrainz service stopped accepting new submissions in 2022. Its remaining records are historical crowdsourced measurements, not a current continuously updated source. SHIT aggregates all returned submissions by median and retains tempo spread/count so disagreement is visible instead of silently selecting the first submission.

## Run

```bash
python compat/enrich_acousticbrainz.py
```

The API accepts up to 25 recording MBIDs per request. The script reads verified IDs from the 32 artist shards, batches requests, checkpoints each batch to `assistant_data/music/audio_profiles.json`, and stores negative lookup results in `assistant_data/music/acousticbrainz_lookup_state.json`. Missing recordings are not queried on every run; the default negative-cache interval is 180 days. Existing one-submission cache entries are eligible for one refresh so all returned submissions can be aggregated. A server reset longer than 15 seconds causes a clean checkpoint-and-stop rather than an early retry. Set `ACOUSTICBRAINZ_MAX_BATCHES` to cap a run.

## Recent-listening priority

The scheduled and manual refresh pipeline builds a deterministic rolling 90-day
Last.fm ranking at `assistant_data/music/recent_top_tracks.json`. It retains
the top 200 unique tracks by recent scrobble count, with all-time plays and
artist/title as deterministic tie-breakers.

That cohort is prioritized across:
- Last.fm track-tag lookups and MusicBrainz recording-tag lookups
- Last.fm duration metadata lookups
- Exact MusicBrainz recording-ID resolution
- AcousticBrainz batch selection, when a verified recording MBID is available

The MusicBrainz resolver accepts only a unique exact artist + recording-title
match. The track-profile builder reuses a shard-resolved recording ID only when
the normalized artist/title maps to exactly one MBID. Ambiguous matches remain
unresolved rather than being guessed. Each enrichment stage checkpoints its
results, so later scheduled runs continue from the remaining due work.

The manual **Update Last.fm History** workflow also performs a read-only Spotify
reference-library sync before refreshing Last.fm history, then runs the recent
top-200 enrichment stages and rebuilds derived analytics. It never edits
Spotify playlists.

## Coverage and limitations

AcousticBrainz stopped accepting new submissions in 2022, but its historical
data archive remains public and CC0. Coverage will vary by track and release.
This source supplies BPM, beat/rhythm descriptors, average loudness, dynamic
complexity and replay gain. Its average_loudness value is **not LUFS**, and the
bulk endpoint does not provide a full within-track loudness envelope.

For tracks without a MusicBrainz recording ID, the next stage is automated
MusicBrainz matching (using artist/title and ISRC when available), followed by
another AcousticBrainz batch pass. Do not infer a recording match from title
alone. GetSongBPM is an optional, separately attributed BPM/key catalog fallback; it is not an acoustic measurement. It uses exact artist/title matching, rejects ambiguity, and caches misses.

Discogs is now an optional release-context source. Configure the GitHub Actions secret `DISCOGS_USER_TOKEN` (or the same environment variable locally) and run:

```bash
python compat/enrich_discogs.py
```

The Discogs resolver searches by exact artist and track, requires one unique master/release, fetches its tracklist, and verifies exactly one exact track-title match and exact artist credit before storing release genres/styles. Since those styles describe the release rather than the individual recording, they are a low-weight semantic cue only. Ambiguous release candidates and identity mismatches are cached and never guessed. Requests are spaced by at least 1.05 seconds; misses are cached for 180 days by default.

The top-200 cohort is based on Last.fm scrobbles in the rolling 90-day window,
not Spotify's opaque popularity score. A track can remain in the cohort even
when an external metadata source has no entry; missing measurements stay
missing and are reported as coverage gaps.

Detailed intros, builds, drops and loudness changes still require actual audio
analysis (Essentia) or a source that publishes segment-level data. Spotify
stream audio is not downloaded or extracted by this pipeline.


## Evidence confidence and redundancy

The sequencer reports acoustic and semantic confidence independently:

- **Acoustic confidence** is based only on direct acoustic/feature evidence. Semantic tag counts cannot raise it. Legacy rows that contain only a generic `confidence=medium` are no longer trusted as measured energy.
- **Semantic confidence** describes descriptive metadata coverage. It can help explain mood/style continuity, but it is not a substitute for sound measurements.
- **Tempo provenance** is retained per provider. The preview reports which sources contributed BPM and whether independent estimates agree after allowing half/double-time equivalence.
- **Disagreement is evidence.** A spread between AcousticBrainz submissions or between Essentia, AcousticBrainz, Spotify-provided tempo, and GetSongBPM is retained and surfaced; it is not hidden by overwriting one source with another.
- **Source dependence matters.** MusicBrainz tags, Last.fm tags, Discogs release styles, and lyric themes are descriptive and may be correlated. Several similar tags do not count as several acoustic confirmations.

For an evidence-focused preview, run the sorter as usual and read the separate acoustic/semantic confidence counts and tempo-source agreement summary. The playlist manager remains the only route to applying a reorder; all changes remain previewed, locked by default, and confirmation-gated.
