# Authentication Management & Recovery

## Purpose

Make Spotify authentication a maintained SHIT capability rather than a one-time mobile setup task. SHIT should continuously know whether its Spotify credential is healthy, automatically perform safe refresh and token-rotation recovery, identify the exact class of failure, and guide the owner through fresh consent only when Spotify requires it.

This workstream is independent of the device used. Phone and desktop browsers are both supported clients for owner-consented reauthorization. GitHub remains the source of truth for code, operational state and the repository Actions secret; GitHub Actions and a narrowly scoped managed broker are the execution plane.

## User-facing target

SHIT should:
1. Check authentication health on a bounded schedule and before Spotify-dependent operations.
2. Refresh access tokens and securely persist any rotated refresh token automatically.
3. Classify outcomes as healthy, reauthorization required, transient provider/network failure, rate-limited, configuration failure, or secret-persistence failure.
4. Avoid repeated calls when a failure cannot be repaired automatically.
5. When fresh consent is required, present a trusted owner-only Spotify authorization flow from either phone or desktop.
6. Verify the resulting Spotify identity and required scopes, then independently confirm the new credential works in a second cloud run.
7. Resume normal Spotify workflows only after health is verified; authentication recovery itself must never mutate playlists.

## Verified baseline

- `SPOTIFY_REFRESH_TOKEN` in repository Actions Secrets is the cloud credential source of truth.
- The existing manager and `spotify-auth-health-check.yml` support refresh-token rotation persistence through a narrowly scoped GitHub App. The workflow now runs daily and on manual dispatch, reports redacted failure categories, and performs one bounded attempt per run. The workflow emits non-secret status markers into its Actions run logs. Scheduled checks inspect the prior run, pause on permanent blockers or interrupted attempts, and honor a stored Retry-After deadline; manual recovery attempts bypass the latch.
- The current saved refresh token was previously rejected with `invalid_grant`. That error cannot be repaired by retrying the same credential; fresh Spotify consent is required.
- A managed OAuth broker implementation exists on the reconciled feature work described in the roadmap. It is source code only until its PR is reviewed/merged and external provisioning and end-to-end checks are completed.
- The owner-authored GitHub issue command path can operate SHIT remotely, but it is not the authentication system's purpose. It remains a separate control plane for authorized SHIT operations.

## Architecture

### 1. Authentication Health Monitor

- Scheduled health verification with a conservative cadence.
- Read-only Spotify token refresh and `GET /v1/me` identity verification.
- Secure persistence of a replacement refresh token when Spotify rotates it.
- Structured, redacted status reporting with a last-success timestamp and failure category.
- No automatic retry loop for `invalid_grant`; respect Retry-After for 429 and bounded backoff for transient failures.
- Authentication preflight integration for Spotify-dependent workflows, designed to avoid duplicate refresh bursts and concurrency races.

### 2. Authorization Broker

A managed HTTPS service (Cloudflare Worker with SQLite-backed Durable Object state) provides owner-consented recovery:
- GitHub owner authentication and Spotify Authorization Code + PKCE.
- One-time state, session binding, replay protection, expiry and active-workflow checks.
- A dedicated repository-scoped GitHub App, separate from the existing manager secret-writer App, with only Actions: write and Secrets: write.
- Writes only the encrypted `SPOTIFY_REFRESH_TOKEN` Actions secret, then dispatches only the read-only auth-health workflow.
- No refresh token in browser JavaScript, HTML, URLs, chat, issues, artifacts, logs or Durable Object storage.
- No playlist API, unlock, preview approval or playlist write capability.

### 3. Recovery Coordinator

The coordinator connects diagnosis to safe next steps:
- Healthy / refreshable: continue and persist rotation.
- Reauthorization required: stop Spotify-dependent operations and request owner consent.
- Rate limited / provider unavailable: defer until eligible; do not mislabel as expired credentials.
- Configuration or secret-write failure: fail closed and report the exact non-secret setup issue.
- After consent: verify account identity, scopes, secret persistence and two independent read-only cloud checks before declaring recovery complete.

## Security boundaries

- GitHub identity and Spotify identity are distinct and both must be verified.
- Refresh tokens remain in GitHub Actions Secrets; the broker never stores them persistently.
- Never place credentials in issues, workflow inputs, query strings, commits, artifacts, ChatGPT messages, browser storage or logs.
- Do not broaden the existing manager GitHub App. The broker uses its own repository-scoped App.
- Never retry `invalid_grant` with the same token. Never retry 429 before Retry-After. Distinguish provider outages and network failures from authentication failures.
- Authentication checks and OAuth completion must never unlock, preview, stage, add, remove, reorder or otherwise modify playlists.
- Preserve every existing playlist ownership check, managed-playlist allowlist, explicit unlock, preview/confirmation, snapshot, audit, rollback and live read-back gate.
- Never claim the feature is deployed or the account is healthy without fresh workflow evidence.

## Current status

- Broker source and tests are implemented in the reconciled feature work; previous reported checks included 24 broker tests, dependency audit, Wrangler dry-run, 519 repository tests and full-history Gitleaks. Any subsequent code change requires fresh checks. The scheduled auth-health monitor, structured failure classifier and run-history recovery latch are implemented on `feature/authentication-management-recovery`; this workflow change has not yet passed CI.
- No Cloudflare Worker deployment, dedicated broker GitHub App installation, Spotify callback registration, OAuth completion or Actions secret replacement is confirmed.
- The saved credential remains blocked by the previously observed `invalid_grant`. Do not repeatedly dispatch Spotify commands until fresh consent and read-only verification succeed.

## Non-goals

- Giving ChatGPT direct access to Spotify refresh tokens or GitHub secret values.
- Making mobile the only supported client.
- Replacing GitHub Actions with an unrestricted always-on server.
- Allowing the broker to manage playlists or bypass SHIT safeguards.
- Treating 429, 5xx, network errors, missing configuration and invalid credentials as the same failure.

## Resume instructions

Read `ROADMAP.md` and `ACTIONS.md`. Inspect the auth-health workflow, broker source/tests, Spotify manager token rotation, all Spotify-dependent workflow entry points, GitHub App permissions, repository rules and Spotify redirect configuration. Update this roadmap and action log with every meaningful implementation or verification result. Never ask the user to paste a token into chat.
