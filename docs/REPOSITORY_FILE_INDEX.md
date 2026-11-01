# Repository file index

This index explains how to read the repository file-by-file without inserting comments into machine-readable data.

## Human-authored source and configuration

- `README.md`: project entry point, setup, navigation, and primary operating instructions.
- `.gitignore`: excludes credentials, local runtime state, caches, and generated/private artifacts from version control.
- `requirements-audio-analysis.txt`: optional dependencies for the local Essentia audio-analysis path; not required for ordinary metadata enrichment or playlist tooling.
- `sitecustomize.py`: adds `compat/` to the Python startup import path so legacy imports continue to work.
- `scripts/`: maintained implementation, grouped by responsibility. Every Python module ends with a `FILE OVERVIEW` section.
- `compat/`: backward-compatible commands and import shims. Every Python entry point identifies its canonical implementation.
- `tests/`: automated regression checks. Each test module explains its scope and invocation.
- `.github/workflows/`: GitHub Actions automation. Each workflow has a file-level overview.
- `docs/`: feature and operating guides. Each guide is self-describing and links related commands and data contracts.

## Machine-readable data and state

Machine-readable files cannot contain free-form footer text without breaking their formats. Their file-level documentation is therefore maintained beside them in the following guides:

- `data/README.md`: `scrobbles.json`, `metadata.json`, and `stats.json`.
- `assistant_data/README.md`: all generated analytics, music metadata, recommendations, playback summaries, Spotify snapshots, indexes, manifests, and history files. The guide documents each directory/file family and how to regenerate it.
- `playback_data/README.md`: raw measured Spotify playback archive and its currently empty placeholder.
- `.github/README.md`: workflow state and audit JSON/JSONL files.
- `docs/BOOZE_OR_BOOS_SORT.md`: the manually curated playlist section preset under `assistant_data/spotify/`.
- `docs/LYRICS_LIBRARY.md`: local lyrics database and compact derived export.
- `playlist_removed_tracks.json`: playlist-specific user-confirmed removal feedback. It is keyed by Spotify playlist ID and stores artist/title identity, source, and explanatory notes; entries without a Spotify track URI use normalized artist/title matching. It is consumed as recommendation feedback rather than as a source listening-history record.

## Generated-file policy

Do not append comments, Markdown, or footer blocks to JSON, JSONL, CSV, or binary/archive files. Document their schema, provenance, owning generator, and regeneration procedure in an adjacent README or feature guide instead. When a new generated file family is added, update the nearest directory README and this index in the same change.
