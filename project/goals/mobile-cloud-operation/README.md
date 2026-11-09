# Authentication Management & Recovery

## Purpose

Make Spotify authentication a maintained SHIT capability rather than a one-time mobile setup task. SHIT should continuously know whether its Spotify credential is healthy, automatically perform safe refresh and token-rotation recovery, identify the exact class of failure, and guide the owner through fresh consent only when Spotify requires it.

This workstream is independent of the device used. Phone and desktop browsers are both supported clients for owner-consented reauthorization. GitHub remains the source of truth for code and operational state; the Cloudflare broker's encrypted Durable Object is the intended source of truth for the long-lived Spotify refresh credential after coordinated cutover.

## User-facing target

SHIT should:
1. Check authentication health on a bounded schedule and before Spotify-dependent operations.
2. Obtain short-lived access tokens from one central broker; only the broker handles the long-lived refresh token and token rotation.
3. Classify outcomes as healthy, reauthorization required, transient provider/network failure, rate-limited, configuration failure, or uncertain provider outcome.
4. Avoid repeated calls when a failure cannot be repaired automatically.
5. When fresh consent is required, present a trusted owner-only Spotify authorization flow from either phone or desktop; the failed health-check summary links directly to the broker when configured, otherwise to the deployment runbook.
6. Verify the resulting Spotify identity and required scopes, then independently confirm the new credential works in a second cloud run.
7. Resume normal Spotify workflows only after health is verified; authentication recovery itself must never mutate playlists.

## Verified baseline

- Central encrypted credential storage, owner-consented initialization/recovery, OIDC refresh endpoint, encrypted access-token cache, and fail-closed broker-only manager mode are implemented on stacked draft PRs #185/#187/#188.
- All nine inventoried Spotify workflow consumers are migrated to the broker client on `feature/oidc-broker-refresh-endpoint`. Each Spotify-consuming job requests an OIDC-issued access token; concurrent jobs reuse one encrypted cached refresh result. The workflow persists non-secret health state in the `spotify-auth-health` GitHub commit status on a fixed anchor commit (`a4ac9def8be5b6e727b777e2660a7bb027a8e51b`), so ordinary code/data commits do not reset the latch. The workflow only runs on `main`. Scheduled checks pause on permanent blockers or interrupted attempts and honor Retry-After deadlines; status API/read/write failure is fail-closed. Manual recovery bypasses permanent blockers but still respects an active rate-limit cooldown; missing/invalid Retry-After uses a conservative 24-hour fallback.
- The current saved refresh token was previously rejected with `invalid_grant`. That error cannot be repaired by retrying the same credential; fresh Spotify consent is required.
- The broker implementation and workflow migrations remain in stacked draft PRs #185/#187/#188. The Worker remains undeployed until merge, controlled deployment and end-to-end checks are completed.
- The auth-health workflow alone may force refresh after an early Spotify `/v1/me` 401; other workflows cannot bypass the shared cache or provider cooldown.
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
- A dedicated repository-scoped GitHub App with Actions: Write only for active-run inspection and auth-health dispatch. The OAuth callback no longer writes repository secrets.
- Stores owner-consented refresh credentials only as AES-GCM ciphertext in the broker Durable Object, then dispatches the read-only auth-health workflow. It no longer writes GitHub Actions secrets.
- No refresh token in browser JavaScript, HTML, URLs, chat, issues, artifacts, logs or Durable Object storage.
- No playlist API, unlock, preview approval or playlist write capability.

### 3. Recovery Coordinator

The coordinator connects diagnosis to safe next steps:
- Healthy / refreshable: continue and persist rotation.
- Reauthorization required: stop Spotify-dependent operations and request owner consent.
- Rate limited / provider unavailable: defer until eligible; do not mislabel as expired credentials.
- Configuration or credential-store failure: fail closed and report the exact non-secret setup issue.
- After consent: verify account identity/scopes, initialize or recover the encrypted central credential store, and pass two independent read-only broker-backed cloud checks before declaring recovery complete.

## Security boundaries

- GitHub identity and Spotify identity are distinct and both must be verified.
- Only the central broker handles the long-lived refresh token. It is encrypted at rest and never returned to workflows. The legacy Actions secret is retained only until coordinated cutover.
- Never place credentials in issues, workflow inputs, query strings, commits, artifacts, ChatGPT messages, browser storage or logs.
- Do not broaden the existing manager GitHub App. The broker uses its own repository-scoped App.
- Never retry `invalid_grant` with the same token. Never retry 429 before Retry-After. Distinguish provider outages and network failures from authentication failures.
- Authentication checks and OAuth completion must never unlock, preview, stage, add, remove, reorder or otherwise modify playlists.
- Preserve every existing playlist ownership check, managed-playlist allowlist, explicit unlock, preview/confirmation, snapshot, audit, rollback and live read-back gate.
- Never claim the feature is deployed or the account is healthy without fresh workflow evidence.

## Current status

- Broker source/tests/deployment workflow are under review in PR #185; broker tests, dependency audit and Wrangler dry-run passed in run #42540593852. The earlier authentication monitor and run-history-latch version passed the full 528-test repository suite in run #42540593870; the full-history Gitleaks scan passed with no leaks in run #42540593842. The commit-status latch is a later refinement and still needs fresh CI. These checks validate source contracts and build behavior, not live Spotify authentication. Any subsequent code change requires fresh checks.
- The owner has reported completing the dedicated broker GitHub App setup, Worker secrets, Spotify callback, repository variables and Cloudflare deployment-token setup. These dashboard values are not independently readable through the repository connector. The Worker source is not confirmed deployed; OAuth completion and Actions secret replacement remain unverified.
- The saved credential remains blocked by the previously observed `invalid_grant`. Do not repeatedly dispatch Spotify commands until fresh consent and read-only verification succeed.

## Non-goals

- Giving ChatGPT direct access to Spotify refresh tokens or GitHub secret values.
- Making mobile the only supported client.
- Replacing GitHub Actions with an unrestricted always-on server.
- Allowing the broker to manage playlists or bypass SHIT safeguards.
- Treating 429, 5xx, network errors, missing configuration and invalid credentials as the same failure.

## Resume instructions

Read `ROADMAP.md` and `ACTIONS.md`. Inspect the auth-health workflow, broker source/tests, Spotify manager token rotation, all Spotify-dependent workflow entry points, GitHub App permissions, repository rules and Spotify redirect configuration. Update this roadmap and action log with every meaningful implementation or verification result. Never ask the user to paste a token into chat.


## 2026-11-09 implementation status

All nine Spotify workflow consumers are migrated to broker-only authentication on the stacked feature branch. The OAuth callback stores the refresh token only as AES-GCM ciphertext in the broker Durable Object, and concurrent jobs reuse an encrypted short-lived access-token cache. The deployed main branch and Worker remain unchanged; no Cloudflare key provisioning, live OAuth, or production cutover has occurred.
