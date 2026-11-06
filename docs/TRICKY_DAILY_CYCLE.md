# Tricky Daily listening trends

Tricky Daily is a rotating discovery queue, not a fixed mood/theme playlist.
Each successful rotation replaces it with exactly 60 tracks. Selection first
tries to use 60 distinct primary artists. If that falls short, discovery retries
Spotify's next search-results page for alternate tracks before relaxing the
diversity rule. If 60 distinct artists still cannot be found, it searches progressively deeper
catalogue pages and expands the artist pool before allowing repeated artists.
The per-artist ceiling is relaxed progressively as a last resort; track URIs
remain unique and playlist removals remain blocked. The fallback is audited.
The cycle stages and pushes a full 60-track set rather than abandoning a rotation
solely because artist diversity is limited.
Its discovery engine keeps established taste and Last.fm similarity as the
foundation, uses recent listening momentum as a small soft nudge, and retains
room for exploration outside current patterns.

> Future work and prioritized implementation checklist: [Tricky Daily TODO](TRICKY_DAILY_TODO.md).
> The TODO is a planning backlog, not a statement that unchecked items are already implemented.

## Latest repository snapshot state — 2026-11-06

The latest confirmed live Daily snapshot was captured at `2026-11-06T17:41:02.779553+00:00` by snapshot workflow run [#42263830309](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42263830309): 29 accessible items were reported and fetched, all 29 URIs were unique, and the removal baseline contains 29 rows. The Daily blacklist contains 55 entries with zero whitelist entries. The reference catalog now reports the same 29 items, and the track/artist index has zero stale or missing Daily memberships. The generated-data audit and full 481-test suite passed on the refreshed state. The prior 37-item snapshot remains in history. The snapshot/catalog/index commit is `d24fb9acbc17a8acaff4e8e893a7681e91c8a5bd`. This was a Spotify GET-only read and repository publication; no playlist tracks or description were changed.

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
- The current `should_run_cycle()` checks the Eastern local hour for scheduled events; it does not inspect GitHub's exact `github.event.schedule` string to reject the stale DST counterpart.

**Pending DST improvement:** open, unmerged [PR #159](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/159) proposes separate 04:00/05:00 UTC cron entries, passes the exact scheduled cron string into the runner, and rejects a cron whose UTC offset does not match the current Eastern offset. Those stricter semantics are proposed, not current mainline behavior; do not document them as implemented until PR #159 is merged and verified.

The workflow also supports a repository test-trigger push to `.github/test-triggers/tricky-daily-live-cycle.json`. That push forces the runner, with an explicit `action` value of `cycle`, `description-only`, or `verify-only`; if the key is absent, it defaults to `description-only`. This is a deliberate test hook, not the normal schedule.

GitHub may delay scheduled events. The current gate allows a scheduled catch-up later on the same Eastern calendar date, while refusing the 23:00 hour. The persisted `last_cycle_date_eastern` guard makes repeated deliveries idempotent and is checked before Spotify is contacted, so a backup delivery after a successful cycle is a local no-op.

Manual dispatch remains midnight-gated unless its `force` input is explicitly set to `true`. The separate remote-verification workflow is safe-test-only: it compiles modules and runs tests without contacting Spotify or changing a playlist.

**Force/idempotency correction (source-checked 2026-11-06):** `should_run_cycle()` allows `--force` to bypass the clock-window gate, but `cycle_already_completed(config, cycle_date)` is called independently without a force override. Force bypasses the clock gate only. The same-Eastern-date completion guard therefore still blocks duplicate forced dispatches before Spotify client construction. A focused regression test covers this. The correction is implemented; remote CI is not yet green because the latest runs exposed stale documentation-contract assertions and a brittle source-count assertion. See [TRICKY_DAILY_TODO.md](TRICKY_DAILY_TODO.md) and the [Daily roadmap](../project/goals/tricky-daily/ROADMAP.md).


After Spotify accepts the playlist replacement, the runner immediately writes
a `replacement_accepted_pending_verification` state and publishes the
`cycled=true` Actions output. The workflow persists that state even if the
subsequent playlist read-back or feedback observation fails. A successful
read-back advances the state to `completed`. A pending-verification state is
evidence that Spotify accepted the write, not proof that the post-change
snapshot was verified; inspect the audit and recovery artifact before retrying.

### What automatic post-write verification actually proves

The candidate builder filters exact negative track keys/URIs and selects unique candidate URIs before publication. The normal cycle caller also validates exactly 60 recommendations, non-empty primary artists, Spotify track-URI shape and URI uniqueness before it saves a backup and calls the protected replacement helper. After the write, the automatic read-back confirms the new description, exactly 60 returned items and a valid primary artist on every item, then saves the resulting snapshot and marks the cycle completed.

**The automatic post-write check is narrower than the full P0 acceptance target.** It does not explicitly recheck duplicate URIs, recheck the blacklist against the returned snapshot, or compare the returned ordered URI list with the exact ordered candidate list. The separate `--verify-only` mode checks 60 items, duplicate URIs, blacklist membership and the expected description, but it also does not compare against a stored pre-write ordered staging payload. Therefore a completed cycle currently means the implemented checks passed; it must not be described as proving every P0 invariant. These remaining gaps are recorded in `docs/TRICKY_DAILY_TODO.md` and the Tricky Daily roadmap.

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
