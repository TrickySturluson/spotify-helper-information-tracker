# The Library — catalogue navigation

The per-recording Library structure was merged into main in [PR #49](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/49). The Great Migration has since populated the canonical catalogue and subsequent enrichment passes have been published.

## Current published catalogue

- The latest canonical Library audit in Enrich Music Metadata run [#42166959478](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42166959478) reported **13,239 songs** after the discovery-candidate merge; publication commit: `3d2c1ded`.
- The legacy Last.fm-derived track index contains 11,130 unique track identities; the published duration overview reports 8,254 tracks with sourced durations and 139,758/152,005 scrobbles covered (91.943%).
- All 5,358 legacy Last.fm artist identities remain represented in the source analytics index. Do not infer that every canonical artist/album entity count is the same as a legacy aggregate count.
- The catalogue also contains Spotify playlist-only and discovery-candidate tracks, including exact playlist-only candidates even when they have zero Last.fm scrobbles. Playlist membership is source/context evidence, not a play, like, save, or proof of listening; it remains distinct from measured Spotify playback.
- The post-enrichment project integrity audit completed 9 checks with 18 warnings and zero errors. The warnings include 16 Spotify playlist snapshots whose item contents were inaccessible and no captured measured-playback intervals; inaccessible snapshots are not empty and retained contents may be stale.
- **Stale report warning:** `migration_report.json` still records the earlier 13,005-song migration snapshot from 2026-11-01. It is historical migration evidence, not the current canonical count. Use a fresh canonical Library audit/health report for current entity counts.
- Metadata coverage remains incomplete; use the current generated manifests and source-specific reports rather than treating this snapshot as a timeless guarantee.


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
