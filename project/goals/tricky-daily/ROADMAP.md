# Tricky Daily — Roadmap

**Last reviewed:** 2026-11-21 UTC / 2026-11-21 Eastern  
**Status:** Mainline scheduled cycle [#44901651168](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/44901651168) ran 2026-11-21 11:59 UTC (06:59 Eastern). Its cycle, recovery-snapshot, and state/feedback persistence steps all succeeded. It committed stage [17852545753640e35014caf8df8557beac999add](https://github.com/TrickySturluson/spotify-helper-information-tracker/commit/17852545753640e35014caf8df8557beac999add) and completed state/audit [663291f042dd6ab08f0c48630ebb464ed048c188](https://github.com/TrickySturluson/spotify-helper-information-tracker/commit/663291f042dd6ab08f0c48630ebb464ed048c188). The committed state records Eastern cycle date 2026-11-21, status completed, 60 ordered after-URIs, and after-snapshot ID `AAAAeu09d2bu354ZxalAyWqCpM6Yeye5`. The later scheduled delivery [#44904728622](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/44904728622) ran at 12:36 UTC (07:36 Eastern). Its cycle step succeeded but the state/feedback persistence step was skipped; the persisted state still points to the first run and remains completed for 2026-11-21, so this is the same-date duplicate no-op rather than a second publication. GET-only snapshot refresh [#44915825720](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/44915825720), published in commit [602b2848ea29653dc3c28eb9e10950ef0e75bf0f](https://github.com/TrickySturluson/spotify-helper-information-tracker/commit/602b2848ea29653dc3c28eb9e10950ef0e75bf0f), captured 2026-11-21T14:48:41.952453Z with 60 accessible items and 60 unique URIs. Its Spotify snapshot ID matches the completed cycle state. This independently confirms the live playlist read-back after the scheduled write. Draft PR [#200](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/200) adds strict cron-to-Eastern-offset matching and durable before/after snapshots for description-only mutations. Jockey reconciled its existing branch with current main using merge commit [b2de95585fa9656ba86c238ca879d767030e4cfa](https://github.com/TrickySturluson/spotify-helper-information-tracker/commit/b2de95585fa9656ba86c238ca879d767030e4cfa): 41 commits ahead, zero behind, 12 changed paths, mergeable clean. The merge tree preserved main's generated Library, playlist-manager state, and audit files; Jockey did not modify those data paths. Exact-head CI on this commit passed Daily/full tests, broker tests, full-history secret scan, and Cloudflare preview build; the lockfile check was skipped. Preview is not production deployment. Mainline has now demonstrated one real scheduled 60-track publication and a same-date duplicate no-op under the legacy combined-cron gate. Strict cron-to-DST matching remains branch-only until owner-controlled merge. Guided resume/rollback/discard for surviving production stages is the next P0 gap; the approved Daily-specific recommendation event/outcome memory remains P1 and is not implemented.

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

Mainline still declares combined UTC cron expressions `0 4,5 * * *` and `15 4,5 * * *`; it uses the Eastern local-hour gate and same-date completion guard but does not inspect the exact `github.event.schedule` value.

Mainline scheduled cycle [#44901651168](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/44901651168) ran 2026-11-21 11:59 UTC (06:59 Eastern). Its cycle, recovery-snapshot, and state/feedback persistence steps all succeeded. It committed stage [17852545753640e35014caf8df8557beac999add](https://github.com/TrickySturluson/spotify-helper-information-tracker/commit/17852545753640e35014caf8df8557beac999add) and completed state/audit [663291f042dd6ab08f0c48630ebb464ed048c188](https://github.com/TrickySturluson/spotify-helper-information-tracker/commit/663291f042dd6ab08f0c48630ebb464ed048c188). The committed state records Eastern cycle date 2026-11-21, status completed, 60 ordered after-URIs, and after-snapshot ID `AAAAeu09d2bu354ZxalAyWqCpM6Yeye5`.

The later scheduled delivery [#44904728622](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/44904728622) ran at 12:36 UTC (07:36 Eastern). Its cycle step succeeded but the state/feedback persistence step was skipped; the persisted state still points to the first run and remains completed for 2026-11-21, so this is the same-date duplicate no-op rather than a second publication.

GET-only snapshot refresh [#44915825720](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/44915825720), published in commit [602b2848ea29653dc3c28eb9e10950ef0e75bf0f](https://github.com/TrickySturluson/spotify-helper-information-tracker/commit/602b2848ea29653dc3c28eb9e10950ef0e75bf0f), captured 2026-11-21T14:48:41.952453Z with 60 accessible items and 60 unique URIs. Its Spotify snapshot ID matches the completed cycle state. This independently confirms the live playlist read-back after the scheduled write.

This proves one actual scheduled publication and a same-date duplicate no-op on the existing mainline schedule. It does **not** prove which exact cron string matched the active offset, strict DST selection, or repeated multi-day reliability.

Draft PR [#200](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/200) adds strict cron-to-Eastern-offset matching and durable before/after snapshots for description-only mutations. Jockey reconciled its existing branch with current main using merge commit [b2de95585fa9656ba86c238ca879d767030e4cfa](https://github.com/TrickySturluson/spotify-helper-information-tracker/commit/b2de95585fa9656ba86c238ca879d767030e4cfa): 41 commits ahead, zero behind, 12 changed paths, mergeable clean. The merge tree preserved main's generated Library, playlist-manager state, and audit files; Jockey did not modify those data paths. Exact-head CI on this commit passed Daily/full tests, broker tests, full-history secret scan, and Cloudflare preview build; the lockfile check was skipped. Preview is not production deployment.

- During EDT, 04:00/04:15 UTC correspond to 00:00/00:15 Eastern; 05:00/05:15 UTC correspond to 01:00/01:15.
- During EST, 05:00/05:15 UTC correspond to 00:00/00:15 Eastern; 04:00/04:15 UTC are 23:00/23:15 on the preceding Eastern date.
- PR #200 accepts only the cron entries matching the active Eastern offset. The 15-minute matching-offset entry is a catch-up opportunity; the independent date guard prevents a second publication.
- User-owned PR #159 overlaps the schedule gate. Jockey did not modify it or its branch; do not merge it blindly.
- The cooldown persistence fix from PR #168 remains in mainline. The current scheduled success is evidence that the old mainline path can complete, not proof that strict offset selection is deployed.

The repository test-trigger push remains a separate manual hook. Its current setting is read-only `verify-only`; Jockey did not dispatch or change it.

Manual dispatch remains midnight-gated unless `--force` is explicitly supplied. **Force bypasses the clock gate only**; the same-Eastern-date completion guard remains active for full cycles and is checked before Spotify client construction. Force does not bypass ownership, managed-playlist permission, unlock, whitelist/blacklist reconciliation, staging, validation, snapshots, audit, or read-back safeguards.

## Current gaps and verification requirements
- **Guided recovery remains P0:** implement and failure-test audited resume/rollback/discard for a surviving production stage. Recovery must compare the committed stage, backup, current live ordered URIs, description, cycle state, and current blacklist/whitelist before taking any action; partial or conflicting state must fail closed.
- **Strict DST gate remains unmerged:** PR #200 is green and branch-current, but the exact cron-to-offset gate is not on mainline. Owner-controlled merge and a later scheduled run that confirms the accepted/rejected cron decision are still required.
- **Description-only snapshots remain branch-only:** PR #200 adds durable pre/post snapshots and accepted/pending state; no live description-only verification was performed by Jockey.
- The 2026-11-21 scheduled run and same-date duplicate no-op prove one mainline schedule cycle, not sustained reliability across multiple dates.
- Spotify quota can still be exhausted. The workflow now persists Retry-After cooldown state even when discovery fails before staging; do not clear a non-expiring manual-clear state without provider evidence.
- Playback-tracker coverage remains unknown because `playback_data/segments.jsonl` is absent. Last.fm and liked-song observations are distinct evidence; missing playback data is not zero plays.
- Daily recommendation memory is approved but not implemented. Candidate intake and track-level feedback are partial evidence, not a Daily-specific recommendation event/outcome ledger. Historical null evidence must not be backfilled as plays, ignores, or approval.
- Verify current mainline state and latest workflow evidence before changing anything. The guide and roadmap are continuity aids, not substitutes for live read-back.

## Current verified state — 2026-11-21 UTC / 2026-11-21 Eastern

Mainline scheduled cycle [#44901651168](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/44901651168) ran 2026-11-21 11:59 UTC (06:59 Eastern). Its cycle, recovery-snapshot, and state/feedback persistence steps all succeeded. It committed stage [17852545753640e35014caf8df8557beac999add](https://github.com/TrickySturluson/spotify-helper-information-tracker/commit/17852545753640e35014caf8df8557beac999add) and completed state/audit [663291f042dd6ab08f0c48630ebb464ed048c188](https://github.com/TrickySturluson/spotify-helper-information-tracker/commit/663291f042dd6ab08f0c48630ebb464ed048c188). The committed state records Eastern cycle date 2026-11-21, status completed, 60 ordered after-URIs, and after-snapshot ID `AAAAeu09d2bu354ZxalAyWqCpM6Yeye5`.

The immutable stage is `assistant_data/spotify/staging/tricky_daily/2026-11-21-44901651168.json`; the pre-write backup is `playlist_backups/20261121T120059739016Z_4yUVHSMQySfWeEowfIMcx7.json`. The stage contains 60 unique target URIs and 59 pre-write URIs. Its record remains marked `staged_before_spotify_write`; completion is established by the linked manager state (`daily_cycle.status=completed`, `last_cycle_date_eastern=2026-11-21`, `last_completed.backup_run_id=44901651168`) and audit, not by mutating the immutable stage. Recovery code must honor that distinction.

The later scheduled delivery [#44904728622](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/44904728622) ran at 12:36 UTC (07:36 Eastern). Its cycle step succeeded but the state/feedback persistence step was skipped; the persisted state still points to the first run and remains completed for 2026-11-21, so this is the same-date duplicate no-op rather than a second publication.

GET-only snapshot refresh [#44915825720](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/44915825720), published in commit [602b2848ea29653dc3c28eb9e10950ef0e75bf0f](https://github.com/TrickySturluson/spotify-helper-information-tracker/commit/602b2848ea29653dc3c28eb9e10950ef0e75bf0f), captured 2026-11-21T14:48:41.952453Z with 60 accessible items and 60 unique URIs. Its Spotify snapshot ID matches the completed cycle state. This independently confirms the live playlist read-back after the scheduled write.

The live test trigger remains in read-only `verify-only` mode. Jockey did not initiate this scheduled run, perform a Spotify/Last.fm request, modify a playlist, change playlist-manager state/audit, or edit canonical generated Library data.

## Next action

1. Implement audited resume/rollback/discard for a surviving production stage on the existing Jockey branch, with strict live-state classification, current policy rechecks, immutable stage/backup validation, explicit owner confirmation, and regression tests. Do not execute a recovery action in this automation.
2. Keep PR #200 draft-only. Owner-controlled merge is required for strict DST matching and description-only snapshot bracketing; Jockey must not merge, approve, mark ready, or dispatch live workflows.
3. After owner-controlled merge, verify the exact cron-to-offset decision on a scheduled run and continue observing scheduled delivery across dates.
4. Once schedule and recovery acceptance criteria are proven, implement the Daily-specific recommendation event/outcome memory, preserving separate Spotify playback, Last.fm, likes, manual removals, retention, ignored, not-yet-observed, and unknown coverage. Then consult the project-wide roadmap for the next workstream rather than keeping Jockey on Daily indefinitely.

## Related records
[README](README.md) · [ACTIONS](ACTIONS.md) · [Playlist Intelligence umbrella roadmap](../playlist-intelligence/ROADMAP.md) · [Daily cycle guide](../../../docs/TRICKY_DAILY_CYCLE.md) · [Daily backlog](../../../docs/TRICKY_DAILY_TODO.md)