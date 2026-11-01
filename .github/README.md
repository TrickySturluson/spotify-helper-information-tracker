# Spotify Helper & Information Tracker (SHIT)

This directory contains the repository's GitHub Actions workflows and the small state/audit artifacts used by automation.

## Workflows

The `workflows/` directory contains scheduled, manually dispatched, and event-triggered automation. Each workflow has its own bottom-of-file overview describing its job, triggers, and operational requirements. Workflow implementations should call maintained code under `scripts/` or legacy launchers under `compat/`; do not duplicate business logic in YAML.

## Automation state

- `spotify_playlist_manager_state.json`: persisted state used by the playlist manager workflow to coordinate safe operations across runs.
- `spotify_playlist_manager_audit.jsonl`: append-oriented audit history for playlist-manager actions and decisions.

These are machine-readable state/audit records. Do not insert comments or hand-edit them casually; use the workflow or manager tooling that owns the state. Review the relevant Spotify playlist manager implementation and workflow before changing their schema.
