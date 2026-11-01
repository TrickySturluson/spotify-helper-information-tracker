# Tricky Daily midnight cycle

Tricky Daily is a special-purpose rotating discovery queue. It is not scored as a
permanent-membership playlist and is deliberately excluded from the general
playlist-fit calibration ledger.

## Schedule

The GitHub Actions workflow `.github/workflows/spotify-daily-midnight-cycle.yml`
runs at 04:00 and 05:00 UTC. A runtime gate using the IANA timezone
`America/New_York` allows only the run that falls in the midnight Eastern
window to proceed. This handles both EST (UTC-5) and EDT (UTC-4), including
daylight-saving transitions, without changing the workflow schedule twice a year.

GitHub scheduled workflows can start a little late. The script accepts the first
30 minutes after midnight Eastern. A per-local-date idempotency marker prevents
the second UTC cron invocation or a manual retry from cycling the playlist twice.
A manual workflow dispatch can use `force=true` for an intentional off-schedule
cycle.

## Rotation is not rejection

Tracks removed because the daily set refreshes are written to Daily's separate
feedback history with reason `curator_rotation`. This is neutral housekeeping,
not a dislike, blacklist event, or playlist-fit rejection. Tracks that remain in
the next set are recorded as another Daily exposure. Listening, Liked Songs
observations, and post-add scrobbles remain available to Daily's own discovery
feedback logic.

The general fit-calibration module rejects Tricky Daily predictions and feedback
events. This prevents routine rotation from contaminating whitelist/blacklist
learning for other playlists.

## Safety and recovery

Before editing, the runner verifies the exact playlist ID and name, authenticated
ownership, managed-playlist permission, and the existing explicit unlocked state.
It does not silently unlock a locked playlist. It requires at least 20 resolved
recommendations, validates unique Spotify track URIs, and saves a complete
pre-change snapshot before replacement.

The workflow uploads the backup as a 30-day artifact and records its run ID and
post-cycle snapshot in playlist-manager state. It also uses a concurrency group,
checks the Spotify API cooldown before requests, and stops on failed discovery or
insufficient recommendations without changing the playlist.

## Credentials

The workflow requires repository variable `SPOTIFY_CLIENT_ID` and secrets
`SPOTIFY_REFRESH_TOKEN` and `LASTFM_API_KEY`.

## Manual operation

Run locally from the repository root:

```bash
python compat/spotify_daily_cycle.py --force
```

The normal scheduled command omits `--force` and runs only during midnight
Eastern. The workflow's manual dispatch exposes the same explicit force option.
