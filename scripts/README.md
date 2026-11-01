# Implementation layout

The implementation lives under this directory, grouped by responsibility:

- `analytics/`: historical archive builders, listening-time aggregates, and project integrity audit.
- `music/`: audio analysis, music metadata enrichment, lyric metadata, and mood inference.
- `spotify/`: playlist intelligence, discovery, sequencing, management, playback tracking, and reference-library tooling.
- `lastfm/`: canonical Last.fm scrobble importer.

## Compatibility

The small Python files at the repository root are intentional compatibility entry points. They preserve existing commands (for example, `python spotify_playlist_manager.py`), imports used by tests and sibling modules, and GitHub Actions workflow paths while delegating execution to the organized implementation. This avoids a risky all-at-once rewrite of imports and automation.

New code should be added to the appropriate package under `scripts/`. Keep root wrappers stable until a later migration can update tests, imports, and workflows together.
