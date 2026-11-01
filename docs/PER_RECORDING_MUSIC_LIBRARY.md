# Per-recording music library

## Purpose

The normalized library makes one recording's metadata retrievable without loading
the complete track, audio, artist, and album aggregates. Individual JSON records
are canonical evidence stores; `library_index.json` is a small resolver index.

## Layout

```text
assistant_data/music/music_library/
  library_index.json
  artists/<shard>/<stable-id>/artist.json
  albums/<shard>/<stable-id>/album.json
  recordings/<shard>/<stable-id>/recording.json
```

Stable IDs prefer verified MusicBrainz MBIDs. Spotify track IDs are retained as
recording aliases. When neither exists, deterministic fallback IDs include
artist, album/release context, title, and duration where available. Name-only
lookups retain all candidates and refuse to choose when multiple versions match.
A fallback identity is explicitly marked as such; it is not represented as a
verified recording match.

Recording files keep track metadata, audio observations, lyric analysis, derived
features, coverage, source status, and artist/album relations in separate fields.
Artist and album evidence remains contextual and is never copied into the
recording's track-specific evidence.

## Migration

Run a dry-run first, then migrate locally:

```bash
python scripts/music/migrate_music_library.py --dry-run
python scripts/music/migrate_music_library.py
```

Migration is local-only. It makes no provider requests, does not modify the
legacy aggregate JSON, and can be repeated to refresh the normalized records.
The old aggregates remain available for rollback and incremental compatibility.

## Lookup behavior

The sequencer first resolves each playlist item by Spotify track ID, then by
verified recording MBID, then by an exact artist/title alias only when unique.
An album name may disambiguate otherwise ambiguous versions. It loads the
recording plus its related artist and album files on demand. If the library
does not exist, the existing aggregate path remains active; during migration,
missing individual records may still fall back to legacy track metadata.

## Boundaries and maintenance

- No metadata provider is called by the migration or lookup layer.
- The JSON index contains paths and aliases, not duplicated provider evidence.
- Preserve source provenance and raw observations; rebuild derived features
  from source data rather than treating derived labels as new evidence.
- Do not resolve collisions by selecting the first artist/title match.
- The initial migration is deliberately conservative. Provider aggregates
  with uncertain identity remain attached only when their source row carries
  an exact artist/title match.
