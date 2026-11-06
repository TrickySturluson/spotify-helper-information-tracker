# Metadata Freshness & Partial Revalidation — Roadmap

**Last reviewed:** 2026-11-06  
**Status:** Read-only field-level planner and unknown-age baseline rotation are merged. Exact legacy duration provenance recovery was applied in issues #107 and #114; the post-backfill planner measurement remains outstanding. Provider-backed execution is still separate and feature work is paused under the documentation-only priority.

## Repository-wide priority override — 2026-11-06

**This workstream is paused for feature implementation while SHIT's documentation audit is active.** The only permitted work here until the Maintainability & Documentation roadmap passes its acceptance criteria is documentation correction, evidence reconciliation, and recording known gaps. Do not run enrichment, modify canonical data, change playlists, or begin feature development. This workstream's feature roadmap remains queued; the active next action is the documentation-only handoff in [project/NEXT_WORK.md](../../NEXT_WORK.md). Resume feature work only when that handoff and the maintainability roadmap explicitly say documentation is complete.

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

## Next action
After documentation completion, run a fresh read-only planner preview and record the post-#114 unknown-age baseline; verify the prior #115–#118 audit evidence before considering any provider-backed executor.

## Related records
[README](README.md) · [ACTIONS](ACTIONS.md) · [Coverage retries](../metadata-coverage-retries/ROADMAP.md)
