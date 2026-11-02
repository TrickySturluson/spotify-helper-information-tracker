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
