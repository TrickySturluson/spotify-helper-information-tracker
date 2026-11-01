# Generated assistant data — file overview

This directory contains derived, reproducible outputs built from the canonical Last.fm archive, measured Spotify playback records, metadata providers, and Spotify playlist snapshots. These files are data products, not source code; do not add comments or prose inside the JSON files.

## File families

- `manifest.json`, `overview.json`, `listening_patterns.json`, `listening_time.json`: top-level summaries, provenance, generation timestamps, and pointers to derived datasets.
- `months/YYYY-MM.json`, `years/YYYY.json`: time-bucketed scrobble aggregates.
- `rankings/`: artist, album, and track rankings derived from the Last.fm archive.
- `advanced/`: deeper discovery, artist lifecycle, rediscovery, monthly diversity, rolling rankings, and session outputs.
- `indexes/`: lookup-oriented indexes for artists and other archive entities.
- `music/`: artist and track metadata, duration totals, metadata shards, recording identifiers, acoustic profiles, and enrichment state. See `docs/AUTOMATED_AUDIO_METADATA.md` and `docs/GETSONGBPM.md`.
- `recommendations/`: derived artist/track features, lyric-theme exports, duration trends, and playlist scoring inputs. See `docs/LYRICS_LIBRARY.md`.
- `playback/`: summaries built from measured Spotify playback records. These are distinct from Last.fm scrobbles; an empty or sparse playback export does not mean the Last.fm archive is empty.
- `spotify/`: Spotify playlist snapshots, managed-playlist metadata, reference-library indexes, playlist-specific presets, health/state summaries, and historical snapshots. Playlist snapshots are generated from Spotify API observations and should not be mistaken for Last.fm listening history.

## Regeneration and maintenance

Use the corresponding maintained modules under `scripts/analytics/`, `scripts/music/`, and `scripts/spotify/`; legacy commands remain available through `compat/`. Each implementation file has a bottom-of-file overview. Check the relevant workflow under `.github/workflows/` for scheduled automation.

Generated outputs may be refreshed or replaced by automation. Do not hand-edit them unless the specific format is explicitly designed for manual curation (for example, a playlist section preset). Preserve source attribution, timestamps, and schema conventions when changing generators.
