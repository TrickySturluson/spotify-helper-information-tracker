# Discovery & Recommendations — Roadmap

**Last reviewed:** 2026-11-05  
**Status:** Proposed; PR #60 and its current implementation/test status require inspection.

## Repository-wide priority override — 2026-11-06

**This workstream is paused for feature implementation while SHIT's documentation audit is active.** The only permitted work here until the Maintainability & Documentation roadmap passes its acceptance criteria is documentation correction, evidence reconciliation, and recording known gaps. Do not run enrichment, modify canonical data, change playlists, or begin feature development. This workstream's feature roadmap remains queued; the active next action is the documentation-only handoff in [project/NEXT_WORK.md](../../NEXT_WORK.md). Resume feature work only when that handoff and the maintainability roadmap explicitly say documentation is complete.

## Purpose
Capture suggested/recommended/discovered tracks as evidence-rich candidate events that can be enriched and retrieved without polluting listening history or falsely claiming user preference.

## Invariants
Recommendation exposure is not a play. Candidate selection is not preference. Distinguish later play, explicit like/save, explicit rejection/removal, ignored, not exposed, and unknown coverage. Preserve source/provider, context, capture time, candidate identity, and observable response. Last.fm scrobbles remain historical listening evidence.

## Roadmap
1. **Review existing PR and schema — next.** Inspect PR #60, current branch/CI, and any merged code; do not duplicate existing implementation.
2. **Define canonical candidate event.** Stable recording identity, source, recommendation context, timestamp, provenance, and separate response fields.
3. **Capture discovery sources.** Spotify recommendations/Discover Weekly and other explicitly supported sources, each with attribution and source-specific coverage.
4. **Reconcile outcomes.** Join later playback/scrobbles, likes/saves, removals/rejections, and playlist additions without collapsing event types.
5. **Expose queryable discovery history.** Support dedupe, source comparison, candidate lifecycle, and recommendation evaluation.
6. **Integrate carefully.** Use evidence as a bounded recommendation signal; never turn unobserved exposure into negative feedback.

## Acceptance criteria
No duplicate canonical recordings; source and exposure are recoverable; no candidate is counted as listening; unknown is not treated as rejection; response signals remain distinguishable and auditable.

## Next action
Inspect PR #60 and current main/tests, then document the exact implemented boundary and remaining schema/ingestion work.

## Related records
[README](README.md) · [ACTIONS](ACTIONS.md) · [Listening analytics](../listening-analytics/ROADMAP.md)
