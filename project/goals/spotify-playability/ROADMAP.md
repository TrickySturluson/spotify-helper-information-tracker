# Spotify Track Playability & Availability — Roadmap

**Last reviewed:** 2026-11-06  
**Status:** Market-aware observation persistence, refresh planning and offline backfill are implemented/merged (PR #78). The explicit playability feature work is paused under the documentation-only priority; freshness and coverage monitoring remain queued.

## Repository-wide priority override — 2026-11-06

**This workstream is paused for feature implementation while SHIT's documentation audit is active.** The only permitted work here until the Maintainability & Documentation roadmap passes its acceptance criteria is documentation correction, evidence reconciliation, and recording known gaps. Do not run enrichment, modify canonical data, change playlists, or begin feature development. This workstream's feature roadmap remains queued; the active next action is the documentation-only handoff in [project/NEXT_WORK.md](../../NEXT_WORK.md). Resume feature work only when that handoff and the maintainability roadmap explicitly say documentation is complete.

## Purpose
Record whether a Spotify-linked recording is playable in a particular market/context, separately from whether it can be found or added to a playlist.

## Invariants
Playability is market-scoped and time-sensitive. Preserve requested and relinked Spotify IDs. Distinguish playable, unplayable, restricted, not_found, unknown and not_checked. Playlist addability is not playability. Failed/absent observations never become false. Checks never mutate playlists.

## Roadmap
1. **Fresh coverage audit — next.** Measure observation counts by market, age, source, status and canonical identity; identify inaccessible snapshots and unmatched records.
2. **Preserve observation history.** Verify append-only behavior and latest-observation pointers without erasing prior evidence.
3. **Bounded refresh.** Use the freshness planner to select due/high-value records; enforce explicit market, budgets, checkpoints and cooldowns.
4. **Relinking and identity tests.** Cover requested/returned IDs, market differences, restricted results, not-found vs unknown, and no accidental canonical merges.
5. **Operational reporting.** Surface stale playability separately from missing identity and metadata.

## Acceptance criteria
Market observations coexist; no global timeless boolean; addability does not imply playability; checks make zero playlist writes; all observations retain source/time/identity.

## Next action
Run a fresh read-only playability coverage report and inspect the weekly refresh plan before any provider-backed check.

## Related records
[README](README.md) · [ACTIONS](ACTIONS.md) · [Metadata freshness](../metadata-freshness/ROADMAP.md)
