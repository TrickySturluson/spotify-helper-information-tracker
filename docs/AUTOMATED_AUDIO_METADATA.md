# Automated acoustic metadata enrichment

SHIT uses the public AcousticBrainz low-level archive/API as its first bulk
acoustic metadata source. It is indexed by MusicBrainz recording MBID, so the
pipeline reuses recording IDs already resolved in the project's 32 artist
metadata shards.

## Run

```bash
python compat/enrich_acousticbrainz.py
```

The API accepts up to 25 recording MBIDs per request. The script reads all
existing shard records, batches IDs, observes rate-limit headers, and
checkpoints after every batch to `assistant_data/music/audio_profiles.json`.
Rerunning resumes by skipping IDs already present. Set
`ACOUSTICBRAINZ_MAX_BATCHES` to cap a run.

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
alone. GetSongBPM is implemented as an optional, separately attributed BPM/key
fallback once an API key is configured; see [GETSONGBPM.md](GETSONGBPM.md). It
uses exact artist/title matching, rejects ambiguity, and caches misses.

The top-200 cohort is based on Last.fm scrobbles in the rolling 90-day window,
not Spotify's opaque popularity score. A track can remain in the cohort even
when an external metadata source has no entry; missing measurements stay
missing and are reported as coverage gaps.

Detailed intros, builds, drops and loudness changes still require actual audio
analysis (Essentia) or a source that publishes segment-level data. Spotify
stream audio is not downloaded or extracted by this pipeline.
