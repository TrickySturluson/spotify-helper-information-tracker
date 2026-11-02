# Playlist Intelligence & Safety — Actions & Evidence

Newest entries first. Record verified outcomes separately from plans, assumptions and unverified artifacts.

## 2026-11-01 — Goal workspace initialized

- **Action:** established this goal's dedicated documentation and action-history location.
- **Context:** 2026-11-01: Sorting, daily learner, generated-playlist safety and transition goals consolidated. No playlist changes made by this documentation. Next: after migration recovery, inspect sorter state/tests and run preview before any authorized write.
- **Outcome:** documentation initialized; no runtime implementation or data mutation implied unless explicitly stated above.

## 2026-11-01 — Project-wide audit: playlist loose ends consolidated

- **References:** Tricky Daily `4yUVHSMQySfWeEowfIMcx7`; Booze or Boos! `4diIlnF8BlgoJrwUfejf49`; open sequence-preview issue #4 https://github.com/TrickySturluson/spotify-helper-information-tracker/issues/4.
- **Sorter requirements:** smooth adjacent transitions are primary; avoid jarring changes; gradual energy/BPM/loudness movement; mood/theme/genre sections; configurable peak placement (roughly 80–90% default concept); smooth resolution.
- **Learner requirements:** use actual plays and explicit likes distinctly; do not treat unplayed Tricky Daily tracks as negative feedback; liked tracks may be down-ranked, not automatically excluded.
- **Booze or Boos! constraints:** energetic, fun Halloween party list; every track should have a strong Halloween connection (murder/monster/slasher/vampire/creature themes), with campy/dark-playful/chaotic/danceable/metal energy. Avoid sad-victim/apocalypse mood and generic novelty staples previously rejected. A prior user report said 66 tracks while project state may have been stale; recheck live Spotify before edits.
- **Safety:** generated playlists only by default; personal playlists read-only absent explicit authorization; Tricky Daily is an approved exception, not blanket write permission. Preview and audit before writes. No playlist writes during migration recovery.
- **Outstanding:** reconcile issue #4 sequence preview with current sorter and live playlist; validate dedupe/removal blacklist persistence, live counts versus snapshots, and daily description rotation.
- **Failed approach / lesson:** stale local playlist snapshots and unplayed daily placements are not reliable current counts or negative preference evidence.
- **Outcome:** documentation only; no Spotify playlist changes.
- **Next action:** after migration recovery, inspect sorter/tests/state and preview before any explicitly authorized write.

## Entry template

### YYYY-MM-DD — Action
- **Purpose:**
- **Changes / files:**
- **Execution:** command, workflow run, PR, commit
- **Verification:** exact tests/audits, including failing steps and diagnostic evidence
- **Outcome:** complete / partial / blocked / deferred
- **Failed or abandoned approaches:** what was tried/rejected and why; never omit meaningful failures
- **Performance / provider limits:** latency, request volume, cooldowns, quotas, caching, or inefficiencies observed
- **Lessons learned / decision changes:**
- **Next action:**
- **References:**



## 2026-11-02 — Offline evaluation work resumed

- **Purpose:** advance the existing evidence-aware sequencer without waiting for complete metadata coverage or making live playlist changes.
- **Changes / files:** added [OFFLINE_EVALUATION.md](OFFLINE_EVALUATION.md), defining baseline-vs-sequenced comparison, evidence coverage, confidence, uncertainty, transition diagnostics, peak-position variants, determinism, and performance reporting.
- **Execution:** branch `codex/sorter-evaluation-ingestion-watchdog`.
- **Verification:** existing implementation and tests inspected; test suite has not yet been executed in this environment. No evaluation report has yet been generated.
- **Outcome:** partial; evaluation contract documented, runtime evaluation pending.
- **Failed or abandoned approaches:** none.
- **Performance / provider limits:** evaluation is offline; no provider requests.
- **Lessons learned / decision changes:** metadata completeness is not a prerequisite for useful sorter development; unknown evidence must remain visible and must not be treated as a mismatch.
- **Next action:** execute sequencer tests, inspect preview CLI, generate deterministic real-snapshot evaluation report, fix concrete failures.
- **References:** [OFFLINE_EVALUATION.md](OFFLINE_EVALUATION.md).


## 2026-11-02 — Real-snapshot offline evaluation harness added

- **Purpose:** test the sequencer against the user's broad taste references rather than relying only on synthetic fixtures or assuming playlist titles define narrow themes.
- **Changes / files:** added `tests/test_spotify_playlist_reference_evaluation.py` on `codex/sorter-evaluation-ingestion-watchdog`. It reads the checked-in All Time (51/51) and Hell (1,388/1,388) snapshots, loads Library-first metadata with the sequencer's legacy per-record fallback, reports full-catalogue field/confidence coverage, compares original-order and sequenced transitions, and summarizes track theme/genre groups.
- **Evaluation scope:** All Time is fully ordered; Hell's full catalogue is scored and its deterministic 192-track evenly-spaced sample is ordered to keep the optimizer bounded. Both are explicitly treated as broad taste references, not single-theme labels.
- **Safety:** snapshot-only, offline and read-only. No Spotify authorization, provider calls, playlist changes, or Library writes. The test asserts exact URI preservation and zero write/request counters.
- **Verification:** test file committed as `8b71a1536cebe65285b3e2a2ec8a95586e8cf6ba`. GitHub Actions run lookup has not yet returned an associated run; runtime outcome is pending and must not be reported as passed until logs confirm it.
- **Outcome:** implementation added; CI/runtime verification pending.
- **Next action:** inspect the pull-request test run and its emitted `OFFLINE_PLAYLIST_REFERENCE_EVALUATION` JSON; diagnose any failures, then decide whether to expand peak-position comparisons and add a compact report artifact.
- **References:** [All Time](https://open.spotify.com/playlist/6ZsqAs5OnRMVudhfB2QzTx), [Hell](https://open.spotify.com/playlist/3XQz9AyZP6ADcr9i8iBaVx), `tests/test_spotify_playlist_reference_evaluation.py`.
