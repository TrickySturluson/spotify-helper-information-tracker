# Song records

This directory contains ID-sharded song records.

- `<shard>/<stable-id>/song.json` — one song's identity, track metadata, audio evidence, lyric evidence, derived features, coverage, source status, and relations.
- `../library_index.json` — maps Spotify IDs, recording MBIDs, ISRCs, source IDs, and exact artist/title candidate lists to song records.
- `../artists/` and `../albums/` — related entity records.

## Spotify playability evidence

When a Spotify playlist snapshot includes playability data, the song record stores it under `evidence.spotify_playability`:
- `observations` preserves timestamped source observations.
- `latest_by_market` is a convenience view keyed by market; `FROM_TOKEN` means Spotify used the authenticated user's account country.
- Each observation includes `is_playable`, status, restriction reason, requested/returned Spotify IDs, relinking information, playlist/source context, and check time.
- Status distinguishes `playable`, `unplayable`, `restricted`, and `unknown`. A missing `is_playable` field remains unknown, never false.
- `linked_from` identifies the originally requested track when Spotify relinks it to another playable recording. The original song record receives the observation; replacement metadata is not merged into the original identity.
- A saved snapshot that was inaccessible at a later refresh retains its last known observation and timestamp. It is not represented as a fresh successful check.

Playlist addability is not proof of playback. Playability is market- and time-dependent; a result for the authenticated user's market is not a universal availability guarantee. The reference-library sync explicitly requests `market=from_token`. The offline `backfill-playability` command imports existing snapshot evidence without provider requests and backs up affected song files first.

Stable IDs and aliases are resolved conservatively. Name collisions remain candidate lists. Album/artist context never becomes track-specific acoustic evidence.
