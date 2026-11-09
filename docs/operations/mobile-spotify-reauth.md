# Spotify Authorization Broker — Deployment Runbook

## Purpose

Deploy the SHIT OAuth broker so the owner can reauthorize Spotify from a phone or desktop browser without a local machine, then verify the new credential through the read-only Spotify Auth Health Check.

Repository: `TrickySturluson/spotify-helper-information-tracker`

Deployment workflow: [Deploy SHIT Mobile Auth Broker](https://github.com/TrickySturluson/spotify-helper-information-tracker/blob/main/.github/workflows/deploy-mobile-auth-broker.yml)

## Current verified state

- Broker source and tests are merged to `main`.
- The deployment workflow exists and is owner-gated.
- The Worker has **not** been deployed.
- No broker OAuth completion has been verified.
- No current Spotify refresh token should be assumed valid.
- Poker Test playlist `4Ccwf3QRr8HfSsK48pTuBI` remains blocked from modification until auth is healthy and the normal SHIT playlist-control sequence is followed.

## Owner-side provisioning checklist

Complete these steps in the relevant dashboards. Do not paste secrets, private keys, authorization codes, or refresh tokens into chat or repository files.

### 1. Cloudflare

- [ ] Create Worker `shit-mobile-auth-broker`.
- [ ] Enable its stable `workers.dev` hostname.
- [ ] Record the exact HTTPS origin, e.g. `https://shit-mobile-auth-broker.<your-subdomain>.workers.dev`.
- [ ] Record the Cloudflare Account ID.
- [ ] Create a Cloudflare API token scoped to the existing Worker with Workers Editor permission.
- [ ] Keep the API token available only for the GitHub Actions secret entry below.

### 2. Dedicated GitHub App

Create a new broker-specific GitHub App; do not broaden the existing SHIT manager App.

- [ ] Enable the user authorization flow.
- [ ] Set callback URL to `<BROKER_BASE_URL>/auth/github/callback`.
- [ ] Grant only repository permissions: Actions: Read and write; Secrets: Read and write (the deployment/runtime implementation needs write; do not grant unrelated permissions).
- [ ] Install it only on `TrickySturluson/spotify-helper-information-tracker`.
- [ ] Record App ID, Client ID, Client Secret, and generate a private key.
- [ ] Keep Client Secret and private key out of GitHub files and chat.

### 3. Spotify Developer Dashboard

- [ ] Use the same Spotify application/client ID already configured for SHIT.
- [ ] Add exact redirect URI `<BROKER_BASE_URL>/spotify/callback`.
- [ ] Do not add a Spotify client secret to this PKCE flow.

### 4. GitHub repository configuration

Add these Actions **variables** under repository Settings → Secrets and variables → Actions → Variables:

- [ ] `CLOUDFLARE_ACCOUNT_ID`
- [ ] `BROKER_BASE_URL` — HTTPS origin only; no path or trailing slash
- [ ] `GITHUB_APP_CLIENT_ID`
- [ ] `GITHUB_APP_ID`
- [ ] `GITHUB_APP_REDIRECT_URI` — exact origin plus `/auth/github/callback`
- [ ] `SPOTIFY_CLIENT_ID`
- [ ] `SPOTIFY_REDIRECT_URI` — exact origin plus `/spotify/callback`

Add this Actions **secret**:

- [ ] `CLOUDFLARE_API_TOKEN`

Set these **Worker secrets** in Cloudflare, not in GitHub variables:

- [ ] `GITHUB_APP_CLIENT_SECRET`
- [ ] `GITHUB_APP_PRIVATE_KEY`

### 5. Deploy and verify

- [ ] Open the repository Actions tab.
- [ ] Select **Deploy SHIT Mobile Auth Broker**.
- [ ] Choose Run workflow on `main`, initiated by the repository owner account.
- [ ] Confirm the deployment run succeeds.
- [ ] Open the canonical Worker URL in a phone or desktop browser.
- [ ] Complete GitHub owner authorization, then Spotify authorization.
- [ ] Confirm the completion page shows the intended Spotify account.
- [ ] Confirm only the `SPOTIFY_REFRESH_TOKEN` repository secret metadata changed; never retrieve or display its value.
- [ ] Confirm the automatically dispatched **SHIT — Spotify Auth Health Check** succeeds.
- [ ] Independently run the read-only health check again and confirm `/v1/me` returns the intended Spotify account.

A successful deployment alone is not successful reauthorization. A successful OAuth completion alone is not sufficient until the read-only health check passes.

## After auth is healthy: Poker Test

Only after all verification gates above pass:

1. Read current manager state, lock state, audit, playlist contents, and latest snapshots.
2. Resolve the owner-authorized unlock command in issue #175 only through the SHIT manager.
3. Stage the exact 40-track Poker Test preview.
4. Review the full proposed diff and confirmation code.
5. Obtain explicit owner confirmation for that exact staged write.
6. Execute the manager's exact confirmation flow.
7. Verify before/after snapshots, audit/state persistence, and live Spotify readback.

Do not use the Spotify app connector or any direct API write to bypass SHIT. Do not claim the playlist was updated until live readback confirms it.

## Safety boundaries

- Never ask the owner to paste secrets or tokens into chat.
- Never print, retrieve, or expose the refresh token.
- OAuth completion must not unlock or modify a playlist.
- Keep the manager App's existing narrow permissions unchanged.
- If any deployment or auth step fails, stop and diagnose that specific failure before retrying.
