# Spotify Track Playability & Availability
> **Roadmap:** [ROADMAP.md](ROADMAP.md) is the durable plan and next-action reference. Read it before work; update it and [ACTIONS.md](ACTIONS.md) in the same session as implementation, testing, decisions, or blockers.

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

**Implemented and merged.** PR #72 added append-only snapshot observation persistence. PR #78 then added market-aware refresh, offline backfill, and a bounded stale-only refresh plan; merged commit `e12b72e`.

**Offline backfill completed in run #82:** 1,856 canonical song records now contain 3,305 timestamped observations from saved Spotify playlist snapshots. The observations report 3,250 playable and 55 unplayable in the authenticated user's market context (`from_token`). Sixteen of 57 saved snapshots were inaccessible; two items could not be matched to a canonical song. The run made zero Spotify API requests and zero playlist writes. Backup artifact #13108782697 was retained; backup files were not committed to the canonical Library.

These are **snapshot-time observations**, not a guarantee of current playback availability. A later bounded refresh should recheck stale records. The refresh planner defaults to 25 songs, uses a 90-day freshness interval, caps at 50 individual Get Track requests, and is dry-run by default. Live requests require explicit execute confirmation.



**Post-backfill validation:** PR #87 merged the health-check rules for playability observation shape, market keys, status/raw boolean consistency, timestamps, requested/relinked IDs, and latest-by-market pointers. Issue #92 validated the full published catalogue with zero health errors/warnings; the populated 3,305-observation history passed. The song-level observation remains snapshot-time evidence and is never treated as a timeless boolean. The bounded live Get Track refresh is available as a dry-run-first planner (25 default, max 50, 90-day TTL), but no live playability API refresh has yet been executed.

## Resume

Read [ACTIONS.md](ACTIONS.md), Run a post-backfill audit/health/confidence check on published main. Then inspect the bounded stale-only refresh plan and current account-market behavior before executing any live Spotify requests.
