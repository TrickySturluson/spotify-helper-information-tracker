## 2026-11-02 — Validate rotating unknown-age baseline on full catalogue (issue #99)

- The corrected PR branch `feature/freshness-baseline-rotation-ci` was checked out by the dedicated Great Migration validation command.
- Full compile and **344 unit tests passed**, including deterministic weekly rotation, due-task priority, due/baseline cross-list deduplication, no-data vs missing-timestamp classification, and CLI flag wiring.
- Full-catalogue read-only planner: 13,005 songs, 6,386 artists, 7,861 albums; 8,621 fresh, 0 stale, 0 missing playability observations, 6,613 data-bearing unknown-age duration observations, 33,689 no-data fields, 1,856 missing duration provenance, 1,362 cooldown skips, 0 invalid timestamps and 0 blocked tasks.
- Baseline candidates: 6,613; selected 25 of 25. All 25 selected tasks were Last.fm duration refresh candidates, labelled `baseline_required`; no stale/due tasks were present. Selection is deterministic within an ISO week and rotates between weeks.
- provider_requests=0 and writes=0. This is a planning sample only; no provider calls or Library writes occurred.
- The 1,856 duration values without source provenance are excluded from provider scheduling; do not blindly query them until their source is resolved.
- Initial PR CI failed due to a duplicate argparse option; issue #98 then passed the 340-test main suite but its temporary wrapper failed from heredoc indentation. The wrapper was fixed; issue #99 then passed the branch-specific 344-test suite and full-catalogue planner.
- The original PR #95 still has failed historical CI attached to its pre-fix head. PR #97 contains the corrected branch plus the new regression tests; rebase its workflow/docs files onto latest main before merge. Public security scan passed on the original PR branch; changes after that scan are limited to removing a duplicate CLI option and adding tests/docs/workflow flag wiring.
- No provider calls, Library writes, or playlist writes.

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
