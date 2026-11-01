# SHIT — Next Work

This is the authoritative session handoff. Read this file first when resuming work, then read [PROJECT_LOG.md](PROJECT_LOG.md) and [README.md](../README.md). Update this file whenever priorities, blockers, or verified status change.

## Immediate resume point — Great Migration

**State: NOT VERIFIED AS PUBLISHED. Do not call the migration complete.**

- Great Migration run #17 failed during the Git rebase/publish stage because generated Library records and indexes conflicted.
- The run produced an artifact and backup, but their contents and final integrity status still need direct inspection.
- Run: https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41357689889
- **Next actions:** inspect logs/artifact/backup; determine whether the prepare, migrate, enrichment, and audit stages completed; compare artifact against current `main`; preserve the best valid checkpoint; repair publication so concurrent generated-data writers cannot overwrite or conflict with the migration; publish only after a fresh integrity audit.
- Do not force-push, blindly resolve generated-data conflicts, restart a write-heavy migration without inspecting the artifact, or modify Spotify playlists as part of migration recovery.

## Priority order

1. **Recover, publish, and verify the Great Migration**
   - Establish the exact last successful stage and durable checkpoint.
   - Confirm entity counts, relationships, aliases, manifest/index consistency, and audit output.
   - Confirm what actually reached `main`; distinguish local/artifact success from published success.
   - Record provider availability and metadata gaps separately.
   - Once publication is verified, continue bounded enrichment passes rather than treating migration as the end state.

2. **Enrichment and verification**
   - Use the coverage planner to build a deterministic, read-only view of missing fields and eligible provider work.
   - Resolve trustworthy recording identifiers first; then improve durations, album/artist context, acoustic/audio features, and track-level tags/mood where supported.
   - Preserve field-level provenance, confidence, timestamps, and evidence. Unknown stays unknown; artist-level mood must not be copied onto every recording.
   - Reconcile exports into the canonical Library and run integrity audits after each meaningful pass.
   - Cache successful results; respect provider-specific request budgets, batch caps, pacing, cooldowns, and negative-cache expiry. Never fetch blindly or repeat a known failure without a reason.

3. **Provider-aware retry queue**
   - Implement `assistant_data/music/retry_queue.json` from canonical Library records plus real provider checkpoints/state, following [RETRY_QUEUE_SPEC.md](RETRY_QUEUE_SPEC.md).
   - One task per recording + provider + requested data family.
   - Distinguish eligible, retry-wait, definitive not-found, ambiguous, complete, blocked, and invalid.
   - Record attempt count, last attempt, next eligible time, reason, requested fields, priority, confidence, and evidence references.
   - A failure at one provider must not block independent providers. Planner/report mode must not perform network calls or mutate records.
   - Validate real schemas before implementation; test cooldown preservation, negative-cache semantics, malformed records, deduplication, and no-write/no-network guarantees.

4. **Discovery and recommendation intake**
   - Bring suggested/recommended songs and other discovered candidates into the Library so they can be identified, enriched, deduplicated, and retrieved later.
   - Store source/provider, source playlist/person/context, prompt or recommendation context when available, capture time, and observable user response (added, saved, played later, rejected, ignored, etc.).
   - Keep candidate/recommendation evidence separate from Last.fm scrobbles, Spotify playback, explicit likes/saves, and confirmed preferences. A recommendation is never a play or a preference by itself.
   - Review and verify PR #60: https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/60

5. **Library coverage planner**
   - Review PR #65 CI and code against actual canonical record/checkpoint schemas.
   - Verify read-only behavior, deterministic output, correct priority ordering, and separation of transient failures from definitive negatives.
   - Do not mark complete based only on PR description; inspect CI and run tests.

6. **Playlist intelligence and safety**
   - Continue sorter work only against generated playlists unless explicitly authorized otherwise; preserve locked-by-default behavior and explicit unlock requirements.
   - Smooth transitions are the primary sorting objective; avoid jarring adjacent tracks. Support controllable progression/peak placement, energy/BPM/loudness, mood/theme/genre sections, and gradual resolution.
   - Use track-level mood/theme evidence rather than assuming an artist has one mood. Lyrics-derived themes may use compact tags/features and provenance; do not store full copyrighted lyrics.
   - Daily learner should use actual plays and explicit likes as distinct signals; unplayed generated daily tracks must not be over-weighted. Liked tracks should be down-prioritized where requested, not automatically excluded.
   - Preserve removal blacklists, deduplication, audit/state files, playlist exceptions (including Tricky Daily), and preview/test-before-write workflows.
   - No playlist writes during migration recovery.

7. **Maintainability and documentation**
   - Every project script/module should explain its purpose, inputs/outputs, side effects, safety boundaries, and how it fits into SHIT.
   - Keep a top-level project overview and a concise per-file overview in scripts.
   - Keep this handoff and the chronological log updated as work proceeds.

## Open pull requests / status to re-check

- **#66 — Project control centre and retry queue specification:** this branch contains the continuity docs; retry queue is specified, not implemented. https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/66
- **#65 — Read-only Library coverage planner:** proposed code/tests; CI and schema compatibility must be verified. https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/65
- **#60 — Provenance-aware recommendation ingestion:** proposed candidate intake; verify CI, merge state, and implementation before relying on it. https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/60

## Standing data and safety rules

- Last.fm scrobbles are the historical listening source of truth.
- Spotify playback-tracker data is optional prospective evidence with coverage gaps; never silently treat it as complete historical listening.
- Recommendations/discoveries are candidate-interest signals, not plays, scrobbles, likes, saves, or confirmed preferences.
- Preserve song, artist, and album identities separately; recording-level evidence must remain recording-level.
- Preserve provenance and confidence for every enrichment. Do not fabricate metadata or silently promote weak matches.
- Respect provider rate limits, caps, cooldowns, caches, and retry state. Avoid blind/redundant requests.
- Prefer preview, bounded batches, backups, checkpoints, deterministic outputs, and final audits.
- Do not write to Spotify playlists without the relevant explicit authorization/unlock.
- Never commit credentials, tokens, private account data, or full copyrighted lyrics.

## Goal-based documentation workflow

Every major project objective has a dedicated folder under [`goals/`](goals/README.md). When starting work, open only the relevant goal's `README.md` and `ACTIONS.md` alongside this handoff. After meaningful work, append a dated action entry recording purpose, files/workflows changed, execution, exact tests/audits, outcome, blockers, and next action. Update the goal README when its scope/design/current status changes. Update this central handoff only when cross-project priority, blockers, or resume order changes. Do not make the central log a duplicate of detailed goal histories.

## Session completion checklist

Before handing off, update this file and the project log with:
- What changed and where (paths, PRs, commits, workflow runs).
- What was actually executed, including exact tests/audits and their results.
- What is published versus only present in an artifact/branch/local workspace.
- Current counts/coverage only when freshly measured, with source and timestamp.
- Remaining gaps, blockers, retry/cooldown state, and the single next concrete action.
- Any user decision or constraint that future work must preserve.
