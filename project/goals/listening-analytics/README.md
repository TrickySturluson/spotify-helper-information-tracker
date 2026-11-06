# Listening Analytics & Evidence Sources
> **Roadmap:** [ROADMAP.md](ROADMAP.md) is the durable plan and next-action reference. Read it before work; update it and [ACTIONS.md](ACTIONS.md) in the same session as implementation, testing, decisions, or blockers.
> **Current repository priority:** This workstream is paused for feature implementation while SHIT's documentation audit is active. Only documentation corrections and evidence reconciliation are permitted. Preserve this roadmap; resume its feature next actions only when the [central handoff](../../NEXT_WORK.md) and Maintainability & Documentation roadmap explicitly say documentation is complete.


## Goal

Maintain accurate historical listening analytics with explicit source, coverage and event semantics.

## Scope, decisions and constraints

Last.fm scrobbles are historical listening source of truth. Spotify playback tracker is optional prospective evidence with coverage gaps; missing tracker data means unknown, not zero. Explicit likes/saves are user actions, not necessarily plays. Recommendations are exposure, not listening. Never merge event types or double-count.

Scope: chronological scrobble archive, derived analytics, playback tracker coverage, cross-source reconciliation, recency signals and evidence-aware recommendation features.

**Status: existing architecture/rules documented; verify source files and coverage before quoting current totals.**

**Resume:** inspect canonical Last.fm archive/manifests; inspect playback tracker coverage separately; verify analytics semantics; test unknown-vs-zero and deduplication; record fresh totals with source and timestamp.

## Documentation and resume

Read [ACTIONS.md](ACTIONS.md) for dated work and evidence. After each meaningful action, update it with files changed, execution, exact verification and outcome. Update [the central handoff](../../NEXT_WORK.md) when priority or blockers change.
