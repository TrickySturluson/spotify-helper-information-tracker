# SHIT — Consolidated Loose Ends & Verification Register

This is the cross-project register of known unfinished work discovered from the repository, open issues/PRs, workflow status, and prior project conversations. It is a tracking index, not proof that any implementation is complete. Goal-specific histories remain in `goals/<goal>/ACTIONS.md`.

**Last reviewed:** 2026-11-06 (default branch main at 80546ae51aeccda56efc6d0b1be554d41baa3c73; Buddy branch/PR state independently rechecked before this batch)  
**Review scope:** current main, documentation work, workflow outcomes, committed-tree inventory, open PRs and high-risk operational contracts.

## Scheduled ChatGPT Buddy — CURRENT PATH; PR #163 DRAFT

- The current recurring path is the scheduled ChatGPT task **SHIT Buddy — daily Babel continuation**, using the connected GitHub app. It is separate from the repository-hosted Codex/API experiment below and does not depend on that workflow or an OpenAI API key.
- The persistent branch babel/chatgpt-buddy and one open draft PR #163 already existed. Before this batch, PR #163 targeted main, was six commits ahead/one behind, and GitHub reported mergeable_state=clean. Its pre-batch head 2090ad97648851f5138856795600f4e582849efb passed Daily curator tests [#42188373512](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42188373512) and the public repository security scan [#42188373527](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42188373527). These are prior-head checks only; the new batch needs its own PR CI.
- The proposed mandatory daily Buddy-check rule is present in PR #163's branch but is **not merged mainline policy** until the user reviews and merges the draft.
- **PR #162, separate temporary connectivity proof:** remains open/draft and was not modified. Its security scan [#42186485000](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42186485000) passed; Daily curator tests [#42186485002](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42186485002) failed because the PR-only guide docs/BABEL_SCHEDULED_TASK_CONNECTIVITY_TEST.md is missing from docs/README.md, triggering test_documentation_index_lists_every_technical_guide. The user retains the decision to retain or close this proof PR.
- **PR #161, existing documentation delivery:** remains open/draft with 117 changed files, 2,330 additions and 493 deletions. Current compare reports 571 commits ahead and 135 behind main; GitHub reports mergeable_state=dirty. Its historical Daily curator tests [#42165157006](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42165157006) and security scan [#42165156989](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42165156989) passed on its own old head, but there are no submitted reviews or review threads. Do not merge or rebase wholesale; use it only as an audit/reference source.
- **Next:** keep PR #163 draft, inspect its updated head/CI after this batch, and continue the semantic documentation audit. Do not modify PR #161 or #162.

## Repository-hosted Codex worker — INTEGRATED; RUNNER FIX VERIFIED; API QUOTA BLOCKER (SEPARATE PATH)

- The separate Codex workflow configuration and its ChatGPT-initiated push trigger are committed. The user reports `OPENAI_API_KEY` is configured and Actions is allowed to create pull requests.
- First run [#42181953313](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42181953313): preflight passed; Codex failed before prompt execution on Ubuntu 26.04 during `drop-sudo` D-Bus socket restriction. This matches [upstream issue #188](https://github.com/openai/codex-action/issues/188).
- The Codex job is pinned to `ubuntu-24.04` with `drop-sudo` retained. Retry [#42183337573](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42183337573) passed preflight and sandbox isolation, then Codex returned `Quota exceeded. Check your plan and billing details.` Validation and publisher were skipped; no Codex proposal PR was produced.
- **Current authorization:** no API spend or retry is authorized. Do not ask the user to add credits or trigger the Codex workflow. Revisit only if the user explicitly reauthorizes this separate API-based experiment; never switch to `unsafe`.
- Repository tests/security are green on the runner-fix commit: Daily curator run [#42183307146](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42183307146) passed 478 tests; security scan [#42183307047](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42183307047) passed.
- The repository-hosted Codex worker remains integrated but not operationally verified; it is a separate API-based experiment, not the current scheduled ChatGPT Buddy path. See [docs/BABEL_AGENT.md](../docs/BABEL_AGENT.md).
## Documentation-first audit checkpoint — ACTIVE PRIORITY

The user explicitly requires documentation to be the sole active project priority until SHIT Documentation & Continuity (internal codename: Babel) meets its acceptance criteria. Do not treat any domain-specific feature backlog below as authorization to resume implementation.

- **Audit baseline:** `aacb70fa0345369398c9bd049d00e24a9ca09eb6`; subsequent same-session commits contain documentation-only audit updates. Canonical documentation identity: [docs/BABEL.md](../docs/BABEL.md).
- **Structure:** all 13 goal workspaces have ROADMAP.md, README.md and ACTIONS.md. The 12 non-documentation roadmaps now separate the current documentation-only action from their preserved next feature action.
- **Per-file overview baseline:** 28 known generic/underspecified implementation overviews were corrected. Current maintained inventory: 55 Python implementation modules, 40 compatibility launchers, 44 test modules, 18 current workflow YAMLs and 21 technical guides. Presence and known-placeholder regression checks cover scripts, compat, tests and workflows; semantic accuracy is still under audit.
- **Complete inventory:** verified at commit `aacb70fa` using a non-recursive root tree and nine recursive directory-scoped tree queries. Every directory result returned `truncated=false`. Total: **28,241 file/blob entries**; `assistant_data/` contains 27,981. The inventory acceptance item is satisfied for that snapshot; refresh after structural changes.
- **CI/security:** Daily curator run #42168520574 passed all 460 tests on `8153028e`; full-history Gitleaks scan #42168520598 passed on the same commit. These results verify automated checks, not semantic correctness of every guide.
- **Enrichment workflow incident — RESOLVED:** Enrich Music Metadata run #42166959478 completed successfully and published commit `aacb70fa`. It merged 195 discovery candidates into the canonical Library, whose audit reported 13,239 songs. Duration coverage is 8,254/11,130 tracks and 139,758/152,005 scrobbles (91.9%). MusicBrainz added 67 duration matches from 182 lookups; artist profiles: 3,373 matched; track profiles with sourced tags: 229; matched album profiles: 905. Final integrity audit: 9 checks, 18 warnings, 0 errors. The warnings are a lack of captured playback intervals and 16 Spotify playlists whose item contents were inaccessible; preserved snapshots may be stale. No Spotify playlist was modified.
- **Open documentation PR #161:** open/draft, 117 changed files, 2,330 additions and 493 deletions. Its branch is divergent from current main (571 commits ahead, 135 behind); it is not safe to merge blindly. Use it as an audit/reference source and selectively port reviewed documentation/tests. Its checks passed on its own branch, not on current main.
- **Other open feature PRs:** #158, #159, #160, #120, #121, #65 and #60 remain proposals. Their behavior is not merged mainline behavior.

## Newly verified high-risk documentation findings

- **Tricky Daily force/idempotency P0:** current `--force` bypasses both the clock gate and same-Eastern-date completion guard; the schedule test currently codifies this. Intended contract: force bypasses the time window only. The implementation/test correction remains deferred until the documentation-only pause ends.
- **Tricky Daily snapshot and post-write gap:** saved snapshot at `2026-11-06T01:48:00.233040+00:00` contains 58 accessible, unique URIs, below the 60-track success target. It is not a live read-back. Automatic post-write verification also lacks exact ordered staged-payload comparison and explicit returned-snapshot blacklist/duplicate rechecks; the verify-only path is stronger but still does not compare exact staging.
- **Stale Library migration report:** latest canonical audit in run #42166959478 reported 13,239 songs, while `assistant_data/music/library/migration_report.json` still records 13,005 from the 2026-11-01 migration. Treat the report as historical until a safe generated-report refresh is planned after the documentation pause.
- **Resolver write boundary:** `MusicLibrary()` may rebuild/write `library_index.json` when the index is missing, empty or incomplete. Use `library health` for strictly read-only structural checks.
- **Credential verification write boundary:** Great Migration `verify` can persist a replacement Spotify refresh token to the repository Actions secret through the narrowly scoped GitHub App. Local verification does not persist it; cloud verification is not purely read-only.
- **Great Migration preflight boundary — source-audited:** `preview` and `prepare-preview` execute the full migrator's `--dry-run` path, which returns before resolver construction, backup creation or canonical Library writes. They make no provider requests and no Spotify playlist writes. A regression test now protects this distinction; CI is pending.
- **Playlist snapshot evidence:** Reference Library sync writes repository snapshots and canonical Library source context but does not mutate Spotify playlists. Membership is not a play, like, save, scrobble or measured playback event. Sixteen playlist item snapshots were inaccessible in the latest enrichment audit; retained contents may be stale.

## Remaining documentation work

1. Complete source-to-document semantic review across all 55 implementation modules, 40 compatibility launchers, 44 tests, 18 workflows and 21 technical guides.
2. Correct high-risk mismatches: Daily force/idempotency, Library resolver/index rebuild writes, Spotify snapshot-versus-listening evidence, Great Migration token rotation and backup boundaries, and Reference Library schedule.
3. Port and adapt PR #161's useful regression checks for workflow budgets/allowlists, local Markdown links, paused roadmaps, and high-risk side-effect contracts. Do not import stale branch assertions without checking current source.
4. Reconcile all goal roadmaps, data schemas/provenance, workflow permissions/trigger filters/publication behavior, open PRs/issues and domain-specific loose ends.
5. Complete the fresh-session resume simulation. Until it passes, do not mark Babel complete or resume feature/provider/playlist work.


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

