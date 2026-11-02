# Song records

This directory contains ID-sharded song records.

- `<shard>/<stable-id>/song.json` — one song's identity, track metadata, audio evidence, lyric evidence, derived features, coverage, source status, and relations.
- `../library_index.json` — maps Spotify IDs, recording MBIDs, ISRCs, source IDs, and exact artist/title candidate lists to song records.
- `../artists/` and `../albums/` — related entity records.

## Spotify playability evidence

When a read-only Spotify snapshot includes playability data, the song record stores it under `evidence.spotify_playability`:
- `observations` preserves timestamped source observations.
- `latest_by_market` is a convenience view keyed by market; `UNKNOWN` means the response did not establish a market.
- Each observation can include `is_playable`, status, restriction reason, requested/returned Spotify IDs, relinking information, playlist/source context, and check time.

Playlist addability is not proof of playability. Missing `is_playable` is not false. Results are time-sensitive and market-scoped; never treat an unknown-market observation as a universal availability guarantee.

Stable IDs and aliases are resolved conservatively. Name collisions remain
candidate lists. Album/artist context never becomes track-specific acoustic
evidence.
