# Tricky Daily — Actions & Evidence

Newest entries first. Separate implemented behavior from plans, test evidence, live API acceptance, and independent read-back verification.
## 2026-11-06 — Daily-related PR branches are stale/diverged from current main

- Live PR inspection: #159 `fix/tricky-daily-schedule-gate` is open/non-draft, 6 commits ahead and 201 behind current main, mergeable=false; old-head Daily tests #42091662410 and security scan #42091662609 passed.
- PR #160 `daily-exposure-aware-discovery` is open/non-draft, 27 ahead / 201 behind, mergeable=false; old-head tests #42081994195 and security scan #42081994125 passed.
- PR #158 `feature/discover-weekly-feedback-tracking` is open/non-draft, 9 ahead / 201 behind, mergeable=false; old-head tests #42071650507 and security scan #42071650219 passed.
- These checks ran on their stale branch heads, not current main. The proposals remain unmerged and must be rebased and reverified after the documentation-only pause. No feature work or PR merge is authorized during this phase.



## 2026-11-06 — Latest saved Daily snapshot is below the 60-track target

- **Evidence:** `assistant_data/spotify/playlists/4yUVHSMQySfWeEowfIMcx7.json`, captured `2026-11-06T01:48:00.233040+00:00`, reports 58 items, 58 fetched, 58 unique track URIs, accessible, and no item error.
- **Requirement:** a successful Tricky Daily cycle should contain exactly 60 unique valid tracks.
- **Interpretation:** the saved snapshot is below target, but it does not establish why the playlist had 58 items or whether the playlist changed afterward. Do not label this a cycle failure without reconciling cycle state, audit and a fresh read-only preflight.
- **Safety:** documentation/evidence review only. No live Spotify request, playlist mutation, candidate push or repair was performed.
- **Next action after documentation completion:** inspect fresh live preflight, manager state/audit and cycle state; reconcile the discrepancy before any authorized write.


## 2026-11-06 — Forced Daily run bypasses the same-date idempotency guard

- **Finding:** source inspection of `scripts/spotify/spotify_daily_cycle.py` found that `--force` is passed to both `should_run_cycle()` and `cycle_already_completed()`. The latter returns `False` immediately for `force=True`, so a forced invocation bypasses the same-Eastern-date completion guard as well as the clock-window gate.
- **Test evidence:** `tests/test_spotify_daily_cycle_schedule.py::test_cycle_date_guard_skips_already_completed_eastern_date` explicitly asserts `cycle_already_completed(..., force=True)` is false. The current test therefore codifies the broader behavior.
- **Requirement conflict:** the user-facing P0 contract in this roadmap/TODO is that force bypasses the clock gate only; same-date idempotency, blacklist/whitelist reconciliation and all safety/verification checks must remain active. This is an unresolved P0 implementation mismatch, not an approved exception.
- **Documentation changes:** updated `docs/WORKFLOWS.md`, `docs/TRICKY_DAILY_CYCLE.md`, `docs/TRICKY_DAILY_TODO.md`, this roadmap and README to distinguish actual behavior from the intended contract. Added a documentation regression test so the mismatch is not silently erased from the handoff.
- **Safety:** no code, test behavior, workflow schedule or Spotify playlist was changed. Feature correction is deferred until the repository-wide documentation-only pause ends.
- **Next action after documentation completion:** change `cycle_already_completed()` so force bypasses only the clock-window gate; update the schedule test to require a same-date forced invocation to remain blocked; then run the full Daily tests and a safe preview before any live cycle.


## 2026-11-06 — Open Daily proposals and CI status reconciled

- [PR #159](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/159) remains open and unmerged. Its observed full tests and full-history security scan passed; it proposes strict cron-to-Eastern-offset gating beyond the current combined cron/local-hour behavior.
- [PR #160](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/160) remains open and unmerged. Its observed tests and security scan passed; exposure-decay ranking, 45/30/25 composition and the new read-only Daily quality report are proposals, not mainline behavior.
- The Daily cycle guide was corrected to describe current mainline scheduling and explicitly distinguish PR #159's proposed stricter DST gate. No Daily cycle, Spotify request or playlist write was performed.

## 2026-11-06 — Daily proposals and live-playlist safety status

- PR #158 (Discover Weekly exposure/feedback), #159 (DST schedule gating) and #160 (exposure-aware discovery) remain open proposals, not merged behavior.
- No Tricky Daily playlist mutation, cycle, description change or candidate push was performed as part of this documentation audit. The accidental Reference Library refresh was read-only against Spotify but did update the repository's Daily removal blacklist: it recorded two manual removals from the 2026-11-05 pre-cycle live snapshot, Joseph Dubay — `Loser Boy` and Mal Blum — `Fine!`, in `playlist_removed_tracks.json` for playlist `4yUVHSMQySfWeEowfIMcx7`. These are user-removal protections, not automation removals or inferred dislikes.
- Daily feature work remains paused until the documentation-only acceptance criteria pass.


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
