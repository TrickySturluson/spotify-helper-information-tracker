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

Detailed intros, builds, drops and loudness changes still require actual audio
analysis (Essentia) or a source that publishes segment-level data. Spotify
stream audio is not downloaded or extracted by this pipeline.
