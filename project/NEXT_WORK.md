# SHIT — Next Work

This is the authoritative session handoff. Read this file first when resuming work, then read [LOOSE_ENDS.md](LOOSE_ENDS.md), [PROJECT_LOG.md](PROJECT_LOG.md), and [README.md](../README.md). Update this file whenever priorities, blockers, or verified status change.

## Cross-project loose-ends register

Read [LOOSE_ENDS.md](LOOSE_ENDS.md) for the current audit index across migration, provider coverage, enrichment, analytics, discovery, playlists, workflows and documentation. Each entry links to its goal history. Update the register when an item is resolved, deferred or newly discovered.

## Immediate resume point — Library reliability and final enrichment

**State: full canonical Library is published on main.** The latest verified main index contains 13,005 songs, 6,386 artists, and 7,861 albums. Run #18 successfully published enrichment commit `c55012f`; run #21 later repeated work from stale checkpoints and failed publication, so none of #21's generated output was pushed. Workflow fix `21cc2ed` now explicitly checks out latest `main` before migration. The independent read-only health check on the full catalogue passed with zero errors and zero warnings; the confidence audit and 314-test main-branch regression suite also passed.

- Run #18: https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41364145298
- Run #21 stale-checkout failure and artifact diagnosis: see [Great Migration ACTIONS](goals/great-migration/ACTIONS.md).
- Full catalogue/source coverage: 11,130/11,130 legacy track-index IDs resolve via source-track or recording-MBID aliases; all 5,358/5,358 legacy artist names are represented.
- Run #22 health operation: https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41367899566 (read-only, successful; 13,005/6,386/7,861; zero errors/warnings).
- Main-branch full CI including confidence audit: https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41368125489 (314 tests passed).
- Latest main enrichment metadata remains incomplete: approx. 91.1% duration coverage; lyric features 0; audio profiles 115; artist profiles 3,998; album profiles 400; track profiles 1,778 in the published run #18 report. Provider limitations include MusicBrainz rate limits/503s, Last.fm HTTP 400s, and absent optional Discogs/GetSongBPM credentials. Re-measure before quoting as current.
- PR #79 (legacy archive coverage reporting) is merged. Its latest main compile/regression and security workflows passed.
- Do not run another full prepare until current playability work and the next targeted enrichment plan are reconciled with durable checkpoints. Run one serialized operation at a time; no concurrent migration writers.
- No Spotify playlist writes, force-pushes, or blind conflict resolution.

## Current Library reliability work

- **Health checker:** merged in PR #73; PR #87 now validates market-aware playability evidence semantics (status/raw value, timestamp, market/latest map, requested/relinked IDs). Full post-merge verification is running in issue #90. See [health-maintenance goal](goals/library-health-maintenance/README.md).
- **Data maintainer:** PR #80 merged. `python shit.py library maintain` previews deterministic index repairs; apply requires `--apply --repair-index`, alias-preservation proof, backup, atomic replacement, and post-repair health validation/rollback. Full-catalogue preview issue #85 passed: safe to rebuild, zero aliases/records lost, zero errors/warnings, no repair needed. No real repair has been applied.
- **Metadata freshness:** PR #81 merged. Read-only planner scans 13,005 songs, 6,386 artists, 7,861 albums and 1,778/3,998/400 track/artist/album profile cache rows; post-backfill plan selected 0 due tasks. Draft PR #86 adds native CLI and weekly read-only review workflow; no provider executor/schedule is enabled.
- **Spotify playability:** initial snapshot persistence merged in PR #72. Draft PR #78 adds market-aware Get Track checks, offline snapshot backfill, and stale-only bounded refresh. Latest full CI and security scan passed after fixing a missing test import; keep it unmerged until final review. No live refresh has been executed.
- **Confidence:** read-only confidence audit is merged; PR #88 now separates missing stored confidence from genuine mismatches. Issue #90 is running a full-catalogue post-merge breakdown of the 1,582 previous differences. Remaining work is gold-set/manual false-match review and confidence distribution analysis.

## Immediate priorities

1. Complete review/CI for PR #86 (native freshness CLI and weekly read-only review) and PR #87 (playability evidence health validation).
2. Run the first manual weekly freshness review on main after PR #86 merges; preserve the report and verify no network/write side effects.
3. Classify the 1,582 metadata-confidence differences and 1,856 missing duration provenance entries; build a curated gold set before any confidence backfill.
4. Design a bounded provider-backed freshness executor using existing retry/checkpoint state; no blind polling. Spotify playability live refresh remains separate and explicit.
5. Continue field coverage/provider gap reporting, then complete confidence verification.
6. Only after these gates, return to sorter evaluation against the new Library.

## Immediate expanded Library requirements

Three new goal workspaces were added on 2026-11-02:
- [Library health checker and data maintainer](goals/library-health-maintenance/README.md): read-only health diagnostics first; safe, backup-protected, idempotent repairs only.
- [Metadata freshness and partial revalidation](goals/metadata-freshness/README.md): field/provider-specific staleness, deterministic rotating partial samples, bounded requests, reuse retry queue/checkpoints.
- [Spotify playability and availability](goals/spotify-playability/README.md): market-scoped, timestamped playability observations distinct from playlist addability; preserve restrictions and relinking IDs.

These are now required Library foundations before sorter confidence verification is considered complete. The [Library confidence verification workspace](goals/library-confidence-verification/README.md) defines the next gate: validate identity and field-level confidence across the full catalogue, inspect ambiguous/weak matches, and test retrieval against a curated gold set before sorter integration. Do not block migration publication on building all three; document and implement in parallel only when safe and non-conflicting.

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

5. **Identity and metadata confidence verification — sorter gate**
   - Read [the confidence verification goal](goals/library-confidence-verification/README.md) and report identity-confidence distribution by match method.
   - Recompute field-level confidence from independent source-family evidence; detect missing provenance, conflicts, stale observations, and stored-vs-recomputed drift.
   - Validate the 11,130 legacy track IDs and 5,358 artist-name matches as permanent regression coverage, not just a one-off comparison.
   - Build a curated gold set for verified IDs, same-title collisions, remasters/live versions, ambiguous names, and false-match traps; manually inspect representative high/medium/low/unknown records.
   - Verify lookup_song/get_song retrieval and sorter input confidence gates; no silent auto-upgrades of confidence.

6. **Library coverage planner**
   - Review PR #65 CI and code against actual canonical record/checkpoint schemas.
   - Verify read-only behavior, deterministic output, correct priority ordering, and separation of transient failures from definitive negatives.
   - Do not mark complete based only on PR description; inspect CI and run tests.

7. **Playlist intelligence and safety**
   - Continue sorter work only against generated playlists unless explicitly authorized otherwise; preserve locked-by-default behavior and explicit unlock requirements.
   - Smooth transitions are the primary sorting objective; avoid jarring adjacent tracks. Support controllable progression/peak placement, energy/BPM/loudness, mood/theme/genre sections, and gradual resolution.
   - Use track-level mood/theme evidence rather than assuming an artist has one mood. Lyrics-derived themes may use compact tags/features and provenance; do not store full copyrighted lyrics.
   - Daily learner should use actual plays and explicit likes as distinct signals; unplayed generated daily tracks must not be over-weighted. Liked tracks should be down-prioritized where requested, not automatically excluded.
   - Preserve removal blacklists, deduplication, audit/state files, playlist exceptions (including Tricky Daily), and preview/test-before-write workflows.
   - No playlist writes during migration recovery.

8. **Maintainability and documentation**
   - Every project script/module should explain its purpose, inputs/outputs, side effects, safety boundaries, and how it fits into SHIT.
   - Keep a top-level project overview and a concise per-file overview in scripts.
   - Keep this handoff and the chronological log updated as work proceeds.

## Open pull requests / status to re-check

- **#67 — Per-goal documentation workspaces:** merged as `4ad701c2c4f36b9f6f73926e83db1f84cbfbcc2c`; tests and secret-history scan passed.
- **#65 — Read-only Library coverage planner:** open draft; unit tests failed while compile/data-doc checks and secret scan passed. Diagnose before relying on it. https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/65
- **#60 — Provenance-aware recommendation ingestion:** open; unit tests and secret-history scan failed. Diagnose both before relying on it. https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/60

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
