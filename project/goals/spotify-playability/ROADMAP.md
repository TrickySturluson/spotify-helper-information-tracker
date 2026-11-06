# Spotify Track Playability & Availability — Roadmap

**Last reviewed:** 2026-11-05  
**Status:** Market-aware observation persistence, refresh planning and offline backfill are implemented/merged; freshness and coverage must be monitored.

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

## Next action (documentation-only priority)

Continue the documentation audit for this workstream: verify this roadmap, README, ACTIONS, linked technical guides, source overviews, tests, workflow references and evidence claims against the current repository. Record any newly discovered contradictions or stale paths here and in the central handoff. **Do not run provider checks/enrichment, alter generated data, modify playlists, or implement features while the documentation-only priority is active.**

## Next feature action after documentation pause
Run a fresh read-only playability coverage report and inspect the weekly refresh plan before any provider-backed check.

## Related records
[README](README.md) · [ACTIONS](ACTIONS.md) · [Metadata freshness](../metadata-freshness/ROADMAP.md)
