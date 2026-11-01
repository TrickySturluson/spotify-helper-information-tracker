# Album records

This directory contains ID-sharded release/album records.

- `<shard>/<stable-id>/album.json` — release identity, related song IDs, album-scoped evidence, source links, and field-level metadata confidence.
- Album evidence may include a verified Last.fm tracklist, short attributed summary, artwork reference, provider URL, community tags, and Discogs release context.
- `../library_index.json` maps release IDs to album record paths.
- `../songs/` contains individual songs with explicit album relationships when verified.

## First worked example

`al/album-3858c5d33d8c2159eb3d/album.json` represents Candy Claws' *Ceres & Calypso in the Deep Time* (standard 12-track album, not the expanded anniversary reissue). Its Spotify album ID is grounded in existing playlist snapshots; descriptive metadata and the ordered tracklist are attributed to Last.fm and the artist's Bandcamp page.

Four already-staged song records are linked to this album by exact title/artist plus their existing recording MBIDs. The other eight tracklist entries remain album-level tracklist entries only; no song records or recording identities are invented for them.

A release tracklist describes a release, not every version of a recording. Keep track position, disc number, release MBID, and source provenance. Album tags/descriptions provide contextual evidence only and must never increase track-level acoustic confidence.
