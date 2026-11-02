# Spotify Track Playability & Availability

## Goal

Record whether each Spotify-linked song can currently be played, separately from whether it can be found or added to a playlist. A track may be addable to a playlist yet unavailable for playback; the Library must preserve that distinction.

## Core semantics

- Playability is **market-scoped and time-sensitive**. Never store a timeless global boolean such as `playable: true` as authoritative.
- A song may have different results in different markets, and Spotify may relink a requested track to another recording. Preserve both requested and relinked identities.
- Distinguish:
  - `playable` — source explicitly confirms playable for the checked market/context.
  - `unplayable` — source explicitly reports not playable for that market/context.
  - `restricted` — a restriction reason is supplied; retain the raw reason/category.
  - `not_found` — provider says the Spotify ID is not found (not equivalent to unplayable).
  - `unknown` — request could not establish playability (auth, market, endpoint, or provider limitation).
  - `not_checked` — no observation exists.
- Playlist addability, library availability, and playability are separate properties. Never infer playability from successful playlist insertion.
- Keep observation history; latest result is a convenience pointer, not a replacement for older evidence.

## Proposed song record structure

Add a namespaced `spotify_playability` object to each Spotify-linked song record, with observations keyed by market and, where relevant, playback context. Each observation should retain:
- `status` (one of the states above)
- `market` (explicit ISO country code or explicit `unknown`; never silently infer)
- `checked_at` (UTC timestamp)
- `provider` and endpoint/source context
- `requested_spotify_id`
- `returned_spotify_id` and `linked_from_spotify_id` when present
- `restrictions_reason` when present
- `is_playable` raw nullable boolean when supplied
- `is_local` and relevant response metadata when supplied
- `error_class` for failed/indeterminate checks, without credentials or sensitive tokens.

A song without a Spotify ID has no Spotify playability observation; do not assign a negative result.

## Collection strategy

1. Capture playability fields already present in read-only Spotify track/playlist responses during normal snapshot ingestion.
2. Add a bounded, rate-limited spot-check for selected Spotify-linked songs, using an explicitly configured market and current supported Spotify API behavior.
3. Prioritize songs currently being considered for playlist placement, recently played songs, and a rotating sample of the remaining catalogue.
4. Store observations in the canonical song JSON, preserve raw evidence/provenance, and let the freshness planner decide when to recheck.
5. Do not mutate playlists as part of checking. A check must never add, remove, or reorder a track.

## Acceptance criteria

- A fixture with successful playlist insertion but `is_playable=false` is recorded as unplayable, not playable.
- Different market observations coexist without overwriting one another.
- Missing market, API error, or absent playability field yields unknown/not_checked, never false.
- Relinked tracks retain requested and returned IDs and do not silently merge two canonical recordings.
- Playability checks are bounded, checkpointed, and separate from metadata identity resolution.
- No Spotify playlist writes occur during checks.

## Current status

**Initial observation persistence merged in PR #72.** Snapshot ingestion stores playability observations in song files, preserving history and distinguishing unknown from false. Market-aware requests, correct relinking behavior, and offline backfill are being refined in PR #78.

Spotify's Web API accepts market=from_token to use the authenticated user's country. When Track Relinking returns a replacement, linked_from identifies the originally requested recording; the replacement ID must not overwrite the original song identity. An absent is_playable value is unknown, not playable or unplayable. See [Get Playlist Items](https://developer.spotify.com/documentation/web-api/reference/get-playlists-items) and [Track Relinking](https://developer.spotify.com/documentation/web-api/concepts/track-relinking). Read-only Spotify playlist snapshot ingestion now carries explicit `is_playable`, restriction details, relinking IDs, source context and an observation timestamp into the canonical song record under `evidence.spotify_playability`. Observations are retained by market, with `unknown` used when the snapshot does not identify a market. This is not yet a market-specific API check, and the change is not merged.

## Resume

Read [ACTIONS.md](ACTIONS.md), inspect saved Spotify reference/playlist snapshots and their response schemas, then add field-level fixtures and ingestion tests before implementing any API polling.
