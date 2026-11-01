# The Library — catalogue navigation

The per-recording Library structure was merged into `main` in [PR #49](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/49). The committed records are currently a **staged sample**, not the full historical catalogue. The Great Migration must populate the canonical structure from the legacy listening and metadata datasets before downstream analytics or the sorter can rely on it.

## Start here

- [Artist records](artists/README.md) — artist identity, sourced artist-level context, and related albums/songs.
- [Album records](albums/README.md) — release identity, album overview, ordered tracklist, sources, and confidence.
- [Song records](songs/README.md) — per-recording identity, track metadata, evidence, and relationships.
- [Library index](library_index.json) — compact resolver mapping stable IDs and names to record paths.
- [Migration report](migration_report.json) — staged coverage and migration boundaries.

## Directory map

| Folder/file | What it contains |
|---|---|
| `artists/<shard>/<stable-id>/artist.json` | One canonical artist record per identity |
| `albums/<shard>/<stable-id>/album.json` | One release-scoped album record per album identity |
| `songs/<shard>/<stable-id>/song.json` | One song/recording record per known identity |
| `library_index.json` | Lookup index for artists, albums, songs, and candidate aliases |
| `migration_report.json` | What was migrated and what remains incomplete |

Open the folder-level README files first; each describes the records below it and the identity/evidence rules that apply.

## First album example

[**Candy Claws — Ceres & Calypso in the Deep Time**](albums/al/album-01632cb9b68c6acda89d/album.json) is the first worked album record. Its record contains a sourced album overview and 12-position tracklist. Four existing song records are linked only where artist/title and the existing recording MBID match. The other eight tracks remain album-level entries; their recording identities are not invented.

## Data and safety rules

- Identity fields and metadata evidence are separate.
- Every descriptive claim should retain its source and field-level confidence where available.
- Album tags and descriptions are contextual evidence, not track-level acoustic measurements.
- Tracklist membership alone does not prove that a song record or specific recording identity exists.
- The staged sample is partial, not a full catalogue migration. Legacy aggregate files remain unchanged until the migration is executed and published.
- The offline `migrate` operation imports existing data without provider calls or Spotify playlist edits. The `prepare` operation orchestrates migration plus bounded provider enrichment; its workflow skips Spotify snapshot refresh and does not write to playlists.
- For local inspection, run `python shit.py library status`, then `python shit.py library preview`. Use `python shit.py library prepare --execute --yes` only when credentials, backups, checkpoints, and publication safeguards are configured.
