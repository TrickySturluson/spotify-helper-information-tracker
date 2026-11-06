# Library Identity & Metadata Confidence Verification — Roadmap

**Last reviewed:** 2026-11-06  
**Status:** Read-only confidence audit is merged and has passed full-catalogue CI; direct evidence coverage and sorter readiness remain incomplete.

## Repository-wide priority override — 2026-11-06

**This workstream is paused for feature implementation while SHIT's documentation audit is active.** The only permitted work here until the Maintainability & Documentation roadmap passes its acceptance criteria is documentation correction, evidence reconciliation, and recording known gaps. Do not run enrichment, modify canonical data, change playlists, or begin feature development. This workstream's feature roadmap remains queued; the active next action is the documentation-only handoff in [project/NEXT_WORK.md](../../NEXT_WORK.md). Resume feature work only when that handoff and the maintainability roadmap explicitly say documentation is complete.

## Purpose
Prove canonical records resolve to the correct recordings and that confidence reflects actual field-level evidence. Prevent weak identity/context from masquerading as strong recording metadata.

## Invariants
Confidence categories are categorical, not calibrated probabilities. Distinct source families—not repeated observations from one provider—are needed for corroboration. Artist/album context cannot upgrade recording identity, mood, theme, sound or energy confidence. Ambiguity remains explicit.

## Roadmap
1. **Refresh full-catalogue audit — next.** Recompute identity and metadata confidence on current main; report drift and unknown coverage.
2. **Recover missing provenance.** Resolve exact legacy duration timestamps where evidence matches; never infer missing observation time.
3. **Build curated gold set.** Include stable-ID matches, ambiguous same-title recordings, remasters/live versions, missing IDs, conflicts and false-match traps.
4. **Expand field evidence.** Improve direct recording-level Genre, Sound, Energy, Mood and Theme evidence with provenance.
5. **Gate downstream consumers.** Ensure sorter/fit model uses field-specific confidence and explains excluded/uncertain tracks.
6. **Regression and audit.** Test false positives, alias uniqueness, confidence preservation, source-family independence, and drift reporting.

## Acceptance criteria
Every confidence value traces to evidence and match method; ambiguous matches never become high; repeated same-provider evidence is not independent; audit is read-only and deterministic; downstream tools respect field-level confidence.

## Next action
After documentation completion, investigate the 214 current track_tags confidence mismatches from CI #42154433350, remeasure the residual 1,968 missing-provenance fields with the freshness planner, and review the existing Candy Claws duplicate artist/album candidates. Do not bulk-rewrite confidence or merge entities from the audit alone.

## Related records
[README](README.md) · [ACTIONS](ACTIONS.md) · [Playlist intelligence](../playlist-intelligence/ROADMAP.md)
