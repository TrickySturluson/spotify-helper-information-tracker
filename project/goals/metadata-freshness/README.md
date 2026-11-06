# Metadata Freshness & Partial Revalidation
> **Roadmap:** [ROADMAP.md](ROADMAP.md) is the durable plan and next-action reference. Read it before work; update it and [ACTIONS.md](ACTIONS.md) in the same session as implementation, testing, decisions, or blockers.
> **Current repository priority:** This workstream is paused for feature implementation while SHIT's documentation audit is active. Only documentation corrections and evidence reconciliation are permitted. Preserve this roadmap; resume its feature next actions only when the [central handoff](../../NEXT_WORK.md) and Maintainability & Documentation roadmap explicitly say documentation is complete.


## Goal

Keep useful Library metadata current without re-scraping everything. Periodically check whether selected fields are outdated, and refresh only records that are due, eligible, and supported by healthy providers.

## Design

- Freshness is **per field and source**, not one timestamp for the whole song. A new Spotify availability observation must not make old genre or duration metadata appear fresh.
- Store observation timestamps, provider/source, field family, result status, and next eligible refresh time. Preserve prior evidence and history; do not erase a valid old value on a failed refresh.
- Use a deterministic rotating sample, not repeated random sampling. Prioritize recently played/high-interest songs, frequently used sorter candidates, records with old or weak evidence, and a small rotating background sample so the long tail is not permanently ignored.
- Use field-specific refresh intervals. Identity and release metadata are low-volatility; Spotify playability and service availability are high-volatility; community tags/descriptions are medium-volatility. Exact intervals must be configured and documented, not guessed inside code.
- Planner/report mode is read-only and makes no provider calls. Executor mode consumes a bounded request budget, respects provider limits, caches, negative-cache expiry, retry-after/cooldowns, and stops cleanly when credentials/provider health is poor.
- Refresh only stale/missing/low-confidence fields. Do not refetch fresh fields just because another field is stale.
- Distinguish unchanged, updated, conflicting, no longer available, ambiguous, not found, transient failure, rate limited, and credential blocked.
- Keep previous values and provenance for audit; new values are appended as observations and promoted only under explicit confidence/identity rules.

## Partial-check schedule

- Run a lightweight local health/freshness report frequently (daily or on each migration publish).
- Run a small provider-backed stale sample on an infrequent cadence (initial proposal: weekly or monthly, depending on provider budgets and field volatility).
- Run targeted refreshes when a track enters a playlist-sort or recommendation workflow and its required data is stale.
- Keep an advancing deterministic cursor/checkpoint so each partial pass covers new records and resumes after interruption.
- Never run the full catalogue lookup loop on every scheduled workflow.

## Proposed data model

A record-level `freshness` map may summarize latest observations, but canonical source evidence remains field-specific. Each observation should include:
- `field_family`, `provider`, `observed_at`, `status`, `confidence`, `source_reference`
- `next_check_after` or a policy-derived due state
- optional `value_hash` to detect changes without duplicating large payloads.

A global `freshness_state.json` may track per-provider cursor, last successful pass, budgets, and failures. It must not become the source of truth for field values.

## Acceptance criteria

- Read-only planner is deterministic, network-free, and produces a reason for every selected/skipped item.
- Repeated planning with unchanged inputs returns the same plan.
- Executor never exceeds configured budgets and respects cooldowns/negative-cache expiry.
- Partial passes advance fairly across the catalogue.
- Failed or ambiguous refreshes preserve prior evidence.
- Tests prove fresh fields are skipped, stale fields selected, and a transient failure does not overwrite a successful value.

## Current status

**Read-only field-level planner merged in PR #81** at `570598f`. It reads market-scoped Spotify playability, existing song Last.fm/MusicBrainz timestamps and duration source, and the saved `track_profiles.json`, `artist_profiles.json`, and `album_profiles.json` caches mapped back to canonical IDs. It respects per-profile and provider-wide cooldowns, and does not infer freshness from record modification times.

Full-catalogue CI scanned 13,005 songs, 6,386 artists, and 7,861 albums; it recognized 1,778 track-profile rows, 3,998 artist-profile rows, and 400 album-profile rows. After the offline playability backfill, it selected **0 due tasks** under the current initial TTL policies. The planner is network-free and write-free. 335 tests and 131 Python module compilations passed on the final PR revision.

**Native CLI and weekly automation merged in PR #86** at `e4ae9b5`. Run `python shit.py library freshness --limit 25 --market from_token` for a bounded plan. The weekly workflow runs structural health, confidence, a read-only maintenance preview, and freshness planning every Sunday at 09:17 UTC, stores reports as a 30-day artifact, and makes no provider requests or Library writes. A manual `[SHIT LIBRARY] freshness-review` operation is also available. No provider-backed periodic executor is enabled; the current scheduled workflow is read-only and produces a plan/report.

Some album/field observations still lack per-field timestamps; these are reported/skipped rather than treated as stale. TTLs are initial configurable defaults and must be reviewed before live execution.



## First manual baseline (2026-11-02)

Issue #90 completed a read-only plan against the 13,005-song catalogue. It scanned 13,005 songs, 6,386 artists, and 7,861 albums; found 1,856 Spotify IDs and cache rows for 1,778 tracks, 3,998 artists, and 400 albums. It reported 8,799 fresh observations, 0 stale/due tasks, 0 missing playability observations, 42,158 missing field/provider timestamps, 1,184 cooldown skips, and no invalid timestamps, blocked tasks, or errors. The selected batch was 0/25; provider requests and writes were both zero.

**Interpretation:** zero due tasks does not mean every Library field has been recently verified. The 42,158 missing-timestamp observations are not proven stale; missing and undated evidence is deliberately not scheduled. Existing track-profile cache rows do have source timestamps (1,778 Last.fm check times; 1,180 MusicBrainz check times). Next work is to classify missing metadata vs present-but-undated evidence vs provider no-result/negative-cache states, and propagate trustworthy timestamps from caches/checkpoints into the canonical evidence model where possible. Only then should a provider-backed partial executor be enabled.



**Unknown-age baseline rotation merged in PR #100** (`61cc5c0`). The planner separates `no_data` from data-bearing fields with missing timestamps, reports missing duration provenance independently, and selects a deterministic weekly rotating sample of up to 25 unknown-age observations. These are labelled `baseline_required`, never `stale`; due tasks take priority and duplicate task keys are removed across due/baseline groups. Full CI and public security scan passed (344 tests); issue #101 also validated the full-catalogue CLI plan. Baseline report: 6,613 candidates, 25 selected (all Last.fm duration), 0 due/stale, 33,689 no-data fields, 1,856 missing duration provenance, 1,362 cooldown skips. This remains a read-only plan with zero provider requests and writes. No provider-backed executor is enabled yet.



## Duration provenance recovery in progress

A follow-up audit found that some duration timestamps were present in legacy artist shards as `metadata_checked_at` but absent from canonical song evidence. At the Gates — Slaughter of the Soul is a confirmed example: exact duration/source and a successful Last.fm check timestamp exist in the legacy row, but the canonical song record has no observation timestamp. This explains at least part of the 6,613 unknown-age duration candidates. The new `library duration-evidence` preview/backfill utility restores only exact ID + duration + source + successful-status matches into append-only `duration_observations`; it is preview-only by default and requires backup-protected explicit apply. Issue #105 preview succeeded: 8,121 exact Last.fm duration observations across 8,121 song files; zero aliases missing/ambiguous, zero duration/source mismatches, zero conflicting duplicates; 2,958 unrecognized-provider rows and 51 invalid/missing timestamps safely skipped. Issue #106 is queued for backup-protected apply. Do not execute baseline provider lookups until the backfill is published and the remaining unknown-age set is remeasured.

## Resume

Read [ACTIONS.md](ACTIONS.md), review PR #86 and its scheduled workflow, then inspect the completed manual baseline in ACTIONS.md and let the weekly report run. Reconcile missing field timestamps and retry queue state before enabling any provider-backed execution. Keep planning read-only; build one bounded executor only after tests prove provider budgets, cooldowns, and evidence preservation.
