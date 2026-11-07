# Tricky Daily — Roadmap

**Last reviewed:** 2026-11-07 UTC / 2026-11-06 Eastern  
**Status:** First fully verified live 60-track cycle completed on 2026-11-06 Eastern. The committed stage and recovery backup were verified before publication; Spotify read-back confirmed 60 unique tracks, zero blacklist hits, exact order, and the rotated description. The GET-only Daily snapshot/catalog/index and removal baseline now also report 60 tracks. The next scheduled automatic rotation after the cooldown-persistence fix remains unverified. Guided recovery and Daily recommendation memory remain open workstreams.

## Purpose
Maintain a reliable daily 60-track discovery playlist that balances familiar taste with fresh discoveries, learns from meaningful feedback, and never overrides explicit user exclusions or playlist safety controls.

## User requirements and invariants
- Publish exactly 60 valid, unique Spotify track URIs on a successful cycle.
- Complete one successful Tricky Daily rotation per Eastern calendar day under the documented schedule, with a recovery delivery for delayed Actions; snapshot refresh alone does not count as playlist rotation.
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

The current workflow declares cron deliveries at `0 4,5 * * *` and `15 4,5 * * *` UTC (midnight coverage plus a 15-minute recovery delivery for both EST and EDT offsets). The runner uses Eastern local time and a same-Eastern-date completion guard; `--force` bypasses only the clock-window check. It currently does not validate the exact scheduled cron string against the active DST offset, so strict cron-to-DST matching remains open.

On 2026-11-06, delayed scheduled runs #42212368912 and #42214834581 both failed with Spotify HTTP 429 `QUOTA_EXCEEDED`. The earlier workflow version did not commit the cooldown file on pre-cycle failure, allowing the second delivery to repeat requests. PR #168 corrected this: the always-run failure-recovery step now commits `.github/spotify_api_cooldown.json`, and the client checks the persisted cooldown before requests. The later successful manual cycle demonstrates recovery after the recorded cooldown, but the next scheduled delivery after this fix has not yet been observed.

The first successful production rotation in this session was a forced/manual push-triggered cycle, not proof of the scheduled cron path. The next scheduled Eastern-midnight delivery must be checked for successful rotation, delayed-run catch-up, same-date duplicate no-op, and cooldown persistence if a provider failure recurs.

**Important distinction:** the GET-only snapshot workflow is separate from playlist rotation. Snapshot refresh #42316906860 ran after the live cycle and confirmed 60 accessible items; that is supporting state reconciliation, not a second rotation.

## Current gaps and verification requirements
- The successful production cycle proves the forced/manual publication path, not the next automatic scheduled delivery. Verify the next scheduled Eastern-midnight run after the durable cooldown-persistence fix.
- Guided resume/rollback/discard from a surviving production stage remains open. A pending or ambiguous stage must continue to block blind regeneration; implement explicit audited recovery before calling the workflow fully self-healing.
- Strict cron-to-DST matching remains open. Current dual cron entries plus Eastern-local gate provide catch-up behavior but do not validate the exact cron event against the active offset.
- Spotify quota can still be exhausted. The workflow now persists Retry-After cooldown state even when discovery fails before staging; do not clear a non-expiring manual-clear state without provider evidence.
- Playback-tracker coverage remains unknown because `playback_data/segments.jsonl` is absent. Last.fm coverage is available and liked-song observations are recorded; missing playback data is not zero plays.
- Daily recommendation memory is approved but not implemented. Historical candidate rows with null listening evidence must not be backfilled as plays, ignores, or approval.
- Verify current mainline state and latest workflow evidence before changing anything. The guide and roadmap are continuity aids, not substitutes for live read-back.

## Current verified state — 2026-11-07 UTC / 2026-11-06 Eastern

Live cycle workflow [#42316296314](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42316296314) completed successfully. It committed production stage `assistant_data/spotify/staging/tricky_daily/2026-11-06-42316296314.json` and recovery backup `playlist_backups/20261107T000907379512Z_4yUVHSMQySfWeEowfIMcx7.json` before Spotify mutation. Stage commit: `e08baedf6c006322ff31abd4d11bc8169d69a123`; accepted-cycle state commit: `d7ce8ec476b59d284d468bb4989ead8b0d109871`. The cycle published exactly 60 tracks; 26 previous tracks rotated out neutrally. The cycle's final Spotify read-back confirmed the exact staged order, 60 unique valid tracks, zero blacklist hits, and description `Today's detour starts here.`.

Post-cycle read-only verification [#42316824364](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42316824364) passed: 60 unique tracks, zero blacklisted, description matched, snapshot ID `AAAAV+t5mQVmRSxOOjmUuVYsGIqAbzv2`. The separate same-day verification guard bug was fixed and regression-tested; full Daily curator suite #42316716912 passed 517 tests.

GET-only snapshot refresh [#42316906860](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42316906860) then published a current Daily snapshot at `2026-11-07T00:13:46.604200+00:00`: 60 accessible items, 60 unique URIs, zero new manual removals, 58 total blacklisted, and 3 idempotent removal-feedback events reconciled. The reference catalog and Daily baseline both report 60 items. Snapshot/catalog/baseline publication commit: `bae0cb6c435c6c12672b97bde88138ddbd9be0fe`.

The live-cycle trigger `.github/test-triggers/tricky-daily-live-cycle.json` is now `action: verify-only`, `force: true`; future edits to that trigger cannot silently launch another replacement. The latest feedback coverage reports Last.fm available, liked-song observations present, and playback tracker unknown because the segment file is absent. Daily recommendation memory remains a committed P1 requirement, not yet implemented.

## Next action

1. Verify the next scheduled Eastern-midnight rotation after the cooldown-persistence fix; distinguish a real 60-track publication from a snapshot-only refresh or duplicate no-op.
2. Implement and failure-test guided resume/rollback/discard for a surviving production stage so interrupted publication is recoverable without blind regeneration.
3. Once the scheduled path and recovery behavior are proven, design and implement Daily recommendation memory, preserving separate Spotify playback, Last.fm scrobbles, likes, manual removals, retention, ignored, and unknown coverage.
4. Keep the trigger in read-only `verify-only` mode unless a future live cycle is explicitly authorized.

## Related records
[README](README.md) · [ACTIONS](ACTIONS.md) · [Playlist Intelligence umbrella roadmap](../playlist-intelligence/ROADMAP.md) · [Daily cycle guide](../../../docs/TRICKY_DAILY_CYCLE.md) · [Daily backlog](../../../docs/TRICKY_DAILY_TODO.md)