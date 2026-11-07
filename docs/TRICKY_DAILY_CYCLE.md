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

## Latest repository snapshot state — 2026-11-07 UTC / 2026-11-06 Eastern

The live Tricky Daily cycle completed in workflow [#42316296314](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42316296314): exactly 60 tracks were published, with 26 previous tracks rotated out neutrally. The committed production stage and recovery backup preceded the Spotify write. The cycle's post-write read-back verified exact staged order, 60 unique valid URIs, zero blacklist hits, and description `Today's detour starts here.`.

The follow-up read-only verification [#42316824364](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42316824364) independently confirmed 60 unique tracks, zero blacklist hits, and the accepted description. The current snapshot workflow [#42316906860](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42316906860) then refreshed the Daily-only saved snapshot at `2026-11-07T00:13:46.604200+00:00`: 60 accessible items, 60 unique URIs, zero new manual removals, 58 blacklisted entries, and 3 removal-feedback events reconciled. The Daily reference catalog and removal baseline also contain 60 items. Snapshot/catalog/baseline commit: `bae0cb6c435c6c12672b97bde88138ddbd9be0fe`.

The current playback-tracker status remains unknown because `playback_data/segments.jsonl` is absent. Last.fm and liked-song observations are available; do not infer zero plays from missing playback coverage. Feedback observation run #42318532288 checked 123 Daily feedback rows using percent-encoded batches of at most 40 and recorded current liked status for all 60 live Daily tracks (all 60 were unliked at observation time). The earlier live cycle's `liked_at_add` baseline is still unknown because its pre-fix 50-URI request returned HTTP 400; do not backfill that historical baseline from the later observation. Future cycles now use the corrected 40-URI helper.

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

`.github/workflows/spotify-daily-midnight-cycle.yml` currently declares two cron expressions: `0 4,5 * * *` and `15 4,5 * * *`. This produces scheduled deliveries at both 04:00 and 05:00 UTC, plus a 15-minute recovery delivery for each. It is **not** yet a strict cron-to-DST-offset match.

- During Eastern Standard Time, 04:00/04:15 UTC are 23:00/23:15 Eastern on the preceding date; the current script gate skips scheduled events when the local Eastern hour is 23. The 05:00/05:15 UTC deliveries are 00:00/00:15 Eastern and can run.
- During Eastern Daylight Time, 04:00/04:15 UTC are 00:00/00:15 Eastern. The 05:00/05:15 UTC deliveries are 01:00/01:15 Eastern; the current gate permits these same-date catch-up/duplicate deliveries. The persisted `last_cycle_date_eastern` guard makes later deliveries local no-ops after a successful cycle.
- The current `should_run_cycle()` checks the Eastern local hour for scheduled events; it does not inspect GitHub's exact `github.event.schedule` string to reject the stale DST counterpart. Scheduled runs #42212368912 and #42214834581 were delayed into the morning and failed on HTTP 429 before cooldown persistence was fixed. PR #168 now commits the cooldown on failed cycles. The manual live cycle #42316296314 succeeded after cooldown expiry, but the next scheduled delivery after this fix remains unverified.

**Pending DST improvement:** open, unmerged [PR #159](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/159) proposes separate 04:00/05:00 UTC cron entries, passes the exact scheduled cron string into the runner, and rejects a cron whose UTC offset does not match the current Eastern offset. Those stricter semantics are proposed, not current mainline behavior; do not document them as implemented until PR #159 is merged and verified.

The workflow also supports a repository test-trigger push to `.github/test-triggers/tricky-daily-live-cycle.json`. That push forces the runner, with an explicit `action` value of `cycle`, `description-only`, or `verify-only`; if the key is absent, it defaults to `description-only`. This is a deliberate test hook, not the normal schedule.

GitHub may delay scheduled events. The current gate allows a scheduled catch-up later on the same Eastern calendar date, while refusing the 23:00 hour. The persisted `last_cycle_date_eastern` guard makes repeated deliveries idempotent and is checked before Spotify is contacted, so a backup delivery after a successful cycle is a local no-op.

Manual dispatch remains midnight-gated unless its `force` input is explicitly set to `true`. The separate remote-verification workflow is safe-test-only: it compiles modules and runs tests without contacting Spotify or changing a playlist.

**Force/idempotency correction (CI-verified 2026-11-06):** `should_run_cycle()` allows `--force` to bypass the clock-window gate, but `cycle_already_completed(config, cycle_date)` is called independently without a force override. Force bypasses the clock gate only. Duplicate forced dispatches are blocked before Spotify client construction. Full safe CI run #42268351897 passed 500 tests. See [TRICKY_DAILY_TODO.md](TRICKY_DAILY_TODO.md) and the [Daily roadmap](../project/goals/tricky-daily/ROADMAP.md).


After Spotify accepts the playlist replacement, the runner immediately writes
a `replacement_accepted_pending_verification` state and publishes the
`cycled=true` Actions output. The workflow persists that state even if the
subsequent playlist read-back or feedback observation fails. A successful
read-back advances the state to `completed`. A pending-verification state is
evidence that Spotify accepted the write, not proof that the post-change
snapshot was verified; inspect the audit and recovery artifact before retrying.

### What automatic post-write verification actually proves

The candidate builder filters exact negative track keys/URIs and selects unique candidate URIs before publication. The normal cycle caller also validates exactly 60 recommendations, non-empty primary artists, Spotify track-URI shape and URI uniqueness before it saves a backup and calls the protected replacement helper. After the write, the automatic read-back confirms the new description, exactly 60 returned items and a valid primary artist on every item, then saves the resulting snapshot and marks the cycle completed.

**Automatic post-write verification now enforces the staged publication contract.** The returned playlist must have complete pagination, exactly 60 entries, exact ordered URI equality with the committed/hash-verified stage, unique valid track URIs, valid primary artists, and no current blacklist hits. A mismatch leaves the cycle pending verification and must not be retried blindly. This was exercised live in workflow #42316296314: the exact staged order, 60 unique valid URIs, primary artists, blacklist exclusion, and description read-back all passed.

## Rotating description

Every successful full cycle also updates the short editorial description using
a deterministic daily rotation of concise lines. It is separate from the
metadata-driven description generator: Tricky Daily has an explicit user-
approved editorial rotation, while the generic generator continues to protect
non-empty manual descriptions on other playlists.

The description PUT is followed by a fresh playlist GET. The cycle is only
marked fully completed when Spotify returns the exact new description. The
accepted description and its verification status are persisted independently
from the track-cycle date guard. A description-only mode is available for a
one-shot live verification; it updates and reads back the description without
replacing tracks.

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
