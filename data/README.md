# Canonical data archive — file overview

This directory holds the source-side Last.fm archive and its small metadata/statistics companions. It is the durable historical input to SHIT's Last.fm analytics, distinct from generated products under `assistant_data/` and measured Spotify playback under `playback_data/`.

- `scrobbles.json`: canonical chronological Last.fm scrobble records. Treat this as source history; do not add comments or manually rewrite records.
- `metadata.json`: archive synchronization state, including the latest imported timestamp, scrobble count, and update time.
- `stats.json`: a generated snapshot of archive-wide statistics. Its listening-time estimate uses the documented legacy average-duration method; it is not a measured Spotify playback total.

Use `scripts/lastfm/update_lastfm.py` (or the legacy `compat/update_lastfm.py` entry point) to update the archive. Analytics builders under `scripts/analytics/` consume this data and write derived results under `assistant_data/`. Keep Last.fm scrobbles separate from measured Spotify playback records. This repository is public: the archive's exact timestamps, listening history, artist/track identities, and URLs are published. Treat it as an intentionally public personal listening diary, not anonymized telemetry; see `docs/PUBLIC_REPOSITORY_PRIVACY.md`.
