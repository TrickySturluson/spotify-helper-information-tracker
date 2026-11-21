# Tricky Daily recommendation memory

## Purpose and boundary

This is the playlist-local event history for **Tricky Daily** (`4yUVHSMQySfWeEowfIMcx7`). It records what Daily selected, whether the selected tracks were published, the intervals during which they were exposed, and later observations. It is not a generic discovery catalogue, a replacement for `daily_feedback.json`, or a scoring model.

The memory is descriptive first. It does not change candidate ranking, blacklist/whitelist policy, artist penalties, playlist-manager state/audit, the canonical Music Library, or Spotify. A track-level rejection remains track-level evidence; the ledger never converts it into an artist rejection.

## Storage and schema

The active store is `assistant_data/spotify/daily_recommendation_memory.jsonl`. Each line is one immutable event with:

- `schema_version`: integer schema version (currently 1)
- `event_id`: deterministic ID; a retry with the same ID and same payload is a no-op, while the same ID with different content is a hard integrity error
- `event_type`, `occurred_at`, `playlist_id`
- `recommendation_event_id` for events attached to one recommendation
- `track`: Spotify URI/ID plus normalized primary-artist/title identity
- `cycle`: Eastern cycle date, GitHub run ID/attempt, stage path and payload hash where known
- `strategy`: strategy version, scoring-config digest and source commit
- `selection`: rank, score, confidence, tier, explanation and fallback metadata
- `evidence_provenance`: separately attributed similarity, Last.fm familiarity, liked status, Daily feedback, listening trends and lyric-analysis evidence

Event types are deliberately separate:

1. `recommendation_selected` records each selected track before the playlist write. It is not proof of publication.
2. `publication_accepted` opens that recommendation's exposure interval after Spotify accepts the track replacement.
3. `publication_verified` records the exact post-write snapshot ID after read-back succeeds.
4. `exposure_closed` closes an interval with a reason such as `user_removed`, `curator_rotation`, or `recovery_rollback`. Curator rotation is neutral.
5. `outcome_observed` records one source-specific observation: measured playback sessions, Last.fm scrobbles, liked status, explicit removal, or retained membership.
6. `recovery_resolved` links a staged recommendation to an owner-confirmed resume, rollback, or discard.
7. `migration_completed` records the one-time migration boundary.

Repeated recommendations for one URI have distinct recommendation-event IDs and share a stable track identity key. Outcomes always point to one recommendation event and carry their own source and observation window.

## Append, idempotency and crash recovery

Writers validate the complete JSONL stream before changing it. They write the old immutable events plus new unique events to a temporary file, flush it, then atomically replace the active file. A malformed line, unsupported schema, duplicate ID with conflicting payload, or invalid event shape stops the operation; it never resets the ledger.

Daily's workflow concurrency group serializes production writers. Recommendation events are included in the immutable pre-write stage commit. Publication and outcome events are persisted by the cycle/observation workflows. The stage stores the recommendation event IDs, so owner-confirmed recovery can resolve the exact same events after a runner failure. If a publication event is missing after a crash, recovery may reconstruct it from the committed stage and exact live-state classification; it must not invent a play or a successful verification.

## Migration

The first migration imports only timestamped Daily additions from `assistant_data/spotify/daily_feedback.json`. These become `legacy-unattributed` recommendation events with unknown strategy/rationale. Timestamped liked observations and removal events may be attached to the matching exposure interval.

The migration **does not** import or infer outcomes from `assistant_data/recommendations/discovery_candidates.json`, historical candidate rows with null listening evidence, aggregate playback totals without per-event timestamps, or aggregate Last.fm counts without a reliable interval. Those remain unknown. The migration marker and deterministic event IDs make retries safe.

## Outcome semantics

The sources remain separate:

- Spotify playback-tracker segments are measured playback, not Last.fm scrobbles.
- Last.fm rows are scrobbles, not proof of Spotify playback.
- Liked/Saved status includes the at-add baseline and later observations; pre-liked tracks are not treated as newly saved.
- Manual removals/blacklist events are explicit playlist-local rejection.
- Retained membership is a snapshot observation, not proof of listening.
- Curator rotation and recovery rollback close exposure without becoming negative preference.

Positive evidence can be recorded even when coverage is incomplete. Absence is not a zero. `no_observed_play` / `retained_unplayed` / `unplayed_then_removed` require explicit complete coverage for the whole exposure interval. Current sources generally report `available` or `unknown`, not complete coverage, so a no-play result must normally remain `unknown_incomplete_coverage`. A newly published event without a post-exposure observation is `not_yet_observed`.

A high-play-then-remove result is distinct from an unplayed removal and preserves the counts and sources. Neither outcome modifies artist-level preference automatically.

## Compaction and retention

The active JSONL is the recent operational ledger. Compaction is cold archival, not deletion:

- Only recommendation-event groups with a terminal exposure close older than the retention horizon are eligible.
- Selected-but-unpublished, open-exposure, pending-verification, and unresolved-recovery groups remain active.
- Compaction writes a content-hashed, immutable compressed JSONL archive first, then updates an atomic archive manifest and a rebuildable per-track checkpoint, and only then removes those event IDs from the active file.
- The archive is the detailed source of truth; the checkpoint is a derived index and can be rebuilt from verified archives.
- A retry after interruption verifies/reuses the same archive and finishes the manifest/checkpoint/active-log steps. It must never compact an open exposure or discard an event without a verified archive entry.

Compaction is an explicit maintenance command, not part of the live cycle. It is not allowed to run during playlist publication.

## Acceptance tests

- Duplicate ingestion is idempotent; conflicting reuse of an event ID fails closed.
- Repeated recommendations create separate events linked to one track identity.
- Delayed scrobbles append a later source-attributed observation without rewriting earlier events.
- High-play-then-remove differs from unplayed-then-remove.
- Retained-but-unplayed is distinct from retained with engagement.
- Missing/incomplete coverage produces unknown, never a fabricated zero or ignore signal.
- Spotify playback, Last.fm, likes/saves, manual removal, retention and curator rotation remain separate.
- Migration imports timestamped Daily addition history only and never derives outcomes from candidate rows with null evidence.
- Recovery resolves only the event IDs in the verified stage.
- Compaction preserves an immutable archive and is retry-safe.

## Related implementation

- `scripts/spotify/daily_recommendation_memory.py`
- `scripts/spotify/spotify_daily_cycle.py`
- `scripts/spotify/daily_stage_recovery.py`
- `scripts/spotify/spotify_daily_feedback.py`
- `.github/workflows/spotify-daily-midnight-cycle.yml`
- `.github/workflows/spotify-daily-feedback-observation.yml`
