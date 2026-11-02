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
