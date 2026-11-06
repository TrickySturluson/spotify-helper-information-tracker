# Listening Analytics & Evidence Sources — Actions & Evidence

Newest entries first. Record verified outcomes separately from plans, assumptions and unverified artifacts.
## 2026-11-06 — Listening/discovery PR branch status rechecked

- PR #158 `feature/discover-weekly-feedback-tracking`: open/non-draft, 9 ahead / 201 behind current main, mergeable=false. Old-head tests #42071650507 and security scan #42071650219 passed; rebase and rerun before review.
- PR #121 `codex/sorter-evaluation-ingestion-watchdog`: open/draft, 10 ahead / 419 behind current main, mergeable=false; no workflow runs found for its observed head.
- Passing old-head checks do not establish compatibility with current main. No code changes or listener/Spotify operations were performed; rebase/implementation review is deferred until documentation completion.



## 2026-11-06 — Discover Weekly observer proposal status verified

- [PR #158](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/158) remains open and unmerged. Its observed full tests and full-history security scan passed. It proposes read-only Discover Weekly exposure, Liked Songs and post-exposure scrobble tracking; do not describe this observer as deployed until merged and verified.
- [PR #121](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/121) remains an open draft and includes a listening-ingestion watchdog specification, not a verified runtime watchdog.

## 2026-11-06 — Update Last.fm History publication also failed on shared-state conflicts

- Run #42146153098 completed its provider/data steps successfully: Last.fm history import, artist genre/mood/theme enrichment, recent-top-200 track tag enrichment, duration prioritization, recording-ID resolution, AcousticBrainz fetch and derived statistics all completed.
- The final publication step failed while rebasing commit `137fab61` ("Update Last.fm history and assistant analytics"). Git reported **120 unique conflicted paths**: 59 canonical music Library files and 61 Spotify playlist snapshots/reference files. The conflict set reflects the concurrent Reference Library commit `3e989e3` changing the same shared generated state.
- The Last.fm import and analytics generated in the workflow workspace were therefore **not published**. Do not update mainline archive counts or claim those enrichment results as canonical.
- This confirms a second shared-writer race in the same incident: Reference Library publication overlapped with the broad Update pipeline. No Spotify playlist writes occurred.
- **Deferred remediation:** shared writer serialization across all workflows touching `assistant_data/music/library/` and `assistant_data/spotify/`; stale-base conflict handling that does not blindly overwrite concurrent state; explicit publication conflict reporting and recovery. Do not fix during the documentation-only phase.

## 2026-11-01 — Goal workspace initialized

- **Action:** established this goal's dedicated documentation and action-history location.
- **Context:** 2026-11-01: Source-of-truth and evidence separation rules consolidated in project handoff. Documentation-only; no new analytics run or fresh counts claimed. Next: preserve these invariants in enrichment, retry priority and recommendation learning.
- **Outcome:** documentation initialized; no runtime implementation or data mutation implied unless explicitly stated above.

## 2026-11-01 — Project-wide audit: duration analytics checklist captured

- **Reference:** open issue #2 https://github.com/TrickySturluson/spotify-helper-information-tracker/issues/2.
- **Outstanding validation:** keep the 3.5-minute legacy estimate as headline all-archive estimate; show verified-duration full-track-equivalent and minimum-qualifying estimates separately; publish duration coverage and unknown-duration counts; include all-scrobble legacy estimates in monthly/yearly buckets; keep measured Spotify tracker intervals separate.
- **Status:** issue checklist says updated workflows/outputs still need to be run and verified. Do not assume checked-in code or previous workflow attempts prove output correctness.
- **Evidence semantics:** Last.fm scrobbles remain historical source of truth. Spotify playback tracker is optional prospective evidence with coverage gaps; missing tracker data is unknown, not zero. Explicit likes/saves, playlist additions, recommendations and inferred preference remain separate.
- **Failed approach / lesson:** never mix estimated time with measured tracker intervals or treat absence of tracker events as zero listening.
- **Outcome:** documentation audit only; no analytics workflow run or fresh counts claimed.
- **Next action:** after migration is verified, run analytics workflows and inspect generated summaries/trend buckets.

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
