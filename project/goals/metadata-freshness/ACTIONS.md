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
