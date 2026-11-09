# SHIT Authentication Management & Recovery — Deployment Runbook

## Purpose

Provide SHIT-wide Spotify authentication diagnosis and owner-consented recovery from any modern phone or desktop browser. The Cloudflare Worker brokers OAuth and writes only the repository's `SPOTIFY_REFRESH_TOKEN` Actions secret after Spotify identity verification. The scheduled/manual health workflow independently refreshes the token and verifies `/v1/me`.

Repository: `TrickySturluson/spotify-helper-information-tracker`

Worker: `shit-auth-broker`

Deployment workflow: [Deploy SHIT Auth Broker](https://github.com/TrickySturluson/spotify-helper-information-tracker/blob/main/.github/workflows/deploy-mobile-auth-broker.yml)

Health workflow: [SHIT — Spotify Auth Health Check](https://github.com/TrickySturluson/spotify-helper-information-tracker/blob/main/.github/workflows/spotify-auth-health-check.yml)

## Current state (maintain this section)

- Broker source, tests, and deployment workflow are in PR #185; they are not considered production-ready until merged and deployed.
- Existing Worker `https://shit-auth-broker.trickysturluson.workers.dev` exists. The PR's Worker source has not been confirmed deployed.
- Owner provisioning has been completed for the dedicated GitHub App, its Cloudflare secrets, Spotify callback, repository variables, and Cloudflare deployment token, based on the owner's setup confirmation. Secret values must never be fetched or printed to verify this.
- The latest confirmed PR validation before merge must be checked live; never copy old green results into a new status claim.
- No OAuth completion or end-to-end live recovery has been verified.
- The auth broker cannot unlock or modify playlists. Poker Test remains subject to the standard SHIT manager lock, staging, confirmation, snapshots, audit, and readback.

## Provisioned configuration

### Cloudflare Worker

- Worker name: `shit-auth-broker`
- Canonical origin: `https://shit-auth-broker.trickysturluson.workers.dev`
- Worker secrets (names only): `GITHUB_APP_CLIENT_SECRET`, `GITHUB_APP_PRIVATE_KEY`
- Deployment credential: repository Actions secret `CLOUDFLARE_API_TOKEN`; account ID is an Actions variable.
- Do not request or expose secret values. The Cloudflare API token currently has account-wide Worker edit scope; the GitHub deployment workflow targets only this Worker.

### Dedicated GitHub App

- App ID: `5674225`
- Client ID: `Iv23li5EfvZlgOPe5kAn`
- Callback: `https://shit-auth-broker.trickysturluson.workers.dev/auth/github/callback`
- Installation is intended to be limited to this repository.
- Required repository permissions: Actions write and Secrets write. The broker mints installation tokens scoped to this repository and requests only these permissions.
- Private key and OAuth client secret remain Cloudflare Worker secrets. Never paste them into chat or repository files.

### Spotify

- Uses SHIT's configured Spotify client ID and Authorization Code + PKCE.
- Exact callback: `https://shit-auth-broker.trickysturluson.workers.dev/spotify/callback`
- No Spotify client secret is required for this PKCE flow.
- Required scopes are defined in `auth-broker/src/index.js`; if scopes change, update the broker tests and this runbook together.

### GitHub Actions variables and secrets

Required variables:

- `CLOUDFLARE_ACCOUNT_ID`
- `BROKER_BASE_URL`
- `BROKER_GH_APP_CLIENT_ID`
- `BROKER_GH_APP_ID`
- `BROKER_GH_APP_REDIRECT_URI`
- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_REDIRECT_URI`

Required secret:

- `CLOUDFLARE_API_TOKEN`

The deployment workflow maps the `BROKER_GH_APP_*` repository variables to the Worker runtime names `GITHUB_APP_*`. Do not rename one side without updating the workflow and tests.

## Deployment and end-to-end verification

Deployment is an explicit production operation. Do not deploy from an unmerged feature branch.

1. Ensure PR #185 is reviewed, all required checks are green on its latest head, and it is merged to `main`.
2. Verify the deployment workflow is still owner-gated, targets `main`, uses the `auth-broker/` working directory, and validates all required settings before deployment.
3. Run **Deploy SHIT Auth Broker** manually from `main`, initiated by the repository owner.
4. Confirm the deployment succeeded and inspect the Worker health/landing page. Deployment success alone does not prove OAuth works.
5. Open the canonical Worker URL from a phone or desktop browser.
6. Complete GitHub owner authorization, then Spotify consent. The owner must personally approve consent; the broker cannot silently grant it.
7. Confirm the completion page identifies the intended Spotify account.
8. Confirm the broker changed only the `SPOTIFY_REFRESH_TOKEN` Actions secret and dispatched the read-only health workflow. Never retrieve or display the token value.
9. Confirm **SHIT — Spotify Auth Health Check** verifies the account through `/v1/me`, persists any rotated refresh token only after successful identity verification, and records a healthy result.
10. Run the health workflow once more manually and confirm it remains healthy.

A successful deployment is not a successful reauthorization. A successful OAuth callback is not sufficient until the independent read-only health check passes.

## Health workflow behavior

- Runs daily and by manual dispatch on `main`.
- Makes one bounded refresh attempt and verifies the resulting access token against `/v1/me`.
- Persists a rotated refresh token only after identity verification.
- Never prints token values or provider response bodies.
- Classifies invalid grant, rate limiting, provider/network failure, configuration, scope/identity, and secret-persistence failures.
- Uses a durable commit-status latch to pause scheduled retries on permanent blockers or interrupted attempts.
- Honors Spotify `Retry-After`; if absent or malformed, applies a conservative 24-hour fallback.
- Manual attempts may bypass permanent blockers, but not an active Retry-After deadline.
- A fresh Spotify owner-consent flow is required after `invalid_grant`.

## Known limitations and follow-up work

- Cross-workflow single-flight is not yet implemented. The broker checks active Spotify-related Actions runs before OAuth and before secret persistence, but a race can still occur if another Spotify workflow starts immediately after the check. Do not claim this is a global lock.
- The workflow concurrency group serializes health-check runs only; it does not serialize every Spotify-related workflow.
- Production OAuth and token-rotation behavior remain unverified until a controlled live deployment and owner-authorized test.
- The GitHub App and Cloudflare deployment credentials must remain least-privilege and periodically reviewed.

## After auth is healthy: Poker Test

Only after all authentication verification gates pass:

1. Read current manager state, lock state, audit, playlist contents, and latest snapshots.
2. Resolve the owner-authorized unlock command in issue #175 only through the SHIT manager.
3. Stage the exact 40-track Poker Test preview.
4. Review the full proposed diff and confirmation code.
5. Obtain explicit owner confirmation for that exact staged write.
6. Execute the manager's exact confirmation flow.
7. Verify before/after snapshots, audit/state persistence, and live Spotify readback.

Do not use the Spotify app connector or any direct API write to bypass SHIT. Do not claim the playlist was updated until live readback confirms it.

## Safety boundaries

- Never ask the owner to paste secrets, private keys, authorization codes, or tokens into chat.
- Never retrieve, print, or expose the refresh token.
- OAuth completion must not unlock or modify a playlist.
- Keep the playlist manager's existing narrow permissions and explicit confirmation flow unchanged.
- If any deployment or auth step fails, stop and diagnose that specific failure before retrying.
