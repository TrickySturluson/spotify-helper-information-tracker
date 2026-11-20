# Tricky Daily — Roadmap

**Last reviewed:** 2026-11-20 UTC / 2026-11-20 Eastern  
**Status:** Mainline's latest user-authorized push-triggered cycle [#44708292405](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/44708292405) completed a 60-track publication and persisted completed state/audit. The later GET-only snapshot at 15:38 UTC contains 60 accessible unique tracks. This is not a scheduled run. Jockey draft PR #200 adds strict cron-to-DST matching and durable description-only before/after snapshots; CI and scheduled live proof remain pending. Guided recovery and Daily recommendation memory remain open workstreams.

## Purpose
Maintain a reliable daily 60-track discovery playlist that balances familiar taste with fresh discoveries, learns from meaningful feedback, and never overrides explicit user exclusions or playlist safety controls.

## User requirements and invariants
- Publish exactly 60 valid, unique Spotify track URIs on a successful cycle.
- Complete one successful Tricky Daily rotation per Eastern calendar day under the documented schedule, with a recovery delivery for delayed Actions; snapshot refresh alone does not count as playlist rotation.
- Prefer distinct artists; retry for alternate tracks and progressively relax artist diversity only as a last resort. Never relax track uniqueness or exclusions.
- Removed/blacklisted tracks are absolute exclusions in normal runs, forced runs, retries, fallback expansion, and final publication.
- Reconcile whitelist/blacklist and live playlist state on every run, including forced runs. Only an explicit playlist-local whitelist entry matching the Spotify track URI or normalized primary-artist/title identity can clear that exact removal; current playlist presence alone is never approval. A stale or unaligned snapshot must not overwrite newer user decisions.
- Forced runs bypass the clock gate only. They must retain the same reconciliation, safety, staging, validation, description update, audit and read-back requirements as scheduled runs.
- Every playlist mutation, including a description-only update, must preserve a complete before snapshot and an after snapshot. The pre-change snapshot and audit must be durable before the Spotify PUT; after acceptance, pending state must be persisted and an after snapshot attempted even if read-back fails. A description-only operation must not change track order or membership.
- Update the rotating playlist description on a successful forced cycle as well as a scheduled cycle, and verify the returned value.
- Learn from actual listening, likes/saves and explicit removals without confusing playlist exposure or missing tracker coverage with rejection. Liked tracks may be down-ranked, not automatically excluded.
- Last.fm scrobbles remain historical source-of-truth evidence; Spotify playback-tracker observations are optional prospective evidence with explicit coverage gaps.
- Keep Daily's own exposure/feedback model separate from generic playlist-fit calibration. Scheduled rotation is neutral housekeeping, not a negative signal.
- Playlist writes remain scoped to the specifically authorized Tricky Daily exception and documented controls; this does not authorize writes to other personal playlists.

## Force/idempotency correction — 2026-11-06

The P0 invariant is **force bypasses the clock gate only**. This is now implemented: `should_run_cycle()` receives the force flag, while `cycle_already_completed(config, cycle_date)` is evaluated independently and cannot be bypassed by force. A forced duplicate is covered by a regression test that asserts the process exits before creating a Spotify client. The stale contract assertions were corrected. Full safe CI run #42268351897 passed 500 tests, including the forced duplicate-dispatch guard. This correction is CI-verified.


## Additional quota-safety test gap found — 2026-11-06

The three Retry-After/cooldown regression tests were moved into `PlaylistManagerTests` and merged in PR #169 as `8d0d2d5e8b0448fde64932aced1014ef944e3312`; PR and post-merge CI passed 512 tests, and both security scans passed. PR #170 then closed the remaining header-format gap: numeric and HTTP-date Retry-After values are persisted as UTC deadlines; missing/unusable values create a non-expiring `manual_clear_required` state that blocks every Spotify request until manually cleared after provider restriction verification. PR #170 merged as `397218ebf4e397ec4a8fd3a1d1ec6e23aefe8db2`; its PR CI passed 514 tests (#42273342714) and security scan passed (#42273342665). Post-merge mainline tests #42273509046 and security scan #42273509063 both passed.

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

## Recommendation memory — accepted product requirement, design pending

Daily must maintain durable, playlist-specific history of its own recommendations and later outcomes. This is an explicit product requirement, not an optional enhancement.

Store recommendation events, not merely current playlist membership. Each event should retain stable track identity (Spotify URI plus normalized artist/title fallback), recommendation timestamp, cycle/run ID, strategy/config version, selection rationale, evidence provenance, and exposure/add/remove intervals. Link repeated recommendations to the same track history while preserving each event.

Keep outcomes distinct: measured Spotify playback; Last.fm scrobbles; likes/saves; explicit manual removal/blacklist; later retention; ignored/no observed play; not-yet-observed; and unknown due to incomplete coverage. Store source and observation windows. Missing playback coverage is unknown, never zero. A high-play-then-remove track must remain distinguishable from an unplayed track that was removed. Track-level rejection must not automatically become artist-level rejection.

Memory must be append-safe/idempotent, versioned, recoverable, auditable, and scoped only to Tricky Daily. Define migration, retention and compaction before implementation. Test repeated recommendations, duplicate ingestion, delayed scrobbles, high-play-then-remove, unplayed-then-remove, retained-but-unplayed, missing coverage, whitelist behavior and source attribution. Do not invent historical outcomes from candidate rows whose listening fields are null. Memory never overrides blacklist/whitelist policy or publication safety.

## Feedback nuance — high-engagement removals

Exact removed-track exclusions remain hard blocks. However, `load_playlist_feedback()` currently adds an artist-level negative event for any removed track with at least one measured post-add play or Last.fm scrobble, regardless of how many plays occurred or how many distinct tracks by that artist were removed. A highly played track removed for rotation/freshness can therefore penalize its artist. This is a P1 scoring-quality issue: decide a conservative aggregation rule (multiple distinct removed tracks vs low/high engagement) and add tests before changing weights. Never weaken exact track exclusions.

## Roadmap

**Execution priority:** prove and stabilize the existing daily operational cycle first. Do not expand recommendation intelligence until the no-write staging path is proven end-to-end and scheduled/forced behavior is reconciled. Recommendation memory is a committed P1 workstream to build after that operational gate.

1. **P0 — Exclusion and reconciliation integrity [IMPLEMENTED].** Centralize blacklist/removed-track enforcement and verify it before scoring and immediately before publication. Reconcile whitelist/blacklist and live playlist state on every invocation, including forced runs.
2. **P0 — Transactional publication [IMPLEMENTED WITH RECOVERY GAPS].** Persist exact 60-track staging, make retries idempotent, guard concurrent invocations, preserve known-good state, and verify live ordered contents/count/uniqueness/exclusions before marking complete.
3. **P0 — Forced-run parity [IMPLEMENTED].** Force bypasses only the clock gate; verify the same policy checks, reconciliation, staging, validation, description update/read-back, audit and post-publication checks as scheduled runs.
4. **P0 — API and recovery resilience [AMBIGUOUS-WRITE GUARD IMPLEMENTED; RESUME GAP OPEN].** Respect Retry-After, bounded transient retries, token refresh, ambiguous write timeout read-back, pending-verification state and safe recovery.
5. **P1 — Daily recommendation memory and feedback correctness.** Persist each recommendation event and its later observed outcomes; distinguish exposure, positive engagement, explicit rejection, ignored, not-yet-exposed and unknown due to coverage gaps; preserve track-level vs artist-level preference.
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

## Schedule reliability — configured behavior vs proven behavior

Mainline currently declares combined UTC cron expressions `0 4,5 * * *` and `15 4,5 * * *`. The mainline runner uses the Eastern local hour and same-date completion guard, but does not validate the exact GitHub schedule string against the current offset.

Draft PR [#200](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/200) splits the primary and 15-minute recovery entries into `0 4`, `15 4`, `0 5`, and `15 5` UTC, passes `github.event.schedule` as `SCHEDULE_CRON`, and accepts only entries matching the active `America/New_York` offset. Missing/unknown strings fail closed; delayed matching-offset deliveries may still catch up later on the same Eastern date. The existing completion guard remains independent of force and schedule selection. Unit tests are added, but PR CI and a live scheduled delivery remain pending. The stale user-owned PR #159 was not modified.

A successful live push-triggered cycle is not proof of the schedule. On 2026-11-20, run #44708292405 was triggered by a user-authorized push to the test-trigger file, not by cron. It completed the 60-track publication and persisted state/audit. The next scheduled run must independently prove the correct EDT/EST entry, exact 60-track publication, and same-date duplicate no-op.

## Current gaps and verification requirements
- The 2026-11-20 publication proves one user-authorized push-triggered cycle, not the automatic scheduled path. Verify a scheduled Eastern-midnight run after PR #200 is merged, including the exact cron/offset decision and a same-date duplicate no-op.
- Draft PR #200 adds strict cron-to-DST matching; its exact-head CI and a scheduled live run remain pending.
- Draft PR #200 adds durable before/after snapshots for description-only updates; its exact-head CI and a live description-only verification remain pending.
- Guided resume/rollback/discard from a surviving production stage remains open. A pending or ambiguous stage must continue to block blind regeneration; implement explicit audited recovery before calling the workflow fully self-healing.
- Spotify quota can still be exhausted. The workflow now persists Retry-After cooldown state even when discovery fails before staging; do not clear a non-expiring manual-clear state without provider evidence.
- Playback-tracker coverage remains unknown because `playback_data/segments.jsonl` is absent. Last.fm coverage is available and liked-song observations are recorded; missing playback data is not zero plays.
- Daily recommendation memory is approved but not implemented. Historical candidate rows with null listening evidence must not be backfilled as plays, ignores, or approval.
- Verify current mainline state and latest workflow evidence before changing anything. The guide and roadmap are continuity aids, not substitutes for live read-back.

## Current verified state — 2026-11-20 UTC / 2026-11-20 Eastern

User-authorized push-triggered cycle [#44708292405](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/44708292405) started at 2026-11-20 09:09:18 UTC and completed at 09:11:02 UTC. It committed stage `assistant_data/spotify/staging/tricky_daily/2026-11-20-44708292405.json` with SHA-256 `c8ad07b1e7f8745ac08db4a2ea7378b8439384015169227d62bffbb035443e49` and recovery backup `playlist_backups/20261120T091051361667Z_4yUVHSMQySfWeEowfIMcx7.json` before Spotify mutation. The cycle, snapshot artifact, and state/feedback persistence steps succeeded. Mainline state records `last_cycle_date_eastern=2026-11-20`, status `completed`, 60 ordered after-URIs, description `A little familiar, a little unhinged.`, and post-cycle snapshot ID `AAAAd7gRBY+iCM4wXDnz0UJ8x+Sq39Ua`.

The later GET-only snapshot refresh at `2026-11-20T15:38:03.306427Z` contains 60 accessible items and 60 unique URIs. The manual trigger is back in `verify-only` mode. This is one real publication and state/audit result, but it is **not** a scheduled cron proof. Playback-tracker coverage remains unknown because `playback_data/segments.jsonl` is absent; Last.fm and liked-song observations remain separately sourced.

Draft PR #200 is Jockey-owned and contains strict schedule offset matching plus description-only snapshot bracketing. No live Spotify/Last.fm operation or production deployment was performed while authoring it.

## Next action

1. Complete exact-head CI and independent diff review for Jockey draft PR #200; keep it draft and do not merge from the automation.
2. After owner-controlled merge, verify a real scheduled Eastern-midnight cycle, exact 60-track read-back, state/audit persistence, and a same-date duplicate no-op. Keep the manual trigger in read-only `verify-only` mode.
3. Implement and failure-test guided resume/rollback/discard for a surviving production stage so interrupted publication is recoverable without blind regeneration.
4. After operational reliability and recovery are proven, design and implement Daily recommendation memory, preserving separate Spotify playback, Last.fm scrobbles, likes, manual removals, retention, ignored, not-yet-observed, and unknown coverage.

## Related records
[README](README.md) · [ACTIONS](ACTIONS.md) · [Playlist Intelligence umbrella roadmap](../playlist-intelligence/ROADMAP.md) · [Daily cycle guide](../../../docs/TRICKY_DAILY_CYCLE.md) · [Daily backlog](../../../docs/TRICKY_DAILY_TODO.md)