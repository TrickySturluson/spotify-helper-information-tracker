# Actions — Spotify Track Playability & Availability

## 2026-11-02 — Initial design and boundaries

- Captured the user's requirement to distinguish tracks that can be added to Spotify playlists from tracks that can actually be played.
- Inspected the canonical song schema overview and Library merge logic. Song records have an extensible `evidence.track_metadata` area, but a dedicated market-scoped playability schema is not yet documented or verified.
- Decision: store observations per market with timestamp, source, restriction reason, requested/returned IDs, and relink metadata. Do not store a timeless global boolean.
- Capture fields from existing read-only Spotify snapshots first; only then consider bounded API spot-checks. No playlist writes.
- No Spotify API calls or playlist changes performed in this documentation pass.
- Next: inspect current Spotify snapshot object shapes and Spotify API behavior at implementation time; add tests for addable-but-unplayable, market differences, unknown results, and relinking.
