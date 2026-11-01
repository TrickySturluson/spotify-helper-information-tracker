# Implementation layout

The maintained implementation lives under this directory, grouped by responsibility:

- `analytics/`: historical archive builders, listening-time aggregates, and project integrity audit.
- `music/`: audio analysis, music metadata enrichment, lyric metadata, and mood inference.
- `spotify/`: playlist intelligence, discovery, sequencing, management, playback tracking, and reference-library tooling.
- `lastfm/`: canonical Last.fm scrobble importer.

## Compatibility entry points

Legacy command-line entry points and import shims live in the repository's `compat/` directory. They preserve existing module names and command behavior while delegating to the organized implementation. A small root-level `sitecustomize.py` adds that directory to Python's import path for existing test and module imports.

Run command-line tools with `python compat/TOOL_NAME.py`. New implementation code belongs under the appropriate package in `scripts/`; do not duplicate logic in `compat/`.
