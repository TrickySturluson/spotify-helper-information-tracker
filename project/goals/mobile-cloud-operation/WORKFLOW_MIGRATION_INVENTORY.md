# Spotify Credential Consumer Inventory

**Status:** Updated on `feature/oidc-broker-refresh-endpoint` on 2026-11-09. The auth-health workflow is migrated in this feature branch to broker-issued OIDC access tokens; the other eight consumers still read `secrets.SPOTIFY_REFRESH_TOKEN` directly. The broker canary is not merged, deployed, or production-verified.

This inventory is a migration control. The shared OIDC client, encrypted credential store, owner-consented initialization path, and manager broker-only mode exist on the stacked feature branch. The auth-health workflow is the first canary. Each remaining workflow must be migrated and tested before the legacy refresh-token secret path is removed.

## Main-branch direct refresh-token consumers

| Workflow | Current role | Current credential behavior | Migration order |
|---|---|---|---|
| `.github/workflows/spotify-auth-health-check.yml` | Scheduled/manual auth health diagnosis | Uses GitHub OIDC to obtain a short-lived broker access token, then verifies `/v1/me`; no refresh secret access | Migrated first as broker canary (feature branch only; CI/deployment verification pending) |
| `.github/workflows/spotify-daily-live-preflight.yml` | Daily live preflight | Reads refresh secret for Spotify preflight | 2 — after broker canary |
| `.github/workflows/spotify-daily-midnight-cycle.yml` | Daily playlist cycle | Reads refresh secret and initializes manager token state | 3 |
| `.github/workflows/spotify-daily-feedback-observation.yml` | Daily feedback observation | Reads refresh secret and initializes manager token state; may persist rotation | 4 |
| `.github/workflows/tricky-daily-snapshot-refresh.yml` | Daily snapshot refresh | Reads refresh secret; manager token setup | 5 |
| `.github/workflows/spotify-reference-library.yml` | Spotify reference/library workflow | Reads refresh secret and initializes manager token state; may persist rotation | 6 |
| `.github/workflows/spotify-playlist-manager.yml` | Cloud playlist manager | Reads refresh secret for manager commands; may persist rotation | 7 |
| `.github/workflows/great-migration.yml` | Migration and verification jobs | Multiple jobs read refresh secret and may persist rotation | 8 — split and migrate each job independently |
| `.github/workflows/update.yml` | General update workflow | Reads refresh secret and initializes manager token state; may persist rotation | 9 |

## Remaining direct refresh-token consumers\n\nThe eight workflows below remain on the legacy secret path and are the remaining migration backlog.\n\n## PR #188 candidate migration

- `.github/workflows/spotify-auth-health-check.yml` no longer references the refresh-token secret or calls Spotify's token endpoint on the PR branch. It requests an OIDC broker access token and independently verifies `/v1/me`.
- This is a code candidate only. Do not merge/enable it before the broker has an initialized credential and all other consumers are ready for the coordinated cutover.

## Explicitly checked adjacent workflows

These were inspected and did not expose the refresh-token secret in the searched workflow source at this baseline:

- `.github/workflows/playlist-manager-check.yml` — read-only checks; no Spotify credentials.
- `.github/workflows/playlist-fit-preview.yml` — no direct refresh-token reference found in workflow source at baseline.

A workflow with no direct secret reference may still invoke code that requires Spotify credentials indirectly; verify its full execution path before classifying it as independent.

## Migration rules

1. Complete and test the OAuth callback's initial credential handoff and same-account reauthorization against the encrypted store before any workflow requests a broker token.
2. Because Spotify refresh-token rotation is shared, do not run the broker refresh canary while legacy consumers remain active: a broker rotation can invalidate the token still held by legacy workflows. Stage all nine migrations, then perform a coordinated cutover by pausing legacy schedules/in-flight jobs, initializing the broker store, and enabling the broker-backed workflows together.
3. Migrate each consumer without changing its playlist lock, preview/confirmation, snapshot, audit, state persistence, or rollback behavior.
4. For multi-job workflows, inventory every job and every Python/script invocation separately. Do not assume a single workflow-level change covers all credential consumers.
5. Add a repository-wide automated test that scans all active workflow files and rejects:
   - `secrets.SPOTIFY_REFRESH_TOKEN` references;
   - environment variables or generated token files populated from the long-lived secret;
   - direct calls to `https://accounts.spotify.com/api/token` from workflow-owned scripts/jobs;
   - legacy secret-writer paths that persist rotated Spotify refresh tokens.
5. Add an allowlist test for exact OIDC workflow identities. Do not use broad wildcards or permit feature branches, pull requests, forks, or caller-supplied workflow identity.
6. After each migration, run its read-only validation and inspect the exact job logs for credential redaction and absence of refresh-token material.
7. Do not remove the GitHub Actions refresh-token secret or legacy fallback until every consumer is migrated, all acceptance tests pass, and the owner explicitly approves production cutover.
8. Broker outage must fail closed. No migrated job may fall back to the legacy secret or independently refresh the token.

## Baseline verification

The updated search inspected all active workflow YAML files for `SPOTIFY_REFRESH_TOKEN`, `accounts.spotify.com/api/token`, and refresh-token setup/rotation references. The auth-health workflow no longer contains a direct secret or token-endpoint path. Eight consumers remain. Refresh this inventory whenever workflows are added, renamed, split, or changed.
