# Canonical Library Enrichment

## Goal

Maximize useful, trustworthy metadata in the canonical music Library through repeatable, bounded enrichment passes with field-level provenance and confidence.

## Scope, decisions and constraints

Scope: recording identity/MBIDs; duration; audio/acoustic features; track-level mood/theme/tags; album tracklists/descriptions; artist profiles/genres; caching and reconciliation.

Invariants: recording, artist and album entities remain distinct; track mood is recording-level and must not be blindly inherited from artist identity; unknown remains unknown; preserve source, timestamp, confidence and evidence; use provider budgets/cooldowns and cache successes; Last.fm plays prioritize work but do not prove metadata.

**Status: ongoing; current published catalogue coverage is verified, but field-level enrichment remains incomplete.** Run #18 reported 91.1% duration coverage (138,515/152,005 scrobbles), 1,778 track profiles, 3,998 artist profiles, 400 album profiles, 115 audio profiles, and zero lyric features. MusicBrainz rate-limited/503'd; Last.fm tag lookups returned HTTP 400; Discogs/GetSongBPM credentials were absent. Treat those as observed provider gaps, not permanent failures. Depends on migration recovery and a read-only coverage report.

**Resume:** audit canonical Library; measure missing fields; resolve trusted recording IDs; enrich high-value fields in bounded passes; reconcile through canonical writer; audit and measure each pass.

## Documentation and resume

Read [ACTIONS.md](ACTIONS.md) for dated work and evidence. After each meaningful action, update it with files changed, execution, exact verification and outcome. Update [the central handoff](../../NEXT_WORK.md) when priority or blockers change.


## Incremental enrichment policy

Full-catalogue completeness is not a prerequisite for feature development. Keep scheduled read-only health/confidence/freshness checks running and enrich records on demand when a feature encounters missing data.

Preferred path: canonical Library lookup → existing local exports/caches → provider-specific status and cooldown check → bounded verified provider lookup → canonical merge with provenance/confidence/timestamp → audit. Do not repeat definitive negative lookups until policy expiry or identity evidence changes; do not retry transient failures before their cooldown; never erase trusted prior values after a failed refresh.

Newly encountered songs and recommendations should enter through a candidate-intake path with source/context and identity-resolution status. They are not plays or preference facts. Sorter work can proceed offline against available profiles with explicit missing-data and confidence reporting. This policy does not authorize playlist writes.
