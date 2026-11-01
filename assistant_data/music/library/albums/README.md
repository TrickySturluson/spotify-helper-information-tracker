# Album records

This directory contains ID-sharded release/album records.

- `<shard>/<stable-id>/album.json` — release identity, related song IDs, and album-scoped evidence.
- Album evidence may include a verified Last.fm tracklist, short attributed summary, artwork reference, provider URL, tags, and Discogs release context.
- `../library_index.json` — maps release IDs to album record paths.
- `../songs/` — individual songs with explicit album relationships when verified.

A release tracklist does not automatically prove that a song is the same
recording or release. Keep track position, disc number, release MBID, and source
provenance. The directory may be empty until source rows establish release
membership.
