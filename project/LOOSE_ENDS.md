# SHIT — Consolidated Loose Ends & Verification Register

This is the cross-project register of known unfinished work discovered from the repository, open issues/PRs, workflow status, and prior project conversations. It is a tracking index, not proof that any implementation is complete. Goal-specific histories remain in `goals/<goal>/ACTIONS.md`.

**Last reviewed:** 2026-11-01  
**Review scope:** repository structure and workflows, open issues/PRs, relevant prior SHIT conversations and user decisions.

## Critical path

### 1. Great Migration run #17 recovery — BLOCKED
- Run: https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41357689889
- Known: Git rebase/publication failed due conflicts between generated Library records and indexes. An artifact and backup were produced.
- Unknown: which prepare/migration/enrichment/audit stages completed, whether the artifact passed a final audit, and which generated records actually reached `main`.
- Next: inspect logs, artifact and backup; compare with current main; preserve newer valid records; fix concurrent generated-data publication; run a fresh audit; publish only after passing.
- Safety: no force-push, blind conflict resolution, competing write-heavy run, or Spotify playlist writes during recovery.

### 2. Read-only coverage planner — PR #65, tests failing
- PR: https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/65 (open draft).
- Observed checks: compile, generated-data audit, and maintained-documentation check passed; unit-test step failed. Secret-history scan passed.
- Failure details have not yet been diagnosed. Do not assume the planner is valid or schema-compatible.
- Next: inspect failing unit-test output, repair, verify deterministic/read-only behavior and real Library/checkpoint schemas, then regenerate and inspect report output.
- The retry queue remains a specification, not an implemented/executed queue.

### 3. Recommendation intake — PR #60, tests and secret scan failing
- PR: https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/60 (open, not merged).
- Observed checks: compile, generated-data audit, and maintained-documentation check passed; unit-test step failed. Full-history secret scan also failed.
- Failure details and whether the secret finding is real, historical, or a false positive are not yet diagnosed. Do not suppress findings without investigation.
- Next: inspect sanitized test output and redacted secret-scan findings; fix tests and resolve any real secret exposure safely; re-run both checks; review candidate deduplication, canonical identity linkage, provenance, and separation from listening evidence.

## Metadata and canonical Library

### 4. Finish post-migration enrichment and coverage measurement
- No fresh, post-publication coverage report has been verified.
- Historical conversational estimates included artist 1,587; track 9,778; album 6,384; unresolved duration 2,919, but these are stale/unverified snapshots and must not be presented as current counts.
- Prior known gaps: lyrics unpopulated; MusicBrainz experienced 503/rate-limit failures; Discogs and GetSongBPM depend on optional credentials; AcousticBrainz required timeout-resilience work.
- Next: after migration publication, run read-only coverage by entity and field; distinguish populated, pending, ambiguous, unavailable, low-confidence, transient failure, and credential-blocked. Record provider usability from actual recent runs, not assumptions.
- Never repeatedly fetch unavailable providers or treat transient errors as definitive not-found.

### 5. Provider-aware retry queue
- Spec: `project/RETRY_QUEUE_SPEC.md`; intended machine path: `assistant_data/music/retry_queue.json`.
- Still to implement/verify: one task per recording + provider + data family; deterministic planner; no network or mutation in planning mode; bounded executor only after planner passes.
- Preserve separate statuses for eligible, retry_wait, not_found, ambiguous, complete, blocked, invalid. Track attempts, cooldown/next-eligible time, reason, priority, evidence and confidence.
- A provider failure must not block independent providers. Transient timeout/rate-limit/network/parse/provider outages are not definitive not-found.

### 6. Enrichment content still to build out
- Recording IDs/MBIDs and alias resolution; duration; audio/acoustic features; track-level tags, mood and themes; album tracklists/descriptions/release context; artist profiles/genres; artwork references where useful.
- User requested song-level mood/theme rather than assigning an artist's identity to every track.
- Lyrics-derived enrichment should use permitted compact tags/features and source provenance, never store full copyrighted lyrics. User previously wanted multiple lyric sources plus local lookup considered; availability/coverage and source policy still need assessment.
- Preserve field-level source, confidence, timestamp and evidence. Unknown stays unknown. Keep recording, album and artist as separate entities.

## Listening analytics

### 7. Duration and listening-time reporting — open issue #2
- Issue: https://github.com/TrickySturluson/spotify-helper-information-tracker/issues/2
- Explicit requirements still unchecked:
  - Keep the 3.5-minute legacy estimate as headline all-archive estimate.
  - Show verified-duration full-track-equivalent and minimum-qualifying estimates separately.
  - Publish duration coverage and unknown-duration counts alongside estimates.
  - Add all-scrobble legacy estimates to monthly and yearly trend buckets.
  - Keep measured Spotify tracker intervals separate from estimates.
- Updated workflows were to be run and outputs verified; the issue checklist still records this as not validated.
- Preserve Last.fm scrobbles as historical source of truth. Spotify playback tracker is optional prospective evidence with coverage gaps; missing tracker data is unknown, not zero.

### 8. Listening evidence semantics
- Keep Last.fm scrobbles, Spotify tracker events, explicit likes/saves, playlist additions/removals, recommendations/exposure and inferred preference as distinct event types.
- A recommendation is not a play; a play is weak positive evidence, not a like. An unplayed daily candidate is not automatically negative feedback.
- Ensure analytics and recommendation ranking never double-count event types or infer complete tracker coverage.

## Discovery and recommendation product

### 9. Deep-Cut Explorer and daily rotating discovery — open issue #2
- Identify artists with meaningful listening frequency but only 1–5 distinct archive tracks; suggest standout/popular tracks and deeper cuts.
- Candidate sources include Last.fm artist top tracks and similar-artist/track signals.
- Exclude archive-heard tracks from unheard discovery; one-scrobble tracks should be labelled previously heard, not new.
- Candidate scoring should retain inspectable reasons and use artist affinity, tag overlap, recency, familiarity, popularity baseline and taste overlap.
- Initial daily mix was proposed as 40% familiar-but-unexplored artists, 40% new taste-matched artists, 20% adventurous picks; treat as tunable starting weights.
- Persist recommendation history and suppress repeats; measure later scrobbles as feedback without treating a play as an explicit like.
- Resolve candidate tracks to Spotify URIs with match confidence before playlist delivery; keep writes explicitly authorized and previewed.

### 10. Capture every recommendation/candidate
- User requirement: every song SHIT suggests, recommends, surfaces, or receives as a discovery candidate should be eligible for canonical Library intake, even if never played or saved.
- Preserve source/provider, prompt/seed/context, capture time, identity confidence and subsequent observable response (accepted, added, saved, played later, rejected, ignored, unknown).
- Deduplicate against Spotify IDs, ISRCs, recording MBIDs and aliases. Keep candidate evidence separate from listening and preference.

## Playlist intelligence and safety

### 11. Sorter and daily learner validation
- Smooth adjacent transitions are the primary objective; no harsh/jarring changes. Support gradual energy/BPM/loudness progression, mood/theme/genre sections, controllable peak placement (roughly 80–90% default concept) and a smooth resolution.
- Need trustworthy audio features and track-level mood/theme; don't rely on artist-wide mood labels.
- Daily learner should weigh actual plays and explicit likes distinctly; avoid over-weighting tracks simply because they appeared in Tricky Daily. Liked tracks can be down-ranked when requested, not categorically excluded.
- Keep generated playlists locked by default, personal playlists read-only unless explicitly authorized, preview before writes, and preserve audit/state/blacklist/deduplication.
- Tricky Daily is the approved exception: `4yUVHSMQySfWeEowfIMcx7`. This does not grant blanket playlist-write permission.
- Booze or Boos!: `4diIlnF8BlgoJrwUfejf49`. User's target is an energetic, fun Halloween party list with a strong Halloween connection for every track (murder/monster/slasher/vampire/creature themes; campy, dark-playful, chaotic, danceable/metal energy). Avoid sad-victim/apocalypse mood and generic novelty staples previously rejected. Verify live contents before edits; a prior user report said 66 tracks while project data may have been stale.
- Outstanding playlist control issue #4 records a sequence-preview command for Booze or Boos!: https://github.com/TrickySturluson/spotify-helper-information-tracker/issues/4. Reconcile with current sorter and live playlist state before action.

### 12. Playlist data correctness
- Verify removal blacklist and deduplication behavior, including duplicate reporting and removed-track persistence.
- Validate playlist cloud snapshots and live counts against Spotify; don't treat stale project snapshots as current.
- Confirm Tricky Daily rotating description/rotation behavior and don't let unplayed daily tracks become negative feedback.

## Maintainability, workflows and operational safety

### 13. Per-file documentation coverage
- Current script inventory includes analytics, Last.fm, music and Spotify modules; workflow inventory includes migration, enrichment, duration backfill, acoustic enrichment, playlist manager, daily cycle/feedback, reference library and update/security workflows.
- Existing `scripts/README.md` is a directory overview, not proof every individual module has the requested bottom-of-file overview.
- Audit every maintained Python script and workflow for purpose, inputs/outputs, side effects, data paths, safety boundaries, run/test instructions and how it fits into SHIT. Add concise in-file overviews consistently; do not add prose to machine-readable JSON.
- Verify docs coverage with an automated check and test it.

### 14. Workflow concurrency and generated-data publication
- Migration run #17 exposes a publication race/conflict between generated Library records and indexes.
- Inspect workflow concurrency groups, checkout/rebase/commit/push behavior, artifact publication, and other workflows that write shared generated paths.
- Define a single-writer or serialization strategy and stale-base detection; preserve unrelated newer valid data. Add a regression test or workflow-level verification before another large migration publish.

### 15. Public repository / security
- Keep public repo read-only in intent; never commit credentials, tokens, private account data, or full copyrighted lyrics.
- PR #60's secret scan failure must be investigated before merge. PR #67's secret-history scan passed.
- Keep sanitized logs; never paste credential values into issues, project notes, or ChatGPT.

## Open work references
- PR #67 goal workspaces: merged as commit `4ad701c2c4f36b9f6f73926e83db1f84cbfbcc2c`; tests and secret-history scan passed.
- PR #65 coverage planner: open draft; tests failing, secret scan passing.
- PR #60 discovery ingestion: open; tests and secret scan failing.
- Issues #63/#64/#62/#61/#59/#57 are repeated Great Migration prepare requests/status records. Consolidate their authoritative state after run #17 recovery; do not assume each issue means a separate completed run.
- Issue #58 is the next-phase enrichment + recommendation-ingestion specification.
- Issue #2 is the broader discovery/deep-cut and duration analytics backlog.
- Issue #4 is the Booze or Boos! sequence-preview request.

## Review discipline
For every item, record status as **not started / in progress / blocked / ready for verification / verified / deferred**. Link evidence. Do not mark a task verified based only on a PR description, stale conversation count, successful compile, or artifact that has not been published and audited.
