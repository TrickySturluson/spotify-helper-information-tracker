# Artist records

## About this folder

This folder stores one JSON record per canonical artist identity. Each record is intended to be the artist-level source of truth: identity identifiers, an optional **About** summary, source provenance, confidence, and links to associated album records. The overview should describe the artist, not a single track or release.

## How to navigate

- Artist record format: `<shard>/<stable-id>/artist.json`
- [Library index](../library_index.json) maps artist IDs and names to record paths.
- [Album records](../albums/README.md) contain release-specific details.
- [Song records](../songs/README.md) contain recording-specific details.

Example: [Candy Claws artist record](mb/mbid-da5eaa3b-397e-4af8-9a12-5c4ec93e8b48/artist.json).

## About section schema

Artist records may contain an `about` object with:

- `summary` — short, attributed artist overview; null if not yet sourced.
- `status` — whether the summary is sourced or awaiting research.
- `sources` — source URLs/provider identifiers supporting the overview.
- `confidence` — confidence in the artist-level description.
- `note` — guardrails or attribution notes.

Do not fabricate a biography to fill the field. If a reliable artist-level source has not been checked, leave the summary null and mark it as not yet sourced. Artist tags and biographies remain artist-level context; they must not be copied into track-specific evidence or acoustic measurements.
