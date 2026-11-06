# The Library — catalogue navigation

The per-recording Library structure was merged into main in [PR #49](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/49). The Great Migration has since populated the canonical catalogue and subsequent enrichment passes have been published.

## Current published catalogue

- Latest read-only catalogue check: Daily curator CI [#42154433350](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42154433350), generated 2026-11-06T03:06:25Z, scanned **13,163 songs, 6,497 artists, and 7,969 albums**. Index counts matched those canonical counts exactly.
- Latest alias counts: 1,991 Spotify IDs, 11,338 recording MBIDs, 1,904 ISRCs, 13,163 source-track IDs, and 11,651 name-candidate keys.
- The read-only Library health report returned `ok=true`, zero errors and zero warnings. The separate repository audit reported 18 warnings (no playback intervals plus 16 inaccessible Spotify playlist snapshots, including the summary warning); these are not Library structural-health warnings.
- The legacy Last.fm-derived track index still has 11,130 historical track identities and all 11,130 were previously cross-checked against canonical source-track-ID or recording-MBID aliases. All 5,358 legacy artist names were previously represented.
- The older 13,005 / 6,386 / 7,861 count is a historical migration baseline, superseded by the 2026-11-06 read-only check above. Run #18's 91.1% duration coverage of 152,005 scrobbles is also historical; do not quote it as current coverage. Metadata and audio-feature coverage remain incomplete; see the Great Migration, confidence and enrichment goal workspaces.

The raw Last.fm event archive remains separate. The Library stores normalized song/artist/album entities and evidence; it does not replace the original per-scrobble event history.

## Start here

- [Artist records](artists/README.md) — artist identity, sourced artist-level context, and related albums/songs.
- [Album records](albums/README.md) — release identity, album overview, ordered tracklist, sources, and confidence.
- [Song records](songs/README.md) — per-recording identity, track metadata, evidence, and relationships.
- [Library index](library_index.json) — compact resolver mapping stable IDs and names to record paths.
- [Migration report](migration_report.json) — migration counts, source coverage and remaining limitations. Its legacy limitation text is being reconciled with the direct source-index coverage check.

## Directory map

| Folder/file | What it contains |
|---|---|
| `artists/<shard>/<stable-id>/artist.json` | One canonical artist record per identity |
| `albums/<shard>/<stable-id>/album.json` | One release-scoped album record per album identity |
| `songs/<shard>/<stable-id>/song.json` | One song/recording record per known identity |
| `library_index.json` | Lookup index for artists, albums, songs, and candidate aliases |
| `migration_report.json` | Migration and enrichment coverage, source provenance, and limitations |

Open the folder-level README files first; each describes the records below it and the identity/evidence rules that apply.

## First album example

[**Candy Claws — Ceres & Calypso in the Deep Time**](albums/al/album-01632cb9b68c6acda89d/album.json) is the first worked album record. Its record contains a sourced album overview and 12-position tracklist. Four existing song records are linked only where artist/title and the existing recording MBID match. The other eight tracks remain album-level entries; their recording identities are not invented.

## Data and safety rules

- Identity fields and metadata evidence are separate.
- Every descriptive claim should retain its source and field-level confidence where available.
- Album tags and descriptions are contextual evidence, not track-level acoustic measurements.
- Tracklist membership alone does not prove that a song record or specific recording identity exists.
- Unknown or ambiguous identities remain explicit; a missing provider field is not an invitation to guess.
- The offline `migrate` operation imports stored data without provider calls or Spotify playlist edits. The `prepare` operation orchestrates migration plus bounded provider enrichment; the current workflow skips Spotify snapshot refresh and does not write to playlists.
- For local inspection, run `python shit.py library status`, `python shit.py library audit`, and `python shit.py library health` (the read-only health command is available in main). Use `python shit.py library prepare --execute --yes` only when credentials, backups, checkpoints, and publication safeguards are configured.
