# Implementation layout

The maintained implementation lives under this directory, grouped by responsibility:

- `analytics/`: historical archive builders, listening-time aggregates, and project integrity audit.
- `music/`: audio analysis, multi-source music metadata enrichment (AcousticBrainz, MusicBrainz/ISRC, Last.fm, Discogs, GetSongBPM), lyric metadata, and mood inference.
- `spotify/`: playlist intelligence, discovery, sequencing, management, playback tracking, and reference-library tooling.
- `lastfm/`: canonical Last.fm scrobble importer.

## Compatibility entry points

Legacy command-line entry points and import shims live in the repository's `compat/` directory. They preserve existing module names and command behavior while delegating to the organized implementation. A small root-level `sitecustomize.py` adds that directory to Python's import path when the repository is on the startup path; the `tests` package also bootstraps it explicitly for unittest discovery.

Run a tool with `python compat/TOOL_NAME.py`. Run the full test suite from the repository root with:

```bash
python -m unittest discover -s tests -t . -v
```

New implementation code belongs under the appropriate package in `scripts/`; do not duplicate logic in `compat/`.


## File overview
This guide explains the maintained implementation package layout, the responsibility of each package, and how compatibility entry points preserve older commands. It is the starting point for navigating scripts/; individual implementation files carry their own file-level overview at the bottom.
