## 2026-11-02 — Merge initial snapshot playability persistence

- PR #72 merged to main: https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/72
- Existing read-only Spotify snapshot ingestion now stores explicit `is_playable`, restrictions, timestamps, and relinking identifiers under song evidence.
- Initial version intentionally left market as unknown and did not backfill old snapshots. Follow-up PR #75 adds explicit `market=from_token`, correct original-vs-returned ID handling, and backup-protected offline backfill.
- No live sync or backfill has been run yet; no playlist writes.
## 2026-11-02 — Capture playability from existing read-only Spotify snapshots

- Inspected `scripts/spotify/spotify_reference_library.py`: `item_record()` already captured `is_playable` and `linked_from`, but `sync()` did not pass those fields into the canonical Library.
- Implemented on draft branch `feature/library-playability-observations`:
  - Preserve explicit presence of `is_playable`, the raw nullable value, restrictions, and the time the item response was fetched.
  - Pass an observation to the canonical Library with status, market (`unknown` unless explicitly known), timestamp, Spotify source, playlist/snapshot context, requested/returned IDs, relink URI/ID, restriction details, and local-track context.
  - Store observations under `song.json` `evidence.spotify_playability`; keep observation history and a latest-by-market convenience map.
  - Preserve old observations across catalogue syncs and deduplicate exact repeated observations.
  - Missing `is_playable` is not converted to false; restricted responses retain the restriction reason.
- Added regression tests for explicit unplayable vs missing values, market-scoped history, restriction state, relink ID preservation, and idempotent duplicate ingestion.
- Updated the song-record guide and file overview comments.
- **Not yet verified:** branch CI has not run to completion; this is not merged and no existing canonical data has been rewritten. Existing playlist snapshots are not yet backfilled into song records.
- **Safety:** no Spotify API request or playlist mutation was made; the implementation only consumes fields from the existing read-only snapshot sync.
- Next: run PR CI, repair any failures, verify fixture output, merge only after checks pass, then perform a bounded offline backfill from saved playlist snapshots. Later add explicit-market spot checks only after verifying current Spotify API behavior and configured market semantics.
# Actions — Spotify Track Playability & Availability

## 2026-11-02 — Initial design and boundaries

- Captured the user's requirement to distinguish tracks that can be added to Spotify playlists from tracks that can actually be played.
- Inspected the canonical song schema overview and Library merge logic. Song records have an extensible `evidence.track_metadata` area, but a dedicated market-scoped playability schema is not yet documented or verified.
- Decision: store observations per market with timestamp, source, restriction reason, requested/returned IDs, and relink metadata. Do not store a timeless global boolean.
- Capture fields from existing read-only Spotify snapshots first; only then consider bounded API spot-checks. No playlist writes.
- No Spotify API calls or playlist changes performed in this documentation pass.
- Next: inspect current Spotify snapshot object shapes and Spotify API behavior at implementation time; add tests for addable-but-unplayable, market differences, unknown results, and relinking.
