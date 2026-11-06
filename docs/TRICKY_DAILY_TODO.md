# Tricky Daily — improvement backlog

This is the persistent planning backlog for future Tricky Daily work. It records gaps and improvements from the architecture review; an unchecked item means the requirement is **not fully satisfied or not yet verified**, not necessarily that no related code exists. `[~]` marks a partially implemented or incompletely verified item. Before changing code, inspect the current implementation and tests: some safeguards and feedback features already exist and must be extended rather than duplicated or regressed. The current live 60-track cycle assembles candidates through `spotify_discovery.py` and `spotify_daily_cycle.py`; `spotify_daily_playlist.py` is a separate legacy/alternate 30-track builder, not the current cycle path.

## Product goals

Tricky Daily should reliably publish exactly 60 valid, unique tracks; learn from actual listening without confusing exposure with preference; discover music without becoming repetitive; and arrange tracks into an enjoyable sequence. Safety and data integrity outrank recommendation preferences.

## Current implementation boundary — source-checked 2026-11-06

- Candidate generation in `spotify_discovery.py` filters exact negative track keys/URIs before ranking, deduplicates candidates, searches deeper pages, and only then relaxes the per-artist cap. The cycle reconciles manual removals against the prior accepted-cycle baseline before generation. The separate `--verify-only` mode checks live count, duplicate URIs and blacklist membership.
- The normal cycle validates 60 candidate rows, primary artists, Spotify track-URI shape and unique URIs; saves a recovery backup; re-reads the live playlist and checks owner/name/description/snapshot ID/complete ordered contents/lock; writes and SHA-256 verifies an immutable stage; commits and pushes that stage plus backup before Spotify mutation; checks repository HEAD and the live snapshot again; then calls the protected replacement helper. After the write it persists `replacement_accepted_pending_verification`, publishes `cycled=true`, rotates and reads back the description, and verifies complete ordered URI equality, 60 count, uniqueness, valid artists, and blacklist exclusion before completion.
- **Automatic post-write validation:** now checks complete pagination, exact ordered URI equality against the verified stage, exactly 60 items, URI uniqueness/shape, valid primary artists, and current blacklist policy. The separate `--verify-only` mode remains a read-only diagnostic and is not a substitute for the staged cycle's full post-write contract.
- **Concurrency:** GitHub Actions concurrency, same-date state/stage guards, repository-head equality after stage commit, and a second live snapshot check reduce races. Spotify does not support conditional writes by snapshot ID; a final race window and stale-lock recovery remain open.
- **Transactional staging:** the exact ordered payload and recovery backup are committed before mutation, verified from the committed tree, and retained as immutable evidence. A same-date pending-stage guard blocks blind regeneration. Guided resume/rollback/discard from a surviving stage is still open.
- **Force/idempotency correction CI-verified 2026-11-06:** `cycle_already_completed()` no longer accepts a force override. Full safe CI run #42268351897 passed 500 tests, including a forced duplicate exiting before Spotify client creation.
- **Description read-back correction CI-verified 2026-11-06:** Spotify's HTML-escaped description is unescaped before comparison in `update_description_and_verify()`; the regression test is included in the 500-test green run #42268351897.
- **Daily-only snapshot refresh added 2026-11-06:** `scripts/spotify/spotify_daily_snapshot.py` and `.github/workflows/tricky-daily-snapshot-refresh.yml` perform GET-only Daily snapshot refresh and manual-removal reconciliation at 06:25 UTC daily. The first push-triggered runs exposed stale test expectations, a compatibility import collision, and stale Daily reference-index memberships. The import path and index reconciliation were corrected and protected by isolated subprocess regression. Snapshot workflow run #42263830309 passed its focused schedule/import tests, authenticated successfully, refreshed the live Daily snapshot, and published the aligned catalog/index/health files: 29 accessible unique items, 29-row baseline, 55 blacklisted entries, zero whitelist entries, and zero stale/missing Daily index links. The generated-data audit and full 481-test suite passed on the refreshed state. This confirms the GET-only snapshot path is operational; live playlist publication remains separately gated.
- **Manual-removal feedback reconciliation merged 2026-11-06:** PR #166 merged as `49d1c61a74a77fb4c7e5d180247f5d8c9eeee7fc`. The GET-only snapshot workflow run [#42268795272](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42268795272) passed after merge, refreshed the Daily snapshot (29 accessible/unique tracks), and reconciled all 55 existing blacklist rows into 55 idempotent `user_removed` feedback events. Feedback now contains 60 track rows. The same run used only two Spotify GET requests and performed zero playlist mutations. Playback-tracker coverage remains unknown because the segment file is absent; Last.fm and liked-song observation statuses are available/observed. Exact removals remain hard exclusions; artist-level negative learning requires measured post-add exposure.
- **Exposure-boundary refinement:** exact manually removed tracks remain hard-blacklisted regardless of measured exposure, but a removal contributes to the broader artist-level negative score only when post-add playback or Last.fm scrobbles were observed. An unexposed removal does not teach the system to avoid the whole artist. Regression tests cover both paths.
- **Quota-aware Daily discovery merged 2026-11-06 in PR #168:** the prior code searched all 300 similar artists immediately, then searched deeper pages across the full pool if needed. The Daily path now searches an initial 80-artist cohort and doubles cumulative coverage only if fewer than 60 unique candidates are found (80 → 160 → 300); deeper catalogue pages are deferred until the available artist pool is exhausted. This preserves the 60-track target and hard exclusions while reducing typical Spotify Search calls. The full 509-test suite and public repository security scan passed on the final PR head before merge.
- **Latest quota evidence:** scheduled midnight cycle run [#42268583897](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42268583897) passed compile/tests and credential validation, then failed on the first Spotify Search with HTTP 429 QUOTA_EXCEEDED (Retry-After 5,781 seconds). No playlist mutation occurred. The failure path preserved 195 name-only discovery candidate rows; these are not yet Spotify-resolved track URIs or a publishable 60-track stage. The cooldown reported by Spotify ended around 2026-11-06 19:49 UTC. The exact cooldown was committed to `.github/spotify_api_cooldown.json` by PR #168 so any run before expiry fails closed.
- **Cooldown persistence gap fixed and merged in PR #168:** the cycle workflow previously preserved surfaced candidate names after failure but did not commit `.github/spotify_api_cooldown.json`. Because the normal state-persistence step only runs after an accepted cycle/description update, a 429 cooldown could be lost between Actions runs and the next scheduled retry could hit Spotify again. The failure-recovery step now persists the cooldown file even when no candidate file exists; a regression test covers this and passed in the 509-test full suite.
- Forced runs otherwise follow the normal ownership, managed-playlist lock, candidate generation, backup, replacement, description and read-back path. Force must never bypass blacklist, uniqueness, whitelist reconciliation or other safety checks.
- Open proposals [PR #159](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/159) (strict DST cron matching) and [PR #160](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/160) (exposure-aware ranking and quality report) remain unmerged. [PR #158](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/158) proposes adjacent Discover Weekly feedback tracking.

## P0 — correctness and publication safety

- [x] **Blacklist is an absolute invariant.** Candidate discovery filters exclusions, the cycle reloads policy after durable staging, and exact post-write read-back is checked again against current blacklist policy. Regression tests cover blocked post-write results.
- [ ] **Whitelist semantics are explicit.** Define exactly what whitelist entries protect/permit; preserve them across refreshes and reconcile them with the live playlist. Do not let a stale snapshot silently undo newer user decisions.
- [~] **Transactional cycle state.** The immutable stage and recovery backup are committed before mutation; accepted/pending/ambiguous states are persisted with a same-date guard. Guided resume/rollback/discard and a fully transactional multi-file state commit remain open.
- [x] **Staging is the publication contract.** Persist the exact ordered 60 Spotify track URIs and candidate metadata, hash the full stage, commit/push it before mutation, and verify the committed blob before writing. A surviving stage blocks blind same-date retries; guided resume remains open.
- [x] **Verify the live result.** Post-write read-back requires complete pagination, exact ordered URI equality with staging, exactly 60 entries, unique valid track URIs, valid primary artists, and no current blacklist hits before completion.
- [~] **Concurrency protection.** Workflow concurrency, same-date state/stage guards, repository-head equality after stage commit, and a second live snapshot check reduce races. Spotify does not support conditional write by snapshot ID; a final race window and stale-lock recovery remain open.
- [~] **Spotify API resilience.** Ambiguous write responses now trigger exact live read-back; exact target/pre-write/partial/unreadable outcomes are distinguished and unsafe outcomes block same-date retries. Provider 429 cooldowns must be respected; broader transient retry/backoff behavior remains to be reviewed.
- [~] **Known-good recovery.** The pre-write backup, immutable stage, audit, pending-verification state, and ambiguous date guard are durable. Guided resume/rollback/discard from a surviving stage remains open.
- [x] **Forced-run parity.** Force bypasses only the clock gate; the same reconciliation, staging, validation, description update/read-back, audit, and post-publication verification apply.

### P0 acceptance checks

- A blacklisted URI is rejected in normal, forced, retry, and every fallback path.
- Injected failures at each stage leave state recoverable and never report a cycle complete prematurely.
- Two simultaneous invocations cannot both publish.
- A simulated timeout after Spotify accepts a write triggers read-back/reconciliation rather than a blind second write.
- A successful run is only marked complete after the live playlist is verified to match the committed staging result and contains exactly 60 unique valid tracks.
- A forced invocation outside the time window is permitted only when the Eastern date has not already completed; a second forced invocation on an already-completed Eastern date is blocked by the same idempotency guard.

## P1 — recommendation quality and learning

- [ ] **Separate signals by meaning.** Keep Last.fm scrobbles, Spotify playback-tracker observations, playlist additions, saves/likes, removals, skips where reliably available, and actual post-add listening as distinct evidence sources. Preserve source and coverage metadata.
- [ ] **Exposure-aware outcomes.** Distinguish positively engaged, explicitly rejected, ignored, not-yet-exposed, and unknown due to missing tracker coverage. Lack of a play is neutral unless there is sufficient exposure and reliable evidence to infer otherwise.
- [ ] **Track-level and artist-level preference.** Learn whether a particular track works independently of the artist's overall popularity. Avoid letting one successful track justify flooding the playlist with that artist.
- [ ] **Diminishing returns.** Reduce the influence of repeated plays/recommendations so one heavily played artist or one short listening burst cannot dominate future cycles.
- [ ] **Artist saturation controls.** Add soft per-cycle and rolling-window artist exposure limits, plus penalties for consecutive-cycle repetition. Relax these limits progressively only when needed to fill 60; audit every relaxation. Never relax track uniqueness or exclusions.
- [ ] **Discovery/familiarity balance.** Maintain separate candidate pools or quotas for comfort discoveries (known artists/styles, unfamiliar tracks) and wildcards (less predictable but taste-compatible discoveries). Tune the balance from measured outcomes.
- [ ] **Recommendation confidence.** Label recommendations as high/medium/low confidence using evidence quality and fit. Use confidence to control experimentation, not as a hard exclusion that prevents the playlist reaching 60.
- [ ] **Discovery debt / diversity recovery.** Track overexposure to artists, genres, and sounds across recent cycles. When diversity debt accumulates, bias subsequent cycles toward underrepresented alternatives without hard-filtering genres.
- [ ] **Adaptive scoring.** Evaluate recommendation strategies against engagement and diversity outcomes. Keep experiments isolated from production until validated; retain rollback to a known-good strategy.
- [ ] **Recommendation explanations.** Record concise reasons each track was selected and which evidence contributed, so poor recommendations can be diagnosed and scoring can be calibrated.

### Candidate scoring — proposed starting hypothesis, not a locked specification

Explore a weighted score with taste match (30%), discovery potential (25%), track-level engagement (20%), recency/rotation (15%), and musical fit/variety (10%). Treat these weights as an experiment, not a requirement. Apply hard exclusions before scoring; measure outcomes and tune weights rather than assuming these values are optimal.

## P1 — sequencing and listening experience

- [ ] **Transition-aware ordering.** Optimize neighboring tracks using available BPM, energy/loudness, mood, genre, instrumentation, and duration metadata. Avoid abrupt transitions while allowing intentional contrast.
- [ ] **Configurable arc.** Support an opening, development, exploration, peak, and closing shape. Preserve the user's desired peak-position control (initial default around 80–90%, subject to testing) and optional reverse/alternate arcs.
- [ ] **Graceful metadata fallback.** Missing BPM/energy/mood data must not break generation; use confidence-aware fallbacks and avoid pretending unknown values are measured.
- [ ] **Sequence diagnostics.** Report unusually large tempo/energy/mood jumps and compare the final ordering with the candidate order.

## P2 — integrations, reporting, and operations

- [ ] **Discover Weekly learning integration.** Track Discover Weekly additions/removals/likes and other observable changes as a separately attributed Spotify source. Feed useful discovery evidence into Daily without conflating Discover Weekly tracks with Daily recommendations or Last.fm history.
- [ ] **Cycle quality report.** Include candidate counts, rejection reasons, retries, fallback relaxations, artist/genre distribution, duplicate checks, blacklist/whitelist checks, staged count, live count, snapshot comparison, publication result, and verification status.
- [ ] **Outcome report.** Track post-publication plays, saves/likes, removals, exposure coverage, and engagement by artist, track, confidence tier, and recommendation strategy.
- [ ] **Automated health monitoring.** Surface failed cycles, pending verification, incorrect track counts, state drift, repeated fallbacks, and credential/preflight failures. Distinguish warnings from confirmed failures.
- [ ] **Audit trail.** Keep a durable per-run record of inputs, state versions, algorithm/config version, selected tracks, rejection reasons, staged payload, Spotify response/snapshot, read-back result, and final status.

## Non-negotiable policy hierarchy

1. Blacklist/removal exclusions and valid Spotify track requirements — never relaxed.
2. Unique track URIs and safe state/publication invariants — never relaxed.
3. User-defined whitelist protections — never silently overridden.
4. Artist diversity and rotation preferences — progressively relaxable with an audit trail.
5. Genre, familiarity, discovery, and recommendation-score preferences — tunable/relaxable to complete the 60-track target.

**Core principle:** Daily should aim to publish 60 valid, unique, verified tracks every cycle. It may relax recommendation preferences to fill the playlist, but it must never sacrifice exclusions, uniqueness, or publication safety to hit 60.

## Implementation order

1. Audit the current code and tests against the P0 checklist; mark already-satisfied items as implemented only after verifying the actual paths.
2. Fix any P0 gaps and add failure-injection/regression tests before expanding recommendation logic.
3. Improve exposure-aware feedback, track/artist learning, and saturation controls.
4. Add confidence/diversity experimentation and transition-aware sequencing.
5. Integrate Discover Weekly attribution, reporting, and health monitoring.

A no-write stage-only attempt (#42268583897) was stopped by Spotify HTTP 429 QUOTA_EXCEEDED with Retry-After: 5781 seconds, before stage creation and before any playlist mutation. Do not retry Spotify requests until the cooldown expires. No live cycle has been authorized or performed.

When continuing this work in a future chat, read this backlog together with `docs/TRICKY_DAILY_CYCLE.md`, `scripts/spotify/spotify_daily_cycle.py`, `spotify_playlist_cloud.py`, `spotify_discovery.py`, the feedback/preflight code, and the relevant workflow files. Treat `spotify_daily_playlist.py` as the legacy 30-track builder unless its role is explicitly changed. Re-check repository state before assuming any unchecked item is still outstanding.
