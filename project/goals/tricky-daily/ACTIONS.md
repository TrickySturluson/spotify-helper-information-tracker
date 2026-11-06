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

## 2026-11-06 — Quota-aware staged Daily artist discovery

- **Diagnosis:** `spotify_discovery.build_discovery_recommendations()` searched every artist in the 300-artist similar pool on the first Spotify pass. If the pool still failed to yield 60 distinct artists, it then queried deeper pages across all 300 artists. This creates a large Search request burst and is consistent with the observed HTTP 429 quota failure.
- **Change on branch `daily-quota-aware-discovery`:** Daily now searches an initial cohort of 80 artists. If fewer than 60 unique candidates are available, it expands cumulative coverage to 160, then 300. Only after exhausting the artist pool does it query deeper result pages and, as a last resort, relax the artist ceiling. General non-Daily discovery is unchanged.
- **Safety:** exact blacklist checks, URI deduplication, the 60-track requirement, and artist-cap fallback semantics remain intact. Candidate generation does not mutate playlists.
- **Tests:** added coverage for the 80 → 160 → 300 cumulative batches and the small-pool single-batch case. Full CI is pending.
- **Next:** verify full CI, inspect Spotify request metrics on the next authorized preview/cycle, and tune the initial cohort only from measured candidate yield. Avoid another large live discovery request until this branch is reviewed.
