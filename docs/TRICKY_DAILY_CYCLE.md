# Tricky Daily listening trends

Tricky Daily is a rotating discovery queue, not a fixed mood/theme playlist.
Each successful rotation replaces it with exactly 60 tracks. Selection first
tries to use 60 distinct primary artists. If that falls short, discovery retries
Spotify's next search-results page for alternate tracks before relaxing the
diversity rule. Only after that retry may a primary artist appear twice, and
never more than twice. This fallback is audited. If 60 tracks still cannot be
resolved, the cycle fails safely before the playlist is changed rather than
publishing a short list or exceeding the two-track artist ceiling.
Its discovery engine keeps established taste and Last.fm similarity as the
foundation, uses recent listening momentum as a small soft nudge, and retains
room for exploration outside current patterns.

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

`.github/workflows/spotify-daily-midnight-cycle.yml` runs at the EST/EDT
midnight UTC offsets and has a second delivery 15 minutes later. In standard
time, the 04:00/04:15 UTC deliveries are 23:00/23:15 Eastern on the prior date
and are deliberately skipped; 05:00/05:15 UTC are midnight/recovery deliveries.
During daylight time, 04:00/04:15 UTC are midnight/recovery deliveries and the
05:00/05:15 UTC entries are harmless duplicate deliveries.

GitHub may delay a scheduled event. The cycle gate therefore permits a
scheduled catch-up later on the same Eastern calendar date, while refusing
the 23:00 hour. The persisted `last_cycle_date_eastern` guard makes repeated
deliveries idempotent and is checked before Spotify is contacted, so a backup
delivery after a successful cycle is a local no-op.

After Spotify accepts the playlist replacement, the runner immediately writes
a `replacement_accepted_pending_verification` state and publishes the
`cycled=true` Actions output. The workflow persists that state even if the
subsequent playlist read-back or feedback observation fails. A successful
read-back advances the state to `completed`. A pending-verification state is
evidence that Spotify accepted the write, not proof that the post-change
snapshot was verified; inspect the audit and recovery artifact before retrying.

Manual dispatch remains midnight-gated unless its `force` input is explicitly
set to `true`. The separate remote-verification workflow is safe-test-only:
it compiles modules and runs tests without contacting Spotify or changing a
playlist.


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
dedicated test trigger and every six hours. It refreshes the OAuth access token
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
