# Great Migration

## Goal

Safely migrate existing metadata into the canonical Music Library, preserve entity relationships and provenance, publish without losing concurrent changes, and verify integrity.

## Scope, decisions and constraints

Scope: prepare/dry-run; backup/checkpoint; offline import; identities, relationships, aliases, indexes and manifests; artifact recovery; publication and post-publish audit. Migration itself must not modify Spotify playlists or invent missing provider metadata.

**Status: BLOCKED / publication unverified.** Great Migration run #17 failed during Git rebase/publication with generated Library/index conflicts. Artifact and backup have not yet been inspected. Do not assume earlier stages or final audit passed.

Run #17: https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41357689889

**Resume:** inspect run logs, artifact and backup; identify last successful stage; compare artifact and backup with current `main`; preserve newer valid records; repair publisher/concurrency; run a fresh integrity audit; publish only after verification. Never force-push or blindly resolve conflicts.

Commands: `python shit.py library status`, `preview`, `migrate`, `audit`.

## Documentation and resume

Read [ACTIONS.md](ACTIONS.md) for dated work and evidence. After each meaningful action, update it with files changed, execution, exact verification and outcome. Update [the central handoff](../../NEXT_WORK.md) when priority or blockers change.
