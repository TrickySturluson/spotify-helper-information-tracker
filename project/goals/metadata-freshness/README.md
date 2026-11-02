# Metadata Freshness & Partial Revalidation

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

**Specification / design stage.** Existing enrichment scripts use bounded lookups and checkpoints, but a unified field-level freshness planner and scheduled partial refresh system have not been verified.

## Resume

Read [ACTIONS.md](ACTIONS.md), inspect provider state/checkpoint formats, and align the freshness planner with the metadata coverage/retry queue rather than creating a competing retry system.
