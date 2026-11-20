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

## Latest repository snapshot state — 2026-11-20 UTC / 2026-11-20 Eastern

The latest mainline user-authorized Tricky Daily publication was workflow [#44708292405](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/44708292405). It was a **push-triggered** `action: cycle` run, not a scheduled cron delivery. It started at 2026-11-20 09:09:18 UTC (04:09 Eastern) and completed successfully at 09:11:02 UTC. The runner committed stage `assistant_data/spotify/staging/tricky_daily/2026-11-20-44708292405.json` (payload SHA-256 `c8ad07b1e7f8745ac08db4a2ea7378b8439384015169227d62bffbb035443e49`) and recovery backup `playlist_backups/20261120T091051361667Z_4yUVHSMQySfWeEowfIMcx7.json` before the Spotify write. The completed state records 60 ordered after-URIs, description `A little familiar, a little unhinged.`, and post-cycle snapshot ID `AAAAd7gRBY+iCM4wXDnz0UJ8x+Sq39Ua`. The run's cycle, recovery-snapshot, and state/feedback persistence steps all succeeded.

The subsequent GET-only snapshot refresh committed as mainline `b606fe0fa7712c01cb8f793eae85afd609187677` and captured `2026-11-20T15:38:03.306427Z`: 60 accessible items, 60 unique Spotify track URIs, and the same verified description. This confirms one actual playlist publication plus persisted state/audit and a later snapshot refresh. It does **not** prove the automatic schedule, DST selection, or a same-date scheduled duplicate no-op.

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

Mainline currently declares combined UTC cron expressions `0 4,5 * * *` and `15 4,5 * * *`. Its runner uses the Eastern local-hour gate and same-date completion guard, but does not inspect the exact scheduled cron string. This can produce extra same-date deliveries during EDT and does not prove which UTC entry matched the active offset.

Draft PR [#200](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/200) splits the schedule into four explicit entries (`0 4`, `15 4`, `0 5`, `15 5` UTC), passes `github.event.schedule` as `SCHEDULE_CRON`, and accepts only entries whose expected offset matches the current `America/New_York` offset. Missing/unknown schedule strings fail closed. Delayed matching-offset deliveries may still catch up later on that Eastern date; the existing date guard prevents duplicate publication. These semantics are implemented only on the PR branch; exact-head CI and a live scheduled delivery remain pending.

- During EDT, only the 04:00/04:15 UTC entries are accepted; 05:00/05:15 entries are rejected as the wrong offset.
- During EST, only the 05:00/05:15 UTC entries are accepted; 04:00/04:15 entries are rejected as pre-midnight deliveries.
- The 15-minute entry is a recovery opportunity for the matching offset. A same-date completed state makes any later accepted delivery a local no-op before Spotify client creation.
- Historical scheduled runs #42212368912 and #42214834581 were delayed into the morning and failed on HTTP 429 before cooldown persistence was fixed. PR #168 now commits the cooldown on failed cycles. The 2026-11-20 user-authorized push-triggered cycle #44708292405 succeeded, but it is not schedule evidence.
- The older user-owned [PR #159](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/159) was not modified and is stale; do not merge it blindly.

The workflow also supports a repository test-trigger push to `.github/test-triggers/tricky-daily-live-cycle.json`. That push forces the runner, with an explicit `action` value of `cycle`, `description-only`, or `verify-only`; if the key is absent, it defaults to `description-only`. This is a deliberate test hook, not the normal schedule.

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
not repeated blindly. Completion requires the exact description and unchanged
ordered 60-track contents. It never replaces tracks. These changes remain in
a draft PR pending CI and live operational verification.

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
