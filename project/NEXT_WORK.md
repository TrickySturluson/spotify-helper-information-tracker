# SHIT — Next Work

This is the authoritative session handoff. Read this file first when resuming work, then read [LOOSE_ENDS.md](LOOSE_ENDS.md), [PROJECT_LOG.md](PROJECT_LOG.md), and [README.md](../README.md). Update this file whenever priorities, blockers, or verified status change.

## Cross-project loose-ends register

Read [LOOSE_ENDS.md](LOOSE_ENDS.md) for the current audit index across migration, provider coverage, enrichment, analytics, discovery, playlists, workflows and documentation. Each entry links to its goal history. Update the register when an item is resolved, deferred or newly discovered.

## Immediate resume point — Library reliability, enrichment and confidence

**State: full canonical Library is published on main; structural health and identity confidence checks have passed.** Latest verified index: 13,005 songs, 6,386 artists, 7,861 albums. Legacy source coverage: 11,130/11,130 legacy track IDs resolve via source-track or recording-MBID aliases; 5,358/5,358 legacy artist names are represented.

- Run #18 successfully published enrichment commit `c55012f`; run #21 later repeated work from stale checkpoints and failed publication. Its generated output was not pushed. Workflow fix `21cc2ed` now checks out latest `main` before migration.
- Run #22 independent health check: https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41367899566 — 13,005/6,386/7,861; zero errors/warnings.
- Main-branch full CI including confidence audit: https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41368125489 — 314 tests passed.
- Issue #83 post-playability verification: audit/health clean; identity confidence drift 0; initial metadata confidence drift 1,582; duration coverage 10,028; track tags 179; audio features 36; playability evidence on 1,856 songs; legacy source coverage complete.
- Issue #85 maintainer preview: full catalogue clean, proposed index matches current, all aliases reconstructable, no repair needed, zero writes.
- PR #87 merged (`6c9fe06`): health checker now validates market-scoped playability evidence history, status/value semantics, timestamps, IDs/relinking, and latest-by-market index.
- PR #88 merged (`67ab44f`): confidence audit separates missing stored confidence from genuine mismatches, per field; read-only.
- Issue #90 freshness baseline: 13,005 songs / 6,386 artists / 7,861 albums; 8,799 fresh, 0 stale/due tasks, 0 missing playability observations, 42,158 missing field/provider timestamps, 1,184 cooldown skips, 0 invalid timestamps/errors; selected 0/25; provider requests=0, writes=0. The 42,158 count is not a stale count; missing/undated fields are deliberately not scheduled.
- PR #86 merged: native `python shit.py library freshness` CLI and weekly Sunday read-only health/confidence/freshness report workflow (30-day artifacts). No provider-backed generic freshness executor is enabled.
- PR #78 merged and offline playability backfill run #82 published: 3,305 observations across 1,856 song records, 3,250 playable and 55 unplayable in `from_token` context from saved snapshots; zero API requests and playlist writes. Snapshot-time results, not live availability guarantees.
- Issue #92 was created after PR #87/#88 merges for a fresh audit/health/confidence verification against latest main; result pending at this checkpoint.
- Latest published enrichment coverage still needs fresh measurement. Historical run #18 report: approx. 91.1% duration coverage; 115 audio profiles; zero lyric features; 1,778 track profiles; 3,998 artist profiles; 400 album profiles. MusicBrainz had rate limits/503s, Last.fm tag lookups returned HTTP 400, and optional Discogs/GetSongBPM credentials were absent.
- No Spotify playlist writes, force-pushes, blind conflict resolution, or confidence rewrites.

## Current Library reliability work

- **Health checker:** merged PR #73; full-catalogue scan clean. PR #87 adds semantic playability checks; issue #92 verified them against the full catalogue with zero errors/warnings.
- **Data maintainer:** PR #80 merged. `python shit.py library maintain` previews deterministic index rebuilds; apply requires `--apply --repair-index`, alias-preservation proof, backup, atomic replacement, and post-repair health validation/rollback. Full-catalogue previews #85 and #93 found no repair needed; #93 confirmed 0 health errors/warnings, all aliases reconstructable, and zero writes. Weekly workflow now includes the same read-only maintenance preview and preserves its report; no automatic repair. Current repair scope is index-only.
- **Metadata freshness:** PR #81 planner and PR #86 CLI/weekly review merged; PR #100 merged as `61cc5c0`. The planner now separates no-data, data-bearing unknown-age, and missing duration provenance, and rotates a 25-item unknown-age baseline weekly. Full CI/security passed (344 tests); issue #101 validated full-catalogue output: 6,613 baseline candidates, 25 selected (all Last.fm duration), 0 due/stale, 33,689 no-data, 1,856 missing provenance, 1,362 cooldown skips. This is read-only; provider_requests=0, writes=0. No generic provider executor yet. Weekly workflow also runs maintenance preview.
- **Spotify playability:** PR #72/#78 merged. Each song stores append-only market-scoped observations under `evidence.spotify_playability`; snapshot backfill covered 1,856 records. A separate Get Track refresh planner defaults to 25, maximum 50, 90-day TTL, dry-run by default, and requires explicit `--execute --yes`; it is not yet exposed through the scheduled weekly workflow. Do not infer playability from playlist addability.
- **Confidence:** read-only audit merged; PR #88 classifies missing vs mismatched confidence. Issue #92 confirms identity drift 0, missing duration confidence 1,582, genuine mismatches 0. The real-data review set now includes exact MBID, Spotify-ID/playability, low-confidence source-ID examples, and a Candy Claws duplicate artist/album candidate. Issue #102 tracks a read-only duplicate-entity audit. Do not bulk-rewrite confidence or merge records.
- **Migration:** full entity catalogue is published. Read-only prepare preflight #94 confirmed 11,130/11,130 legacy track IDs and 5,358/5,358 artist names represented; 13,005/6,386/7,861 canonical records; current profile caches and bounded provider caps; zero provider requests/writes. It did not prove new enrichment is due. Continue only from durable checkpoints, one serialized writer at a time; do not repeat provider batches merely because a runner-side operation failed publication.

## Immediate priorities

1. **Complete issue #92 verification** against latest main: confirm the new playability semantic health checks pass over all 3,305 observations and inspect missing-vs-mismatch confidence breakdown.
2. **Improve freshness evidence classification:** distinguish absent metadata, present-but-undated values, fresh no-result/negative cache, provider transient failure, cooldown, and genuinely stale observations. Propagate trustworthy source timestamps from existing caches/checkpoints; never infer from file mtimes.
3. **Recover duration observation provenance before any refresh.** Issue #103 and `scripts/music/backfill_duration_observations.py` recover exact `metadata_checked_at` timestamps from legacy shards into canonical song `duration_observations` only when ID, duration, source and matched status agree. Inspect issue #104 preview; apply only with a clean conflict report and backup. Re-run freshness plan to measure the remaining true unknown-age set.
4. **Design a bounded partial refresh executor** only after provenance recovery. It should consume durable checkpoints/retry state, advance the deterministic rotating sample, respect provider budgets/cooldowns, preserve old evidence on failure, and default to preview. Keep Spotify playability refresh separately market-aware and capped.
4. **Re-measure provider coverage** from current published data; continue only eligible enrichment. Diagnose Last.fm HTTP 400 and MusicBrainz 503/rate-limit behavior before retries; do not repeat no-result requests without cache expiry or changed query evidence.
5. **Finish confidence verification:** use PR #88's missing/mismatch split; inspect missing duration provenance; run the curated [identity review set](goals/library-confidence-verification/IDENTITY_REVIEW_SET.md); implement issue #102's read-only duplicate artist/album/song audit. The Candy Claws fallback artist/album pair is a concrete candidate: do not merge until external-ID evidence and reference preservation are verified.
6. **Return to sorter evaluation only after gates 1–5:** test retrieval, field-specific confidence gating, unknown handling, and smooth transitions against real generated playlists before any playlist write.

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
