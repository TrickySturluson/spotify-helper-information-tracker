# Five-axis playlist-fit preview runner

## Purpose

`scripts/spotify/playlist_fit_preview.py` connects the read-only scorer to the canonical song Library, the exact-ID track-profile cache, and the five registered reference playlist snapshots. It produces a separate preview artifact; it does not connect to Spotify, alter snapshots, read human ratings, or write playlists.

## Run

Create an identity-only JSON file containing a list of candidate tracks or an object with a `tracks` list. Each row needs a Spotify track URI, Spotify track URL, or 22-character Spotify track ID. Include exact title, primary artist, album and duration when available; the corroborated fallback uses all four fields:

```json
{
  "tracks": [
    {"uri": "spotify:track:0123456789012345678901", "title": "Track", "artist": "Artist", "album": "Album", "duration_ms": 180000}
  ]
}
```

The current identity-only 24-track held-out batch is stored at `assistant_data/spotify/playlist_fit_heldout_candidates_20261102.json`. It excludes the unplayable Dog — Floating Room item and contains no human scores or model outputs.

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
- Candidate identity fields only are extracted: Spotify URI/ID, title, artist, album, duration and ISRC. Extra fields (including any scores or confidence values) are ignored.
- The entire candidate batch is excluded from every target profile, not just one candidate at a time. Exclusion also follows a candidate's resolved canonical source-record ID so a Spotify-only record and its exact corroborated Last.fm source record cannot leak into the same profile.
- Canonical song records are resolved by exact Spotify track ID first. Legacy track-profile rows are joined to canonical records through the Library's exact source-track/recording-MBID/Spotify-ID alias maps. If the Spotify record has no fit evidence, a fallback may use an exact canonical artist + title + album bucket only when exactly one alternative source record has a duration within 2,000 ms of the Spotify snapshot duration. This fallback is marked medium identity confidence and is never a fuzzy or artist/title-only match.
- Missing Library records or dimensions remain unknown. No fabricated zeros, genre-to-sound inference, tempo-to-energy inference, or artist/album mood promotion.
- AcousticBrainz `average_loudness` and `dynamic_complexity` are not converted into perceived energy or sound labels. Those fields require a separately validated mapping before use.
- Human slider data is not an input. The runner does not import the human-rating or comparison files.
- No Spotify API calls or playlist writes are performed.

## Output

The JSON contains target snapshot provenance, profile size and confidence, per-dimension coverage, candidate-to-target fit scores, independent confidence tiers, explanations, and explicit safety flags. Fit scores are compatibility estimates, not probabilities. The output is marked `read_only_preview_not_for_sorting` and must not be treated as an enabled production recommender.

## Current limitation

The Library's track-profile cache is the only legacy cache currently joined. Sound, energy, mood and theme remain unknown unless the canonical song record itself contains correctly scoped evidence. The legacy AcousticBrainz cache currently exposes low-level loudness/complexity values but not a validated playlist-energy or sound descriptor; BPM is not a substitute. The next enrichment work should add validated recording-level evidence before broadening the adapter.
