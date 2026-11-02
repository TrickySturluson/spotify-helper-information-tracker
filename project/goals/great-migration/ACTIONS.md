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
