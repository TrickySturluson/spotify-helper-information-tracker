# Canonical Library Enrichment

## Goal

Maximize useful, trustworthy metadata in the canonical music Library through repeatable, bounded enrichment passes with field-level provenance and confidence.

## Scope, decisions and constraints

Scope: recording identity/MBIDs; duration; audio/acoustic features; track-level mood/theme/tags; album tracklists/descriptions; artist profiles/genres; caching and reconciliation.

Invariants: recording, artist and album entities remain distinct; track mood is recording-level and must not be blindly inherited from artist identity; unknown remains unknown; preserve source, timestamp, confidence and evidence; use provider budgets/cooldowns and cache successes; Last.fm plays prioritize work but do not prove metadata.

**Status: planned / ongoing; current post-migration coverage has not been freshly measured.** Depends on migration recovery and a read-only coverage report.

**Resume:** audit canonical Library; measure missing fields; resolve trusted recording IDs; enrich high-value fields in bounded passes; reconcile through canonical writer; audit and measure each pass.

## Documentation and resume

Read [ACTIONS.md](ACTIONS.md) for dated work and evidence. After each meaningful action, update it with files changed, execution, exact verification and outcome. Update [the central handoff](../../NEXT_WORK.md) when priority or blockers change.
