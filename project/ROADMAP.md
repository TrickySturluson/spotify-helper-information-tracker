# SHIT — Project-wide Roadmap

**Last reviewed:** 2026-11-06  
**Status:** Active; cross-workstream index. Detailed implementation plans and acceptance evidence remain in each goal's roadmap.

## Mission

Maintain a durable, reliable, cloud-operable music intelligence system that combines Spotify playlist operations with the canonical Last.fm listening archive and a structured music Library. A fresh contributor or assistant must be able to understand the project, preserve user decisions, and resume work without chat history.

## Non-negotiable project rules

- The documentation system is publicly named **SHIT Documentation & Continuity** and internally codenamed **Babel**. Always define the descriptive name before relying on the codename; see [Babel operating guide](../docs/BABEL.md).
- Last.fm scrobbles remain the historical listening source of truth. Spotify playback-tracker observations are optional prospective evidence and must expose coverage gaps.
- Recommendations, playlist exposure, saves/likes, removals, Last.fm scrobbles, and measured Spotify playback are distinct evidence types.
- Missing evidence is unknown, not zero or negative preference.
- Canonical Library records and provenance are authoritative; generated indexes are rebuildable outputs.
- Spotify playlist writes remain deny-by-default, scoped to SHIT-managed playlists or explicit user-approved exceptions, with locks, blacklists, deduplication, preview, audit, and read-back verification.
- Do not run concurrent writers against shared generated state. Preserve backups, atomic publication, recovery and rollback contracts.
- GitHub is the canonical development and operations home; do not depend on the user's PC for normal operation unless explicitly requested.
- Documentation is part of implementation. Follow [DOCUMENTATION_RULES.md](DOCUMENTATION_RULES.md) and root [AGENTS.md](../AGENTS.md) every session.

## Workstream roadmap index

| Workstream | Current documented focus | Authoritative roadmap |
|---|---|---|
| Great Migration | Verify published canonical Library and safely recover remaining migration/enrichment state | [ROADMAP](goals/great-migration/ROADMAP.md) |
| Library Enrichment | Bounded, provider-aware recording/artist/album enrichment with provenance | [ROADMAP](goals/library-enrichment/ROADMAP.md) |
| Metadata Coverage & Retries | Coverage measurement, cooldown-aware retries, retry queue contract | [ROADMAP](goals/metadata-coverage-retries/ROADMAP.md) |
| Discovery & Recommendations | Preserve discovery provenance and separate candidates from listening evidence | [ROADMAP](goals/discovery-recommendations/ROADMAP.md) |
| Listening Analytics | Accurate Last.fm analytics and explicitly bounded Spotify playback observations | [ROADMAP](goals/listening-analytics/ROADMAP.md) |
| Playlist Intelligence & Safety | Shared fit model, sorter, learner, generated-playlist safeguards and Booze workflow | [ROADMAP](goals/playlist-intelligence/ROADMAP.md) |
| Tricky Daily | Dedicated 60-track discovery rotation, feedback, schedule, safety, recovery and description verification | [ROADMAP](goals/tricky-daily/ROADMAP.md) |
| Playlist Sequencing | Evidence-aware transition scoring, user-controlled energy journeys, presets and preview-first ordering | [ROADMAP](goals/playlist-sequencing/ROADMAP.md) |
| Maintainability & Documentation | Complete file-level documentation coverage and enforce fresh-session continuity | [ROADMAP](goals/maintainability-documentation/ROADMAP.md) |
| Library Health & Maintenance | Read-only health, confidence and maintenance previews; guarded repair path | [ROADMAP](goals/library-health-maintenance/ROADMAP.md) |
| Metadata Freshness | Timestamp/provenance recovery and safe freshness planning | [ROADMAP](goals/metadata-freshness/ROADMAP.md) |
| Spotify Playability | Market-scoped availability evidence and refresh policy | [ROADMAP](goals/spotify-playability/ROADMAP.md) |
| Mobile Cloud Operation & Spotify Reauthorization | Phone-based Spotify OAuth bootstrap and PC-independent SHIT control | [ROADMAP](goals/mobile-cloud-operation/ROADMAP.md) |
| Library Confidence Verification | Identity confidence, duplicate review and evidence-preserving reconciliation | [ROADMAP](goals/library-confidence-verification/ROADMAP.md) |

## Cross-project priority order

This is a coordination order, not a replacement for goal-specific roadmaps. The user's explicit current direction makes documentation the sole active workstream until its acceptance criteria pass. Do not advance lower-priority feature work during this phase. If a dependency or fresh failure changes the order, record why in NEXT_WORK and the affected roadmaps.

1. **Complete documentation coverage and fresh-session continuity.** Audit maintained files and data contracts against source; verify every goal roadmap; reconcile links, operational guides, open PRs/issues and workflow evidence; improve automated checks; complete the fresh-session simulation. No feature development, playlist operations or unrelated project work until this is complete.
2. **Protect canonical state and recoverability.** Resolve migration/publication loose ends, verify canonical Library integrity, and prevent unsafe concurrent writes.
3. **Repair metadata provenance and coverage.** Recover timestamps, measure genuine gaps, and run only bounded provider-aware enrichment/retries.
4. **Maintain operational confidence.** Keep health, freshness, confidence, playability and security checks current.
5. **Improve discovery and listening intelligence.** Preserve source distinctions, ingest candidates safely, and validate evidence quality before scoring.
6. **Improve playlist intelligence and live operations.** Keep sorting and recommendation systems preview-first until evidence, safety and rollback gates pass.
7. **Validate cloud independence.** Close remaining authentication and optional local-tracker dependencies before describing the product as fully PC-independent.

## Completion standard

A workstream is not complete merely because code exists or a PR merged. Its roadmap must name the acceptance criteria and evidence. Depending on the task, evidence may include passing tests, a clean audit, a successful workflow run, a fresh read-back, or a verified live operation. Keep planned, implemented, merged, deployed, and verified states separate.

## Current handoff

Read [NEXT_WORK.md](NEXT_WORK.md) for the single active cross-project task. Read [LOOSE_ENDS.md](LOOSE_ENDS.md) before selecting additional work. Detailed histories are in each goal's ACTIONS file and [PROJECT_LOG.md](PROJECT_LOG.md).
