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
