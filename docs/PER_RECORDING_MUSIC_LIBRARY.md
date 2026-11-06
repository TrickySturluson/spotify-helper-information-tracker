# The Library

## Purpose

The Library makes one song's metadata retrievable without loading
the complete track, audio, artist, and album aggregates. Individual JSON records
are canonical evidence stores; `library_index.json` is a small resolver index.

## Layout

```text
assistant_data/music/library/
  library_index.json
  artists/<shard>/<stable-id>/artist.json
  albums/<shard>/<stable-id>/album.json
  songs/<shard>/<stable-id>/song.json
```

Stable IDs prefer verified MusicBrainz MBIDs, followed by Spotify track IDs.
When neither exists, a stable source-profile ID is retained as a non-verified
fallback so same-title releases do not collapse just because album metadata is
missing. If no source ID exists, the fallback uses available artist, release
context, title, and duration. Name-only lookups retain all candidates and refuse
to choose when multiple versions match. Fallback identities are explicitly
marked; they are never represented as verified song matches.

Song files keep track metadata, audio observations, lyric analysis, derived
features, coverage, source status, and artist/album relations in separate fields.
Artist and album evidence remains contextual and is never copied into the
song's track-specific evidence.

## Migration

Run a dry-run first, then migrate locally:

```bash
python scripts/music/migrate_music_library.py --dry-run
python scripts/music/migrate_music_library.py

# Optional staged migration: up to 50 unique songs from recent listening
python scripts/music/migrate_music_library.py --recent-limit 50 --dry-run
```

A bounded recent batch carries play counts in a separate listening-context field;
missing album information does not create placeholder album records. This legacy
compatibility path is local-only and makes no provider requests or legacy-archive
changes. The direct `--recent-limit` write path does not create its own backup and
defaults to the canonical Library root; do not execute it against that root unless
a separate verified backup exists. Use the supported full migration command
`python shit.py library migrate --yes` for canonical migration; it creates a
timestamped backup when an existing indexed Library is present. Legacy aggregate
exports remain untouched, but they are not a backup of canonical Library writes.

The initial staged validation batch (historical; not a current Library count)
contained 50 unique recent songs and 22 artist identity records. It had no album
records because those source track profiles did not contain release metadata;
seven songs had track-tag evidence, while 43 preserved an explicit no-tag/empty-
evidence state. This was a partial integration sample, not the full migration.
Use the current Library status/health reports for live record counts.

## Spotify reference-snapshot integration

`scripts/spotify/spotify_reference_library.py sync` is read-only against Spotify playlists, but it does write repository data. For non-relinked playlist tracks it sends catalogue rows through `MusicLibrary.put_catalogue()`, preserving Spotify track/artist/album identifiers, duration, ISRC where available, playlist source IDs/positions, and a `listening_context` whose source is explicitly `Spotify reference-library snapshot`. It also appends market-scoped, timestamped Spotify playability observations to matched song records.

This evidence has strict semantics:

- Playlist membership proves only that the track appeared in that playlist snapshot at that time. It does **not** prove the user played, liked, saved, or listened to it.
- These rows are not Last.fm scrobbles and are not measured Spotify playback. The canonical Last.fm event archive remains the historical listening source of truth.
- Playability is a snapshot-time, market-scoped observation, not a timeless boolean.
- Requested and relinked Spotify IDs remain distinct; replacement-recording metadata must not be merged into the original requested song identity.
- An inaccessible or incomplete playlist is not an empty playlist. Retain prior complete contents as stale evidence rather than erasing them.

The workflow writes Spotify snapshots/history/catalogue indexes and canonical Library evidence while making no playlist mutations. See [Spotify API operations](SPOTIFY_API_OPERATIONS.md) and [workflow catalogue](WORKFLOWS.md).

## Lookup behavior

The sequencer first resolves each playlist item by Spotify track ID, then by
verified recording MBID, then by an exact artist/title alias only when unique.
An album name may disambiguate otherwise ambiguous versions. It loads the
song plus its related artist file and, only when known, its album file on demand. If the library
does not exist, the existing aggregate path remains active; during migration,
missing individual records may still fall back to legacy track metadata.

## Boundaries and maintenance

- No metadata provider is called by the migration or lookup layer.
- The JSON index contains paths and aliases, not duplicated provider evidence.
- Preserve source provenance and raw observations; rebuild derived features
  from source data rather than treating derived labels as new evidence.
- Do not resolve collisions by selecting the first artist/title match.
- The migration is deliberately conservative. Provider aggregates with uncertain
  identity remain attached only when their source row carries an exact
  artist/title match. Use `MusicLibrary.audit()` to validate index aliases and
  referenced song/artist/album files.
