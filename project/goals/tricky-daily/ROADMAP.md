# Tricky Daily — Roadmap

**Last reviewed:** 2026-11-06  
**Status:** Feature work paused under the documentation-only priority. Core 60-track rotation, fallback, Eastern-time scheduling, description handling, preflight and feedback tooling exist; end-to-end live correctness and remaining P0 safeguards are not yet fully verified.

## Repository-wide priority override — 2026-11-06

**This workstream is paused for feature implementation while SHIT's documentation audit is active.** The only permitted work here until the Maintainability & Documentation roadmap passes its acceptance criteria is documentation correction, evidence reconciliation, and recording known gaps. Do not run enrichment, modify canonical data, change playlists, or begin feature development. This workstream's feature roadmap remains queued; the active next action is the documentation-only handoff in [project/NEXT_WORK.md](../../NEXT_WORK.md). Resume feature work only when that handoff and the maintainability roadmap explicitly say documentation is complete.

## Purpose
Maintain a reliable daily 60-track discovery playlist that balances familiar taste with fresh discoveries, learns from meaningful feedback, and never overrides explicit user exclusions or playlist safety controls.

## User requirements and invariants
- Publish exactly 60 valid, unique Spotify track URIs on a successful cycle.
- Prefer distinct artists; retry for alternate tracks and progressively relax artist diversity only as a last resort. Never relax track uniqueness or exclusions.
- Removed/blacklisted tracks are absolute exclusions in normal runs, forced runs, retries, fallback expansion, and final publication.
- Reconcile whitelist/blacklist and live playlist state on every run, including forced runs; stale snapshots must not undo newer user choices.
- Forced runs bypass the clock gate only. They must retain the same reconciliation, safety, staging, validation, description update, audit and read-back requirements as scheduled runs.
- Update the rotating playlist description on a successful forced cycle as well as a scheduled cycle, and verify the returned value.
- Learn from actual listening, likes/saves and explicit removals without confusing playlist exposure or missing tracker coverage with rejection. Liked tracks may be down-ranked, not automatically excluded.
- Last.fm scrobbles remain historical source-of-truth evidence; Spotify playback-tracker observations are optional prospective evidence with explicit coverage gaps.
- Keep Daily's own exposure/feedback model separate from generic playlist-fit calibration. Scheduled rotation is neutral housekeeping, not a negative signal.
- Playlist writes remain scoped to the specifically authorized Tricky Daily exception and documented controls; this does not authorize writes to other personal playlists.

## Current source discrepancy — 2026-11-06

The intended invariant above is **force bypasses the clock gate only**. Current source does not fully satisfy it: `spotify_daily_cycle.py` passes `args.force` into `cycle_already_completed()`, which returns `False` for forced calls and therefore bypasses the same-Eastern-date completion guard too. `tests/test_spotify_daily_cycle_schedule.py` currently asserts that behavior. This allows a second forced cycle on an Eastern date already marked complete and is a P0 idempotency mismatch, not an approved relaxation. Keep the requirement unchanged; after the documentation-only pause, fix the implementation and regression test so force bypasses only the time-window check and still respects same-date idempotency. No runtime change is authorized during the current documentation phase.


## System map
- Current discovery candidate generation: scripts/spotify/spotify_discovery.py (the cycle explicitly requests 60 candidates).
- 60-track assembly, safety checks and publication: scripts/spotify/spotify_daily_cycle.py.
- Legacy/alternate 30-track candidate builder: scripts/spotify/spotify_daily_playlist.py; it is not the current live 60-track cycle.
- Feedback and learning: scripts/spotify/spotify_daily_feedback.py, assistant_data/spotify/daily_feedback.json
- Preflight: scripts/spotify/spotify_daily_preflight.py
- Trend context: scripts/spotify/spotify_listening_trends.py, assistant_data/spotify/listening_trends.json
- Cycle guide and schedule semantics: [TRICKY_DAILY_CYCLE.md](../../../docs/TRICKY_DAILY_CYCLE.md)
- Prioritized safety and quality backlog: [TRICKY_DAILY_TODO.md](../../../docs/TRICKY_DAILY_TODO.md)
- Workflows: .github/workflows/spotify-daily-midnight-cycle.yml, spotify-daily-live-preflight.yml, spotify-daily-remote-verification.yml, spotify-daily-feedback-observation.yml
- Regression tests: tests/test_spotify_daily_cycle_schedule.py, test_spotify_daily_feedback_scoring.py, test_spotify_daily_playlist.py, test_spotify_daily_preflight.py

## Roadmap
1. **P0 — Exclusion and reconciliation integrity.** Centralize blacklist/removed-track enforcement and verify it before scoring and immediately before publication. Reconcile whitelist/blacklist and live playlist state on every invocation, including forced runs.
2. **P0 — Transactional publication.** Persist exact 60-track staging, make retries idempotent, guard concurrent invocations, preserve known-good state, and verify live ordered contents/count/uniqueness/exclusions before marking complete.
3. **P0 — Forced-run parity.** Force bypasses only the clock gate; verify the same policy checks, reconciliation, staging, validation, description update/read-back, audit and post-publication checks as scheduled runs.
4. **P0 — API and recovery resilience.** Respect Retry-After, bounded transient retries, token refresh, ambiguous write timeout read-back, pending-verification state and safe recovery.
5. **P1 — Feedback correctness.** Distinguish exposure, positive engagement, explicit rejection, ignored, not-yet-exposed and unknown due to coverage gaps; preserve track-level vs artist-level preference.
6. **P1 — Candidate quality and diversity.** Improve familiarity/discovery balance, artist saturation, confidence, diminishing returns, diversity recovery and concise selection explanations.
7. **P1 — Operational visibility.** Publish quality, feedback, safety, run and recovery summaries; alert on stale data or failed cycles.
8. **P2 — Evaluation.** Evaluate recommendation changes against engagement, discovery and diversity outcomes with isolated experiments and rollback.

## Acceptance criteria
- Every successful publication has exactly 60 valid unique track URIs and no blacklisted/removed entries.
- A forced run cannot bypass any policy or state-reconciliation check.
- A second forced invocation on an already-completed Eastern date is blocked; force bypasses the time-window gate only.
- A stale snapshot cannot reintroduce a user-removed track or erase a newer whitelist/blacklist decision.
- Failures at any stage preserve a recoverable state and never report completion prematurely.
- Concurrent invocations cannot race to publish.
- An ambiguous Spotify write timeout triggers live read-back/reconciliation before any retry.
- The live playlist is read back and verified against the approved staging artifact.
- Description changes are verified independently; successful tracks with failed description verification remain distinguishable.
- Feedback reports preserve source and coverage; no-play is not automatically negative.
- CI regression tests pass, and live workflow evidence is recorded separately from unit-test evidence.

## Current gaps and verification requirements
- The detailed P0 checklist remains in TRICKY_DAILY_TODO.md; unchecked items are not assumed implemented.
- Verify current main code and latest workflow runs before changing anything. The guide documents expected behavior but is not proof of current live Spotify state.
- Reconcile the most recent live playlist, feedback, blacklist/whitelist, description and staging state before another live write.

## Latest saved playlist evidence — 2026-11-06

The latest repository snapshot at `assistant_data/spotify/playlists/4yUVHSMQySfWeEowfIMcx7.json` was captured at `2026-11-06T01:48:00.233040+00:00`: 58/58 items fetched, 58 unique URIs, accessible, no item error. This is below the 60-track success target. The snapshot does not establish why the playlist had 58 items or whether it changed afterward; re-run read-only preflight and reconcile cycle/audit state before any later authorized write. No playlist repair is permitted during the documentation-only pause.

## Open proposals (not merged)

- [PR #159 — Tricky Daily DST schedule gating](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/159) is open/non-draft on `fix/tricky-daily-schedule-gate`, but its branch is diverged (6 commits ahead, 201 behind current main; mergeable=false). Its old-head tests #42091662410 and security scan #42091662609 passed, but it must be rebased and reverified before merge. Current main still uses combined cron/local-hour gating; strict cron-to-Eastern-offset matching is proposed, not implemented.
- [PR #160 — Exposure-aware Daily discovery and quality reporting](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/160) is open/non-draft on `daily-exposure-aware-discovery`, diverged (27 ahead, 201 behind current main; mergeable=false). Old-head tests #42081994195 and security scan #42081994125 passed; rebase and rerun before merge. Its 45/30/25 mix, exposure-decay ranking and read-only quality report remain proposals.
- [PR #158 — Discover Weekly exposure and feedback tracking](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/158) is open/non-draft on `feature/discover-weekly-feedback-tracking`, diverged (9 ahead, 201 behind current main; mergeable=false). Old-head tests #42071650507 and security scan #42071650219 passed; rebase and rerun before merge. It is adjacent listening-analytics work, not a Daily playlist-write feature.

## Next action
Read NEXT_WORK.md, this roadmap, README.md, ACTIONS.md, the Daily TODO/cycle guides, and the relevant code/tests/workflows. Then audit current Daily code and latest successful workflow evidence against P0 acceptance criteria; fix the highest-risk gap before any further live cycle.

## Related records
[README](README.md) · [ACTIONS](ACTIONS.md) · [Playlist Intelligence umbrella roadmap](../playlist-intelligence/ROADMAP.md) · [Daily cycle guide](../../../docs/TRICKY_DAILY_CYCLE.md) · [Daily backlog](../../../docs/TRICKY_DAILY_TODO.md)