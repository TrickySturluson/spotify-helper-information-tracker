# Discovery & Recommendations
> **Roadmap:** [ROADMAP.md](ROADMAP.md) is the durable plan and next-action reference. Read it before work; update it and [ACTIONS.md](ACTIONS.md) in the same session as implementation, testing, decisions, or blockers.
> **Current repository priority:** This workstream is paused for feature implementation while SHIT's documentation audit is active. Only documentation corrections and evidence reconciliation are permitted. Preserve this roadmap; resume its feature next actions only when the [central handoff](../../NEXT_WORK.md) and Maintainability & Documentation roadmap explicitly say documentation is complete.


## Goal

Capture suggested, recommended and discovered songs in the Library so they can be identified, enriched, deduplicated and retrieved without polluting listening history or overstating preference.

## Scope, decisions and constraints

Store source/provider, context, capture time, candidate identity and observable response (added, saved, played later, explicitly liked, rejected, ignored) where available. Keep recommendations/exposure distinct from Last.fm scrobbles, Spotify playback, explicit likes/saves and confirmed preferences. A recommendation is never a play or preference by itself.

PR #60: https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/60

**Status: proposed; PR implementation and tests require review.**

**Resume:** review PR #60 and CI; validate candidate schema and canonical linkage; implement provenance-aware ingestion; test deduplication and evidence separation.

## Documentation and resume

Read [ACTIONS.md](ACTIONS.md) for dated work and evidence. After each meaningful action, update it with files changed, execution, exact verification and outcome. Update [the central handoff](../../NEXT_WORK.md) when priority or blockers change.
