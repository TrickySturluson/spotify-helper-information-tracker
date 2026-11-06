# Canonical Library Enrichment — Roadmap

**Last reviewed:** 2026-11-05  
**Status:** Ongoing; canonical Library exists, field-level enrichment is incomplete.

## Purpose
Increase useful, trustworthy metadata for recordings, artists, and albums using bounded provider-aware enrichment with exact identity, provenance, timestamps, confidence, and evidence.

## Invariants
- Recording, artist, and album are distinct entities.
- Recording mood/theme must not be inferred from artist identity.
- Unknown is unknown, not negative evidence.
- Preserve source, observation time, confidence, and conflicts.
- Respect provider budgets, cooldowns, caches, and credential availability.
- Last.fm listening frequency prioritizes effort; it does not prove metadata.

## Baseline (historical; refresh before use)
Run #18 reported ~91.1% duration coverage, 1,778 track profiles, 3,998 artist profiles, 400 album profiles, 115 audio profiles, and zero lyric features. Provider issues included MusicBrainz 503/rate limits, Last.fm tag HTTP 400, and unavailable optional Discogs/GetSongBPM credentials.

## Roadmap
1. **Fresh coverage audit — next.** Measure per-field and per-entity coverage, provenance, confidence, freshness, and provider checkpoints on current main.
2. **Recording identity and duration.** Resolve exact recording IDs; preserve verified durations and legacy default estimates distinctly; backfill provenance only when exact evidence matches.
3. **Direct track-level metadata.** Prioritize recording-level genre/tags, mood, lyrics-derived themes, and trustworthy audio/energy features. Do not substitute artist tags for track evidence.
4. **Artist and album enrichment.** Improve profiles, genres, release metadata, and tracklists with source-specific confidence.
5. **Provider-aware bounded execution.** Reuse successful cache entries, skip active cooldowns, classify transient vs definitive failures, cap requests, checkpoint, and resume.
6. **Canonical publication and audit.** Merge through canonical writer; verify identities, relationships, provenance, confidence, and health after every batch.

## Acceptance criteria
No blind repeated lookups; no identity guessing; every promoted field has source and timestamp; failed lookups preserve old evidence; unknown coverage remains explicit; post-write health passes.

## Next action
Run a fresh read-only coverage/provider-checkpoint audit and select a small, high-value batch based on actual gaps and provider eligibility.

## Related records
[README](README.md) · [ACTIONS](ACTIONS.md) · [Retry specification](../../RETRY_QUEUE_SPEC.md)
