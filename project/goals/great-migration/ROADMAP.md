# Great Migration — Roadmap

**Last reviewed:** 2026-11-06  
**Status:** Feature work paused under the repository-wide documentation-only priority. The canonical catalogue migration is published and structurally verified; controlled enrichment/provenance follow-through remains queued.

## Repository-wide priority override — 2026-11-06

**This workstream is paused for feature implementation while SHIT's documentation audit is active.** The only permitted work here until the Maintainability & Documentation roadmap passes its acceptance criteria is documentation correction, evidence reconciliation, and recording known gaps. Do not run enrichment, modify canonical data, change playlists, or begin feature development. This workstream's feature roadmap remains queued; the active next action is the documentation-only handoff in [project/NEXT_WORK.md](../../NEXT_WORK.md). Resume feature work only when that handoff and the maintainability roadmap explicitly say documentation is complete.

## Purpose and success criteria
Maintain one canonical per-recording music Library while preserving source identities, aliases, relationships, provenance, and recoverability. Publish only audited outputs without losing concurrent main-branch changes. Migration must not modify Spotify playlists or invent provider metadata.

## Verified baseline
- Canonical catalogue published on main: 13,005 songs, 6,386 artists, 7,861 albums (historical verified baseline; refresh before quoting as current).
- Legacy identity coverage: 11,130/11,130 source track IDs and 5,358/5,358 legacy artist names represented.
- Read-only health and confidence CI passed with zero health errors/warnings in the documented full-catalogue audit.
- Run #21 generated output but failed publication after stale issue-event checkout; that output was not published. Workflow fix checks out latest main.
- Historical enrichment report: ~91.1% duration coverage, 1,778 track profiles, 3,998 artist profiles, 400 album profiles, 115 audio profiles, zero lyric features. These are not fresh counts.

## Roadmap
1. **Preserve migration safety — verified/maintain.** Keep serialized writers, latest-main checkout, durable checkpoints, backup/recovery, no force-push, and post-publish audit.
2. **Reconcile outstanding publication/recovery artifacts — verify current relevance.** Inspect unresolved historical run/PR artifacts before retrying any work; never assume artifact data is published.
3. **Measure current canonical state — next.** Run current status, health, confidence, alias/source coverage, and enrichment coverage against main.
4. **Continue bounded enrichment only through canonical writers.** Check provider health, credentials, cooldowns, request budgets, and checkpoints first. Do not run blind retry batches.
5. **Verify every publication.** Compare artifact and published main, run health/confidence checks, record exact counts and workflow/commit links.

## Acceptance criteria
- No canonical identity/alias loss; all source coverage gaps explained.
- No concurrent generated-data writers or stale-base publication.
- Backups/checkpoints support recovery.
- Post-publish health, confidence, and source coverage pass.
- No Spotify playlist side effects.

## Next action (documentation-only priority)

Continue the documentation audit for this workstream: verify this roadmap, README, ACTIONS, linked technical guides, source overviews, tests, workflow references and evidence claims against the current repository. Record any newly discovered contradictions or stale paths here and in the central handoff. **Do not run provider checks/enrichment, alter generated data, modify playlists, or implement features while the documentation-only priority is active.**

## Next feature action after documentation pause

Inspect the latest main-branch status and current provider checkpoints; establish a fresh measured baseline before choosing any enrichment batch.
## Related records
[README](README.md) · [ACTIONS](ACTIONS.md) · [Central handoff](../../NEXT_WORK.md) · [Loose ends](../../LOOSE_ENDS.md)
