# Tricky Daily — improvement backlog

This is the persistent planning backlog for future Tricky Daily work. It records gaps and improvements from the architecture review; an unchecked item means the requirement is **not fully satisfied or not yet verified**, not necessarily that no related code exists. `[~]` marks a partially implemented or incompletely verified item. Before changing code, inspect the current implementation and tests: some safeguards and feedback features already exist and must be extended rather than duplicated or regressed. The current live 60-track cycle assembles candidates through `spotify_discovery.py` and `spotify_daily_cycle.py`; `spotify_daily_playlist.py` is a separate legacy/alternate 30-track builder, not the current cycle path.

## Product goals

Tricky Daily should reliably publish exactly 60 valid, unique tracks; learn from actual listening without confusing exposure with preference; discover music without becoming repetitive; and arrange tracks into an enjoyable sequence. Safety and data integrity outrank recommendation preferences.

## Current implementation boundary — source-checked 2026-11-06

- Candidate generation in `spotify_discovery.py` filters exact negative track keys/URIs before ranking, deduplicates candidates, searches deeper pages, and only then relaxes the per-artist cap. The cycle reconciles manual removals against the prior accepted-cycle baseline before generation. The separate `--verify-only` mode checks live count, duplicate URIs and blacklist membership.
- The normal cycle validates 60 candidate rows, primary artists, Spotify track-URI shape and unique URIs before saving a backup and calling the protected replacement helper. It then persists `replacement_accepted_pending_verification`, publishes `cycled=true`, rotates and reads back the description, and reads the playlist again.
- **Automatic post-write validation remains incomplete:** the normal path checks 60 returned items and valid primary artists, but does not explicitly recheck duplicate URIs, recheck blacklist membership, or compare the returned ordered URIs with a durable pre-write ordered staging artifact. The separate `--verify-only` mode checks duplicates and blacklist but does not compare with a stored expected order. Keep the related P0 items open.
- A GitHub Actions concurrency group serializes workflow runs with `cancel-in-progress: false`; there is no durable cross-process lease or stale-lock recovery. Mark concurrency protection partial, not fully solved.
- The cycle persists a backup and pending-verification marker before marking completion, but the exact ordered 60-item plan is not stored as a dedicated immutable staging artifact before replacement. Transactional staging/recovery is therefore partial.
- **Force/idempotency correction published 2026-11-06:** `cycle_already_completed()` no longer accepts a force override, and both cycle guard call sites use it without a force argument. The focused schedule test now asserts a forced duplicate exits before any Spotify client is created. This is implemented but remains pending remote CI confirmation; do not mark the acceptance criterion verified until the test run completes.
- **Description read-back correction published 2026-11-06:** Spotify's HTML-escaped description is unescaped before comparison in `update_description_and_verify()`; a regression test covers the apostrophe encoding observed in the current snapshot. Pending remote CI confirmation.
- **Daily-only snapshot refresh added 2026-11-06:** `scripts/spotify/spotify_daily_snapshot.py` and `.github/workflows/tricky-daily-snapshot-refresh.yml` perform GET-only Daily snapshot refresh and manual-removal reconciliation at 06:25 UTC daily. First workflow execution and current live read-back remain unverified.
- Forced runs otherwise follow the normal ownership, managed-playlist lock, candidate generation, backup, replacement, description and read-back path. Force must never bypass blacklist, uniqueness, whitelist reconciliation or other safety checks.
- Open proposals [PR #159](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/159) (strict DST cron matching) and [PR #160](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/160) (exposure-aware ranking and quality report) remain unmerged. [PR #158](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/158) proposes adjacent Discover Weekly feedback tracking.

## P0 — correctness and publication safety

- [ ] **Blacklist is an absolute invariant.** Enforce removed-track/blacklist exclusions in one central policy layer before scoring and again before publication. Forced runs, retries, fallback expansion, stale caches, and artist-limit relaxation must never bypass it.
- [ ] **Whitelist semantics are explicit.** Define exactly what whitelist entries protect/permit; preserve them across refreshes and reconcile them with the live playlist. Do not let a stale snapshot silently undo newer user decisions.
- [ ] **Transactional cycle state.** Separate candidate generation, validation, staging, publication, read-back verification, and final state commit. A failed stage must not partially advance history or overwrite known-good state.
- [ ] **Staging is the publication contract.** Persist the exact proposed 60 Spotify track URIs and associated metadata before writing. Publish only that validated staging artifact; make retries idempotent and resume from the last safe stage.
- [ ] **Verify the live result.** After publication, fetch the playlist and compare its ordered contents (or the intended order if ordering is guaranteed) against staging. Confirm exactly 60 entries, unique track URIs, no blacklist hits, valid/available items, and expected playlist identity before marking the cycle complete.
- [ ] **Concurrency protection.** Prevent scheduled, recovery, and forced runs from executing concurrently or racing on state. Use a durable lock/lease or equivalent workflow-level concurrency guard, with safe stale-lock recovery.
- [ ] **Spotify API resilience.** Handle 429 using Retry-After, transient 5xx/network failures with bounded exponential backoff and jitter, token expiry separately, and ambiguous write timeouts by reading live state before retrying. Never blindly repeat a non-idempotent or destructive operation.
- [ ] **Known-good recovery.** Preserve the last verified playlist snapshot and enough run metadata to recover safely after interrupted publication. A pending-verification state must remain distinguishable from a fully completed cycle.
- [ ] **Forced-run parity.** Forced runs must execute the same policy checks, state reconciliation, staging, validation, description update/read-back, audit, and post-publication verification as scheduled runs. Force may bypass the clock gate only, not safety rules.

### P0 acceptance checks

- A blacklisted URI is rejected in normal, forced, retry, and every fallback path.
- Injected failures at each stage leave state recoverable and never report a cycle complete prematurely.
- Two simultaneous invocations cannot both publish.
- A simulated timeout after Spotify accepts a write triggers read-back/reconciliation rather than a blind second write.
- A successful run is only marked complete after the live playlist is verified to match the approved staging result and contains exactly 60 unique valid tracks.
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

When continuing this work in a future chat, read this backlog together with `docs/TRICKY_DAILY_CYCLE.md`, `scripts/spotify/spotify_daily_cycle.py`, `spotify_discovery.py`, the feedback/preflight code, and the relevant workflow files. Treat `spotify_daily_playlist.py` as the legacy 30-track builder unless its role is explicitly changed. Re-check repository state before assuming any unchecked item is still outstanding.
