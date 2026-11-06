# Discovery & Recommendations
> **Roadmap:** [ROADMAP.md](ROADMAP.md) is the durable plan and next-action reference. Read it before work; update it and [ACTIONS.md](ACTIONS.md) in the same session as implementation, testing, decisions, or blockers.
> **Current repository priority:** This workstream is paused for feature implementation while SHIT's documentation audit is active. Only documentation corrections and evidence reconciliation are permitted. Preserve this roadmap; resume its feature next actions only when the [central handoff](../../NEXT_WORK.md) and Maintainability & Documentation roadmap explicitly say documentation is complete.


## Goal

Capture suggested, recommended and discovered songs in the Library so they can be identified, enriched, deduplicated and retrieved without polluting listening history or overstating preference.

## Scope, decisions and constraints

Store source/provider, context, capture time, candidate identity and observable response (added, saved, played later, explicitly liked, rejected, ignored) where available. Keep recommendations/exposure distinct from Last.fm scrobbles, Spotify playback, explicit likes/saves and confirmed preferences. A recommendation is never a play or preference by itself.

PR #60: https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/60

**Status: partial mainline implementation.** Main includes `scripts/music/discovery_ingestion.py` and `tests/test_discovery_ingestion.py`, which preserve recommendation candidates and their `discovery_evidence` in `assistant_data/recommendations/discovery_candidates.json` without treating them as plays or preferences. PR #60 remains open and proposes an additional canonical song `discovery_context` field plus `scripts/music/record_discovery.py` and a separate test. That PR is not merged; compare its exact diff with main before deciding whether to integrate or close it. Do not assume discovery capture is wholly absent or that PR #60's richer schema is already present.

**Resume after documentation completion:** compare PR #60 with the mainline candidate-ingestion path; decide whether candidate-only storage is sufficient or canonical per-song context is required; preserve separation from scrobbles, playback, likes and confirmed preference; validate idempotency and identity resolution.

## Documentation and resume

Read [ACTIONS.md](ACTIONS.md) for dated work and evidence. After each meaningful action, update it with files changed, execution, exact verification and outcome. Update [the central handoff](../../NEXT_WORK.md) when priority or blockers change.
