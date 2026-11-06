# Discovery & Recommendations — Roadmap

**Last reviewed:** 2026-11-06  
**Status:** Partial mainline candidate-ingestion implementation exists; richer per-song context remains proposed in open PR #60. Feature work is paused under the documentation-only priority. PR #60 is open/non-draft on `feature/recommendation-discovery-ingestion`, rechecked 2026-11-06 against main `a5fe4de`: diverged (4 ahead, 627 behind; mergeable=false). Its old-head unit tests #41350320527 and full-history security scan #41350320524 both failed; rebase, triage the test failure and Gitleaks findings, then rerun CI before review.

## Repository-wide priority override — 2026-11-06

**This workstream is paused for feature implementation while SHIT's documentation audit is active.** The only permitted work here until the Maintainability & Documentation roadmap passes its acceptance criteria is documentation correction, evidence reconciliation, and recording known gaps. Do not run enrichment, modify canonical data, change playlists, or begin feature development. This workstream's feature roadmap remains queued; the active next action is the documentation-only handoff in [project/NEXT_WORK.md](../../NEXT_WORK.md). Resume feature work only when that handoff and the maintainability roadmap explicitly say documentation is complete.

## Purpose
Capture suggested/recommended/discovered tracks as evidence-rich candidate events that can be enriched and retrieved without polluting listening history or falsely claiming user preference.

## Invariants
Recommendation exposure is not a play. Candidate selection is not preference. Distinguish later play, explicit like/save, explicit rejection/removal, ignored, not exposed, and unknown coverage. Preserve source/provider, context, capture time, candidate identity, and observable response. Last.fm scrobbles remain historical listening evidence.

## Roadmap
1. **Review existing PR and schema — next.** After the documentation pause, rebase the stale/diverged PR #60 branch, triage its failed old-head tests and Gitleaks findings, inspect current branch/CI and merged code; do not duplicate existing implementation.
2. **Define canonical candidate event.** Stable recording identity, source, recommendation context, timestamp, provenance, and separate response fields.
3. **Capture discovery sources.** Spotify recommendations/Discover Weekly and other explicitly supported sources, each with attribution and source-specific coverage.
4. **Reconcile outcomes.** Join later playback/scrobbles, likes/saves, removals/rejections, and playlist additions without collapsing event types.
5. **Expose queryable discovery history.** Support dedupe, source comparison, candidate lifecycle, and recommendation evaluation.
6. **Integrate carefully.** Use evidence as a bounded recommendation signal; never turn unobserved exposure into negative feedback.

## Acceptance criteria
No duplicate canonical recordings; source and exposure are recoverable; no candidate is counted as listening; unknown is not treated as rejection; response signals remain distinguishable and auditable.

## Next action (documentation-only priority)

Continue the documentation audit for this workstream: verify this roadmap, README, ACTIONS, linked technical guides, source overviews, tests, workflow references and evidence claims against the current repository. Record any newly discovered contradictions or stale paths here and in the central handoff. **Do not run provider checks/enrichment, alter generated data, modify playlists, or implement features while the documentation-only priority is active.**

## Next feature action after documentation pause

After documentation completion, compare PR #60's per-song discovery_context proposal with mainline discovery_ingestion.py and its tests; decide whether candidate-only storage is sufficient or canonical per-song context is still needed.
## Related records
[README](README.md) · [ACTIONS](ACTIONS.md) · [Listening analytics](../listening-analytics/ROADMAP.md)
