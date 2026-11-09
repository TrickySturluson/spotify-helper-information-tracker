# Authentication Management & Recovery

## Purpose

Make Spotify authentication a maintained SHIT capability rather than a one-time mobile setup task. SHIT should continuously know whether its Spotify credential is healthy, automatically perform safe refresh and token-rotation recovery, identify the exact class of failure, and guide the owner through fresh consent only when Spotify requires it.

This workstream is independent of the device used. Phone and desktop browsers are both supported clients for owner-consented reauthorization. GitHub remains the source of truth for code and workflow definitions. The repository Actions secret is the legacy credential source on current `main`; the target architecture moves long-lived refresh-token custody into an encrypted SQLite Durable Object and gives workflows only short-lived access tokens through OIDC.

## Current status — 2026-11-09

The Spotify app uses Authorization Code with PKCE. For PKCE refreshes, Spotify requires `client_id` in the form body and does not require a client secret or HTTP Basic authentication; the broker must not provision or depend on a Spotify client secret. See [Spotify's refresh-token guide](https://developer.spotify.com/documentation/web-api/tutorials/refreshing-tokens).

- Base broker PR #185, diagnostic follow-ups #190 and #191 are merged. Production Worker `shit-auth-broker` version 14 receives 100% traffic. The base OAuth broker is live, but its Spotify callback has two recent redacted `broker.route_dispatch` failures on version 14; end-to-end authorization is not verified.
- Cloudflare metadata confirms the GitHub App client secret and private key are both `secret_text`. Version 14 has Durable Object migration v2 and only `OAUTH_STATE` / `SPOTIFY_REFRESH_LEASE`; it does not have the new `SPOTIFY_CREDENTIAL_STORE` binding or encryption keyring.
- PR #187 adds the encrypted credential-store prototype. Its broker tests and Wrangler dry-run pass on head `1c8e6b46c292525c3a13019325a270d91f97a84d` (run #42598447923); its security scan is pending (run #42598447639).
- PR #188 adds the OIDC-authorized refresh endpoint and migrates all nine current token consumers to short-lived broker access tokens. Its latest head `12ca9de8c4767277d96f0ec14cf6b55f215d4e27` passed broker security tests, Cloudflare SQLite Durable Object integration tests, broker-client tests, script documentation checks, dependency audit, Wrangler dry-run and full-history security scan (tests #42600292437; security #42600292392).
- PR #188 contains the encrypted credential store, OIDC refresh endpoint and all nine workflow migrations. It is being consolidated onto current `main`; keep it draft until the encryption keyring is provisioned and owner-controlled deployment is ready. PR #187 is the earlier credential-store prototype. The current production version is not the broker-owned credential architecture. Do not retry OAuth until the integrated version is deployed and verified.
- The previously saved credential was rejected with `invalid_grant`; fresh owner consent will be required after the integrated flow is ready. No token values are to be requested or exposed.
- All nine workflow consumers are migrated on the PR #188 feature branch; tests verify broker-only OIDC access and no direct legacy refresh-token secret references. Auth-health alone may force refresh after an early Spotify `/v1/me` 401; other workflows cannot bypass the shared cache or provider cooldown.
- No auth-health success, credential replacement, or playlist operation has been verified.

## User-facing target

SHIT should:
1. Check authentication health on a bounded schedule and before Spotify-dependent operations.
2. Refresh access tokens and securely persist any rotated refresh token automatically.
3. Classify outcomes as healthy, reauthorization required, transient provider/network failure, rate-limited, configuration failure, or secret-persistence failure.
4. Avoid repeated calls when a failure cannot be repaired automatically.
5. When fresh consent is required, present a trusted owner-only Spotify authorization flow from either phone or desktop; the failed health-check summary links directly to the broker when configured, otherwise to the deployment runbook.
6. Verify the resulting Spotify identity and required scopes, then independently confirm the new credential works in a second cloud run.
7. Resume normal Spotify workflows only after health is verified; authentication recovery itself must never mutate playlists.

## Verified baseline

- Current `main` still uses `SPOTIFY_REFRESH_TOKEN` in repository Actions Secrets as its legacy cloud credential source. The target broker-owned architecture in PRs #187/#188 moves the long-lived refresh token into encrypted Durable Object storage and removes direct refresh-secret reads from all nine workflows; this target is not yet merged/deployed.
- The existing manager and `spotify-auth-health-check.yml` support refresh-token rotation persistence through a narrowly scoped GitHub App. The workflow now runs daily and on manual dispatch, reports redacted failure categories, and performs one bounded attempt per run. The workflow persists non-secret health state in the `spotify-auth-health` GitHub commit status on a fixed anchor commit (`a4ac9def8be5b6e727b777e2660a7bb027a8e51b`), so ordinary code/data commits do not reset the latch. The workflow only runs on `main`. Scheduled checks pause on permanent blockers or interrupted attempts and honor Retry-After deadlines; status API/read/write failure is fail-closed. Manual recovery bypasses permanent blockers but still respects an active rate-limit cooldown; missing/invalid Retry-After uses a conservative 24-hour fallback.
- The current saved refresh token was previously rejected with `invalid_grant`. That error cannot be repaired by retrying the same credential; fresh Spotify consent is required.
- The base managed OAuth broker, its security tests and owner-only deployment workflow are merged in PR #185; diagnostic fixes #190/#191 are also merged. The base Worker is deployed as production version 14 at 100% traffic, but Spotify callback completion remains failing/unverified and the broker-owned credential-store migration is still in PRs #187/#188.
- Nine current GitHub Actions workflows consume `SPOTIFY_REFRESH_TOKEN`. Most use independent concurrency groups and `update.yml` has none; a cross-workflow refresh-token single-flight design is still required before broad preflight rollout.
- The owner-authored GitHub issue command path can operate SHIT remotely, but it is not the authentication system's purpose. It remains a separate control plane for authorized SHIT operations.

## Architecture

### 1. Authentication Health Monitor

- Scheduled health verification with a conservative cadence.
- Read-only Spotify token refresh and `GET /v1/me` identity verification.
- Secure persistence of a replacement refresh token in the encrypted broker Durable Object when Spotify rotates it; workflows receive only short-lived access tokens.
- Structured, redacted status reporting with a last-success timestamp and failure category.
- No automatic retry loop for `invalid_grant`; respect Retry-After for 429 and bounded backoff for transient failures.
- Authentication preflight integration for Spotify-dependent workflows, designed to avoid duplicate refresh bursts and concurrency races.

### 2. Authorization Broker

A managed HTTPS service (Cloudflare Worker with SQLite-backed Durable Object state) provides owner-consented recovery:
- GitHub owner authentication and Spotify Authorization Code + PKCE.
- One-time state, session binding, replay protection, expiry and active-workflow checks.
- A dedicated repository-scoped GitHub App, separate from the existing manager secret-writer App. The base broker still has a legacy Secrets: write path until cutover; the target broker requests only Actions: write for active-run inspection and auth-health dispatch.
- Stores owner-consented refresh credentials only as AES-GCM ciphertext in the broker Durable Object, then dispatches read-only auth-health. It does not write GitHub Actions secrets.
- No plaintext refresh token in browser JavaScript, HTML, URLs, chat, issues, artifacts, logs or Durable Object storage; ciphertext only in the broker Durable Object.
- No playlist API, unlock, preview approval or playlist write capability.

### 3. Recovery Coordinator

The coordinator connects diagnosis to safe next steps:
- Healthy / refreshable: continue and persist rotation.
- Reauthorization required: stop Spotify-dependent operations and request owner consent.
- Rate limited / provider unavailable: defer until eligible; do not mislabel as expired credentials.
- Configuration or credential-store failure: fail closed and report the exact non-secret setup issue.
- After consent: verify account identity/scopes, encrypted credential-store persistence and two independent read-only broker-backed cloud checks before declaring recovery complete.

## Security boundaries

- GitHub identity and Spotify identity are distinct and both must be verified.
- Current `main` still uses the legacy Actions secret until coordinated cutover. After cutover, the encrypted broker Durable Object is the sole long-lived refresh-token store; do not dual-write or silently fall back.
- Never place credentials in issues, workflow inputs, query strings, commits, artifacts, ChatGPT messages, browser storage or logs.
- Do not broaden the existing manager GitHub App. The broker uses its own repository-scoped App.
- Never retry `invalid_grant` with the same token. Never retry 429 before Retry-After. Distinguish provider outages and network failures from authentication failures.
- Authentication checks and OAuth completion must never unlock, preview, stage, add, remove, reorder or otherwise modify playlists.
- Preserve every existing playlist ownership check, managed-playlist allowlist, explicit unlock, preview/confirmation, snapshot, audit, rollback and live read-back gate.
- Never claim the feature is deployed or the account is healthy without fresh workflow evidence.

## Current status

- Broker source/tests/deployment workflow are under review in PR #185; broker tests, dependency audit and Wrangler dry-run passed in run #42540593852. The earlier authentication monitor and run-history-latch version passed the full 528-test repository suite in run #42540593870; the full-history Gitleaks scan passed with no leaks in run #42540593842. The commit-status latch is a later refinement and still needs fresh CI. These checks validate source contracts and build behavior, not live Spotify authentication. Any subsequent code change requires fresh checks.
- Cloudflare metadata now confirms the GitHub App client secret/private key are `secret_text` Worker Secrets. The active Worker version still lacks the broker-owned credential-store binding, encryption keyring required by the new refresh implementation. Never read secret values.
- The saved credential remains blocked by the previously observed `invalid_grant`. Do not repeatedly dispatch Spotify commands until fresh consent and read-only verification succeed.

## Non-goals

- Giving ChatGPT direct access to Spotify refresh tokens or GitHub secret values.
- Making mobile the only supported client.
- Replacing GitHub Actions with an unrestricted always-on server.
- Allowing the broker to manage playlists or bypass SHIT safeguards.
- Treating 429, 5xx, network errors, missing configuration and invalid credentials as the same failure.

## Resume instructions

Read `ROADMAP.md` and `ACTIONS.md`. Inspect the auth-health workflow, broker source/tests, Spotify manager token rotation, all Spotify-dependent workflow entry points, GitHub App permissions, repository rules and Spotify redirect configuration. Update this roadmap and action log with every meaningful implementation or verification result. Never ask the user to paste a token into chat.
