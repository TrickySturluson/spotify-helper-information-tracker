# The Library — staged batch

This directory contains two staged batches totaling 100 unique songs from the saved 90-day Last.fm recent-track view. The second batch also preserves stable source-profile IDs where a verified recording MBID was unavailable.

- `library_index.json` is the resolver index.
- `artists/` and `songs/` contain one JSON record per entity.
- `albums/` is intentionally empty: these source rows did not include release identities.
- `migration_report.json` records coverage and migration boundaries.

The current sample has 100 song records and 47 artist identity records; album records remain empty because the staged track rows did not prove release membership. This is a partial validation batch, not the full catalogue migration. The legacy aggregate files remain unchanged. The migration used no provider requests and did not touch Spotify playlists. Run `python compat/migrate_music_library.py --dry-run` before a full local migration.

