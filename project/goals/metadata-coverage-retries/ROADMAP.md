# Metadata Coverage & Provider Retries — Roadmap

**Last reviewed:** 2026-11-05  
**Status:** Design specification exists; planner/executor implementation and live-schema verification must be confirmed before use.

## Purpose
Turn missing or weak metadata into a deterministic, bounded work queue without confusing provider failures with definitive absence or repeatedly spending request budgets.

## Required semantics
Task identity is recording + provider + data family. Statuses include eligible, retry_wait, not_found, ambiguous, complete, blocked, and invalid. Timeouts, rate limits, network/server/parse/auth errors are not not_found. A failed provider must not block other providers. Planning is read-only and network-free. Successful values merge through canonical writer with provenance.

## Roadmap
1. **Audit current PR/code and real schemas — next.** Verify PR #65 status, merged code (if any), current checkpoints, and actual canonical Library schema.
2. **Deterministic planner.** Generate one explainable task per eligible recording/provider/field family; deduplicate and preserve cooldown/negative-cache state.
3. **Comprehensive tests.** Cover transient errors, definitive negatives, malformed records, ambiguous identities, duplicate tasks, cooldowns, provider isolation, and zero network/write side effects in planning.
4. **Generated retry queue.** Build the queue from canonical records and provider state; queue is a worklist, never source of truth.
5. **Bounded executor.** Only after planner validation; enforce per-provider request budgets, Retry-After, backoff, credentials, cache, checkpoint and clean stop.
6. **Canonical merge and audit.** Preserve previous evidence, append provenance, run health/confidence/freshness checks.

## Acceptance criteria
Repeated plans with unchanged inputs are deterministic; no ineligible request is issued; provider failure never becomes not_found; no successful value bypasses canonical writer; all network/write budgets are tested.

## Next action (documentation-only priority)

Continue the documentation audit for this workstream: verify this roadmap, README, ACTIONS, linked technical guides, source overviews, tests, workflow references and evidence claims against the current repository. Record any newly discovered contradictions or stale paths here and in the central handoff. **Do not run provider checks/enrichment, alter generated data, modify playlists, or implement features while the documentation-only priority is active.**

## Next feature action after documentation pause
Inspect PR #65 and current main implementation/CI; reconcile this roadmap against actual code before implementing anything.

## Related records
[README](README.md) · [ACTIONS](ACTIONS.md) · [Retry contract](../../RETRY_QUEUE_SPEC.md)
