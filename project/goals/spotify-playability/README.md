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

**Initial snapshot persistence is merged in PR #72.** Canonical song records store append-only playability observations under `evidence.spotify_playability`, including raw nullable `is_playable`, restrictions, timestamps, playlist/source context, and requested/returned/relinked IDs. Unknown market remains explicit; missing `is_playable` is not false.

**Market-aware refresh and offline backfill are in PR #78** (open; draft). The current implementation:
- Uses authenticated-user market context (`market=from_token`) and the individual Spotify Get Track endpoint.
- Preserves requested and relinked Spotify IDs without merging replacement metadata into the original song identity.
- Provides offline backfill from saved playlist snapshots.
- Adds a stale-only planner (default 25 songs, 90-day interval, maximum 50 requests per run); dry-run is default and live requests require explicit execute flags.
- Treats absent `is_playable` and 404 as unknown/not-found rather than unplayable.
- Has no playlist write path.

The first complete compile and data audits passed on the latest PR revision; the unit suite previously exposed a missing `datetime/timezone` import in a new planner test. That test import has been fixed and a new CI run is queued/in progress. Do not merge or execute live refresh until the latest full CI run passes and the API request semantics are reviewed.

## Resume

Read [ACTIONS.md](ACTIONS.md), inspect PR #78 and its final CI result; merge only after all checks pass. Then run the offline backfill from saved snapshots, audit the affected song files, and only afterward consider the bounded stale-only API refresh.
