# The Library — staged batch

This directory contains a staged migration of the 50 highest-priority unique songs in the saved 90-day Last.fm recent-track view, joined to their existing track profiles by verified MusicBrainz recording MBID.

- `library_index.json` is the resolver index.
- `artists/` and `songs/` contain one JSON record per entity.
- `albums/` is intentionally empty: these source rows did not include release identities.
- `migration_report.json` records coverage and migration boundaries.

This is a partial validation batch, not the full catalogue migration. The legacy aggregate files remain unchanged. The migration used no provider requests and did not touch Spotify playlists. Run `python compat/migrate_music_library.py --dry-run` before a full local migration.

