# Actions — Library Health Checker & Data Maintainer

## 2026-11-02 — Initial design and boundaries

- Recorded the requested automated health checker and data maintainer as a distinct project goal.
- Inspected current `MusicLibrary.audit()`, `library_cli.py`, canonical song README, and current manifest.
- Existing support: `status` reports indexed entity/alias counts; `audit` delegates to `MusicLibrary.audit()`; library index can rebuild from canonical records when key collections are empty.
- Missing/uncertain: comprehensive health severity/report schema, full path/index/relationship checks, maintenance preview/apply separation, repair journal, and safe repair policy.
- Decision: health check is read-only; maintenance is a separate opt-in action. Never auto-repair identity ambiguity or overwrite source evidence.
- No code execution or Library mutation performed in this documentation pass.
- Next: inspect full audit implementation and tests, specify deterministic issue codes and fixture cases, implement health report first, then safe repair subset.
