# SHIT — Next Work

This is the session handoff. Update it whenever priorities or blockers change.

## Active blocker

### Great Migration publish/rebase failure
- Run #17 failed while rebasing/publishing generated output; many canonical Library records and generated indexes conflicted.
- Do not assume the migration data was published successfully.
- **Next:** inspect the run artifact and backup; establish whether the migration output passed its integrity audit; then fix the workflow publishing strategy before another write-heavy run.
- Do not force-push or blindly resolve generated-data conflicts.

## Current priorities

1. **Recover and verify Great Migration**
   - Inspect run #17 artifacts and logs.
   - Compare artifact contents with current main and pre-run backup.
   - Run/confirm final integrity audit against the recovered output.
   - Report remaining metadata gaps and provider availability separately.

2. **Finish Library coverage planner**
   - Review PR #65 CI and correct any failures.
   - Validate the planner against real canonical record schemas.
   - Ensure transient errors, cooldowns, negative-cache results, and unchecked providers remain distinct.
   - Keep report generation read-only and deterministic.

3. **Implement the metadata retry queue**
   - Build it from canonical Library records plus provider lookup/checkpoint state.
   - Track per-recording missing fields and per-provider status, attempts, last attempt, next eligible retry, and reason.
   - Prioritize by listening evidence (Last.fm scrobbles), metadata value, and retry eligibility.
   - Never count recommendations as plays or confirmed preferences.
   - Keep provider limits/cooldowns authoritative; do not blindly retry unresolved records.

4. **Continue enrichment by bounded passes**
   - Resolve trusted recording IDs first, then use them to improve duration, acoustic metadata, track-level tags/mood, album context, and artist context.
   - Preserve source, confidence, timestamps, and raw evidence.
   - Keep track mood independent from artist identity.
   - Cache successful results and distinguish permanent negatives from transient failures.

5. **Maintain project continuity**
   - Update `project/PROJECT_LOG.md` at meaningful milestones.
   - Update this file when a task is completed, reprioritized, or blocked.

## Completed / in progress

- Read-only Library coverage planner and tests proposed in PR #65 (CI status must be checked before calling it verified).
- Project control-centre documentation added in this branch; retry queue implementation remains pending.

## Standing constraints

- Last.fm scrobbles remain the historical listening source of truth.
- Spotify playback tracker is optional prospective evidence with known coverage gaps.
- Recommendations/discoveries are separate candidate-interest evidence, not listening events.
- Do not modify Spotify playlists during migration recovery.
- Prefer preview, bounded batches, backups, checkpoints, and final integrity audits.
