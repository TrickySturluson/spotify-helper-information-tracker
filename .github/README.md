# Spotify Helper & Information Tracker (SHIT)

## Project overview

**Spotify Helper & Information Tracker (SHIT)** is a personal toolkit for exploring listening history, enriching music data, discovering music, and building and maintaining Spotify playlists. It combines the long-term listening history archived by Last.fm with Spotify playlist references and locally measured playback data, while keeping each source distinct so estimates, sourced metadata, and unknown information are not confused.

The project is built to make music curation explainable and safe. Analytics and recommendations expose the evidence behind them; playlist sequencing evaluates song-to-song transitions; and playlist changes use previews, locks, backups, confirmations, and audit history rather than making unreviewed edits.

## Main features

- **Listening-history archive and analytics** — preserves the chronological Last.fm scrobble archive and builds artist, album, track, daily, monthly, yearly, discovery, and listening-pattern reports.
- **Music metadata enrichment** — gathers track durations and artist/track tags from external sources, tracks provenance and confidence, and leaves unresolved details explicitly unknown.
- **Playback-time tracking** — measures Spotify playback prospectively with a local tracker and keeps measured playback separate from scrobble-based estimates.
- **Music discovery and recommendations** — ranks candidate tracks and artists using listening history, similarity signals, familiarity, recency, and playlist feedback.
- **Playlist intelligence and health checks** — summarizes playlist identity and metadata coverage, detects duplicates and missing items, and reports artist concentration and feedback.
- **Playlist sequencing** — creates previewable arrangements with Smooth Flow transition optimization, configurable energy journeys, anchors, sections, and explanations of uncertain handoffs.
- **Safe playlist management** — supports playlist inspection and approved changes with default locks, ownership and snapshot checks, pre-change backups, explicit confirmation, undo, and audit records.
- **Automated maintenance and validation** — uses GitHub Actions to refresh reference data, enrich metadata, run tests and integrity checks, and observe curation feedback.

## This directory

This directory contains the repository's GitHub Actions workflows and the small state/audit artifacts used by automation.

## Workflows

The `workflows/` directory contains scheduled, manually dispatched, and event-triggered automation. Each workflow has its own bottom-of-file overview describing its job, triggers, and operational requirements. Workflow implementations should call maintained code under `scripts/` or legacy launchers under `compat/`; do not duplicate business logic in YAML.

## Automation state

- `spotify_playlist_manager_state.json`: persisted state used by the playlist manager workflow to coordinate safe operations across runs.
- `spotify_playlist_manager_audit.jsonl`: append-oriented audit history for playlist-manager actions and decisions.

These are machine-readable state/audit records. Do not insert comments or hand-edit them casually; use the workflow or manager tooling that owns the state. Review the relevant Spotify playlist manager implementation and workflow before changing their schema.

## File overview

This guide introduces the project and summarizes its main capabilities, then documents the purpose of the `.github/` directory, its automation workflows, and the state/audit records stored here.
