# The Library — staged batch

This directory contains the staged 100-song sample from the saved 90-day Last.fm recent-track view, plus a first release-level album example.

- `library_index.json` is the compact resolver index for songs, artists, albums, Spotify IDs, recording MBIDs, ISRCs, source IDs, and exact-name candidate lists.
- `artists/` and `songs/` contain one JSON record per entity.
- `albums/` contains release-scoped album records. The first example is **Candy Claws — Ceres & Calypso in the Deep Time**.
- `migration_report.json` records coverage and migration boundaries.

## Album example

`albums/sp/spotify-5kkgazrad4n4rc5friwgz/album.json` stores the 12-track ordered tracklist, approximate durations, release date, Last.fm community tags, a short attributed description, source links, confidence by field, and the Spotify album ID observed in saved playlist snapshots.

The artist record links to the album, and four existing song records are linked to it only where the artist/title and recording MBID already match the staged sample. The album's full tracklist is not treated as proof that every track is present in the song library or that every recording belongs to this release. This makes the example useful for testing album recall without manufacturing 12 song identities.

The sample remains partial, not a full catalogue migration. Legacy aggregate files remain unchanged. Migration is local-only and makes no provider requests; it does not edit Spotify playlists. Run `python compat/migrate_music_library.py --dry-run` before a full local migration.
