# Five-axis playlist-fit preview runner

## Purpose

`scripts/spotify/playlist_fit_preview.py` connects the read-only scorer to the canonical song Library, the exact-ID track-profile cache, and the five registered reference playlist snapshots. It produces a separate preview artifact; it does not connect to Spotify, alter snapshots, read human ratings, or write playlists.

## Run

Create an identity-only JSON file containing a list of candidate tracks or an object with a `tracks` list. Each row needs a Spotify track URI, Spotify track URL, or 22-character Spotify track ID:

```json
{
  "tracks": [
    {"uri": "spotify:track:0123456789012345678901"}
  ]
}
```

Then run from the repository root:

```bash
python scripts/spotify/playlist_fit_preview.py \
  --candidates path/to/candidate-identities.json \
  --output assistant_data/spotify/playlist_fit_preview.json
```

Optional `--library`, `--music-data`, and `--spotify-data` arguments support alternate local data roots.

## Input and safety rules

- Exactly five playlists with role `sorter_calibration_target` must be registered.
- Every target snapshot must be accessible, have a matching playlist ID, and have reported/fetched counts consistent with its item list. An inaccessible or incomplete target aborts the run; it is never interpreted as an empty playlist.
- Candidate identities are extracted only. Extra fields in the candidate file (including scores) are ignored.
- The entire candidate batch is excluded from every target profile, not just one candidate at a time.
- Canonical song records are resolved by exact Spotify track ID. Track-profile cache rows are joined only by exact source-track ID, recording MBID, or Spotify ID. Artist/title fuzzy matching is prohibited.
- Missing Library records or dimensions remain unknown. No fabricated zeros, genre-to-sound inference, tempo-to-energy inference, or artist/album mood promotion.
- AcousticBrainz `average_loudness` and `dynamic_complexity` are not converted into perceived energy or sound labels. Those fields require a separately validated mapping before use.
- Human slider data is not an input. The runner does not import the human-rating or comparison files.
- No Spotify API calls or playlist writes are performed.

## Output

The JSON contains target snapshot provenance, profile size and confidence, per-dimension coverage, candidate-to-target fit scores, independent confidence tiers, explanations, and explicit safety flags. Fit scores are compatibility estimates, not probabilities. The output is marked `read_only_preview_not_for_sorting` and must not be treated as an enabled production recommender.

## Current limitation

The Library's track-profile cache is the only legacy cache currently joined. Sound, energy, mood and theme remain unknown unless the canonical song record itself contains correctly scoped evidence. The legacy AcousticBrainz cache currently exposes low-level loudness/complexity values but not a validated playlist-energy or sound descriptor; BPM is not a substitute. The next enrichment work should add validated recording-level evidence before broadening the adapter.
