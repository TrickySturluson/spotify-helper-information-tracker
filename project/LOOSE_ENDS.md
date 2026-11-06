# SHIT — Consolidated Loose Ends & Verification Register

This is the cross-project register of known unfinished work discovered from the repository, open issues/PRs, workflow status, and prior project conversations. It is a tracking index, not proof that any implementation is complete. Goal-specific histories remain in `goals/<goal>/ACTIONS.md`.

**Last reviewed:** 2026-11-05 (documentation audit checkpoint; domain-specific loose ends below still require individual revalidation)  
**Review scope:** repository structure and workflows, open issues/PRs, relevant prior SHIT conversations and user decisions.

## Documentation-first audit checkpoint — ACTIVE PRIORITY

The user has explicitly directed that documentation be the sole active project priority until the repository is as complete and accurate as reasonably achievable. Do not treat the domain-specific items below as permission to resume feature work during this phase.

- Current main inspected at `b542ceab2c40f6910a91ea3fcb84c204fc412c2d`; subsequent documentation-only commits update NEXT_WORK, the maintainability roadmap/action history, and the project-wide priority order.
- 13 goal workspaces exist and each has ROADMAP.md, README.md and ACTIONS.md. 17 GitHub Actions workflows are listed in `docs/WORKFLOWS.md`.
- The automated documentation contract and file-layout tests passed in Daily curator run #42144512658 on the inspected main SHA; public repository security scan #42144512423 also passed. These results establish test success on that SHA, not semantic accuracy of every document.
- The recursive Git tree API response was truncated by generated per-record Library data. A complete local `git ls-files` inventory remains required for exhaustive path reconciliation.
- Maintained code directories currently enumerate 7 analytics modules, 1 Last.fm module, 24 music modules and 19 Spotify modules. The bottom FILE OVERVIEW presence test also covers compatibility launchers, tests and workflow YAMLs. Manual accuracy review remains open.
- Open Daily PRs observed during the audit: #158, #159 and #160. Their proposed changes are not merged mainline behavior; review their diffs and current status before updating implementation documentation.
- **Remaining documentation work:** complete tracked-file inventory; semantically audit every maintained FILE OVERVIEW; reconcile each technical guide, workflow permission/secret/side-effect description, data schema and goal roadmap against source/tests; update stale domain-specific loose ends with current evidence; add targeted checks for real gaps; complete a fresh-session resume simulation.
- **Status:** documentation architecture and structural guardrails are established; full semantic and operational documentation audit is still in progress. Do not mark this register or the project documentation complete yet.

## Documentation audit — workflow side-effect incident

- Nine workflow YAML bottom overviews were rewritten with specific triggers, credentials, data writes and safety boundaries. This was documentation-only at the file-content level, but the YAML paths themselves matched configured push filters.
- Reference Library workflow #42146148971 completed and committed generated state as `3e989e33282efab6cc1416e35970e7c59af5f056` (249 files; 184 Library records, 63 Spotify snapshot/history files, 2 removal-state files). This was a read-only Spotify snapshot refresh and repository commit, not a Spotify playlist write.
- Update Last.fm History #42146153098, Enrich Music Metadata #42146121471 and Acoustic Metadata Enrichment #42146097964 remained active at last inspection. Record their final outcomes and any generated commits here before considering the incident closed.
- The connected GitHub interface did not expose workflow cancellation. Future workflow-YAML edits must first inspect push-path filters; comment-only edits can start provider and data-writing jobs.

## Additional verified workflow defects from 2026-11-06

- **Reference Library run #42146148971:** completed and committed 249 files as `3e989e33282efab6cc1416e35970e7c59af5f056` (184 Library records, 63 Spotify reference/history files, 2 removal-state files). This was a repository snapshot refresh; no Spotify playlist mutation occurred.
- **Enrich Music Metadata run #42146121471:** provider/enrichment stages completed but publication failed during rebase because canonical song JSON additions conflicted with the simultaneous Reference Library commit. No enrichment workspace output was published.
- **Acoustic Metadata Enrichment run #42146097964:** 100 batches completed (2,500 IDs, 207 found, 2,293 misses, 322 total profiles, 3,678 negative-cache entries). Optional GetSongBPM skipped without its key. Commit failed because the workflow staged a missing optional `assistant_data/music/getsongbpm_lookup_state.json` path. No acoustic output was published.
- **Update Last.fm History run #42146153098:** still active at latest inspection; final result and any commit must be reconciled.
- **Deferred remediation:** serialize shared Library writers / detect stale-base conflicts, and make optional provider output paths conditional before staging. Keep this deferred until documentation acceptance criteria pass.

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


### 6A. Playlist intelligence and five-axis fit model — PREVIEW PIPELINE MERGED; PRODUCTION BLOCKED

- PR #126 merged to main as `2f84924`. It adds the read-only five-target preview pipeline, exact-ID / duration-corroborated identity bridge, explicit scoped artist/release context, and a separate post-hoc human-reference diagnostic. Model version: `five-axis-fit-v0.3`.
- Full CI passed 398 tests; focused preview/comparison tests passed 29; full-history Gitleaks passed. Preview workflow #35 passed: https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41405523394.
- Five calibration targets: To 11, Somber Party, . . ., =^=, Smooth. All Time and Hell remain broad taste references; SHITting Grounds is the separate audition destination and is not in the current reference snapshot.
- 24-track held-out identity batch; Dog — Floating Room was unplayable and excluded. Full batch excluded from all target profiles by Spotify URI and resolved canonical record ID. Human slider ratings are never read by the scorer; the separate comparison runs after frozen prediction generation.
- Direct profile coverage: To 11 0.2, Somber Party 0.0, . . . 0.2, =^= 0.2, Smooth 0.0. Context coverage: 0.2, 0.2, 0.4, 0.4, 0.0. Only Genre has direct evidence (3, 0, 3, 4, 0 tracks). Sound/Energy/Theme are absent; Mood has only sparse context-only evidence. All target profiles remain low confidence.
- 15 candidate tracks score against each of the first four targets; 9 are unknown per target; Smooth has no comparable scores. All 60 scored pairs are low confidence and support only one dimension; 12/15 are context-only. No medium/high prediction exists.
- Human-reference diagnostic: 24/25 tracks matched (unmatched: Dog — Floating Room). Across 60 scored pairs: MAE 26.85, median absolute error 16.79, Pearson 0.4473, Spearman 0.4862. To 11 and =^= have higher rank alignment, but these remain low-confidence genre/context signals, not validation. Human labels are exploratory reference only, not ground truth/training data.
- Preview and diagnostic artifacts: 13122763665 and 13122659752 (expire 2026-11-16). No Spotify API calls or playlist writes.
- **Next:** increase direct recording-level evidence for all five dimensions, especially sound, energy, recording-level mood and lyric-derived theme; improve direct genre coverage. Preserve context scopes and down-weighting. Inspect provider cooldowns/failures before retries. Keep scorer disconnected from sequencer and Spotify writes until coverage/confidence gates pass.

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
- Automatic playlist descriptions: generator and tests are present, but periodic/cloud invocation is not yet wired. Manual descriptions must remain untouched; next work is safe preview/confirmation and bounded scheduling for managed playlists only.


### Booze five-axis integration — AUDIT MERGED; LIVE SORT BLOCKED ON EVIDENCE

- PR #127 merged (`ad391369`); read-only five-axis audit artifact 13124415230 (expires 2026-11-16). Saved snapshot has 64 tracks; current live preview has 72, so refresh/persist snapshot and regenerate candidate manifest before using the audit as a current baseline.
- Current model evidence is insufficient for automatic decisions: 32/64 tracks score per calibration target, all low-confidence and one-axis; 31/32 are artist-context genre only; 32/64 unknown. Only 2/64 Booze track-profile rows have Last.fm tags; zero lyrics, direct mood, recognized energy; one sparse audio-profile match.
- Live sequence preview run #41407486669: 72 tracks; 48 reorder operations; 8 unassigned; 0 gentle/moderate/supported potential jumps; 71 transitions limited-evidence; 62 low-confidence, 10 unknown. No Spotify changes made. Do not confirm this sequence.
- Next: refresh snapshot; bounded provider-aware recording-level enrichment; explicit Halloween-theme review; substantial verified additions; rerun and inspect the full sequence; only then consider confirmation-gated sorting.


### 2026-11-02 — Recommendation batch workflow

- Run #41408232279 failed in `booze20_preview` due to `NameError: time is not defined`; fixed by importing `time` in `scripts/spotify/spotify_playlist_cloud.py` (commit `5730e78`). No playlist write occurred.
- Resolved Booze candidates now get persisted to `assistant_data/recommendations/discovery_candidates.json` via `append_candidates`, with a source/context event and audit count. This is discovery evidence, not a claim that the track was listened to or that the canonical Library has completed enrichment.
- Verify with a fresh live `booze20_preview` run, then inspect candidate rows and compare all proposed additions against the live playlist and removed-track blacklist. Follow any confirmed addition with a new live sequence preview; do not automatically apply reorder operations while confidence remains low.


### 2026-11-02 — Discovery-to-Library automation wired; first run pending

- `.github/workflows/enrich-music-metadata.yml` now runs canonical Library sync after metadata enrichment and before summary/analytics generation. It triggers on changes to discovery intake, ingestion, sync code, or its own workflow; the daily scheduled enrichment also includes the merge.
- `scripts/music/sync_music_library.py` merges Spotify-ID candidates into the canonical Library via `MusicLibrary.put_catalogue`, preserving `discovery_only` and separate discovery evidence; it does not create plays/scrobbles or inferred likes.
- Sync is audit-gated (`audit.ok` must be true). Initial implementation commits: `0703e77`, metric correction `f5d9b7a`.
- The baseline test run for `6666be0` passed, but the new workflow integration still needs a live Actions run. Inspect it before calling this complete.
- Remaining gap: candidate metadata enrichment is bounded by existing provider jobs and may not enrich every discovery-only record in the same cycle. Add explicit coverage reporting/retry queue for discovery-only rows with missing album, duration, tags, lyrics/theme or mood evidence. Do not falsely mark unavailable provider fields as complete.

### Recommendation removal feedback — fix published, CI pending

- **Fixed:** exact playlist-local removed-track filtering is now applied to both curated Booze and legacy horror previews. The discovery helper checks exact artist/title key or Spotify URI. A track currently present in that same playlist is whitelisted before filtering.
- **Preserved semantics:** Tricky Daily still treats removals as soft scoring penalties; artist-only removal is not a blanket artist blacklist. Curated manual candidate batches hard-skip only exact track/URI removals.
- **Commits:** `92f86c7`, `ea97b6c`, `7196fdd`. Regression tests cover exact block, URI block, whitelist after re-add, and block while absent.
- **Data:** Booze has 3 removal records; none match the 15-track batch already added. That earlier batch was resolved before this guard existed; no retroactive filtering claim.
- **Status:** ready for verification; CI runs #41415718003/#41415724736/#41415730381 pending at last check. Next: inspect final CI, then use a fresh read-only preview to verify live feedback counts.

