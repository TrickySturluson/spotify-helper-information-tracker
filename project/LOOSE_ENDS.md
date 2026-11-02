# SHIT — Consolidated Loose Ends & Verification Register

This is the cross-project register of known unfinished work discovered from the repository, open issues/PRs, workflow status, and prior project conversations. It is a tracking index, not proof that any implementation is complete. Goal-specific histories remain in `goals/<goal>/ACTIONS.md`.

**Last reviewed:** 2026-11-02 (after PR #100 freshness baseline, duration provenance recovery work, and issue #105 preview trigger)  
**Review scope:** repository structure and workflows, open issues/PRs, relevant prior SHIT conversations and user decisions.

## Critical path

### 1. Great Migration — FULL CATALOGUE PUBLISHED; STRUCTURAL HEALTH VERIFIED

- Per-recording Library structure merged in PR #49. Full canonical catalogue is published on `main`: 13,005 songs, 6,386 artists, 7,861 albums.
- Legacy source coverage: 11,130/11,130 track IDs resolve through source-track/recording-MBID aliases; 5,358/5,358 legacy artist names represented.
- Run #18 published enrichment commit `c55012f`. Run #21 later used stale issue-event SHA `b892f3b`, repeated work from stale checkpoints, and failed publication; its output was not pushed. Workflow fix `21cc2ed` checks out latest `main` before migration.
- Issue #92 / run 41372492615 passed canonical audit and full structural health: zero errors/warnings. It also validated the merged playability checks.
- Latest enrichment coverage still needs a fresh measurement. Historical run #18: approx. 91.1% duration coverage, 115 audio profiles, 1,778 track profiles, 3,998 artist profiles, 400 album profiles, zero lyric features. MusicBrainz had rate-limit/503 issues; Last.fm tag lookups returned HTTP 400; Discogs/GetSongBPM credentials absent.
- No Spotify playlist writes. Do not start concurrent migration writers or force-push generated data.

### 2. Library health checker and data maintainer — AUTOMATED READ-ONLY MONITORING

- PR #73 health checker merged; PR #80 index-only maintainer merged. Full-catalogue preview #85 and issue #93 both found no repair needed, no alias loss, zero errors/warnings, zero writes.
- PR #87 merged market-aware playability validation. Issue #92 passed full catalogue with zero health errors/warnings.
- Weekly Sunday workflow now runs health, confidence, read-only maintenance preview, and freshness planning; reports retained as 30-day artifacts. Maintenance is preview-only; no automatic repairs.
- Repair scope remains derived-index-only and requires explicit apply, alias-preservation proof, backup, atomic write and post-repair health/rollback.

### 3. Metadata freshness and partial revalidation — BASELINE ROTATION MERGED; PROVENANCE RECOVERY IN PROGRESS

- PR #81 planner, PR #86 CLI/weekly workflow, and PR #100 unknown-age baseline rotation are merged. PR #100 passed full CI/security (344 tests); issue #101 validated full-catalogue planning.
- Baseline result before duration provenance recovery: 6,613 data-bearing unknown-age observations, 25 selected weekly (all Last.fm duration); 0 stale/due; 33,689 no-data fields; 1,856 missing duration provenance; 1,362 cooldown skips. Planning is read-only: provider_requests=0, writes=0. Unknown age is not automatically stale.
- **Provenance gap found:** At the Gates — Slaughter of the Soul has duration 183,000 ms and source Last.fm track.getInfo in canonical song JSON but no timestamp. Exact legacy shard row has `metadata_checked_at=1793324246`, `metadata_status=matched`, `retry_after=0` (2026-10-30T01:37:26Z). At least some of the 6,613 unknown-age candidates are migration omissions, not overdue lookups.
- Issue #103 tracks exact legacy timestamp recovery. Added `scripts/music/backfill_duration_observations.py`, `python shit.py library duration-evidence` (preview default), freshness-planner support for matching duration observations, and health validation for the new evidence. Apply requires `--apply --yes`, exact ID/duration/source/matched status, backup, atomic writes and post-write health/rollback.
- Issue #104 preview initially failed because the CLI action had not yet been registered; fixed in commit `46fc6ad`. Issue #105 preview passed: 8,121 exact Last.fm duration observations across 8,121 songs; zero alias/duration/source/duplicate conflicts; 2,958 unrecognized-provider rows and 51 invalid/missing timestamps skipped; safe_to_apply=true. Issue #106 is queued for backup-protected apply.
- No generic provider-backed freshness executor is enabled. Do not execute the 25-item baseline refresh until existing timestamps have been recovered and the remaining genuinely unknown-age set is measured.

### 4. Confidence verification and duplicate-entity review

- PR #88 merged missing-vs-mismatch confidence classification. Issue #92: identity confidence drift 0; metadata differences are 1,582 missing stored duration confidence and 0 genuine mismatches.
- Curated [identity review set](goals/library-confidence-verification/IDENTITY_REVIEW_SET.md) includes a verified recording-MBID song, a high-confidence Spotify-ID song with market-scoped playability, and a low-confidence source-track-only song.
- Concrete duplicate candidate: Candy Claws has a verified MBID artist and an empty name-fallback artist; the same album has enriched and empty fallback records. Spotify track `spotify:0lw2mlzncwftftvdojdysg` carries the enriched album's exact Spotify album ID but points to the fallback album.
- Issue #102 tracks a read-only duplicate artist/album/song audit. Do not merge on name alone or delete records. Preserve release editions, references, source IDs, listening context, playability history and provenance.

### 5. Spotify playability — SNAPSHOT BACKFILL AND HEALTH VALIDATED

- PRs #72 and #78 merged. Offline snapshot backfill run #82 stored 3,305 market-scoped observations across 1,856 song records: 3,250 playable and 55 unplayable; zero API requests and playlist writes.
- Observations live under `evidence.spotify_playability` and preserve market, checked_at, requested/returned/relinked IDs and status. They are snapshot-time evidence, not a timeless boolean.
- PR #87 health checks validate observation shape, status/raw boolean, market, timestamp, identity/relink continuity and latest-by-market. Issue #92 passed.
- Live Get Track refresh is separate: 25 default, max 50, 90-day TTL, dry-run by default, explicit execute confirmation. No live playability refresh has been executed.

### 6. Remaining enrichment and provider-aware retry queue

- No fresh post-publication provider-coverage report has been verified. Re-measure duration, track tags, artist/album profiles, acoustic/audio features, lyrics-derived compact tags, and provider availability after the provenance backfill.
- Do not repeat Last.fm HTTP 400, MusicBrainz 503/rate-limit, or credential-blocked Discogs/GetSongBPM requests without changed inputs, expired cooldown, or confirmed provider recovery.
- Retry queue spec: `project/RETRY_QUEUE_SPEC.md`; intended path `assistant_data/music/retry_queue.json`. Still to implement/verify: one task per recording + provider + data family; deterministic read-only planner; separate eligible, retry_wait, not_found, ambiguous, complete, blocked, invalid; attempt history and next-eligible timestamps.
- A failure at one provider must not block independent providers. Transient errors are not definitive not-found. Keep all provider budgets and checkpoints durable.

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


## 2026-11-02 — Latest checkpoint after second duration provenance pass

- The ISO-8601 timestamp parser now accepts timezone-qualified strings and still rejects timezone-naive values. Issue #113 preview found 8,172 exact timestamped matches across 32 shards / 11,130 rows; 8,121 were already backfilled and 51 additional MusicBrainz observations were eligible. All alias, file, duration, source, status, timestamp, and duplicate conflict counts were zero; 2,958 unknown-provider rows skipped; no network calls or preview writes.
- Issue #114 apply reported success and 51 changed song files, a backup, post-write health success, zero provider requests, and zero playlist writes. Independent read of a published song JSON confirmed a new MusicBrainz duration observation is on `main`.
- Fresh post-publication checks queued: #115 audit, #116 health, #117 freshness review, #118 combined audit/health/confidence. Results are pending; don't infer completion from issue creation.
- Remaining work: inspect the fresh unknown-age baseline; audit duplicate artist/album/song candidates (especially the Candy Claws exact Spotify-album cross-link); implement the provider-aware durable retry queue in `assistant_data/music/retry_queue.json` per [`RETRY_QUEUE_SPEC.md`](RETRY_QUEUE_SPEC.md); then review provider coverage and only execute eligible bounded enrichment. Sorter evaluation remains gated. No provider or playlist writes are authorized by these read-only tasks.