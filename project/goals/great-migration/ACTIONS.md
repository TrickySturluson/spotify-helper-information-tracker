## 2026-11-02 — Duration provenance preview passed; exact backfill queued

- Issue #105 `duration-evidence-preview` completed successfully on latest main (workflow run 41375146233).
- Scanned all 32 legacy artist shards and 13,005 canonical song records; 11,130 legacy rows.
- 8,121 rows had valid timestamps and matched canonical songs exactly by alias, duration value, and duration source with `metadata_status=matched`. The plan would add 8,121 append-only duration observations across 8,121 song files.
- Conflicts: 0 missing aliases, 0 ambiguous aliases, 0 missing song files, 0 duration mismatches, 0 source mismatches, 0 non-matched statuses, 0 conflicting duplicate legacy IDs.
- Skipped safely: 2,958 unrecognized-provider rows and 51 invalid/missing timestamps. No guesses.
- `safe_to_apply=true`; provider_requests=0, writes=0, spotify_playlist_writes=0. Preview created no backup and changed no files.
- Added workflow operation `duration-evidence-apply` to require `--apply --yes`, preserve backup artifact, run post-write health/rollback, and publish only `assistant_data/music/library/`.
- Issue #106 is queued to apply the 8,121 exact matches. At this entry, no canonical song files have yet been modified.
- Next: confirm #106 commits successfully and the backup artifact is present; then run independent health/audit and freshness review to measure how many of the 6,613 unknown-age baseline candidates remain. Do not run provider refresh until that post-backfill plan is inspected.

## 2026-11-02 — Add exact legacy duration-observation provenance recovery

- Investigation of the 6,613 unknown-age duration candidates found a canonical/legacy mismatch: At the Gates — Slaughter of the Soul (`mbid:14c4ff34-27e4-491d-8c65-c1773a1bea46`) has duration 183,000 ms and source `Last.fm track.getInfo` in its canonical song file but no check timestamp; the exact legacy row in `assistant_data/music/artists/shard-18.json` has the same duration/source, `metadata_checked_at=1793324246`, `metadata_status=matched`, `retry_after=0` (2026-10-30T01:37:26Z).
- This indicates freshness provenance was dropped during migration for at least some rows. The 6,613 unknown-age candidates must not be treated as stale or re-fetched until this provenance is recovered.
- Issue #103 records the required exact-ID/value/source match and safe backfill.
- Added `scripts/music/backfill_duration_observations.py`: read-only by default; resolves legacy rows through canonical source-track/recording-MBID aliases; requires exact duration and source match plus a successful matched status; adds append-only `evidence.track_metadata.duration_observations`; skips conflicts; apply requires `--apply --yes`, timestamped backup, atomic writes, and post-write health check.
- Updated `metadata_freshness.py` to age duration from the latest matching provider/duration/source observation, separate from Last.fm tag timestamps.
- Updated `library_health.py` to validate duration observation structure/provider/source/timestamp/value/retry fields.
- Exposed CLI `python shit.py library duration-evidence` (preview default) and added tests for exact matches, mismatch/duplicate handling, newer observations, no-write preview, backup and rollback.
- Added workflow command `[SHIT LIBRARY] duration-evidence-preview`; issue #104 is running a full-catalogue read-only preview. At this entry, no apply has been run and no canonical song files have been changed.
- No provider requests or Spotify playlist writes.

**Next:** inspect issue #104's full preview report. If exact match coverage is high and conflicting duplicate/ambiguous alias counts are zero, run the backup-protected missing-only backfill, then verify health and freshness baseline reduction. Do not run the weekly baseline executor until after timestamp recovery.

## 2026-11-02 — Merge rotating freshness baseline and verify clean branch

- PR #100 merged to main as `61cc5c0b108559746443a4ad8d83bf2ec2ca97d8`; superseded PRs #95 and #97 were closed.
- PR CI passed: 344 tests, compile, generated-data audit, full Library health/confidence/freshness checks, documentation tests; public repository security scan passed.
- Issue #101 validated the clean rebased branch on latest main: full compile and 344 tests passed; native freshness CLI accepted `--include-unknown-age`; full catalogue 13,005 songs / 6,386 artists / 7,861 albums.
- Freshness baseline: 6,613 data-bearing unknown-age candidates; 25 selected (all Last.fm duration); 0 stale/due; 33,689 no-data fields; 1,856 missing duration provenance; 1,362 cooldown skips; 0 invalid timestamps; 0 blocked; provider_requests=0, writes=0.
- Weekly workflow now includes the read-only maintenance preview and unknown-age baseline plan. No provider-backed refresh executor is enabled; no provider requests or Library writes occurred.
- New issue #102 tracks a read-only duplicate artist/album/song audit after identifying a Candy Claws name-fallback artist/album pair that is internally consistent but likely duplicates the verified MBID/Spotify-ID entities. No records were merged or changed.

## 2026-11-02 — Verify safe maintainer preview and add prepare preflight command

- Issue #93 `maintain-preview` completed successfully on latest main: health clean (0 errors/warnings); current and proposed counts match at 13,005 songs, 6,386 artists, 7,861 albums; `repair_needed=false`; `safe_to_rebuild=true`; no IDs/aliases would be lost; `changed=false`; provider_requests=0; spotify_playlist_writes=0. No repair or backup was created.
- Added `prepare-preview` to `.github/workflows/great-migration.yml`. It invokes `python shit.py library prepare --skip-spotify-refresh` without `--execute` or `--yes`, so it is a safe read-only preflight distinct from the provider-running `prepare` operation. Commit `f69f64c`.
- Issue #94 `prepare-preview` completed successfully. It confirmed legacy archive coverage 11,130/11,130 track IDs and 5,358/5,358 artist names; existing Library 13,005 songs / 6,386 artists / 7,861 albums; 1,778 track profiles, 3,998 artist profiles, 400 album profiles, 115 audio profiles, zero lyric features; 57 snapshots with 16 inaccessible; 3,306 playlist occurrences / 1,856 unique Spotify IDs; combined input rows 3,634. Provider caps were reported; optional Discogs/GetSongBPM credentials remain absent. Provider requests=0, writes=0, Spotify playlist writes=0.
- This preflight does not yet provide a per-provider due-task count, so it is not sufficient by itself to justify another full prepare. It does establish that the existing source and checkpoint data are present and the current catalogue remains intact.
- PR #95 (`feature/freshness-baseline-rotation`) adds the next freshness improvement: distinguish no-data from data-bearing-but-undated fields, report missing duration provenance separately, and rotate a deterministic 25-item unknown-age baseline weekly without treating it as stale. Its first CI run failed because `--include-unknown-age` was declared twice in argparse; the duplicate declaration was removed in branch commit `e7b2bac` and a follow-up docs commit is on the branch. No passing post-fix CI run has been observed yet; do not merge until full tests and security scan pass.
- No migration/enrichment run, provider lookup, Spotify snapshot refresh, Library write, or playlist write was performed by issues #93/#94.

**Next:** obtain a passing CI run for PR #95; inspect the post-fix freshness planner's full-catalogue output (due vs unknown-age baseline vs no-data vs missing provenance); only then consider a small provider-backed executor. Keep full prepare paused until provider due-work is demonstrated.

---

## 2026-11-02 — Post-merge full-catalogue verification passed (issue #92)

- Latest-main workflow run [#30](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41372492615) completed successfully after PR #87 and #88 merged.
- Compile and full regression suite passed; canonical integrity audit: 13,005 songs, 6,386 artists, 7,861 albums, zero errors.
- Structural health: 13,005 song/6,386 artist/7,861 album records; index counts match; 1,856 Spotify IDs, 11,338 recording MBIDs, 1,816 ISRCs, 13,003 source-track IDs, 11,529 name-candidate aliases; zero errors and zero warnings. New playability-history semantic checks passed across the populated catalogue.
- Confidence: identity high 7,525 / low 5,480; methods 5,669 recording MBIDs, 5,480 source-track IDs, 1,856 Spotify IDs; identity drift 0.
- Metadata confidence: 1,582 differences are all **missing stored duration confidence**; genuine mismatches=0. This confirms no existing stored metadata confidence disagrees with recomputation in this report.
- Field coverage: duration 10,028; track tags 179; audio features 36; Spotify playability 1,856. Missing duration provenance count 1,856. Legacy source coverage remains 11,130/11,130 tracks and 5,358/5,358 artists. No errors.
- Read-only operation; no provider requests, repairs, confidence writes, or Spotify playlist writes.
- The full-catalogue health and identity confidence baseline is now verified after the new checks. Remaining confidence work is to understand missing duration provenance and decide whether safe missing-only confidence materialization is worthwhile, then perform curated gold-set review.

## 2026-11-02 — Merge playability health validation and confidence drift classification; run freshness baseline

- PR #87 merged to `main` as `6c9fe067a8af6bc504548bc45e715ed27aa0cea8`. The read-only health checker now validates market-scoped Spotify playability history: observation shape, status/raw boolean consistency, timestamps, market keys, requested/canonical identity, relink continuity, and latest-by-market consistency. Missing playability remains optional; malformed present evidence is an error.
- PR #88 merged to `main` as `67ab44f17a1c94093e4a71328abded6b80d66455`. Confidence audit now separates missing stored metadata confidence from genuine stored/recomputed mismatches, with per-field counts/examples. It remains read-only.
- Both PR heads passed the full Daily curator CI (compile, generated-data audit, full-catalogue health/confidence/freshness steps, documentation checks, and tests) and the public repository security scan before merge.
- Issue #90 `freshness-review` completed successfully on main. It scanned 13,005 songs, 6,386 artists, and 7,861 albums; recognized 1,856 Spotify IDs; saw 1,778 track-profile rows, 3,998 artist-profile rows, and 400 album-profile rows. Results: 8,799 fresh observations, 0 stale/due tasks, 0 missing playability observations, 42,158 missing field/provider timestamps, 1,184 cooldown skips, 0 invalid timestamps, 0 blocked tasks, and 0 errors. The bounded selection was 0/25; provider requests=0 and writes=0.
- Interpretation: the 42,158 missing-timestamp count is **not** 42,158 confirmed stale fields. Missing/undated evidence is deliberately not aged from file modification times and is not scheduled blindly. The next improvement is to distinguish absent metadata, present-but-undated metadata, and provider attempts with no usable result, then backfill trustworthy observation timestamps from existing checkpoints/cache evidence where possible.
- Weekly read-only freshness workflow is merged (PR #86); the manual `freshness-review` operation also works. No provider-backed generic metadata executor is enabled.
- Issue #92 was opened after both merges for a fresh full-catalogue audit/health/confidence verification including the new playability semantic checks and missing-vs-mismatch confidence breakdown. At the time of this entry it had no result comment; completion is not claimed.
- Spotify playability is stored per song under `evidence.spotify_playability`, market-scoped and append-only. Offline backfill run #82 recorded 3,250 playable and 55 unplayable observations across 1,856 canonical song records from saved snapshots; these are snapshot-time results, not current live availability.
- No Spotify playlist writes, live provider refreshes, Library repairs, or confidence rewrites were performed in this entry.

**Next:** inspect issue #92; classify undated field coverage and confidence missing/mismatch counts; only then implement a bounded provider-backed executor that consumes durable provider cooldowns/checkpoints. Keep live Spotify playability refresh separately capped (25 default, max 50, 90-day TTL, explicit execute confirmation).

---

## 2026-11-02 — Verify maintainer against the published catalogue

- Issue #85 full-catalogue `maintain-preview` succeeded after fixing direct-script imports in `library_maintenance.py`.
- Read-only health was clean: 13,005 songs, 6,386 artists, 7,861 albums; zero errors and zero warnings.
- Proposed index counts exactly matched current counts. All existing entity IDs and aliases were reconstructable; no records or aliases would be lost; `safe_to_rebuild=true`.
- `repair_needed=false`; no repair, backup, provider request, or playlist write occurred.
- This confirms the current canonical index is healthy and the maintainer can preview the entire catalogue without mutation.

## 2026-11-02 — Publish offline Spotify playability backfill

- Merged PR #78 (`e12b72e`) for market-aware playability observations, offline backfill, and bounded stale-only refresh.
- Added `backfill-playability` and `verify-catalogue` operations to `.github/workflows/great-migration.yml`.
- Issue #82 triggered successful run [41369906166](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41369906166).
- Backfill read 57 saved playlist snapshots (16 inaccessible), scanned 3,308 items, found 3,308 observations, matched 3,306, updated 3,305 observations across 1,856 canonical song records; 2 items unmatched and 0 already present.
- Snapshot statuses: 3,250 playable, 55 unplayable; all 3,305 observations were tagged `market=from_token`. No restriction reasons or relinked IDs occurred in this batch. These are snapshot-time observations, not live current availability guarantees.
- Provider requests: 0. Spotify playlist writes: 0. Timestamped backup directory was preserved in artifact #13108782697 and excluded from the canonical Library commit.
- Published commit: `3316dbe9f8ccd5d668b71d730016befeabdd8502` (1,856 song files changed).
- Run #82's final job was successful and its issue comment reported the exact backfill summary. A separate post-backfill `audit`, `health`, and `confidence` verification is queued as issue #83; do not call post-backfill verification complete until that run finishes.
- No live Spotify playability refresh was executed.

## 2026-11-02 — Merge Library maintainer and add freshness planner

- PR #80 merged to main as `f74e8ba3de296da8b9fe14e3f7f357d8247bc1d4`; adds read-only maintenance preview and explicit backup-protected index-only repair. No real Library repair was applied.
- PR #81 adds a read-only field-level freshness planner on draft branch `feature/metadata-freshness-planner`. Full CI ran the planner against all 13,005 songs, selected 25 of 1,856 due playability tasks, passed all 318 tests, and passed the secret scan. This was before the offline playability backfill; the plan should be re-run against post-backfill main after integration.
- Planner uses explicit observation timestamps, field-specific TTL defaults, cooldowns, stable tie-breaks, and no network/write behavior. Generic field observation timestamps are not yet populated by existing enrichers; do not enable generic provider polling until the schema is reconciled with real provider checkpoints and retry queue.
- Next: verify issue #83; review/merge freshness planner only after integrating current-main changes and validating the post-backfill due plan; continue with field-level freshness ingestion and bounded execution.

## 2026-11-02 — Permanent legacy archive coverage report (PR #79)

- Adds source-index coverage measurements to migration_report.json: all legacy unique track IDs must resolve to canonical source-track or recording-MBID aliases; artist identities resolve by stable ID or exact normalized name.
- Replaces the misleading limitation text with the correct boundary: the Library stores normalized song entities; raw Last.fm scrobble events remain in the separate event archive.
- Adds fixture tests for MBID aliases, source-track aliases, and artist ID/name matching.
- PR #74 is now merged, so current-base CI includes the full-catalogue confidence audit.
- Branch: feature/migration-coverage-report-v2; CI pending.
## 2026-11-02 — Diagnose failed checkpoint-resuming run #21 and fix stale checkout

- **Run #21:** [41364361982](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41364361982) completed the requested prepare operation and final runner-side audit successfully (13,005 songs, 6,386 artists, 7,861 albums; zero audit errors), but the publish step failed during rebase. Artifact #13107866614 uploaded (47,678,297 bytes; 54,558 files), preserving the generated state and backup.
- **Root cause:** issue-triggered runs checked out the issue-event SHA, not the latest main at job start. Issue #71 was opened before run #18 published commit c55012f. Run #21 therefore started from stale commit b892f3b and attempted to rebase its generated music data over the newer run #18 state. Rebase produced conflicts in hundreds of canonical song files and provider checkpoints; no conflict was force-resolved and nothing from run #21 was published.
- **Wasted work identified:** because it started from old checkpoints, run #21 repeated much of run #18's enrichment: 100 artist-profile lookups, 100 album-profile lookups, 198 Last.fm track-tag lookups, 119 MusicBrainz track-tag lookups, and 20 AcousticBrainz batches (500 batch slots). The final profile counts matched run #18 (1,778 track profiles, 3,998 artist profiles, 400 album profiles, 115 audio profiles); duration lookups were 0 due and no duration matches were added. This was redundant work caused by the stale checkout, not a reason to rerun the same batch.
- **Workflow fix:** changed `.github/workflows/great-migration.yml` to explicitly check out `ref: main` before migration. Commit `21cc2edf5a527b9d9ddbbf708c4c181774945682`. This ensures the run sees the latest published canonical records and checkpoints before planning provider work, and should avoid the same stale-base conflicts.
- **Permanent coverage report fix in progress:** draft branch `feature/migration-coverage-report` adds legacy track/artist source-index coverage to `migration_report.json` and removes the misleading sentence that the entire raw scrobble archive must be duplicated into track_profiles. The Library is an entity catalogue; raw scrobble events remain separate.
- **Next:** complete CI for the coverage-report change; once merged, create one new `[SHIT LIBRARY] prepare` request from the latest-main workflow, then wait for completion and run a separate published-branch audit/health check. Do not enqueue another request before the current operation reaches terminal state.
- **Safety:** no generated output from failed run #21 was pushed. The artifact remains available for recovery/comparison. No Spotify playlist writes.
## 2026-11-02 — Verify published catalogue coverage and successful enrichment publication

- **Run #18:** [41364145298](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41364145298) completed successfully. Compile and full regression suite passed; prepare's final canonical audit passed with zero errors; publish step pushed commit c55012f1d9707d9059be9096d0be88dbf50b1bcb to main; artifact #13107605034 uploaded (46,841,540 bytes; 54,558 files). The report/issue comment and full job log were inspected.
- **Correction to earlier recovery narrative:** the full catalogue was already present on main before run #18. Index history shows the Library expanded from the 100-song PR #49 sample to 11,149 songs at commit c0f48e97ac96a7c83fcf817332103371f94b1d8a, then to 13,005 songs at 351095395a801fde221f98b069c0daca781aa373. Run #18 was a subsequent enrichment/reconciliation pass, not the first full publication.
- **Independent source-index cross-check against current main:** parsed assistant_data/music/indexes/tracks.json (11,130 unique legacy track IDs), indexes/artists.json (5,358 artist IDs/names), and library/library_index.json (13,005 songs, 6,386 artists, 7,861 albums). All 11,130 legacy track IDs resolve through either the canonical source-track-ID map or recording-MBID map; all 5,358 legacy artist names are represented in canonical artist records. The 19 IDs without direct source-track aliases are covered by recording-MBID aliases.
- **Current alias counts:** 1,856 Spotify IDs; 11,338 recording MBID aliases; 1,816 ISRCs; 13,003 source-track aliases; 1,428 ambiguous artist/title candidate aliases.
- **Run #18 enrichment result:** duration coverage 138,515 / 152,005 scrobbles (91.1%); track profile rows 1,778; artist profiles 3,998; album profiles 400; audio profiles 115; lyric features 0. Final sync audit: 13,005 songs, 6,386 artists, 7,861 albums, zero errors.
- **Provider limitations:** MusicBrainz hit rate limiting and transient 503s; ID resolution produced zero unique matches in 21 attempts; duration fallback found 3 matches from 10 lookups; Last.fm recording tag lookups repeatedly returned HTTP 400. Discogs and GetSongBPM credentials absent. Do not retry blindly; inspect request/parameter handling and persisted cooldowns first.
- **Run queue:** #21 ([run 41364361982](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41364361982), issue #71) is currently in progress as the checkpoint-resuming follow-up. #19/#20 were cancelled by the single-pending concurrency behavior. Wait for #21 to finish before creating the next issue-triggered operation.
- **Remaining verification:** run #18's final audit was on the runner before publish. The index was independently parsed from published main, but a full post-publication audit/status run is still required. Add the legacy source-index coverage cross-check to the permanent migration report/health checker; current migration_report.json retains a stale limitation sentence about tracks absent from track_profiles.json.
- **Safety:** no Spotify playlist writes. Run #18 skipped Spotify refresh, staged only assistant_data/music/, rebased onto latest main, and pushed successfully. The log contained shell command-substitution errors in the optional step-summary echo (unescaped Markdown backticks), but the operation, publish, artifact, and issue-report steps all completed successfully. Fix that cosmetic workflow logging bug separately.
## 2026-11-02 — Find and monitor issue-triggered migration runs; define expanded Library reliability goals

- **Actions discovery:** used the repository-wide Actions runs endpoint after earlier issue-comment checks failed to expose run state. This confirmed issue-triggered workflow runs are visible and should be queried directly.
- **Run #18:** [run 41364145298](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41364145298), triggered by issue #68, is `in_progress`. Job `library` passed request validation, checkout, Python setup, compilation and full regression suite; the requested Library operation is still running. Publish, artifact, and issue-report steps are pending. No generated Library publication or completion is claimed.
- **Run queue:** #19 (issue #69 prepare) and #20 (issue #70 audit) were cancelled; #21 (issue #71 prepare) is pending behind #18. The shared concurrency group permits one running and one pending run; opening several request issues quickly causes intermediate pending requests to be cancelled/replaced. Do not enqueue additional issues until #21 resolves. A single prepare includes a final integrity audit; a separate published-branch audit should follow after publication.
- **New required reliability goals:** created goal workspaces for [Library Health Checker & Data Maintainer](../library-health-maintenance/README.md), [Metadata Freshness & Partial Revalidation](../metadata-freshness/README.md), and [Spotify Track Playability & Availability](../spotify-playability/README.md). Their specifications keep read-only diagnostics, safe repairs, stale-field refresh, and market-scoped playability as separate concerns.
- **Schema inspection:** current `MusicLibrary.audit()` validates indexed song records, identity basics, artist/album references, and alias targets. It does not yet provide the complete health report / safe maintainer described in the new goal. Canonical song records have an extensible metadata evidence area but no verified dedicated market-scoped Spotify playability schema.
- **Workflow queue rule:** until queue behavior is redesigned, submit one issue-triggered operation at a time and wait for its terminal run result before creating the next. Avoid overlapping migration/enrichment writers.
- **Safety:** no provider lookups, canonical Library writes, or Spotify playlist writes were performed in this documentation/design pass.
- **Next:** monitor run #18 and pending #21; inspect terminal logs and artifact; confirm published Library and checkpoints; run independent audit/status on published `main`. Then implement the read-only health checker and playability capture from existing snapshots before adding any scheduled provider polling.
## 2026-11-01 — Reconcile Library branch status and migration trigger evidence

- **Action:** checked PR #49 and the current Library navigation file on `main`; rechecked issues #69, #70 and #71 and their comment threads.
- **PR #49:** confirmed merged into `main` at merge commit `b2df17b9b7c73267c523c15ceab92e69b1672080`. The README's claim that the Library was still only on the feature branch was stale.
- **Actual remaining scope:** PR #49 explicitly describes the committed Library as a staged sample (100 songs, 47 artist records, one album example), not the complete historical migration. Legacy aggregate data remains to be imported and published.
- **Documentation fix:** updated `assistant_data/music/library/README.md` to remove the stale branch warning, state that the catalogue structure is merged but the sample is partial, and distinguish offline `migrate` from provider-enriched `prepare`. Commit: `1f2d799a17e31dd42c4aceb299e35a5d22698f3c`.
- **Trigger evidence:** issues #69/#70/#71 exist and are owner-authored with valid command titles, but all remain open with no workflow result comments at the time of inspection. This connector does not expose a repository-wide Actions-run listing/dispatch action, and the PR-triggered commit-run helper cannot enumerate issue-triggered runs. Therefore no run start, completion, artifact, or publication is claimed.
- **Safety:** no provider requests, migration writes, or Spotify playlist writes were performed during this inspection/documentation correction.
- **Next:** obtain issue-triggered run evidence or a manually dispatched run; verify that the workflow checks out the merged Library implementation and that the full legacy migration is published to `main`; then perform a separate post-publication audit/status. Do not repeat provider enrichment until durable checkpoint state is confirmed.
- **References:** [PR #49](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/49), [issue #69](https://github.com/TrickySturluson/spotify-helper-information-tracker/issues/69), [issue #70](https://github.com/TrickySturluson/spotify-helper-information-tracker/issues/70), [issue #71](https://github.com/TrickySturluson/spotify-helper-information-tracker/issues/71).

## 2026-11-01 — Queued migration publication, independent audit, and continuation pass

- **Action:** opened issue #69 `[SHIT LIBRARY] prepare` against the repaired workflow, then queued issue #70 `[SHIT LIBRARY] audit` for a fresh audit/status against the published default branch, followed by issue #71 `[SHIT LIBRARY] prepare` for another checkpoint-resuming enrichment pass.
- **Requests:** #69 reuses saved Spotify snapshots and publishes only `assistant_data/music/`; #70 is read-only and explicitly verifies the published branch rather than trusting a runner-side audit; #71 resumes provider checkpoints, avoids completed/definitive-negative lookups, and reports remaining realistically unfillable gaps if no work remains.
- **Safety:** no Spotify playlist refresh or playlist writes requested; no force-push or blind conflict resolution.
- **References:** https://github.com/TrickySturluson/spotify-helper-information-tracker/issues/69 ; https://github.com/TrickySturluson/spotify-helper-information-tracker/issues/70 ; https://github.com/TrickySturluson/spotify-helper-information-tracker/issues/71
- **Execution status at documentation time:** all three issues were created successfully; no workflow result comments had appeared yet. This is queued work, not evidence that any run has started or completed.
- **Next:** inspect #69 result/artifact; verify publication; then inspect #70 audit; then inspect #71 enrichment and repeat bounded passes only while there is eligible, useful provider work.
- **Coverage goal:** maximize reliable, provenance-backed track/artist/album/duration/acoustic/theme data, not manufacture 100% coverage. Keep unknowns unknown and explain provider/API/catalogue limitations.

# Great Migration — Actions & Evidence

Newest entries first. Record verified outcomes separately from plans, assumptions and unverified artifacts.

## 2026-11-01 — Fixed-workflow migration rerun requested

- **Action:** opened owner-authored issue #68, `[SHIT LIBRARY] prepare`, after confirming the publication fix is on `main`.
- **Request:** reuse saved Spotify snapshots, skip Spotify refresh, publish only `assistant_data/music/`, and preserve generated music data/checkpoints plus backup/log in the artifact.
- **Reference:** https://github.com/TrickySturluson/spotify-helper-information-tracker/issues/68
- **Outcome:** request submitted; workflow completion and publication not yet observed. Do not report migration complete until post-publish audit/status passes.
- **Next:** inspect issue result and Actions run; if successful, independently run audit/status against `main`; if publication fails, recover generated output from the new artifact rather than repeating provider work blindly.

## 2026-11-01 — Recover run #17 evidence and repair publication scope

- **Purpose:** determine whether the Great Migration itself completed and remove the publication failure that prevented its data from reaching `main`.
- **Evidence:** run #17 https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41357689889; artifact #13104699873; job #125005910236.
- **Verified execution:** compile/regression step passed; `prepare` command exited successfully; incremental syncs and final audit passed with 13,005 songs, 6,382 artists, 7,861 albums and zero audit errors. Final status reported 1,856 Spotify-ID aliases, 11,338 recording-MBID aliases, 1,816 ISRC aliases and 13,003 source-track-ID aliases.
- **Verified enrichment snapshot:** 1,580 track profiles; 3,898 artist profiles; 300 album profiles; 93 acoustic profiles. Duration coverage was 138,473 / 152,005 scrobbles (91.1%). Discogs and GetSongBPM were skipped because optional credentials were absent. AcousticBrainz queried 500 batch slots and stored 36 additional profiles; 907 negative-cache entries were recorded. Track/album profile backlog remained large.
- **Publication failure:** Git rebase failed with conflicts in dozens of `assistant_data/spotify/playlists/*.json` files and `assistant_data/spotify/reference_index.json`. The run had refreshed read-only Spotify snapshots, then staged all of `assistant_data/`. This was the conflict source; it did not mean the migration or final audit failed.
- **Artifact inspection:** downloaded and inspected artifact #13104699873 (23,946,780 bytes). It contains the pre-migration backup and `shit-library-run.log`; it does **not** contain the generated Library output. Therefore the successful runner state was not recoverable from that artifact.
- **Workflow fix:** commit `bdf75f74d7fd156e9d5e54ae8a66c814e5667dc8` removes the Spotify refresh-token setup from prepare, invokes `prepare --skip-spotify-refresh`, stages only `assistant_data/music/`, and uploads the complete music data directory plus log so generated output/checkpoints survive even if publication fails. This intentionally leaves all Spotify playlist snapshots and live playlists untouched.
- **Safety:** no Spotify playlist writes were performed. No force-push or blind conflict resolution was used.
- **Outcome:** run #17's migration/enrichment/audit are verified on its ephemeral runner; publication remains unverified. Workflow fix and goal status are committed to `main`.
- **Next action:** start a fresh `[SHIT LIBRARY] prepare` run on the fixed workflow; verify successful publication; then run a separate audit/status against `main` and continue enrichment from the newly durable checkpoints.
- **Lessons:** successful pre-publish audit is not proof of published data; failure artifacts must include generated output/checkpoints as well as rollback backup; migration publication must not include unrelated Spotify reference snapshots.

## 2026-11-01 — Goal workspace initialized

- **Action:** established this goal's dedicated documentation and action-history location.
- **Context:** Run #17 recovery is the immediate action. The only verified fact in the handoff is that publication/rebase failed; whether earlier migration stages or final audit completed is unknown. Next: inspect artifact and backup, reconcile safely, then verify published state.
- **Outcome:** documentation initialized; no runtime implementation or data mutation implied unless explicitly stated above.

## 2026-11-01 — Project-wide audit: migration recovery remains the critical path

- **Purpose:** reconcile previous migration requests and current repository state.
- **Evidence:** run #17 https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41357689889; open repeated prepare issues #61, #62, #63, #64 and earlier #57/#59.
- **Verified:** publication/rebase failed due generated Library/index conflicts; an artifact and backup were reported. The exact last successful stage, artifact contents, backup contents, audit result and published state remain unverified.
- **Loose ends:** inspect logs/artifact/backup; compare with main; preserve valid newer records; inspect all workflows writing shared generated paths; serialize writers/stale-base checks; fresh integrity audit before publish.
- **Failed approach / lesson:** do not blindly rerun a write-heavy migration or force-resolve generated data conflicts. The run failure at publication does not prove earlier stages failed or passed.
- **Outcome:** blocked; no migration recovery or Library write performed during this documentation audit.
- **Next action:** inspect run #17 artifact and backup, then reconcile safely.

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
