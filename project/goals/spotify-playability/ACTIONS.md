## 2026-11-02 — Market-aware playability and offline backfill implementation (draft)

- Added optional market support to Spotify playlist item reads; the reference-library sync explicitly requests market=from_token while other playlist-manager callers retain their existing default request behavior.
- Spotify documents from_token as the authenticated user's country. The API response's is_playable is market-specific and appears when Track Relinking is applied; linked_from identifies the originally requested track when a replacement is returned.
- Updated observations to store market context, status, restrictions, check timestamp, requested original Spotify ID, returned/relinked Spotify ID, linked_from ID, playlist/snapshot context, and latest snapshot accessibility.
- Relinked replacement metadata is not merged into the original song identity. The playability observation is attached to the existing original song record; unknown IDs are skipped rather than creating new records.
- Added an append-only MusicLibrary.add_spotify_playability_observation() method that preserves history and deduplicates exact repeats.
- Added backfill_playability_from_snapshots() / CLI backfill-playability: reads saved playlist JSON only, makes no Spotify requests, backs up affected song files, and appends observations to existing song records.
- Added tests for market query behavior, explicit unknown vs false, restricted state, relinking IDs, append-only updates, no accidental record creation, and offline backup-protected backfill.
- Updated song-record guide and file overviews.
- PR #74 (confidence audit) is now merged, so the base-branch CI workflow includes its confidence-report step.
- Branch: feature/market-aware-playability; not merged; CI rerun pending. No live sync or backfill has been run.
- Next: run PR CI, fix failures, merge only after checks pass; then run offline backfill once against saved snapshots and inspect counts/backup. Afterward perform a bounded live reference-library sync to refresh current playability with latest main/checkpoints, recording inaccessible playlists as stale rather than empty.
