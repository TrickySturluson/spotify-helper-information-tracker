# Library Health Checker & Data Maintainer — Actions & Evidence

Newest entries first. Record verified outcomes separately from plans, assumptions and unverified artifacts.

## 2026-11-06 — Latest full Library health check passed on 13,163-record catalogue

- Daily curator CI [#42154433350](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42154433350) ran the full read-only health check against 13,163 songs, 6,497 artists and 7,969 albums. Index counts matched exactly; the health report returned `ok=true`, zero errors and zero warnings.
- Alias counts: 1,991 Spotify IDs, 11,338 recording MBIDs, 1,904 ISRCs, 13,163 source-track IDs and 11,651 name-candidate keys.
- The preceding general repository audit emitted 18 warnings (no captured playback intervals plus 16 inaccessible Spotify playlist item snapshots and the summary warning); these are distinct from the Library health report, which had zero warnings.
- This was validation only; no Library maintenance, migration, repair or provider enrichment was performed. Feature work remains paused until documentation acceptance criteria pass.

## 2026-11-02 — Verify new playability health rules against full catalogue

- Issue #92 / Great Migration workflow run [41372492615](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41372492615) completed successfully.
- Canonical audit: 13,005 songs, 6,386 artists, 7,861 albums; zero errors.
- Read-only structural health: index counts match; zero errors and zero warnings. Alias counts: 1,856 Spotify IDs, 11,338 recording MBIDs, 1,816 ISRCs, 13,003 source-track IDs, 11,529 name candidates.
- The merged playability semantic checks passed against all populated song records, including observation history, status/value consistency, market keys, requested/relinked IDs, timestamps, and latest-by-market index.
- No provider requests, Library writes, repairs, or playlist writes.

## 2026-11-02 — Merge market-aware playability evidence validation

- PR #87 merged to main as `6c9fe067a8af6bc504548bc45e715ed27aa0cea8`.
- The read-only health checker now validates any present `evidence.spotify_playability`: observation object/list shape, allowed status values, boolean/status consistency, timestamp validity, market keys, requested Spotify ID against canonical identity, and relinked-ID continuity.
- It also verifies `latest_by_market` matches the newest append-only observation for each market.
- Missing playability evidence remains optional; malformed present evidence is an error. No playability state is rewritten.
- Fixture tests cover valid observations, mismatched status/value, relinked identity mismatch, and latest-market index mismatch. Full CI and secret scan passed.
- Issue #92 was opened after merge to run the full canonical audit/health/confidence verification against latest main; result pending at this documentation checkpoint.

## 2026-11-02 — Merge market-aware playability evidence validation

- PR #87 merged to main as `6c9fe067a8af6bc504548bc45e715ed27aa0cea8`.
- The read-only health checker now validates any present `evidence.spotify_playability`: observation object/list shape, allowed status values, boolean/status consistency, timestamp validity, market keys, requested Spotify ID against canonical identity, and relinked-ID continuity.
- It also verifies `latest_by_market` matches the newest append-only observation for each market.
- Missing playability evidence remains optional; malformed present evidence is an error. No playability state is rewritten.
- Fixture tests cover valid observations, mismatched status/value, relinked identity mismatch, and latest-market index mismatch. Full CI and secret scan passed.
- Next: verify full main catalogue after merge with `[SHIT LIBRARY] verify-catalogue`.

## 2026-11-02 — Validate maintainer against full published catalogue

- Issue #84 preview attempt exposed a direct-script import bug (`ModuleNotFoundError: No module named 'scripts'`); fixed in main commit `86c23e4` by supporting both package and direct-script import contexts.
- Retried as issue #85; full-catalogue preview passed: `health_ok=true`, 0 health errors, 0 warnings; current/proposed counts match at 13,005 songs, 6,386 artists, 7,861 albums.
- Existing entity IDs and aliases were all reconstructable: `safe_to_rebuild=true`, `aliases_or_records_that_would_be_lost={}`, no blocking record findings.
- `repair_needed=false`; no repair was applied, no backup created, no provider requests, no Spotify playlist writes.
- This validates the maintainer preview against the published full catalogue without mutating it. An actual `--apply --repair-index` remains unnecessary while the current index is healthy.
- Next: extend health validation to market-aware playability observation consistency and retain preview-only default.

## 2026-11-02 — Merge safe derived-index maintainer

- PR #80 merged to `main`: https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/80
- Added `scripts/music/library_maintenance.py` and `python shit.py library maintain`.
- Default mode is read-only. Apply requires both `--apply --repair-index`.
- Preview builds the proposed index in a temporary workspace over the canonical records, compares existing song/artist/album keys and all alias maps, and refuses if anything would be lost or if record-level health findings are present.
- Apply creates a timestamped backup of the old index, atomically replaces only `library_index.json`, runs the read-only health check, and rolls back if post-repair errors or warnings remain.
- Tests cover preview no-write behavior, unindexed records, missing index recovery, explicit apply, backup creation, and refusal to drop aliases. Full CI and secret scan passed on the final PR head.
- Scope is intentionally narrow: it does not rewrite song identities, metadata evidence, provider observations, or playlist state. No real Library repair was applied; this was implementation/test work only.
- Next: validate the preview on a disposable copy of the full canonical Library before using apply against main. Broader maintenance remains separately scoped.

## 2026-11-02 — Merge and run health checker against full catalogue

- PR #73 merged to main: https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/73
- CI ran `python shit.py library health --json` against the full published Library.
- Result: `ok: true`; 13,005 songs, 6,386 artists, 7,861 albums; index counts match exactly; 1,856 Spotify IDs, 11,338 recording MBIDs, 1,816 ISRCs, 13,003 source-track IDs, 11,529 name-candidate aliases; zero errors and zero warnings.
- This is a read-only scan; it does not rebuild or repair records. The separate data maintainer remains unimplemented.
## 2026-11-02 — Implement read-only structural health checker (draft)

- Added `scripts/music/library_health.py` with a standalone, read-only scanner. It deliberately avoids `MusicLibrary()` because the resolver constructor can rebuild and write the index.
- Checks JSON parseability, record IDs, stable shard-path convention, index collection shape/targets, path traversal, aliases/candidate lists, song→artist/album references, album→song/artist references, and unindexed/orphan records.
- Produces human-readable or JSON output with counts, errors, warnings, and an exit status.
- Added `python shit.py library health` and `--json` CLI support.
- Added fixture tests for a valid library, no-write behavior, dangling aliases/relations, malformed JSON, and path traversal.
- Branch: `feature/library-health-checker`; not merged. CI not yet verified.
- **Not implemented:** the data maintainer/apply-repair command. Repairs remain a separate opt-in design requiring backup, atomic writes, idempotence, and a repair journal.
- Next: run CI, fix failures, then test against a copy of the actual staged Library and inspect warnings before considering any repair.
# Actions — Library Health Checker & Data Maintainer

## 2026-11-02 — Initial design and boundaries

- Recorded the requested automated health checker and data maintainer as a distinct project goal.
- Inspected current `MusicLibrary.audit()`, `library_cli.py`, canonical song README, and current manifest.
- Existing support: `status` reports indexed entity/alias counts; `audit` delegates to `MusicLibrary.audit()`; library index can rebuild from canonical records when key collections are empty.
- Missing/uncertain: comprehensive health severity/report schema, full path/index/relationship checks, maintenance preview/apply separation, repair journal, and safe repair policy.
- Decision: health check is read-only; maintenance is a separate opt-in action. Never auto-repair identity ambiguity or overwrite source evidence.
- No code execution or Library mutation performed in this documentation pass.
- Next: inspect full audit implementation and tests, specify deterministic issue codes and fixture cases, implement health report first, then safe repair subset.
