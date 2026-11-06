# Library Health Checker & Data Maintainer — Roadmap

**Last reviewed:** 2026-11-06  
**Status:** Read-only health checker and preview-only derived-index maintenance are merged; broader repairs remain restricted/proposed. Feature work is paused under the documentation-only priority.

## Repository-wide priority override — 2026-11-06

**This workstream is paused for feature implementation while SHIT's documentation audit is active.** The only permitted work here until the Maintainability & Documentation roadmap passes its acceptance criteria is documentation correction, evidence reconciliation, and recording known gaps. Do not run enrichment, modify canonical data, change playlists, or begin feature development. This workstream's feature roadmap remains queued; the active next action is the documentation-only handoff in [project/NEXT_WORK.md](../../NEXT_WORK.md). Resume feature work only when that handoff and the maintainability roadmap explicitly say documentation is complete.

## Purpose
Keep the canonical Library structurally sound and recoverable while separating diagnosis from mutation.

## Safety invariants
Health and preview modes are read-only and network-free. Repairs must be deterministic, allow-listed, backed up, atomic, idempotent, journaled, and followed by health checks/rollback. Never guess identities, merge ambiguous recordings, overwrite stronger evidence, invent metadata, or delete conflicting records. No playlist writes.

## Roadmap
1. **Reconfirm latest health baseline — next.** Run full-catalogue health/integrity audit and record fresh counts/results.
2. **Maintain current safe scope.** Verify index-only repair behavior, backup/alias proof, atomic write and rollback.
3. **Expand fixtures.** Test malformed records, orphaned files, duplicate/dangling aliases, invalid relationships, stale indexes, and provenance issues.
4. **Evaluate additional repair classes.** Only propose deterministic repairs with explicit allow-list, backup, preview, apply confirmation and rollback.
5. **Operational monitoring.** Preserve weekly read-only health/confidence/freshness reports and actionable summaries.

## Acceptance criteria
Read-only modes make zero writes/network calls; repairs preserve identity and aliases; every mutation is reversible and audited; post-repair health passes.

## Next action
Inspect latest weekly health and maintainer artifacts, then confirm current index-only repair implementation and regression tests before proposing any new repair scope.

## Related records
[README](README.md) · [ACTIONS](ACTIONS.md) · [Metadata freshness](../metadata-freshness/ROADMAP.md)
