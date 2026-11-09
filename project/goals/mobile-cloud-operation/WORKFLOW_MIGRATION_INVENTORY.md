# Spotify Credential Consumer Inventory

**Status:** Baseline inventory verified against `feature/broker-owned-spotify-credential-store` on 2026-11-09. All listed consumers still read `secrets.SPOTIFY_REFRESH_TOKEN` directly. None has been migrated to broker-issued access tokens.

This inventory is a migration control, not permission to change production workflows. Each workflow must be migrated and tested before the legacy refresh-token secret path is removed.

## Direct refresh-token consumers

| Workflow | Current role | Current credential behavior | Migration order |
|---|---|---|---|
| `.github/workflows/spotify-auth-health-check.yml` | Scheduled/manual auth health diagnosis | Reads refresh secret, calls Spotify token endpoint, verifies `/v1/me`, may write rotated secret | 1 — migrate first as broker canary |
| `.github/workflows/spotify-daily-live-preflight.yml` | Daily live preflight | Reads refresh secret for Spotify preflight | 2 — after broker canary |
| `.github/workflows/spotify-daily-midnight-cycle.yml` | Daily playlist cycle | Reads refresh secret and initializes manager token state | 3 |
| `.github/workflows/spotify-daily-feedback-observation.yml` | Daily feedback observation | Reads refresh secret and initializes manager token state; may persist rotation | 4 |
| `.github/workflows/tricky-daily-snapshot-refresh.yml` | Daily snapshot refresh | Reads refresh secret; manager token setup | 5 |
| `.github/workflows/spotify-reference-library.yml` | Spotify reference/library workflow | Reads refresh secret and initializes manager token state; may persist rotation | 6 |
| `.github/workflows/spotify-playlist-manager.yml` | Cloud playlist manager | Reads refresh secret for manager commands; may persist rotation | 7 |
| `.github/workflows/great-migration.yml` | Migration and verification jobs | Multiple jobs read refresh secret and may persist rotation | 8 — split and migrate each job independently |
| `.github/workflows/update.yml` | General update workflow | Reads refresh secret and initializes manager token state; may persist rotation | 9 |

## Explicitly checked adjacent workflows

These were inspected and did not expose the refresh-token secret in the searched workflow source at this baseline:

- `.github/workflows/playlist-manager-check.yml` — read-only checks; no Spotify credentials.
- `.github/workflows/playlist-fit-preview.yml` — no direct refresh-token reference found in workflow source at baseline.

A workflow with no direct secret reference may still invoke code that requires Spotify credentials indirectly; verify its full execution path before classifying it as independent.

## Migration rules

1. Migrate the auth-health workflow first and prove that an OIDC-authenticated broker call returns a short-lived access token only to the authorized job.
2. Migrate each remaining consumer without changing its playlist lock, preview/confirmation, snapshot, audit, state persistence, or rollback behavior.
3. For multi-job workflows, inventory every job and every Python/script invocation separately. Do not assume a single workflow-level change covers all credential consumers.
4. Add a repository-wide automated test that scans all active workflow files and rejects:
   - `secrets.SPOTIFY_REFRESH_TOKEN` references;
   - environment variables or generated token files populated from the long-lived secret;
   - direct calls to `https://accounts.spotify.com/api/token` from workflow-owned scripts/jobs;
   - legacy secret-writer paths that persist rotated Spotify refresh tokens.
5. Add an allowlist test for exact OIDC workflow identities. Do not use broad wildcards or permit feature branches, pull requests, forks, or caller-supplied workflow identity.
6. After each migration, run its read-only validation and inspect the exact job logs for credential redaction and absence of refresh-token material.
7. Do not remove the GitHub Actions refresh-token secret or legacy fallback until every consumer is migrated, all acceptance tests pass, and the owner explicitly approves production cutover.
8. Broker outage must fail closed. No migrated job may fall back to the legacy secret or independently refresh the token.

## Baseline verification

The baseline search inspected the workflow files listed above for `SPOTIFY_REFRESH_TOKEN`, `accounts.spotify.com/api/token`, and refresh-token setup/rotation references. The inventory must be refreshed whenever workflows are added, renamed, split, or changed.
