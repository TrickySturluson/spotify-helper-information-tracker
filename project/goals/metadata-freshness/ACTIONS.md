# Metadata Freshness & Partial Revalidation — Actions & Evidence

Newest entries first. Record verified outcomes separately from plans, assumptions and unverified artifacts.

## 2026-11-06 — Freshness validation and open PR status

- Daily curator tests run #42149783445 passed the bounded, read-only metadata freshness planning step on draft PR #161's then-current base data; this did not run provider enrichment or modify Library records.
- PR #120 remains an open draft proposing incremental Library enrichment/sorter development. Do not treat it as merged or assume its behavior is present.
- Feature implementation and provider calls in this goal remain paused until documentation acceptance criteria pass.

## 2026-11-02 — Full duration timestamp recovery preview passed (issue #105)

- The read-only backfill scanned 32 legacy shards and 11,130 rows; 8,121 rows had valid Last.fm timestamps and exact canonical ID/duration/source matches with `matched` status.
- Planned changes: 8,121 song files, one append-only `duration_observations` entry each.
- All conflict counts were zero: missing/ambiguous aliases, missing files, duration/source mismatch, non-matched status, and conflicting duplicate legacy IDs.
- Skipped 2,958 unrecognized-provider rows and 51 invalid/missing timestamps; no source or timestamp was guessed.
- `safe_to_apply=true`; provider_requests=0, writes=0. Preview made no changes.
- Issue #106 queued the backup-protected apply. After it publishes, rerun freshness planner; expect the unknown-age duration baseline to shrink substantially, but measure rather than assume.
- Keep scheduled provider lookups disabled until the post-backfill baseline is reviewed.

## 2026-11-02 — Discover and implement duration timestamp provenance recovery

- The full-catalogue unknown-age baseline (6,613 duration candidates) was traced to at least one migration gap: At the Gates — Slaughter of the Soul has exact `metadata_checked_at=1793324246` in legacy shard 18 with `metadata_status=matched`, `duration_ms=183000`, `duration_source=Last.fm track.getInfo`, but the canonical song record omitted that timestamp.
- This means unknown-age does not necessarily mean unverified. Do not issue provider lookups for these records until legacy check timestamps have been carried into canonical evidence.
- Added `scripts/music/backfill_duration_observations.py` and `python shit.py library duration-evidence`. It resolves by exact canonical aliases, requires exact duration/source and matched status, writes append-only `duration_observations` only on explicit `--apply --yes`, creates a backup, writes atomically, and rolls back if post-write health fails.
- Updated freshness planning to use the latest observation matching the current duration/source/provider; Last.fm tag timestamps remain separate. Updated health validation for duration observation schema.
- Tests cover exact match, mismatched duration/source, non-matched status, existing/newer observations, duplicate legacy IDs, malformed timestamps, preview no-write, backup and rollback. Workflow issue #104 runs the read-only full-catalogue preview; result pending.
- No provider requests or canonical data writes have occurred.

## 2026-11-02 — Merge weekly rotating unknown-age freshness baseline (PR #100)

- PR #100 merged to main as `61cc5c0b108559746443a4ad8d83bf2ec2ca97d8`.
- Full PR CI passed: 344 unit tests, compile, generated-data audit, full-catalogue health/confidence checks, freshness planner, and documentation checks. Public repository Gitleaks scan passed.
- Clean rebased branch validation via issue #101 also passed 344 tests and ran the native CLI against the full catalogue.
- Full-catalogue planner result: 13,005 songs, 6,386 artists, 7,861 albums; 8,621 fresh; 0 stale; 0 missing playability observations; 6,613 data-bearing unknown-age observations; 33,689 fields with no data; 1,856 missing duration provenance; 1,362 cooldown skips; 0 invalid timestamps; 0 blocked tasks.
- The baseline sample contained 6,613 candidates and selected 25; all 25 were Last.fm duration tasks labelled `baseline_required`. No due tasks existed. Known stale tasks take priority; duplicate due/baseline task keys are deduplicated. Selection is deterministic within the ISO week and rotates between weeks.
- Planner is read-only: provider_requests=0, writes=0. Weekly review and manual freshness-review now include the rotating baseline; no automatic provider refresh is enabled.
- Missing provenance (1,856 duration values) is kept separate and excluded from blind scheduling. Missing metadata/no-data fields are also not treated as stale.
- PRs #95 and #97 were closed as superseded by the clean rebased PR #100. The earlier duplicate argparse flag and temporary validation-wrapper heredoc failures are resolved; final validation passed.
- Next: implement a separate explicit, bounded provider-backed executor. Start with the 25 Last.fm duration baseline candidates as an opt-in pilot, persist checkpoints/results, and re-run the planner after writes. Do not automatically enable weekly provider calls yet.

## 2026-11-02 — Add weekly maintenance preview and unknown-age baseline rotation

- The weekly read-only workflow was extended to run `python shit.py library maintain --json` and preserve `library-maintenance-plan.json` alongside health, confidence and freshness reports. It validates `mode=preview`, `changed=false`, zero provider requests and zero playlist writes; it never applies repairs. Commit `cb3adf2`; its push CI and public security scan both passed.
- Issue #93 full-catalogue maintainer preview independently passed: 13,005 songs, 6,386 artists, 7,861 albums; health errors/warnings=0; `repair_needed=false`; `safe_to_rebuild=true`; no IDs/aliases lost; no writes.
- PR #95 (`feature/freshness-baseline-rotation`) introduces separate counts for `no_data`, data-bearing fields with `missing_timestamp`, and `missing_provenance`; it also adds a deterministic weekly rotating unknown-age sample (up to the existing 25-item cap), clearly labelled `baseline_required`, not stale. It exposes `--include-unknown-age` in CLI and weekly/manual workflows.
- Initial PR CI failed before tests because the new argparse option was accidentally declared twice. The duplicate declaration has been removed on the PR branch (commit `e7b2bac`, followed by a documentation update). No passing post-fix CI run has yet been observed; keep PR #95 open until the full test and security workflows pass.
- This design is still read-only: baseline selection makes no provider requests and does not mutate a cursor or Library state. It gives us a deterministic rotating sample to inspect unknown-age data without claiming that it is stale.
- Next: obtain passing CI for PR #95, then run its full-catalogue planner against main and inspect baseline candidate counts before designing a bounded provider-backed executor.

## 2026-11-02 — Run first manual read-only freshness review

- Issue #90 `[SHIT LIBRARY] freshness-review` completed successfully against the then-current main branch.
- Scanned 13,005 songs, 6,386 artists, 7,861 albums; 1,856 Spotify IDs; cache rows: 1,778 track, 3,998 artist, 400 album profiles.
- Plan: 8,799 fresh, 0 stale, 0 missing playability observations, 42,158 missing field/provider timestamps, 1,184 cooldown skips, 0 invalid timestamps, 0 blocked tasks, 0 errors; 0 selected from the 25-task limit.
- Explicit side-effect counters: provider_requests=0, writes=0. This was a plan/report only, not an actual provider refresh.
- The large missing-timestamp count is ambiguous: it includes fields/records without explicit observation timestamps and is not proof they are stale. Current code correctly avoids inferring age from file mtimes, but reporting should split missing metadata, present-but-undated values, provider checks with no data, and retry/negative-cache states.
- Existing track-profile cache rows have explicit `lastfm_checked_at` on all 1,778 rows; 1,180 rows also have `musicbrainz_checked_at`. The planner should preserve these source-specific timestamps when mapping into canonical song evidence.
- No provider requests or Library writes were made.

## 2026-11-02 — Merge native freshness CLI and weekly read-only review

- PR #86 merged to main as `e4ae9b535a74d745b2adb29aed57f7af0afacbe7`.
- Added `python shit.py library freshness --limit 25 --market from_token`.
- Added `.github/workflows/library-freshness-review.yml`: Sundays 09:17 UTC, or manual dispatch; runs health, confidence, and freshness reports; validates read-only behavior; uploads JSON artifacts for 30 days.
- Full PR CI and secret scan passed. The workflow does not call providers or mutate Library/playlists.
- Added a manual `freshness-review` command to the Great Migration issue workflow. Issue #89 is queued to run the planner against current main and report entity/cache counts and due-task breakdown.
- No provider-backed periodic executor is enabled. A weekly plan identifies due work; it does not perform lookups.

## 2026-11-02 — Merge field-level freshness planner; add CLI and weekly review

- PR #81 merged to main as `570598fe95bc0c2314324c8f4565023ff3a2382b`.
- The planner now consumes canonical song evidence, market-specific playability, `track_profiles.json`, `artist_profiles.json`, `album_profiles.json`, canonical alias maps, and provider cooldowns.
- Full-catalogue CI scanned 13,005 songs, 6,386 artists, and 7,861 albums; cache coverage included 1,778 track profiles, 3,998 artist profiles, and 400 album profiles. It selected 0 due tasks after the playability backfill. 335 tests and 131 module compilations passed.
- Added native CLI `python shit.py library freshness --limit 25 --market from_token` on branch `feature/library-freshness-automation`.
- Added a weekly read-only workflow on that branch: Sunday 09:17 UTC; runs health, confidence and freshness; uploads JSON reports for 30 days; no provider requests, Library writes, or playlist writes.
- PR #86/CI pending at time of entry. No provider-backed periodic executor is enabled.
- Missing timestamps remain explicitly unscheduled; do not infer age from file modification time. TTLs are initial configurable defaults, not provider mandates.
- Next: review PR #86 and run the first scheduled/manual weekly report; only then design a bounded executor tied to provider retry/cooldown state.

## 2026-11-02 — Implement initial read-only field freshness planner

- Added `scripts/music/metadata_freshness.py` with deterministic bounded planning for market-specific Spotify playability and explicit field/provider observation timestamps.
- Policies are field-specific: Spotify playability 90 days, Last.fm track tags 180 days, MusicBrainz track tags 365 days, artist/album profiles 365 days, and duration 730 days. These are initial configurable defaults, not provider mandates. These are initial configurable defaults for planning, not a live provider schedule; review provider policy before enabling execution.
- Planner uses `evidence.spotify_playability.latest_by_market` for market-scoped checks; existing `evidence.track_metadata` timestamps, statuses, retry state and duration source; saved `track_profiles.json` mapped through recording/source/Spotify aliases; saved `artist_profiles.json` and `album_profiles.json` mapped to canonical IDs; source-stamped artist/album evidence; and optional `freshness.observations` as a forward-compatible normalized input.
- Unknown-market playability does not satisfy a requested market. Missing field timestamps are reported and skipped; record modification time is never treated as metadata freshness.
- Oldest due observations are selected first, with stable task-key hashing as tie-breaker. The run limit is capped at 100.
- No provider executor, scheduler, CLI integration, or state mutation has been added. Planning is strictly no-network/no-write.
- Added tests for stale vs fresh fields, market separation, future and relative retry cooldowns, missing timestamps, provider profile cache resolution, artist/album profile freshness, deterministic bounded selection, and no-write behavior.
- Branch: `feature/metadata-freshness-planner`; PR/CI pending at time of this entry.
- **Next:** inspect CI, validate schema against real saved evidence/checkpoints, align with PR #78 and `RETRY_QUEUE_SPEC.md`, then add CLI integration and a single bounded executor only after plan correctness is established.

# Actions — Metadata Freshness & Partial Revalidation

## 2026-11-02 — Initial design and boundaries

- Captured the requirement for infrequent/partial lookups to identify and refresh outdated metadata.
- Inspected `prepare_music_library.py`: enrichment is already bounded by per-provider limits and individual scripts/checkpoints, but it is a sequential full preparation plan rather than a unified per-field freshness planner.
- Decision: reuse provider-specific caches/checkpoints and the planned retry queue; do not build a second retry engine. Freshness must be field/provider scoped, with a deterministic rotating sample and separate planning/execution.
- Initial cadence concept: local health checks daily/on publish; small provider-backed partial refresh weekly/monthly or targeted on demand. Actual intervals remain configurable and must be grounded in provider policies.
- No provider requests or data mutations performed in this documentation pass.
- Next: inspect existing state schemas and retry queue specification; define stable planner output and due rules before implementing.


## 2026-11-02 — Second duration provenance pass published (issues #113–#114)

- Updated `epoch_iso()` to accept timezone-qualified ISO-8601 timestamps as well as positive Unix epochs; timezone-naive timestamps remain rejected rather than guessed.
- Issue #113 read-only preview passed against 32 legacy shards / 11,130 rows and 13,005 canonical songs. It found 8,172 exact timestamped rows: 8,121 observations were already present from the Last.fm pass and 51 additional MusicBrainz observations were safe to add.
- Preview conflicts were all zero: missing/ambiguous aliases, missing files, duration/source mismatches, non-matched statuses, invalid timestamps, and conflicting duplicate legacy IDs. 2,958 unknown-provider rows were skipped. `safe_to_apply=true`, provider_requests=0, writes=0, playlist writes=0.
- Issue #114 apply reported success, 51 changed song files, a timestamped backup, and post-write health success; provider requests=0 and Spotify playlist writes=0. Independently fetched published canonical song `source:3e2d305ebc76ea39` (Supermega — Brand New Shirt) and confirmed its MusicBrainz duration observation is present with exact 139,000 ms value, source, and 2026-10-31T07:22:42.965634+00:00 timestamp.
- Next: fresh audit, health, freshness, and confidence verification are queued as issues #115–#118. Do not start provider refresh until their reports establish the true remaining gap.
