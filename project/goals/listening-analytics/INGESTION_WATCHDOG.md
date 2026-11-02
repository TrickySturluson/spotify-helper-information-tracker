# Listening Ingestion Watchdog

## Purpose

Detect an unexpected cessation of listening-data ingestion early enough to prevent another multi-month history gap. This is an operational verification feature, not an enrichment scraper and not a claim that the user is currently listening.

## Sources are independent

1. **Last.fm scrobble ingestion (critical historical feed).** Inspect the latest actual scrobble timestamp in the canonical archive and the last successful sync/checkpoint timestamp from the Last.fm importer. A successful sync that returns zero new scrobbles is still a successful poll, but does not prove the account is actively scrobbling. Compare both poll freshness and newest-scrobble freshness.
2. **Spotify local playback tracker (optional measurement feed).** Inspect the newest valid `sampled_at` in `playback_data/segments.jsonl` and/or `assistant_data/playback/overview.json:last_sample`. A missing/old sample is a warning that local tracking is not running or has no captured playback; it is not evidence that Spotify account OAuth is disconnected. The tracker is explicitly local and coverage-limited.
3. **Spotify API/OAuth health (separate signal).** Where a scheduled authorized check already exists, record its last successful authenticated API check and classify 401/403, expired/revoked authorization, rate limiting, transient network/server errors, and success distinctly. Never make an unbounded new poll just to test connectivity.

## Detection model

- Persist per-source `last_successful_check_at`, `last_data_at`, `last_nonempty_data_at` (where meaningful), `consecutive_failures`, `last_error_class`, and `last_alert_at`.
- Use event timestamps and provider checkpoints, never Git file modification times.
- Make thresholds configurable. Initial defaults to validate against real workflow cadence: Last.fm importer check stale after 36 hours; newest scrobble stale after 72 hours; Spotify local tracker stale after 36 hours only if the user has opted into expected continuous tracking. These are warnings, not automatic reconnects.
- Escalate to critical when Last.fm sync has failed repeatedly or both sync checkpoint and archive scrobble timestamp exceed the threshold; show exact last-seen times and elapsed duration.
- Suppress false alarms during documented maintenance, workflow outages, or known provider incidents; keep a visible `unknown/not configured` state rather than green.
- Distinguish `healthy`, `warning_no_recent_scrobbles`, `warning_sync_stale`, `critical_sync_failure`, `tracker_not_running`, `provider_rate_limited`, `auth_action_required`, `provider_outage`, and `unknown`.

## User-facing alert

Report which source is stale, the last successful check, newest event timestamp, age, consecutive failures, and likely next action. If authorization failure is confirmed, say reconnect Last.fm and/or reauthorize Spotify as appropriate. Never ask for or log tokens. Include a link/instruction to the existing local OAuth flow only after verifying its actual command and scopes.

## Safety and implementation

- First implement a deterministic read-only CLI/report and unit tests with synthetic timestamps.
- Then wire it into the existing scheduled read-only health workflow and retain a compact JSON artifact plus concise workflow summary.
- Alert only on state transitions or a controlled reminder interval to avoid spam.
- No automatic OAuth flow, credential mutation, provider scraping, Library writes, or playlist writes.
- Validate thresholds against actual schedule frequency and historical archive/checkpoint data before enabling notifications.
- A fresh successful empty Last.fm poll must reset poll-failure state but must not reset the newest-scrobble age.
- A local Spotify playback log with no rows must remain `unknown/not configured` unless tracking has explicitly been enabled.
- Tests must cover clock boundaries, timezone handling, malformed rows, empty archives, fresh poll + stale scrobble, stale poll + fresh archive, 401/403, 429, transient 5xx/network errors, disabled local tracker, alert deduplication, and no-network/no-write report mode.

## Relationship to other project work

This watchdog is distinct from metadata freshness planning and provider retry queues. It verifies that listening ingestion is alive; it does not fetch song metadata. It complements Library health checks and should be documented under the listening-analytics goal.


## Listening-habit context and alert copy

The watchdog should attach a compact, source-labelled listening context snapshot to alerts so a reconnect gap can be understood against the user's actual patterns:

- **Current habits:** rolling 30-day and 90-day scrobble counts, top artists/tracks, active-day cadence, and most recent actual scrobble. Refresh from the canonical Last.fm archive after successful imports; do not use stale generated rankings without showing their generation time.
- **Deep reference:** all-time rankings and artist/track recurrence as a stable historical baseline. This is context, not an expectation that the user must listen at their all-time average every day.
- **Expected activity:** estimate a personal cadence from active days and rolling windows, but never assume silence alone proves disconnection. Distinguish user inactivity from a failed importer by checking the importer checkpoint and auth/API status.
- **Alert display:** show current vs usual cadence and the all-time reference only where useful; always identify each source and its data-through timestamp. A 30-day shift in taste must update the current profile without overwriting the all-time reference.
- **Humour:** when a verified connection/feed failure is detected, append a light status line such as: `Tricky appears to have died (or the connection did). The music stopped reporting in; please reconnect the affected service.` For uncertain inactivity use a softer variant: `Tricky may simply be taking a break. The tracker hasn't heard from you lately.` Do not use the death joke for normal inactivity, unconfigured tracking, or an unverified provider outage. Keep the actionable diagnosis prominent and the joke secondary.
- The joke is a user-requested notification flourish, not a health inference and not a substitute for clear reconnect instructions.
