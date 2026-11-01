# Artist records

This directory contains ID-sharded artist records.

- `<shard>/<stable-id>/artist.json` — canonical artist identity and artist-scoped evidence.
- `../library_index.json` — maps artist IDs to record paths and display names.
- `../albums/` — albums associated with an artist when release identity is known.
- `../songs/` — song records associated with an artist.

Artist tags, biographies, and themes remain artist-level context; they are not
copied into track-specific evidence or acoustic measurements.
