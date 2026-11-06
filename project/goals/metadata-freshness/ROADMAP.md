# Metadata Freshness & Partial Revalidation — Roadmap

**Last reviewed:** 2026-11-05  
**Status:** Read-only field-level planner and unknown-age baseline rotation are merged; provenance recovery and any provider-backed executor remain separate work.

## Purpose
Refresh only stale or weak metadata fields using deterministic, bounded, provider-aware passes instead of repeatedly scanning/refetching everything.

## Invariants
Freshness is per field and source. One updated field must not make other fields fresh. Planner is deterministic, read-only and network-free. Failed refreshes preserve prior evidence. Distinguish stale, missing, unknown age, transient failure, not found, ambiguous, rate-limited and credential-blocked. Respect provider budgets/cooldowns and advance deterministic coverage fairly.

## Roadmap
1. **Recover duration provenance — next.** Verify the existing exact legacy observation backfill and outstanding apply/audit status; do not infer timestamps.
2. **Refresh current planner baseline.** Run read-only full-catalogue plan and report counts, due reasons, unknown-age and cooldown skips.
3. **Improve field-level provenance.** Audit missing timestamps and provider/source mismatches; append exact recoverable evidence only.
4. **Fair partial rotation.** Verify deterministic cursor/checkpoint behavior and no starvation of long-tail records.
5. **Provider-backed executor (gated).** Design only after provider budgets, credential health, retry semantics, and stop/resume behavior are proven.
6. **Regression tests.** Cover deterministic planning, stale-vs-fresh selection, transient failure preservation, cooldowns, and zero network calls in planner.

## Acceptance criteria
Planner repeatability; no provider calls in planning; no fresh-field refetch; failed lookups do not overwrite valid evidence; every selection/skip is explainable; request caps/cooldowns are enforced.

## Next action (documentation-only priority)

Continue the documentation audit for this workstream: verify this roadmap, README, ACTIONS, linked technical guides, source overviews, tests, workflow references and evidence claims against the current repository. Record any newly discovered contradictions or stale paths here and in the central handoff. **Do not run provider checks/enrichment, alter generated data, modify playlists, or implement features while the documentation-only priority is active.**

## Next feature action after documentation pause
Inspect issues #103–#106 and current main to determine whether exact duration provenance recovery has been applied and audited; then run a fresh planner preview.

## Related records
[README](README.md) · [ACTIONS](ACTIONS.md) · [Coverage retries](../metadata-coverage-retries/ROADMAP.md)
