# Canonical Library Enrichment — Roadmap

**Last reviewed:** 2026-11-06  
**Status:** Feature work paused under the repository-wide documentation-only priority; the canonical Library exists, but field-level enrichment remains incomplete.

## Repository-wide priority override — 2026-11-06

**This workstream is paused for feature implementation while SHIT's documentation audit is active.** The only permitted work here until the Maintainability & Documentation roadmap passes its acceptance criteria is documentation correction, evidence reconciliation, and recording known gaps. Do not run enrichment, modify canonical data, change playlists, or begin feature development. This workstream's feature roadmap remains queued; the active next action is the documentation-only handoff in [project/NEXT_WORK.md](../../NEXT_WORK.md). Resume feature work only when that handoff and the maintainability roadmap explicitly say documentation is complete.

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

## 2026-11-06 operational findings — documentation record only

- A concurrent metadata-enrichment run (#42146121471) completed its provider work but failed publication on add/add conflicts in canonical song records introduced by the simultaneous Reference Library commit. Enrichment workspace changes were not published.
- AcousticBrainz run #42146097964 completed 100 batches (2,500 candidate IDs; 207 found; 2,293 misses; 322 total profiles; 3,678 negative-cache entries) but failed publication because the workflow unconditionally staged an absent optional `getsongbpm_lookup_state.json` after the optional GetSongBPM provider was skipped.
- These are workflow/publication reliability defects, not proof that the corresponding metadata is now present in canonical main. Do not count either run's uncommitted workspace output as Library coverage.
- Remediation is deferred until the user-authorized documentation-only phase is complete. Future work: shared-writer serialization/stale-base conflict handling and conditional staging of optional provider files.

## Additional publication finding — 2026-11-06

The broad Update Last.fm History run #42146153098 completed its Last.fm, artist/track, duration, recording-ID, AcousticBrainz and statistics steps but failed to publish during rebase. It encountered 120 unique conflicts: 59 canonical music Library paths and 61 Spotify playlist snapshot/reference paths. The separate Reference Library run had committed changes to those shared paths. None of the Update run's workspace outputs should be counted as canonical mainline enrichment or analytics. Shared-writer serialization and safe stale-base publication are required future work.

## Roadmap
1. **Fresh coverage audit — next.** Measure per-field and per-entity coverage, provenance, confidence, freshness, and provider checkpoints on current main.
2. **Recording identity and duration.** Resolve exact recording IDs; preserve verified durations and legacy default estimates distinctly; backfill provenance only when exact evidence matches.
3. **Direct track-level metadata.** Prioritize recording-level genre/tags, mood, lyrics-derived themes, and trustworthy audio/energy features. Do not substitute artist tags for track evidence.
4. **Artist and album enrichment.** Improve profiles, genres, release metadata, and tracklists with source-specific confidence.
5. **Provider-aware bounded execution.** Reuse successful cache entries, skip active cooldowns, classify transient vs definitive failures, cap requests, checkpoint, and resume.
6. **Canonical publication and audit.** Merge through canonical writer; verify identities, relationships, provenance, confidence, and health after every batch.

## Acceptance criteria
No blind repeated lookups; no identity guessing; every promoted field has source and timestamp; failed lookups preserve old evidence; unknown coverage remains explicit; post-write health passes.

## Open proposal (not merged)

- [PR #120 — Adopt incremental Library enrichment and parallel sorter development](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/120) is open and draft. It records the strategy decision; it does not implement or prove a bounded provider executor, retry queue, or completed on-demand enrichment path.

## Next action
Run a fresh read-only coverage/provider-checkpoint audit and select a small, high-value batch based on actual gaps and provider eligibility.

## Related records
[README](README.md) · [ACTIONS](ACTIONS.md) · [Retry specification](../../RETRY_QUEUE_SPEC.md)
