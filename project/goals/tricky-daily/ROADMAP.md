# Tricky Daily — Roadmap

**Last reviewed:** 2026-11-06  
**Status:** Active. Force/idempotency, explicit playlist-local whitelist/blacklist semantics, manual-removal feedback reconciliation, quota-aware progressive discovery, immutable pre-write staging, repository concurrency checks, ambiguous-write reconciliation, exact post-write verification, and GET-only snapshot/catalog/index reconciliation are implemented and covered by CI. The latest live snapshot remains 29 accessible/unique tracks; no 60-track replacement has been performed. The first end-to-end stage-only attempt was blocked by Spotify's recorded quota cooldown, which expires at 2026-11-06 19:49:46 UTC (14:49:46 Eastern).

## Purpose
Maintain a reliable daily 60-track discovery playlist that balances familiar taste with fresh discoveries, learns from meaningful feedback, and never overrides explicit user exclusions or playlist safety controls.

## User requirements and invariants
- Publish exactly 60 valid, unique Spotify track URIs on a successful cycle.
- Prefer distinct artists; retry for alternate tracks and progressively relax artist diversity only as a last resort. Never relax track uniqueness or exclusions.
- Removed/blacklisted tracks are absolute exclusions in normal runs, forced runs, retries, fallback expansion, and final publication.
- Reconcile whitelist/blacklist and live playlist state on every run, including forced runs. Only an explicit playlist-local whitelist entry matching the Spotify track URI or normalized primary-artist/title identity can clear that exact removal; current playlist presence alone is never approval. A stale or unaligned snapshot must not overwrite newer user decisions.
- Forced runs bypass the clock gate only. They must retain the same reconciliation, safety, staging, validation, description update, audit and read-back requirements as scheduled runs.
- Update the rotating playlist description on a successful forced cycle as well as a scheduled cycle, and verify the returned value.
- Learn from actual listening, likes/saves and explicit removals without confusing playlist exposure or missing tracker coverage with rejection. Liked tracks may be down-ranked, not automatically excluded.
- Last.fm scrobbles remain historical source-of-truth evidence; Spotify playback-tracker observations are optional prospective evidence with explicit coverage gaps.
- Keep Daily's own exposure/feedback model separate from generic playlist-fit calibration. Scheduled rotation is neutral housekeeping, not a negative signal.
- Playlist writes remain scoped to the specifically authorized Tricky Daily exception and documented controls; this does not authorize writes to other personal playlists.

## Force/idempotency correction — 2026-11-06

The P0 invariant is **force bypasses the clock gate only**. This is now implemented: `should_run_cycle()` receives the force flag, while `cycle_already_completed(config, cycle_date)` is evaluated independently and cannot be bypassed by force. A forced duplicate is covered by a regression test that asserts the process exits before creating a Spotify client. The stale contract assertions were corrected. Full safe CI run #42268351897 passed 500 tests, including the forced duplicate-dispatch guard. This correction is CI-verified.


## Additional quota-safety test gap found — 2026-11-06

A source review found that three existing Retry-After/cooldown tests in tests/test_spotify_playlist_manager.py were indented beneath the module-level if __name__ == "__main__" guard, after unittest.main(). They were therefore not defined during normal unittest discovery and could not protect the manager's cooldown persistence, active-cooldown initialization guard, or expired-cooldown behavior. A test-only correction is proposed in [PR #169](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/169), moving those existing methods into PlaylistManagerTests. The first PR run discovered all three tests (512 tests total) but failed because the HTTP 429 test fixture omitted the request-metrics structure; the fixture was corrected in commit `2ba8f7423f3c1d28a9ff0f45ccd57902aba57d89`. Updated PR CI is pending; do not treat the gap as fixed until the rerun passes. Runtime cooldown behavior itself is unchanged by PR #169.

## Explicit whitelist contract — source/test verified 2026-11-06

The playlist-local `playlist_removed_tracks.json` record has separate `removed` and `whitelisted` lists. A whitelist entry is explicit positive permission for the matching track identity in that playlist only. Matching uses the Spotify track URI and/or normalized primary-artist plus title identity. It clears only the matching removal; it does not whitelist the artist, other playlists, or unrelated tracks. Merely seeing a previously removed track in the live playlist does not clear its removal, because automation could have re-added it. During live-removal reconciliation, a matching whitelist entry prevents that missing baseline row from being newly recorded as a removal. Malformed/unreadable blacklist data fails closed during feedback loading. Source: `scripts/spotify/spotify_discovery.py` (`reconcile_daily_manual_removals`, `load_playlist_feedback`, `is_playlist_candidate_blocked`); regression coverage: `tests/test_spotify_discovery.py` (`test_daily_live_reconciliation_records_only_missing_tracks_and_honors_whitelist`, `test_readded_removed_track_remains_blocked_without_explicit_whitelist`, `test_explicit_playlist_whitelist_overrides_removal`). The current Daily whitelist has zero entries, so no historical removal is presently cleared.

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

Babel remains active while ChatGPT continues explicitly authorized Tricky Daily work in parallel. The force/idempotency guard, description read-back correction, GET-only snapshot refresh, manual-removal feedback reconciliation, quota-aware 80 → 160 → 300 artist discovery, durable cooldown persistence, immutable staging, pre-write rechecks, ambiguous-write reconciliation, and exact post-write validation are now implemented on main and covered by the current CI evidence recorded in ACTIONS.md. The playlist-local whitelist contract is source- and test-verified: only an explicit exact-track whitelist entry clears that track's removal; current membership does not. The current whitelist contains zero entries.

The latest confirmed live snapshot remains 29 accessible/unique tracks, captured by snapshot workflow #42268795272 at `2026-11-06T18:14:16.140845+00:00`; the removal baseline has 29 rows, blacklist has 55 entries, and whitelist has zero. The feedback ledger has 60 track rows and 55 idempotent manual-removal events. This was a GET-only snapshot/reconciliation with two Spotify GET requests and zero playlist mutations. Playback-tracker coverage remains unknown because `playback_data/segments.jsonl` is absent; do not infer zero plays. Last.fm and liked-song observation statuses were available/observed.

The push-triggered stage-only verification run #42268583897 failed before staging on Spotify HTTP 429 `QUOTA_EXCEEDED` with `Retry-After: 5781` seconds. Its GitHub event is `push`, with display title “Trigger safe Daily stage-only durability verification”; it was not a scheduled midnight rotation. The exact persisted deadline is `2026-11-06T19:49:46+00:00` (14:49:46 Eastern). PR #168 fixed progressive artist discovery and durable cooldown persistence. The latest saved candidate artifact has 195 Spotify-resolved URIs across 105 artists, but it is historical and not freshly scored; the 61 Booze-preview rows must not be mixed into Daily automatically. Do not call Spotify before the deadline, and after expiry begin with a no-write stage-only verification—not a live replacement. The first stage-only attempt failed before stage creation, so the end-to-end Actions stage commit/read-back path remains unverified.

The latest documentation-related mainline checks passed: Daily curator tests #42270239847 and public security scan #42270239536 on commit `b278da8f4f81bd8202fda50d6ed457e4ccfcb62e` (both successful). No live track replacement or description mutation has been authorized. See [ACTIONS.md](ACTIONS.md) for detailed run evidence.

## Next action

After `2026-11-06T19:49:46Z`, re-check the local cooldown file and current Eastern time, then run only the protected no-write stage-only path. Confirm the exact 60 candidate payload, exclusions, deduplication, artist fallback audit, stage commit/push, and committed-blob hash/order read-back. If discovery still cannot produce 60 or any gate fails, stop without Spotify playlist mutation and record the reason. A live 60-track replacement or description change requires separate user authorization.

## Related records
[README](README.md) · [ACTIONS](ACTIONS.md) · [Playlist Intelligence umbrella roadmap](../playlist-intelligence/ROADMAP.md) · [Daily cycle guide](../../../docs/TRICKY_DAILY_CYCLE.md) · [Daily backlog](../../../docs/TRICKY_DAILY_TODO.md)