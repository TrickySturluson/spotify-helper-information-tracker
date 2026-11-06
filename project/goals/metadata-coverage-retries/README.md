# Metadata Coverage & Provider Retries
> **Roadmap:** [ROADMAP.md](ROADMAP.md) is the durable plan and next-action reference. Read it before work; update it and [ACTIONS.md](ACTIONS.md) in the same session as implementation, testing, decisions, or blockers.
> **Current repository priority:** This workstream is paused for feature implementation while SHIT's documentation audit is active. Only documentation corrections and evidence reconciliation are permitted. Preserve this roadmap; resume its feature next actions only when the [central handoff](../../NEXT_WORK.md) and Maintainability & Documentation roadmap explicitly say documentation is complete.


## Goal

Identify missing metadata and the provider-specific work needed to fill it, while respecting cooldowns, request budgets, caches and definitive negative results.

## Scope, decisions and constraints

Scope: deterministic read-only coverage planner; provider checkpoints; generated queue at `assistant_data/music/retry_queue.json`; task identity = recording + provider + data family; bounded executor only after planner validation.

Statuses: eligible, retry_wait, not_found, ambiguous, complete, blocked, invalid. Timeout/rate limit/network/server/parse/auth errors are not definitive not-found. A provider failure must not block other providers. Planner must not perform network requests or mutate canonical records. Successful results merge through canonical writer with provenance.

Design contract: [RETRY_QUEUE_SPEC.md](../../RETRY_QUEUE_SPEC.md). PR #65: https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/65

**Status: specification and proposed planner exist; implementation/live-schema verification outstanding.**

**Resume:** inspect PR #65 and CI; validate real Library/checkpoint schemas; implement deterministic planner; test cooldown preservation, negative cache, malformed records, dedupe, no-write/no-network; generate queue; only then implement bounded executor.

## Documentation and resume

Read [ACTIONS.md](ACTIONS.md) for dated work and evidence. After each meaningful action, update it with files changed, execution, exact verification and outcome. Update [the central handoff](../../NEXT_WORK.md) when priority or blockers change.
