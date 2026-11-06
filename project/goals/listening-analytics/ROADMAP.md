# Listening Analytics & Evidence Sources — Roadmap

**Last reviewed:** 2026-11-06  
**Status:** Architecture and source rules established; fresh coverage and semantic verification required. Feature work is paused under the repository-wide documentation-only priority.

## Repository-wide priority override — 2026-11-06

**This workstream is paused for feature implementation while SHIT's documentation audit is active.** The only permitted work here until the Maintainability & Documentation roadmap passes its acceptance criteria is documentation correction, evidence reconciliation, and recording known gaps. Do not run enrichment, modify canonical data, change playlists, or begin feature development. This workstream's feature roadmap remains queued; the active next action is the documentation-only handoff in [project/NEXT_WORK.md](../../NEXT_WORK.md). Resume feature work only when that handoff and the maintainability roadmap explicitly say documentation is complete.

## Purpose
Provide accurate historical listening analytics and prospective playback evidence without double-counting or pretending incomplete tracker coverage is complete.

## Non-negotiable source semantics
- Last.fm scrobbles are the historical source of truth.
- Spotify playback tracking is optional prospective evidence with coverage gaps.
- Missing tracker data means unknown, not zero.
- Likes/saves, recommendations, playlist additions, and playback are separate event types.
- Never merge unlike events or double-count the same listening evidence.

## Roadmap
1. **Fresh source audit — next.** Verify canonical scrobble archive/manifests and tracker coverage separately; timestamp all totals.
2. **Historical analytics.** Validate daily/monthly/yearly, artist/track/album rankings, sessions, durations, and timezone semantics against canonical events.
3. **Playback tracker reliability.** Document capture coverage, gaps, resume behavior, and whether data is local-only or cloud-hosted; do not imply always-on tracking until verified.
4. **Cross-source reconciliation.** Link identities and detect overlap without replacing Last.fm history or inventing missing plays.
5. **Evidence-aware recommendation features.** Provide recency/momentum signals with coverage/confidence, never treating missing tracker observations as dislikes.
6. **Regression and reporting.** Test dedupe, event typing, unknown-vs-zero, timezone boundaries, and source attribution.

## Acceptance criteria
Every metric names its source and period; tracker coverage is visible; no event type is silently converted into a scrobble; totals reconcile to canonical data.

## Open proposals (not merged)

- [PR #158 — Discover Weekly exposure and feedback tracking](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/158) is open/non-draft on `feature/discover-weekly-feedback-tracking`, diverged (9 ahead, 201 behind current main; mergeable=false). Its old-head tests #42071650507 and security scan #42071650219 passed, but it must be rebased and reverified before merge. It proposes a read-only observer for weekly appearances/disappearances, Liked Songs changes and separately labelled post-exposure Last.fm scrobbles; it does not expose Spotify's explicit hide action or write playlists.
- [PR #121 — Offline sorter evaluation and listening-ingestion watchdog specification](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/121) is open/draft on `codex/sorter-evaluation-ingestion-watchdog`, diverged (10 ahead, 419 behind current main; mergeable=false). No workflow runs were found for its observed head; rebase and obtain CI before relying on it. Its watchdog remains a specification until runtime implementation and tests are verified.

## Next action (documentation-only priority)

Continue the documentation audit for this workstream: verify this roadmap, README, ACTIONS, linked technical guides, source overviews, tests, workflow references and evidence claims against the current repository. Record any newly discovered contradictions or stale paths here and in the central handoff. **Do not run provider checks/enrichment, alter generated data, modify playlists, or implement features while the documentation-only priority is active.**

## Next feature action after documentation pause

Inspect current archive manifest, analytics outputs, tracker workflow/runtime and coverage report; publish fresh separately sourced baselines.
## Related records
[README](README.md) · [ACTIONS](ACTIONS.md) · [Discovery](../discovery-recommendations/ROADMAP.md)
