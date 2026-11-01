# Great Migration

## Goal

Safely migrate existing metadata into the canonical Music Library, preserve entity relationships and provenance, publish without losing concurrent changes, and verify integrity.

## Scope, decisions and constraints

Scope: prepare/dry-run; backup/checkpoint; offline import; identities, relationships, aliases, indexes and manifests; artifact recovery; publication and post-publish audit. Migration itself must not modify Spotify playlists or invent missing provider metadata.

**Status: RECOVERY READY / rerun required.** Run #17 completed migration, bounded enrichment, and a final integrity audit on the runner (13,005 songs; 6,382 artists; 7,861 albums; zero audit errors), but publication failed because the workflow refreshed and staged Spotify playlist snapshots alongside the Library. The uploaded artifact contains the rollback backup and run log, not the completed generated Library. A workflow fix is now on `main`: prepare skips Spotify snapshot refresh, publishes only `assistant_data/music/`, and retains generated music data plus backup in the artifact. The migration is not complete until a new run publishes and a fresh audit passes on `main`.

Run #17: https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41357689889

**Resume:** run `[SHIT LIBRARY] prepare` using the fixed workflow; inspect the new run's steps and artifact; confirm the generated Library and enrichment checkpoints publish to `main`; run `[SHIT LIBRARY] audit` and `status` against the published branch. Never force-push or blindly resolve conflicts.

Commands: `python shit.py library status`, `preview`, `migrate`, `audit`.

## Documentation and resume

Read [ACTIONS.md](ACTIONS.md) for dated work and evidence. After each meaningful action, update it with files changed, execution, exact verification and outcome. Update [the central handoff](../../NEXT_WORK.md) when priority or blockers change.
