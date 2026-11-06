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