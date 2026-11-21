# Tricky Daily listening trends

Tricky Daily is a rotating discovery queue, not a fixed mood/theme playlist.
Each successful rotation replaces it with exactly 60 tracks. Selection first
tries to use 60 distinct primary artists. If that falls short, discovery retries
Spotify's next search-results page for alternate tracks before relaxing the
diversity rule. If 60 distinct artists still cannot be found, it searches progressively deeper
catalogue pages and expands the artist pool before allowing repeated artists.
The per-artist ceiling is relaxed progressively as a last resort; track URIs
remain unique and playlist removals remain blocked. The fallback is audited.
The cycle now commits an immutable, hashed 60-track staging payload and recovery backup to the repository before any Spotify write. It verifies the committed stage, rechecks the repository head and live playlist after the commit, then publishes only the exact ordered staged URIs. Artist diversity may relax as a last resort; track uniqueness and exclusions never do.
Its discovery engine keeps established taste and Last.fm similarity as the
foundation, uses recent listening momentum as a small soft nudge, and retains
room for exploration outside current patterns.

> Future work and prioritized implementation checklist: [Tricky Daily TODO](TRICKY_DAILY_TODO.md).
> The TODO is a planning backlog, not a statement that unchecked items are already implemented.

## Latest repository snapshot state — 2026-11-21 UTC / 2026-11-21 Eastern

Mainline scheduled cycle [#44901651168](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/44901651168) ran 2026-11-21 11:59 UTC (06:59 Eastern). Its cycle, recovery-snapshot, and state/feedback persistence steps all succeeded. It committed stage [17852545753640e35014caf8df8557beac999add](https://github.com/TrickySturluson/spotify-helper-information-tracker/commit/17852545753640e35014caf8df8557beac999add) and completed state/audit [663291f042dd6ab08f0c48630ebb464ed048c188](https://github.com/TrickySturluson/spotify-helper-information-tracker/commit/663291f042dd6ab08f0c48630ebb464ed048c188). The committed state records Eastern cycle date 2026-11-21, status completed, 60 ordered after-URIs, and after-snapshot ID `AAAAeu09d2bu354ZxalAyWqCpM6Yeye5`.

The later scheduled delivery [#44904728622](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/44904728622) ran at 12:36 UTC (07:36 Eastern). Its cycle step succeeded but the state/feedback persistence step was skipped; the persisted state still points to the first run and remains completed for 2026-11-21, so this is the same-date duplicate no-op rather than a second publication.

GET-only snapshot refresh [#44915825720](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/44915825720), published in commit [602b2848ea29653dc3c28eb9e10950ef0e75bf0f](https://github.com/TrickySturluson/spotify-helper-information-tracker/commit/602b2848ea29653dc3c28eb9e10950ef0e75bf0f), captured 2026-11-21T14:48:41.952453Z with 60 accessible items and 60 unique URIs. Its Spotify snapshot ID matches the completed cycle state. This independently confirms the live playlist read-back after the scheduled write.

The live state is `daily_cycle.status=completed`, `last_cycle_date_eastern=2026-11-21`, with 60 ordered after-URIs. The saved stage is `assistant_data/spotify/staging/tricky_daily/2026-11-21-44901651168.json` and the pre-write backup is `playlist_backups/20261121T120059739016Z_4yUVHSMQySfWeEowfIMcx7.json`. The stage record remains immutable and still says `staged_before_spotify_write`; the completed manager state/audit and matching post-cycle snapshot establish completion.

Feedback coverage remains explicit: Last.fm is available, liked-song observations are present, and Spotify playback-tracker coverage is unknown because `playback_data/segments.jsonl` is absent. Missing playback coverage is not zero plays or rejection.

## Trend profile

`scripts/spotify/spotify_listening_trends.py` builds
`assistant_data/spotify/listening_trends.json` from canonical Last.fm scrobbles
and artist genre/tag metadata. It reports 7-day, 30-day, 90-day, preceding
60-day, and all-time artist activity. Genre/tag trends are aggregated from
recent plays and the artist metadata already available in the project.

The trend layer distinguishes a rising interest from an established favorite.
Sparse or missing comparison history is marked low confidence, never treated
as zero or as an artificial spike. The candidate-ranking nudge is capped at
0.03 and only applies to medium/high-confidence artist trends. No genre is
hard-filtered. Daily ignores playlist lyric-theme affinity; other playlists
retain their playlist-specific theme system.

## Feedback boundaries

Daily's own saves, post-add listening and scrobbles remain useful outcome
signals. Scheduled rotation is neutral housekeeping and never a blacklist or
playlist-fit rejection. This trend profile is user-wide context, not a
replacement for Daily's separate exposure feedback or general playlist-fit
calibration.

## Automatic schedule and recovery

Mainline still declares combined UTC cron expressions `0 4,5 * * *` and `15 4,5 * * *`; its current runner uses the Eastern local-hour gate and same-date completion guard but does not inspect the exact `github.event.schedule` string.

Mainline scheduled cycle [#44901651168](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/44901651168) ran 2026-11-21 11:59 UTC (06:59 Eastern). Its cycle, recovery-snapshot, and state/feedback persistence steps all succeeded. It committed stage [17852545753640e35014caf8df8557beac999add](https://github.com/TrickySturluson/spotify-helper-information-tracker/commit/17852545753640e35014caf8df8557beac999add) and completed state/audit [663291f042dd6ab08f0c48630ebb464ed048c188](https://github.com/TrickySturluson/spotify-helper-information-tracker/commit/663291f042dd6ab08f0c48630ebb464ed048c188). The committed state records Eastern cycle date 2026-11-21, status completed, 60 ordered after-URIs, and after-snapshot ID `AAAAeu09d2bu354ZxalAyWqCpM6Yeye5`.

The later scheduled delivery [#44904728622](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/44904728622) ran at 12:36 UTC (07:36 Eastern). Its cycle step succeeded but the state/feedback persistence step was skipped; the persisted state still points to the first run and remains completed for 2026-11-21, so this is the same-date duplicate no-op rather than a second publication.

GET-only snapshot refresh [#44915825720](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/44915825720), published in commit [602b2848ea29653dc3c28eb9e10950ef0e75bf0f](https://github.com/TrickySturluson/spotify-helper-information-tracker/commit/602b2848ea29653dc3c28eb9e10950ef0e75bf0f), captured 2026-11-21T14:48:41.952453Z with 60 accessible items and 60 unique URIs. Its Spotify snapshot ID matches the completed cycle state. This independently confirms the live playlist read-back after the scheduled write.

This is one actual scheduled 60-track publication and one same-date duplicate no-op on mainline. It does not prove which exact cron expression matched the active offset, nor does it prove the strict DST gate is deployed.

Draft PR [#200](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/200), current head `b2de95585fa9656ba86c238ca879d767030e4cfa`, splits the schedule into four explicit entries (`0 4`, `15 4`, `0 5`, `15 5` UTC), passes `github.event.schedule` as `SCHEDULE_CRON`, and accepts only entries whose expected offset matches the current `America/New_York` offset. Missing/unknown schedule strings fail closed. Delayed matching-offset deliveries may still catch up later that Eastern date; the existing date guard prevents duplicate publication. Exact-head CI passes; these semantics remain branch-only until owner-controlled merge.

- During EDT, 04:00/04:15 UTC correspond to 00:00/00:15 Eastern; 05:00/05:15 UTC correspond to 01:00/01:15.
- During EST, 05:00/05:15 UTC correspond to 00:00/00:15 Eastern; 04:00/04:15 UTC are 23:00/23:15 on the preceding Eastern date.
- The 15-minute entry is a recovery opportunity for the matching offset. A same-date completed state makes any later accepted delivery a local no-op before Spotify client creation.
- Historical scheduled runs #42212368912 and #42214834581 were delayed into the morning and failed on HTTP 429 before cooldown persistence was fixed. PR #168 now commits the cooldown on failed cycles.
- User-owned PR #159 overlaps the schedule gate and was not modified. Do not merge it blindly; the current Jockey PR contains the stricter four-entry mapping and pre-auth schedule check.

The workflow also supports a repository test-trigger push to `.github/test-triggers/tricky-daily-live-cycle.json`. That push forces the runner, with an explicit `action` value of `cycle`, `description-only`, or `verify-only`; if the key is absent, it defaults to `description-only`. This is a deliberate test hook, not the normal schedule. The current trigger is left in read-only `verify-only` mode; Jockey did not dispatch or change it.

Manual dispatch remains midnight-gated unless `--force` is explicitly supplied. **Force bypasses the clock gate only**; the same-Eastern-date completion guard remains active for full cycles and is checked before Spotify client construction. Force does not bypass ownership, managed-playlist permission, unlock, whitelist/blacklist reconciliation, staging, validation, snapshot, audit, or read-back safeguards.

## Rotating description

Every successful full cycle also updates the short editorial description using
a deterministic daily rotation of concise lines. It is separate from the
metadata-driven description generator: Tricky Daily has an explicit user-
approved editorial rotation, while the generic generator continues to protect
non-empty manual descriptions on other playlists.

The description PUT is followed by a fresh playlist GET. The cycle is only
marked fully completed when Spotify returns the exact new description. The
accepted description and its verification status are persisted independently
from the track-cycle date guard.

The description-only path is also a playlist mutation and must be bracketed by
durable snapshots. Draft PR #200 adds a guarded flow that requires the current
playlist to contain exactly 60 unique valid tracks, saves and commits the
pre-change snapshot plus audit before the PUT, persists an accepted/pending
state immediately after Spotify accepts the PUT, then saves and commits the
post-change snapshot. It does this post-change capture even if description
read-after-write verification fails, so an accepted-but-unverified update is
not repeated blindly. The accepted-but-pending state records the committed
after-snapshot path and Spotify snapshot ID before final validation, so the
snapshot remains directly addressable if verification fails. Completion
requires the exact description and unchanged ordered 60-track contents. It
never replaces tracks. Exact-head CI passes; merge and live operational
verification remain pending.

## Live preflight

`.github/workflows/spotify-daily-live-preflight.yml` runs on updates to the
dedicated test trigger, every six hours, and manual `workflow_dispatch`. It refreshes the OAuth access token
when required, then performs read-only Spotify requests to verify the
authenticated account, the exact Tricky Daily ID and name, playlist ownership,
the managed-playlist exception, the explicit unlock state, and playlist-item
readability. It never writes to Spotify or commits project state.

A failed preflight blocks confidence in the next scheduled cycle. In
particular, a locked playlist is reported as a safe refusal rather than
silently unlocked. Unit tests mock Spotify and verify that the preflight only
uses GET operations; the live workflow checks the real credentials and
permissions.

## Operation

The midnight cycle refreshes the trend report before building recommendations.
To inspect or regenerate it independently:

```bash
python compat/spotify_listening_trends.py
```

## Durable staging and failure-safe publication — 2026-11-06

Before a production track replacement, the runner writes a unique JSON stage containing the exact ordered 60 URIs, candidate metadata, intended description, pre-write snapshot ID/URI order, recovery backup path, and a SHA-256 digest over the complete record. In GitHub Actions it commits and pushes the stage, backup, audit, candidate/trend/feedback and removal-reconciliation outputs to main, then reads the committed blob back and verifies its hash/order. A push failure aborts before Spotify mutation. A repository-head check and second live playlist/policy recheck run after the stage commit and immediately before replacement.

spotify_playlist_cloud.replace_playlist() reconciles write exceptions by reading the live ordered URIs. Exact target means the write applied despite a lost response; exact pre-write order means it did not apply; partial or unreadable state raises an explicit ambiguous error. The Daily runner persists a same-date guard for ambiguous outcomes. A surviving production stage blocks same-date automatic retries. After a successful write, the complete live snapshot must match the staged ordered URIs exactly, with 60 unique valid track URIs, valid primary artists and no current blacklist hits.

The safe --stage-only action performs the full candidate/pre-write/stage-commit/read-back path but exits before Spotify playlist writes or description changes. Stage-only run #42316048566 succeeded after the description snapshot and ignored-backup persistence fixes: the committed payload contained 60 unique tracks from 60 distinct artists, had zero blacklist overlaps, and its SHA-256/order was verified from the committed Git tree. The production cycle #42316296314 then repeated the normal generation/staging path and completed the live replacement. The earlier 429 runs #42212368912 and #42214834581 occurred before cooldown persistence was reliably committed; PR #168 fixed the always-run persistence path. Current trigger action is `verify-only` to prevent accidental repeat publication.


## Owner-confirmed production-stage recovery — draft PR #200

A surviving production stage is never retried automatically. Draft PR #200 adds an owner-only manual recovery path to the Tricky Daily midnight-cycle workflow. It is **branch-only until PR #200 is owner-merged** and has not been exercised against Spotify by Jockey.

Use the workflow's \`recovery_action\`, \`recovery_stage_path\`, and \`recovery_confirmation\` inputs only after inspecting the stage and audit. The actor must be \`TrickySturluson\`, the run must be a manual \`workflow_dispatch\` in the canonical repository, the central SHIT auth broker must be active, and the confirmation must be exactly \`RECOVER TRICKY DAILY\`. Supply the exact committed path directly under \`assistant_data/spotify/staging/tricky_daily/\`; the stage and referenced \`playlist_backups/\` file are read from the committed Git tree and checked against the stage SHA-256 and exact ordered pre-write URI list.

- **resume:** accepts only the exact staged target or the exact pre-write order with a known staged description. If the pre-write order is still live, it writes the staged 60-track target; if the target is already live, it does not repeat the track PUT. It rechecks the current playlist-local blacklist before any re-add and requires the playlist to be explicitly unlocked for any write.
- **rollback:** accepts only the exact staged target or a known pre-write/description-only intermediate state. It restores the exact pre-write backup and description. The backup must have unique valid tracks and must pass current blacklist checks before restoration; a blocked or malformed backup is refused.
- **discard:** is read-only and is allowed only when the exact pre-write ordered tracks, original description, and pre-write Spotify snapshot ID are still live. It never calls a Spotify write endpoint.

Every recovery write is bracketed by a committed before snapshot and a committed after snapshot. Recovery state and audit record the in-progress action, before/after paths, and terminal result without overwriting unrelated playlist-manager pending state. A resolved stage clears the same-date stage guard only when its resolution ledger hash matches the immutable stage. Partial, unreadable, stale, blacklisted, locked, wrong-owner, or otherwise conflicting states remain blocked for human inspection.

The Nov 21 production stage \`assistant_data/spotify/staging/tricky_daily/2026-11-21-44901651168.json\` is already recorded as completed by mainline state/audit and must be rejected by recovery; it is not an unresolved recovery target. Jockey did not dispatch the recovery workflow, call Spotify, or modify live playlist/state/audit data. A passing CI run will verify mocked behavior only, not live recovery.
