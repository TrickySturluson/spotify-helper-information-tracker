# Actions — Metadata Freshness & Partial Revalidation

## 2026-11-02 — Initial design and boundaries

- Captured the requirement for infrequent/partial lookups to identify and refresh outdated metadata.
- Inspected `prepare_music_library.py`: enrichment is already bounded by per-provider limits and individual scripts/checkpoints, but it is a sequential full preparation plan rather than a unified per-field freshness planner.
- Decision: reuse provider-specific caches/checkpoints and the planned retry queue; do not build a second retry engine. Freshness must be field/provider scoped, with a deterministic rotating sample and separate planning/execution.
- Initial cadence concept: local health checks daily/on publish; small provider-backed partial refresh weekly/monthly or targeted on demand. Actual intervals remain configurable and must be grounded in provider policies.
- No provider requests or data mutations performed in this documentation pass.
- Next: inspect existing state schemas and retry queue specification; define stable planner output and due rules before implementing.
