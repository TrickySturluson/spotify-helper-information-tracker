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
python scripts/music/migrate_music_library.py --recent-limit 50
```

A bounded recent batch carries play counts in a separate listening-context field;
missing album information does not create placeholder album records. Migration
is local-only. It makes no provider requests, does not modify the legacy
aggregate JSON, and can be repeated to refresh the normalized records. The old
aggregates remain available for rollback and incremental compatibility.

The initial staged validation batch (historical; not a current Library count)
contained 50 unique recent songs and 22 artist identity records. It had no album
records because those source track profiles did not contain release metadata;
seven songs had track-tag evidence, while 43 preserved an explicit no-tag/empty-
evidence state. This was a partial integration sample, not the full migration.
Use the current Library status/health reports for live record counts.

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
