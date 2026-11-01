# Song records

This directory contains ID-sharded song records.

- `<shard>/<stable-id>/song.json` — one song's identity, track metadata, audio evidence, lyric evidence, derived features, coverage, source status, and relations.
- `../library_index.json` — maps Spotify IDs, recording MBIDs, ISRCs, source IDs, and exact artist/title candidate lists to song records.
- `../artists/` and `../albums/` — related entity records.

Stable IDs and aliases are resolved conservatively. Name collisions remain
candidate lists. Album/artist context never becomes track-specific acoustic
evidence.
