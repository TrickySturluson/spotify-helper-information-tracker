# Tricky Daily — Roadmap

**Last reviewed:** 2026-11-06  
**Status:** Active. Force/idempotency, exclusion rechecks, immutable pre-write staging, repository concurrency checks, ambiguous-write reconciliation, exact post-write verification, and GET-only snapshot/catalog/index reconciliation are implemented and covered by CI. A live track cycle has not been run; it remains separately gated by user authorization and provider cooldown.

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

## Force/idempotency correction — 2026-11-06

The P0 invariant is **force bypasses the clock gate only**. This is now implemented: `should_run_cycle()` receives the force flag, while `cycle_already_completed(config, cycle_date)` is evaluated independently and cannot be bypassed by force. A forced duplicate is covered by a regression test that asserts the process exits before creating a Spotify client. The stale contract assertions were corrected. Full safe CI run #42268351897 passed 500 tests, including the forced duplicate-dispatch guard. This correction is CI-verified.


## System map
- Candidate generation and publication: scripts/spotify/spotify_daily_playlist.py, scripts/spotify/spotify_daily_cycle.py
- Feedback and learning: scripts/spotify/spotify_daily_feedback.py, assistant_data/spotify/daily_feedback.json
- Preflight: scripts/spotify/spotify_daily_preflight.py
- Trend context: scripts/spotify/spotify_listening_trends.py, assistant_data/spotify/listening_trends.json
- Cycle guide and schedule semantics: [TRICKY_DAILY_CYCLE.md](../../../docs/TRICKY_DAILY_CYCLE.md)
- Prioritized safety and quality backlog: [TRICKY_DAILY_TODO.md](../../../docs/TRICKY_DAILY_TODO.md)
- Workflows: .github/workflows/spotify-daily-midnight-cycle.yml, spotify-daily-live-preflight.yml, spotify-daily-remote-verification.yml, spotify-daily-feedback-observation.yml
- Regression tests: tests/test_spotify_daily_cycle_schedule.py, test_spotify_daily_feedback_scoring.py, test_spotify_daily_playlist.py, test_spotify_daily_preflight.py

## Roadmap
1. **P0 — Exclusion and reconciliation integrity [IMPLEMENTED].** Centralize blacklist/removed-track enforcement and verify it before scoring and immediately before publication. Reconcile whitelist/blacklist and live playlist state on every invocation, including forced runs.
2. **P0 — Transactional publication [IMPLEMENTED WITH RECOVERY GAPS].** Persist exact 60-track staging, make retries idempotent, guard concurrent invocations, preserve known-good state, and verify live ordered contents/count/uniqueness/exclusions before marking complete.
3. **P0 — Forced-run parity [IMPLEMENTED].** Force bypasses only the clock gate; verify the same policy checks, reconciliation, staging, validation, description update/read-back, audit and post-publication checks as scheduled runs.
4. **P0 — API and recovery resilience [AMBIGUOUS-WRITE GUARD IMPLEMENTED; RESUME GAP OPEN].** Respect Retry-After, bounded transient retries, token refresh, ambiguous write timeout read-back, pending-verification state and safe recovery.
5. **P1 — Feedback correctness.** Distinguish exposure, positive engagement, explicit rejection, ignored, not-yet-exposed and unknown due to coverage gaps; preserve track-level vs artist-level preference.
6. **P1 — Candidate quality and diversity.** Improve familiarity/discovery balance, artist saturation, confidence, diminishing returns, diversity recovery and concise selection explanations.
7. **P1 — Operational visibility.** Publish quality, feedback, safety, run and recovery summaries; alert on stale data or failed cycles.
8. **P2 — Evaluation.** Evaluate recommendation changes against engagement, discovery and diversity outcomes with isolated experiments and rollback.

## Acceptance criteria
- Every successful publication has exactly 60 valid unique track URIs and no blacklisted/removed entries.
- A forced run cannot bypass any policy or state-reconciliation check.
- A stale snapshot cannot reintroduce a user-removed track or erase a newer whitelist/blacklist decision.
- Failures at any stage preserve a recoverable state and never report completion prematurely.
- Concurrent invocations cannot race to publish.
- An ambiguous Spotify write timeout triggers live read-back/reconciliation before any retry.
- The live playlist is read back and verified against the approved staging artifact.
- Description changes are verified independently; successful tracks with failed description verification remain distinguishable.
- Feedback reports preserve source and coverage; no-play is not automatically negative.
- CI regression tests pass, and live workflow evidence is recorded separately from unit-test evidence.

## Current gaps and verification requirements
- The live track-replacement path has not been exercised in this session. The user has not authorized a live cycle; no playlist tracks or description were changed.
- The no-write stage-only workflow attempt (#42268583897) stopped during candidate discovery on Spotify HTTP 429 QUOTA_EXCEEDED with Retry-After: 5781 seconds (about 1h36m). It failed before stage creation/commit and before any playlist mutation. Do not issue further Spotify API requests until that cooldown expires; repeated calls may extend it.
- The durable staging Git commit/push path is unit-tested but has not yet completed an end-to-end GitHub Actions stage-only run because of the provider quota response.
- Recovery is fail-closed, not automatic: a surviving production stage blocks same-date retries and ambiguous/partial writes persist a date guard. A guided resume/rollback/discard workflow remains open.
- GitHub concurrency plus repository-head and live-snapshot rechecks greatly reduce races, but Spotify does not provide a conditional write tied to snapshot ID; the last race window cannot be eliminated entirely.
- The detailed P0 checklist remains in TRICKY_DAILY_TODO.md; unchecked items are not assumed implemented.
- Verify current main code and latest workflow runs before changing anything. The guide documents expected behavior but is not proof of current live Spotify state.
- Reconcile the most recent live playlist, feedback, blacklist/whitelist, description and staging state before another live write.

## Current parallel-work status — 2026-11-06

Babel remains active. ChatGPT is continuing explicitly authorized Tricky Daily work in parallel. The force/idempotency defect has been corrected: force bypasses the clock-window gate only; the same-Eastern-date completion guard remains active. A regression test now asserts that a forced duplicate exits before creating a Spotify client. Spotify description read-back now HTML-unescapes provider text before comparison; a focused regression test covers the encoded apostrophe observed in the saved Daily snapshot.

A Daily-only snapshot refresher has been added. It uses Spotify GET requests only, verifies playlist identity/ownership and complete item pagination, reconciles manual removals against the last accepted-cycle baseline, preserves prior snapshots, and is scheduled daily at 06:25 UTC. The latest saved Daily snapshot inspected during this work was captured 2026-11-06 14:18 UTC and contained 37 accessible tracks; the removal baseline contained 37 rows, and the Daily blacklist contained 47 removed entries with no whitelist entries. These repository facts are not a new live Spotify read.

The latest accepted cycle state remains pending verification from 2026-11-05. The audit records multiple forced cycles on that same Eastern date before the force guard was fixed, and the final attempt stopped after the replacement helper's first-page completion. The HTML-escaped description comparison is a likely cause of the incomplete post-write path. No live playlist mutation was performed in this work. See [ACTIONS.md](ACTIONS.md) for commits and verification boundaries.

## Next action

Confirm the safe remote full-suite and focused Daily tests, then confirm the first run of the Daily-only snapshot workflow and inspect any newly detected manual removals. Continue the remaining P0 publication safeguards: durable exact-order staging, pre-write live-snapshot race detection, ambiguous-write read-back, and post-write exact-order/count/uniqueness/blacklist verification. Do not start a live track replacement until the remaining safeguards and workflow readiness are verified and the user separately authorizes that write.

## Related records
[README](README.md) · [ACTIONS](ACTIONS.md) · [Playlist Intelligence umbrella roadmap](../playlist-intelligence/ROADMAP.md) · [Daily cycle guide](../../../docs/TRICKY_DAILY_CYCLE.md) · [Daily backlog](../../../docs/TRICKY_DAILY_TODO.md)