## 2026-11-06 — Feedback nuance: high-engagement removals and artist-level penalties

- **Source review:** `load_playlist_feedback()` in `scripts/spotify/spotify_discovery.py` adds one negative artist event whenever a removed track has any positive post-add measured-play or Last.fm-scrobble count. It does not distinguish a single play from many plays or repeated track removals for the same artist.
- **Why this matters:** exact track removals must remain hard exclusions, but a track removed after substantial listening may reflect rotation/freshness rather than dislike of the artist. A single highly played removal currently contributes the same one-count artist-level penalty as a low-exposure removal.
- **Current safeguards:** an unexposed or zero-play removal does not create an artist penalty; measured playback and Last.fm post-add scrobbles remain separate sources; exact URI/key exclusions are preserved independently.
- **Decision needed before runtime change:** design a conservative artist-level aggregation rule (for example, require multiple distinct removed tracks from the same artist, or distinguish low engagement from high engagement) and test the cases explicitly. Do not guess a play-count threshold or let this work weaken exact track blocks. This is a P1 scoring-quality issue, not a current hard-exclusion bypass.
- **Next:** add a regression scenario for a high-play-count single-track removal and multiple distinct removals from one artist; agree on the intended artist-level signal before changing scoring weights.

---

## 2026-11-06 — Retry-After parsing and fail-closed quota recovery merged

- **Merge:** PR [#170](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/170) merged to main as `397218ebf4e397ec4a8fd3a1d1ec6e23aefe8db2`.
- **Behavior:** the manager parses `Retry-After` as either delta-seconds or an HTTP-date and persists a UTC cooldown deadline. If the header is missing or unusable, it writes `manual_clear_required: true` and blocks client initialization and every subsequent API request until an operator verifies the restriction has elapsed and manually clears the state. Timezone-naive persisted cooldown timestamps are rejected.
- **Regression coverage:** added mocked tests for HTTP-date persistence and missing-header fail-closed behavior; the numeric Retry-After test remains active from PR #169.
- **PR verification:** Daily curator tests [#42273342714](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42273342714) passed all 514 tests; public repository security scan [#42273342665](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42273342665) passed.
- **Post-merge:** mainline Daily curator tests [#42273509046](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42273509046) and full-history security scan [#42273509063](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42273509063) both passed.
- **Manual-clear procedure:** when `manual_clear_required` is true, do not delete the file merely to resume work. Verify the 429 restriction has elapsed using authoritative provider/account evidence; then remove `.github/spotify_api_cooldown.json` in a reviewed commit to main. The guard otherwise remains intentionally non-expiring.
- **Safety:** no Spotify/Last.fm/provider request, workflow dispatch, playlist write, description mutation, or generated-data change was performed by this PR.
- **Next:** after the existing cooldown expires, re-check the deadline and run only the protected no-write Daily stage-only verification. A live playlist replacement still requires separate authorization.

---

## 2026-11-06 — Cooldown regression coverage restored and merged

- **Merge:** PR [#169](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/169) merged to main as `8d0d2d5e8b0448fde64932aced1014ef944e3312`. The change is test-only; runtime Spotify manager behavior is unchanged.
- **Defect corrected:** the three existing Retry-After/cooldown tests were previously nested beneath the module-level `if __name__ == "__main__"` guard after `unittest.main()`, so normal unittest discovery did not define them. They now reside in `PlaylistManagerTests` before the entry-point guard.
- **Test fixture corrections:** initialized the `request_metrics` structure on the partially constructed test client and corrected the deterministic formatted duration expectation for 13,060 seconds from 3h 38m to 3h 37m.
- **PR verification:** final PR test run [#42272711018](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42272711018) passed all 512 discovered tests; public repository security scan [#42272711156](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42272711156) passed.
- **Post-merge verification:** mainline Daily curator tests [#42272911280](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42272911280) passed all 512 tests on merge commit `8d0d2d5e8b0448fde64932aced1014ef944e3312`. Mainline full-history security scan [#42272911119](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42272911119) also passed.
- **Outcome:** the previously dormant cooldown regressions are now part of normal test discovery and pass in PR and post-merge CI. No Spotify request, workflow dispatch, playlist mutation, description mutation, or generated-data change was performed.
- **Next:** after the recorded Spotify cooldown expires, re-check the saved deadline and perform only the protected no-write Daily stage-only verification. Live playlist replacement still requires separate authorization.

---

## 2026-11-06 — Retry-After regression tests found outside unittest discovery

- **Finding:** source inspection of tests/test_spotify_playlist_manager.py showed that three existing cooldown tests were indented beneath the module-level if __name__ == "__main__" block, after unittest.main(). They were not defined during normal unittest discovery and therefore did not provide CI coverage for Retry-After persistence, active-cooldown client initialization, or expired-cooldown handling.
- **Correction proposed:** PR [#169](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/169) moves the three existing tests into PlaylistManagerTests before the script-entry guard. Branch: daily-cooldown-test-discovery-fix; head: ab21a2f260a3bad8d4f30ec1934ff2bcfde6bb1a.
- **Read-back:** the branch file was fetched after update; all three methods are class-indented at lines 274, 301 and 312, before the module guard at line 323. PR #169 changes one test file only; no runtime code or workflow behavior changes.
- **CI / correction:** first PR test run [#42272223932](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42272223932) discovered all three tests and ran 512 tests, but failed because the HTTP 429 test constructed a partial `Spotify` object without initializing `request_metrics`; the test failed in `record_request()` before reaching the cooldown assertions. The security scan [#42272224111](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42272224111) passed. The fixture was corrected by initializing the normal metrics structure in commit `2ba8f7423f3c1d28a9ff0f45ccd57902aba57d89`. The next PR test run [#42272539944](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42272539944) again discovered 512 tests but failed because the old assertion expected 3h 38m, while the implementation correctly formats 13,060 seconds as 3h 37m. The assertion was corrected in commit `2417b0a35c3b5887097da5d92e03a371fda4791a`. New PR test/security runs are pending; final pass remains pending.
- **Safety:** no Spotify/Last.fm/provider request, workflow dispatch, playlist write, description mutation, or generated-data change was performed.
- **Next:** inspect PR CI, confirm the cooldown tests are counted and pass, and only then merge the test-only correction. Continue to respect the persisted Spotify cooldown until 2026-11-06T19:49:46Z.

---

## 2026-11-06 — Whitelist contract audit and latest mainline verification

- **Purpose:** close the remaining P0 documentation question around whether a whitelist can accidentally erase unrelated or newer Daily removal decisions.
- **Source review:** inspected current-main `scripts/spotify/spotify_discovery.py`. `reconcile_daily_manual_removals()` honors whitelist URI and normalized primary-artist/title identities when comparing the last accepted-cycle baseline; `load_playlist_feedback()` builds playlist-scoped positive identities and removes only matching removal records from the active negative set; `is_playlist_candidate_blocked()` enforces exact removal identity. Live playlist presence is not approval and does not clear a historical removal.
- **Defined contract:** whitelist is playlist-local and exact-track scoped. URI and normalized primary-artist/title identity are supported match keys. A whitelist does not authorize an artist, another playlist, or unrelated tracks. The current Daily whitelist is empty (0 entries).
- **Regression evidence:** `tests/test_spotify_discovery.py` contains tests for whitelist-aware live reconciliation, re-added removed tracks remaining blocked without explicit whitelist, and explicit whitelist override. These tests support the documented semantics; no runtime behavior was changed.
- **Latest mainline CI:** Daily curator tests [#42270239847](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42270239847) and public repository security scan [#42270239536](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42270239536) both completed successfully on commit `b278da8f4f81bd8202fda50d6ed457e4ccfcb62e`. These runs verify the then-current mainline, including documentation contract and unit tests; they do not verify a live playlist cycle.
- **Latest live state / cooldown:** the last confirmed GET-only Daily snapshot remains 29 accessible unique tracks (workflow #42268795272); baseline 29; blacklist 55; whitelist 0; feedback ledger 60 track rows. Push-triggered stage-only verification run #42268583897 (GitHub event `push`; display title “Trigger safe Daily stage-only durability verification”) failed on Spotify HTTP 429 with Retry-After 5,781 seconds; durable deadline is `2026-11-06T19:49:46+00:00`. It was not a scheduled midnight rotation and no playlist mutation occurred. Do not issue Spotify requests before that deadline.
- **Outcome:** whitelist semantics are implemented and regression-tested; the TODO's P0 whitelist item can be marked complete. No provider call, workflow dispatch, playlist write, or generated-data edit was performed during this audit.
- **Next action:** after the persisted cooldown expires, run the protected no-write stage-only workflow and verify candidate completeness (60), exclusion/deduplication checks, stage commit/push, and committed-blob hash/order read-back. If successful, report readiness and request separate authorization before any live replacement.

---

## 2026-11-06 — Durable Daily staging and publication safeguards

- **Authorization boundary:** all work in this section is code, tests, repository state, and read-only verification. No live Daily track replacement or description mutation was performed or authorized.
- **Pre-write race protection:** the cycle re-reads the exact live playlist immediately before staging and again after the stage commit. It verifies playlist ID/name/owner, description, snapshot ID, complete pagination, ordered pre-write URIs, and unlocked state. Candidate blacklist/whitelist policy is reloaded and rechecked after staging.
- **Immutable staging:** the exact ordered 60-track URI payload, candidate metadata, target description, pre-write snapshot ID/URIs, and recovery backup path are written to a unique JSON stage. The full record is SHA-256 hashed. In GitHub Actions, the stage, backup, audit, candidate/trend/feedback, and removal reconciliation outputs are committed and pushed to main before any Spotify write; the committed blob is read back with git show and re-hashed. A failed commit/push or repository-head advance aborts before Spotify mutation.
- **Same-date recovery guard:** a surviving production stage blocks automatic same-date regeneration/retry. If Spotify's write response is ambiguous, spotify_playlist_cloud.replace_playlist() reads live ordered URIs: exact target means accepted, exact pre-write contents means not applied, and partial/unreadable state raises AmbiguousPlaylistMutationError. The Daily runner persists a same-date idempotency guard for ambiguous/partial outcomes.
- **Post-write verification:** the live read-back must be complete and match the staged ordered URIs exactly, contain 60 unique valid track URIs, valid primary artists, and no current blacklist hits before completion is recorded.
- **Safe stage-only path:** added --stage-only and a test-trigger action that performs the full read-only candidate/pre-write checks, commits and verifies a test-only stage, then exits before any Spotify playlist write or description update. Test stages live under assistant_data/spotify/staging/tricky_daily/tests/ and do not block a production cycle.
- **CI:** full safe run #42268351897 passed 500 tests; generated-data audit and canonical Library health/confidence checks passed. This includes failure-injection coverage for ambiguous write read-back, exact order/blacklist validation, stage hashing/commit failure, repository concurrency, and pending-stage retry blocking.
- **Stage-only attempt:** workflow run #42268583897 authenticated but hit Spotify HTTP 429 QUOTA_EXCEEDED during candidate search (Retry-After: 5781, about 1h36m). It failed before the stage was created or committed. The workflow log explicitly reports that no playlist changes were attempted. Do not retry Spotify reads until the provider cooldown expires.
- **Remaining:** the GitHub Actions stage commit/push has not yet been proven end-to-end because of the quota stop; guided resume/rollback/discard for a surviving stage remains open; no live cycle should run without separate user authorization.

---
## 2026-11-06 — Force guard, description read-back, and Daily-only snapshot refresh

- **Authorization:** user explicitly authorized the Daily runtime/test corrections, safe verification, and a refresh of the Daily snapshot. No live playlist mutation was authorized or performed.
- **Force/idempotency correction:** scripts/spotify/spotify_daily_cycle.py no longer passes args.force to cycle_already_completed(). Force still bypasses the clock gate, but the same-Eastern-date completion guard now applies to forced invocations too. Commit: 18bb798f4df3d2c59c2b4757af2c71cb324490fa.
- **Regression coverage:** tests/test_spotify_daily_cycle_schedule.py now expects the date guard to remain active and adds a forced duplicate-dispatch test that asserts no Spotify client is created. Commit: b38dbe736ed01acaabb223af11265df9e133fd56. Added a test for Spotify HTML-escaped apostrophes in description read-back. Commit: 42a66e99e813ccb7435d1cec50e12f94d8c3374d.
- **Description verification fix:** update_description_and_verify() now HTML-unescapes the Spotify description before comparing it with the expected string. The live snapshot currently contains "Today&#x27;s detour starts here.", while the helper previously compared the encoded value to the literal apostrophe. The Nov 5 audit stops after the replacement was accepted and the state remained replacement_accepted_pending_verification; this mismatch is a concrete likely explanation for the incomplete cycle. Commit: c405757a2528e4e7a6a09e01f9397f3748fea711.
- **Snapshot cadence:** added scripts/spotify/spotify_daily_snapshot.py and .github/workflows/tricky-daily-snapshot-refresh.yml, a Daily-only, GET-only snapshot/reconciliation workflow scheduled for 06:25 UTC. It validates exact playlist identity/ownership and complete item pagination, detects removals against the last accepted-cycle baseline, preserves the old snapshot in history, and advances the baseline only after aligned reconciliation. Commits: dc12dc96fbd1cc9f100edad26666c07beadf60d9 and ffba51873164b431996a90234da8f14d3249b175.
- **Current saved data inspected:** Daily snapshot captured 2026-11-06T14:18:18.958752+00:00; 37 accessible tracks / 37 reported. Removal baseline also has 37 rows and marker 2026-11-05T23:11:08.463502+00:00. Playlist-local blacklist has 47 removed entries and zero whitelisted entries. These are repository snapshot facts, not a new live Spotify request by ChatGPT.
- **Cycle cadence diagnosis:** the last cycle attempt was Nov 5 at 23:11 UTC, replacing 60 tracks; its audit ends immediately after restore_replace_first_page_completed, and persisted state is still pending verification. There is no Nov 6 completed-cycle evidence in the inspected state. Earlier Nov 5 audit shows multiple cycles on the same Eastern date, consistent with the former force/idempotency defect. The new date guard prevents repeat forced rotations on a date already accepted.
- **Verification:** a safe remote regression trigger was updated at commit c1f60aa04e734dc5f79afef50fb79a9941008f1a to run the full test suite and focused schedule tests; the same trigger also starts the read-only Daily preflight. Workflow completion is not yet independently confirmed in this log. The new snapshot workflow was added with a push trigger; its first run/commit is not yet confirmed. Local tests could not be run because this session cannot clone the repository.
- **Outstanding P0:** durable staging, pre-write live snapshot race check, ambiguous-write reconciliation, and exact ordered post-write/blacklist/duplicate validation remain unimplemented. An attempted source update for these safeguards was blocked by the GitHub write safety layer; no claim of completion is made.
- **Next:** confirm remote tests and the first Daily-only snapshot refresh; inspect any newly detected removals; diagnose the next scheduled cycle and keep live track replacement separate until explicitly authorized.

## 2026-11-06 — Resumed parallel SHIT work; Tricky Daily read-only audit

- **Purpose:** begin SHIT feature work while SHIT Documentation & Continuity (Babel) continues in parallel, following the current mainline policy. First candidate workstream: Tricky Daily, whose roadmap identifies force/idempotency as a P0 invariant.
- **Source inspection:** read current-main `scripts/spotify/spotify_daily_cycle.py` (blob `81b0a9c2c8fbd5524ef5991183aa0a2b17ed07fc`) and `tests/test_spotify_daily_cycle_schedule.py` (blob `993ff5c269a45dc39a9eeeee6414da7ac5edb110`). The runner passes `args.force` to both the time-window gate and `cycle_already_completed()`. That function returns `False` when forced, bypassing the same-Eastern-date completion guard. The current test explicitly expects this behavior. It conflicts with the required contract: force bypasses the clock gate only.
- **Other evidence:** the roadmap and cycle guide record a saved 2026-11-06 01:48 UTC snapshot with 58 accessible unique tracks against the 60-track success target. This is historical repository evidence, not a live Spotify read or explanation of the discrepancy.
- **Buddy review:** today's scheduled ChatGPT Buddy run `a1354400-ad1c-8320-906e-888d071012ee` updated draft PR #163 at head `c8e4a2ad74b8c50868a6806abf9869b9da4b5725`. The 13-file diff was inspected. Independent review outcome: NEEDS CHANGES because the draft's AGENTS/Buddy policy language says ChatGPT must never publish directly to `main`, contradicting current mainline documentation-publication authority. No PR reviews or inline threads were present. Daily curator CI #42239266411 and security scan #42239266381 both completed successfully; Buddy reports 478 tests passed.
- **Changes / side effects:** read-only GitHub source/documentation inspection only. No runtime or test files changed; no workflow dispatch, Spotify/provider request, playlist write, generated-data change, secret, or permission change.
- **Authorization boundary:** the runtime/test correction and any live Spotify operation are not performed until separately authorized. Babel remains active in parallel; PR #163 stays draft and must not be merged while its policy contradiction remains.
- **Next action:** obtain user authorization for the smallest Daily force/idempotency correction and regression test, then implement, run focused/full safe tests, and record exact evidence.

# Tricky Daily — Actions & Evidence

Newest entries first. Separate implemented behavior from plans, test evidence, live API acceptance, and independent read-back verification.


## 2026-11-06 — Daily P0 discrepancies and saved-snapshot gap documented

- **Source finding:** `--force` is passed into both `should_run_cycle()` and `cycle_already_completed()`; forced calls bypass the same-Eastern-date completion guard as well as the clock gate. The current schedule test asserts this. This contradicts the intended P0 contract that force bypasses the clock gate only.
- **Saved snapshot:** main's latest Tricky Daily reference snapshot is timestamped `2026-11-06T01:48:00.233040+00:00`, with 58 accessible items and 58 unique URIs. This is below the 60-track success target and is not a live preflight/read-back.
- **Verification boundary:** automatic post-write checks do not yet compare the returned ordered URI list with an immutable staged payload or explicitly recheck blacklist/duplicate invariants against the returned snapshot. The separate verify-only command is stronger but does not prove exact staged-order equality.
- **Disposition:** documented in `docs/TRICKY_DAILY_CYCLE.md`, `docs/TRICKY_DAILY_TODO.md`, `docs/WORKFLOWS.md` and this roadmap. Runtime/test corrections remain deferred until the repository-wide documentation-only pause ends. No playlist or feature changes made.


## 2026-11-06 — Documentation-only pause recorded

- The repository-wide priority remains completion of SHIT Documentation & Continuity (internal codename: Babel).
- The roadmap now separates the current documentation-only next action from the preserved next feature action. Feature plans and acceptance criteria remain intact for later resumption.
- No feature implementation or Spotify playlist operation is part of this documentation update.


## 2026-11-05 — Dedicated Daily workstream documentation created

- **Purpose:** preserve Tricky Daily as an independently resumable active workstream rather than relying only on a long feature backlog nested under Playlist Intelligence.
- **User requirements captured:** exactly 60 unique tracks; absolute removed-track/blacklist protection; whitelist reconciliation; forced-run parity; description refresh on forced runs; bounded retries and artist-diversity relaxation; feedback that distinguishes exposure from preference and handles missing playback coverage neutrally; explicit live verification.
- **Documentation created:** ROADMAP.md defines purpose, invariants, prioritized milestones, acceptance criteria, known verification gaps and next action. README.md maps implementation, workflows, tests and safe resume procedure. Existing docs/TRICKY_DAILY_TODO.md and docs/TRICKY_DAILY_CYCLE.md remain detailed feature references and were not replaced.
- **Implementation status:** documentation references the current maintained Daily modules and workflows. This entry does not claim every P0 item is implemented or that the current live playlist has been verified.
- **Verification:** source documentation and file paths were cross-checked against the repository's Daily cycle guide, TODO, workflow naming and known test modules. Daily curator CI run #42143770161 passed on commit 79af1f93756878d27a40a02c3a2abc4b627643ce after this workspace was added; the full unit-test suite and documentation contract completed successfully. This verifies documentation structure, not live Spotify state.
- **Outcome:** dedicated workspace initialized; runtime behavior unchanged.
- **Next action:** add this goal to the goal index and project roadmap, then let the documentation contract test verify that ROADMAP/README/ACTIONS exist. Audit the latest Daily code and workflow evidence against the P0 checklist.

## Entry template

### YYYY-MM-DD — Action
- **Purpose:**
- **Changes / files:**
- **Execution:** command, workflow run, PR, commit
- **Verification:** exact tests/audits and results, including failures
- **Outcome:** complete / partial / blocked / deferred
- **Failed or abandoned approaches:**
- **Next action:**
- **References:**
## 2026-11-06 — Remote CI findings and live preflight

- **Live preflight:** run #42260095302 passed read-only Spotify authentication and Tricky Daily identity/ownership/access checks. It fetched 29 playlist items across the paginated `sp.items()` reader and reported `playlist_mutation: false`. This is the freshest live item-count evidence currently available.
- **Snapshot mismatch:** saved repository snapshot remains 37 items, captured at 2026-11-06T14:18:18.958752+00:00. It is stale relative to the 29-item live preflight. Do not infer the identity of the eight-item difference. Snapshot-refresh run #42257653420 failed in its focused schedule-test step before credential validation and Spotify GET requests, so it did not refresh the snapshot or removal baseline.
- **CI failures:** remote full-suite and focused verification initially exposed four stale failures (three documentation-contract expectations and one brittle source-count assertion). After updating those, a subsequent run exposed a stale whole-catalogue assertion; the next exposed a stale phrase in the midnight workflow's bottom FILE OVERVIEW. The test and workflow/source comments have now been corrected. Run #42260512826 is the last confirmed failed full-suite run and predates the workflow-comment correction in commit 4cab258d8114571a7fbb49240069a82e74d1335c. A post-fix green run is still required.
- **Snapshot import defect corrected:** run #42261171958 passed its focused schedule tests and credential validation, then failed before any Spotify request because `compat/spotify_listening_trends.py` shadowed the maintained module and caused a circular import. The snapshot script now prioritizes `scripts/spotify/` ahead of `compat/`. New isolated subprocess coverage verifies the actual imported module paths and passed in full suite run #42261959032 (481 tests). The dedicated snapshot workflow's focused gate now includes this regression before Spotify GET refresh. No live snapshot or removal baseline was changed by the failed run.
- **Snapshot refresh and index repair success:** workflow run [#42263830309](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42263830309) passed the focused schedule/import gate, validated credentials, refreshed the live Spotify snapshot, reconciled Daily-only catalog/index memberships, and published the repository state. Current snapshot: 29 accessible/unique tracks, captured `2026-11-06T17:41:02.779553+00:00`; baseline: 29 rows; blacklist: 55 total; whitelist: 0. The earlier 37-item snapshot is retained in history. Reference index now has zero stale or missing Daily track/artist links; the generated-data audit passed in run #42263946943, and the full 481-test suite, remote verification, and read-only preflight passed on the refreshed state. The first reconciliation detected these 8 manual removals: The Best Ever Death Metal Band in Denton (The Mountain Goats), Spanish Sahara (Foals), I Love You, I'm Sorry (Gracie Abrams), Rule #21 - Momento Mori (Fish in a Birdcage), I Turn My Camera On (Spoon), Holly Hobby (Version) (Casiotone For The Painfully Alone), Only You (Ebony Riley), and Maniac (Conan Gray). No Spotify playlist tracks or description were changed.
- **Current safety boundary:** preserve all 55 recorded Daily removals; never restore manually removed tracks merely to reach 60. The GET-only snapshot path is operational. Live replacement remains blocked on durable exact-order staging, pre-write race detection, ambiguous-write read-back, and post-write exact-order/count/uniqueness/blacklist verification, plus separate user authorization.

## 2026-11-06 — Manual-removal outcome feedback and observer repair (current-mainline branch)

- **Implementation:** branch `daily-manual-removal-feedback-current` was created from the latest `main` after the previous attempt exposed unrelated failures caused by its stale base.
- **Feedback:** `spotify_daily_feedback.record_manual_removals()` replays the complete Daily blacklist into feedback history as idempotent `user_removed` events. Existing history is preserved.
- **Snapshot publication:** the GET-only Daily snapshot reconciler calls the feedback reconciler after blacklist reconciliation and publishes `assistant_data/spotify/daily_feedback.json` with snapshot artifacts.
- **Observer repair:** the scheduled feedback observer adds `compat/` to `sys.path` before importing the playlist manager.
- **Regression tests:** cover idempotent event recording, neutral scoring with no observed exposure, negative scoring with measured post-add exposure, and the observer import order.
- **Safety:** no Spotify playlist mutation, no removal whitelist changes, and no conversion of missing playback coverage to zero. The exact blacklist remains independently enforced.
- **Verification:** previous PR #164's full tests and security scan passed, but it was stale; PR #165 exposed two existing Daily stage/repository-head test failures because main advanced after the branch fork. This current-mainline branch requires fresh CI.
- **Next:** inspect fresh CI results, resolve any genuine regressions, and close superseded draft PRs only after this branch is green.

- **Exposure-boundary refinement:** current branch also changes artist-level negative feedback so a manually removed track teaches broader artist dislike only when post-add measured playback or Last.fm scrobbles exist. Exact track blacklist enforcement remains unconditional. Added integration-style tests that load the actual blacklist and feedback JSON: an unexposed removal stays neutral for the artist but remains an exact hard block; measured exposure can inform the artist-level penalty.

- **Unknown exposure-start safety:** adding removal-only rows exposed a Last.fm observer edge case: legacy rows with `first_added_at=null` could raise while comparing scrobble timestamps. The observer now skips post-add attribution when the exposure start is unknown, rather than crashing or inventing a start time. A regression test creates a removal-only row, supplies a matching Last.fm scrobble, and verifies it remains unattributed.

## 2026-11-06 — Quota-aware staged Daily artist discovery

- **Diagnosis:** `spotify_discovery.build_discovery_recommendations()` searched every artist in the 300-artist similar pool on the first Spotify pass. If the pool still failed to yield 60 distinct artists, it then queried deeper pages across all 300 artists. This creates a large Search request burst and is consistent with the observed HTTP 429 quota failure.
- **Change on branch `daily-quota-aware-discovery-current`:** Daily now searches an initial cohort of 80 artists. If fewer than 60 unique candidates are available, it expands cumulative coverage to 160, then 300. Only after exhausting the artist pool does it query deeper result pages and, as a last resort, relax the artist ceiling. General non-Daily discovery is unchanged.
- **Safety:** exact blacklist checks, URI deduplication, the 60-track requirement, and artist-cap fallback semantics remain intact. Candidate generation does not mutate playlists.
- **Tests:** added coverage for the 80 → 160 → 300 cumulative batches and the small-pool single-batch case. Full CI is pending.
- **Next:** verify full CI, inspect Spotify request metrics on the next authorized preview/cycle, and tune the initial cohort only from measured candidate yield. Avoid another large live discovery request until this branch is reviewed.

## 2026-11-06 — Manual-removal feedback merged and exercised by live GET-only snapshot

- **Merge:** PR #166 merged to main as `49d1c61a74a77fb4c7e5d180247f5d8c9eeee7fc`. The branch passed the full 503-test suite and public repository security scan on its final head before merge.
- **Production-path verification:** push-triggered snapshot workflow [#42268795272](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42268795272) passed all steps, including safe regression tests, credential validation, authenticated GET-only snapshot/reconciliation, and publication.
- **Observed result:** snapshot captured `2026-11-06T18:14:16.140845+00:00`; 29 accessible unique tracks; baseline 29; blacklist 55; whitelist 0. The run added 55 manual-removal feedback events; the feedback ledger now contains 60 track rows. Spotify request metrics: 2 GET requests (`/me`, `/playlists/{id}`), 0 playlist mutations.
- **Coverage:** liked-song observation is marked observed and Last.fm coverage available. Playback tracker remains unknown because `playback_data/segments.jsonl` is absent. Do not infer zero plays from this missing tracker file.
- **Outcome:** the new removal feedback path is now merged and has successfully executed in the scheduled snapshot workflow. This does not mean the live playlist is at 60; it remains at 29 accessible tracks. Live replacement remains gated on safe exact-order staging/read-back and quota-aware candidate generation.

## 2026-11-06 — Push-triggered stage-only verification quota failure and candidate preservation

- **Run:** [#42268583897](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42268583897) was triggered by a push (display title: “Trigger safe Daily stage-only durability verification”), not by the schedule. It passed compilation, unit tests, and Spotify credential validation, then failed on its first Spotify artist Search request with HTTP 429 QUOTA_EXCEEDED; Retry-After was 5,781 seconds. The run made no playlist mutations and skipped cycle-state/feedback persistence.
- **Recovery artifact:** the failure-preservation step committed `assistant_data/recommendations/discovery_candidates.json` containing 195 candidate rows / 105 distinct artist names. These are Spotify-resolved rows with 195 unique track URIs across 105 artists: 134 from prior Daily recommendations and 61 from Booze preview runs. Within the Daily-source subset, 55 rows are blacklisted, 29 remain in the current playlist, and 50 are non-current/non-blacklisted. The 61 Booze-source rows have separate playlist context and must not be blindly mixed into Daily. All saved listening-evidence fields are null; this is a historical candidate pool, not a freshly scored or verified 60-track payload.
- **Quota response:** the reported cooldown ended around 2026-11-06 19:49 UTC. Do not retry Search/preview/cycle before the cooldown is confirmed clear.
- **Improvement:** PR #168 implements progressive 80 → 160 → 300 artist search coverage to avoid paying for the full 300-artist Spotify Search burst when the initial cohort can already fill 60 unique tracks.

## 2026-11-06 — Persist Spotify quota cooldown across failed Actions runs

- **Fatal gap found:** the manager correctly wrote Retry-After to `.github/spotify_api_cooldown.json`, but the midnight workflow only committed that file in the accepted-cycle persistence step. When discovery failed before publishing `cycled=true`, that step was skipped. The failure recovery step committed only `discovery_candidates.json`, so the next scheduled workflow could lose the cooldown and retry Spotify while still rate-limited.
- **Fix on branch `daily-quota-aware-discovery-current`:** the always-run recovery step now commits both surfaced candidates and `.github/spotify_api_cooldown.json`, and runs when either file exists. This preserves cooldown state even if discovery fails before producing candidates.
- **Regression:** added a workflow-contract test asserting the cooldown file is persisted under `always()` and included in the step's trigger condition.
- **Safety:** no Spotify request or playlist mutation is performed by the workflow change. It makes the existing fail-closed cooldown durable across scheduled Actions runs.
- **Verification:** full CI pending on PR #168.

## 2026-11-06 — Quota-aware discovery and durable cooldown merged

- **Merge:** PR #168 merged as `232db2e6891b19077843b719cf9cb1cd67bf6356`.
- **Staged discovery:** Daily now searches 80 similar artists initially, doubles cumulative coverage to 160 and then 300 only if the candidate pool cannot fill 60 unique artists. Deeper Spotify result pages are deferred until the available artist pool is exhausted. Other playlist discovery behavior is unchanged.
- **Cooldown persistence:** the midnight workflow's always-run failure recovery now commits `.github/spotify_api_cooldown.json` even when the cycle fails before accepted replacement state. The latest observed 429 from run #42268583897 was also recorded with its 5,781-second Retry-After deadline.
- **Verification:** full 509-test suite passed in run [#42269711590](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42269711590); public repository security scan passed in run [#42269711587](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42269711587). Main-branch post-merge checks are running separately.
- **Safety:** no playlist mutation or Spotify Search request was made by this change. The 60-track target, exact blacklist, whitelist, URI uniqueness, and final artist-cap fallback remain intact.
