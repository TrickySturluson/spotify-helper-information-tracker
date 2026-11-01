# Album records

## About this folder

This folder stores one JSON record per album/release identity. Album records should have a concise **About** overview alongside release metadata, an ordered tracklist, source provenance, field-level confidence, and links to song records only when the relationship is supported.

## How to navigate

- Album record format: `<shard>/<stable-id>/album.json`
- [Library index](../library_index.json) maps album IDs and artist/title pairs to record paths.
- [Artist records](../artists/README.md) hold artist-level identity and context.
- [Song records](../songs/README.md) hold recording-specific identity and evidence.

## About section schema

Album records may contain an `about` object with:

- `summary` — short paraphrased overview of the album.
- `summary_attribution` and `source_url` — who/what the summary is based on.
- `source_family` — provider or source family.
- `confidence` — confidence in the description, kept separate from recording identity confidence.
- `note` — important limits on interpretation.

The About text must be concise and attributed; do not copy long provider biographies or wiki text. Album descriptions and tags are context only and must never increase track-level acoustic confidence.

## First worked example

[**Candy Claws — Ceres & Calypso in the Deep Time**](al/album-01632cb9b68c6acda89d/album.json) is the standard 12-track album, distinct from the expanded anniversary reissue. Its Spotify album ID is corroborated by existing playlist snapshots; the ordered tracklist is attributed to Last.fm and cross-checked against the artist's Bandcamp page.

Four existing song records are linked by their current recording MBIDs and matching artist/title. The remaining eight tracklist entries are not treated as verified song identities. Release tracklists describe a release; they do not, by themselves, identify every recording/version.
