# Spotify Track Playability & Availability — Actions & Evidence

Newest entries first. Record verified outcomes separately from plans, assumptions and unverified artifacts.

## 2026-11-06 — Reference Library refresh distinguished from playability refresh

- Reference Library workflow #42146148971 completed and committed repository snapshots/removal state as `3e989e33282efab6cc1416e35970e7c59af5f056`.
- This was a read-only Spotify playlist snapshot refresh plus local repository-state publication; it did not mutate Spotify playlists.
- Do not count it as the explicit market-aware `refresh-playability` operation or as proof that all saved tracks have fresh `from_token` market observations. The last explicit playability backfill remains the previously documented PR #78 / issue #82 evidence until a separate bounded refresh is verified.
- This goal's feature work remains paused until documentation acceptance criteria pass.

## 2026-11-02 — Merge market-aware refresh and backfill saved observations

- PR #78 merged to `main` as `e12b72ee24f1440115961282cd7baf7879ebeec8`.
- Adds authenticated-user market context (`from_token`), individual Spotify Get Track lookups, requested/relinked ID preservation, offline snapshot backfill, and a bounded stale-only refresh planner (default 25, 90-day freshness, maximum 50 requests per run).
- CI and full-history security scan passed on the final PR head. The missing `datetime/timezone` import in the planner test was fixed before merge.
- Added the `backfill-playability` operation to the Great Migration workflow. It stages only canonical song records; backups are preserved in the workflow artifact. It does not refresh Spotify snapshots or write playlists.
- **Offline backfill run #82:** [workflow run](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41369906166), issue #82. Published commit `3316dbe9f8ccd5d668b71d730016befeabdd8502`; 1,856 canonical song files changed.
- Backfill scanned 57 saved snapshots (16 inaccessible), 3,308 playlist items, found 3,308 observations, matched 3,306 items to canonical songs, and updated 3,305 observations across 1,856 song records. Two items were unmatched; none were already present.
- Snapshot observations: 3,250 playable and 55 unplayable, all under `market=from_token`; zero restriction-reason records and zero relinked-ID cases in this batch. These are snapshot-time observations, not a claim that all songs remain playable now.
- Provider requests: 0. Spotify playlist writes: 0. Backups are in artifact #13108782697; the backup directory was not committed into the canonical Library.
- Next: run post-backfill `audit`, `health`, and `confidence` against published main; then run a bounded live refresh only for stale records, after checking the current Spotify account market and rate-limit behavior.
- No live playability API refresh has been executed.

## 2026-11-02 — Add bounded current playability refresh

- Added a stale-only refresh planner over canonical Spotify IDs. It defaults to 25 tracks per run, a 90-day freshness interval, and caps a run at 50 individual lookups.
- Uses `GET /tracks/{id}?market=from_token`; does not use deprecated bulk `GET /tracks`. The official Spotify Track Relinking guide confirms `from_token` uses the user's account country, `is_playable=false` means no playable relink was found, and `linked_from` identifies the original recording when returned.
- A direct check records requested ID (the path ID), returned/relinked ID, market, status, restrictions, response code, source and check time. Missing `is_playable` or a 404 is recorded as unknown, not false.
- The planner skips recent observations and always rechecks when the latest playlist snapshot is inaccessible. Execute mode creates a backup of affected song files before updates; dry-run is the default and provider requests require both `--execute --yes`.
- Added tests for bounded planning, recent-check skipping, relinked ID preservation, backup creation and 404-as-unknown.
- PR #78 remains draft; CI pending. No provider calls have been made.
- References: [Get Track](https://developer.spotify.com/documentation/web-api/reference/get-track), [Track Relinking](https://developer.spotify.com/documentation/web-api/concepts/track-relinking), [Get Several Tracks](https://developer.spotify.com/documentation/web-api/reference/get-several-tracks) (deprecated; not used).
## 2026-11-02 — Market-aware playability and offline backfill implementation (PR #78)

- Added optional market support to Spotify playlist item reads; the reference-library sync explicitly requests market=from_token while other playlist-manager callers retain their existing default request behavior.
- Spotify documents from_token as the authenticated user's country. The API response's is_playable is market-specific and appears when Track Relinking is applied; linked_from identifies the originally requested track when a replacement is returned.
- Updated observations to store market context, status, restrictions, check timestamp, requested original Spotify ID, returned/relinked Spotify ID, linked_from ID, playlist/snapshot context, and latest snapshot accessibility.
- Relinked replacement metadata is not merged into the original song identity. The playability observation is attached to the existing original song record; unknown IDs are skipped rather than creating new records.
- Added an append-only MusicLibrary.add_spotify_playability_observation() method that preserves history and deduplicates exact repeats.
- Added backfill_playability_from_snapshots() / CLI backfill-playability: reads saved playlist JSON only, makes no Spotify requests, backs up affected song files, and appends observations to existing song records.
- Added tests for market query behavior, explicit unknown vs false, restricted state, relinking IDs, append-only updates, no accidental record creation, and offline backup-protected backfill.
- Updated song-record guide and file overviews.
- PR #74 (confidence audit) is merged, so the base-branch CI workflow includes its confidence-report step.
- Branch: feature/market-aware-playability-v2; not merged; CI pending. No live sync or backfill has been run.
- Next: run PR CI, fix failures, merge only after checks pass; then run offline backfill once against saved snapshots and inspect counts/backup. Afterward perform a bounded live reference-library sync to refresh current playability with latest main/checkpoints, recording inaccessible playlists as stale rather than empty.

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

## 2026-11-02 — Initial design and boundaries

- Captured the user's requirement to distinguish tracks that can be added to Spotify playlists from tracks that can actually be played.
- Inspected the canonical song schema overview and Library merge logic. Song records have an extensible `evidence.track_metadata` area, but a dedicated market-scoped playability schema is not yet documented or verified.
- Decision: store observations per market with timestamp, source, restriction reason, requested/returned IDs, and relink metadata. Do not store a timeless global boolean.
- Capture fields from existing read-only Spotify snapshots first; only then consider bounded API spot-checks. No playlist writes.
- No Spotify API calls or playlist changes performed in this documentation pass.
- Next: inspect current Spotify snapshot object shapes and Spotify API behavior at implementation time; add tests for addable-but-unplayable, market differences, unknown results, and relinking.
