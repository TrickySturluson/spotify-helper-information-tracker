# Broker-Controlled Spotify Refresh and Credential Persistence

**Status:** Central encrypted credential store, owner-consented callback handoff, OIDC refresh endpoint, and first auth-health workflow consumer are implemented on stacked draft PRs #187/#188. They are not merged, deployed, or production-verified. Eight direct workflow consumers remain.  
**Parent:** Authentication Management & Recovery (PR #185).  
**Purpose:** Make the broker the sole owner of the rotating Spotify refresh token and the serialized refresh/persistence critical section.

## Why central ownership is required

The existing nine GitHub Actions consumers each received the rotating refresh token and could refresh independently. A lease alone cannot fence a later GitHub Secrets write: a workflow can lose a lease while a network request is in flight and still persist a stale token after a successor starts. The broker-owned credential store removes that race by keeping the long-lived token outside Actions and serializing refresh and commit inside one SQLite Durable Object.

## Target architecture

1. The owner completes GitHub identity verification and Spotify Authorization Code + PKCE consent in the broker.
2. The Worker verifies Spotify `/v1/me` and required scopes.
3. The Worker passes the refresh token directly to the fixed `SpotifyCredentialStore` Durable Object. AES-256-GCM ciphertext is stored with nonce, key version, credential version, account ID, and timestamps.
4. The Durable Object is the only component that decrypts and refreshes the long-lived credential.
5. GitHub Actions jobs authenticate with signed OIDC JWTs. The Worker validates signature/JWKS, issuer, audience, repository, immutable owner ID, main ref, allowed event, exact workflow identity, run identity, and time claims.
6. An authorized job receives only a short-lived Spotify access token and expiry. The refresh token is never returned.
7. A successful refresh verifies `/v1/me` against the stored Spotify account before atomically committing the rotated encrypted refresh credential and an encrypted short-lived access-token cache. Concurrent authorized jobs wait for the same refresh and reuse the cached access token.
8. Every Spotify workflow migrates to the broker. No workflow falls back to the legacy refresh-token secret or refreshes independently.
9. After every consumer and rollback path is verified, the legacy GitHub Actions refresh-token secret can be retired with explicit owner approval.

## Implemented source-branch behavior

- `POST /internal/spotify/refresh` accepts only a minimal operation ID and requires the dedicated OIDC audience `shit-spotify-refresh`.
- The Worker uses a fixed Durable Object identity (`spotify-primary`); caller-supplied account/owner claims are ignored.
- The `SpotifyCredentialStore` `/authorize` operation initializes an empty store or restores a blocked credential only for the same Spotify account. It refuses to overwrite a ready or in-progress record and refuses silent account changes.
- The refresh object reserves operations transactionally, rejects replayed operations, checks account identity, and commits rotated ciphertext only after successful verification. Concurrent callers wait for the active operation and reuse its encrypted access-token cache; a persistent Retry-After cooldown prevents refresh storms.
- Versioned encryption keys are supported. Successful refresh re-encrypts under the active key version; historical keys must remain configured until migration is complete.
- A definite provider HTTP 429 releases the reservation without changing the credential and propagates Retry-After. Ambiguous network/provider outcomes, identity mismatch, corrupted ciphertext, or uncertain commit block further refresh and require owner-consented recovery.
- `scripts/spotify/broker_access_token.py` requests GitHub OIDC with the dedicated audience and has no legacy fallback.
- The Spotify manager supports broker-only access-token mode and fails closed on expiry without reading the local legacy token file or refreshing directly.
- The OAuth callback now stores credentials in the encrypted Durable Object. The broker no longer writes `SPOTIFY_REFRESH_TOKEN` to GitHub Actions secrets.
- The auth-health workflow is the first OIDC canary in the feature branch. It retains the fixed commit-status latch, requests a broker token, verifies `/v1/me`, and performs no playlist or Library writes.

## Remaining direct consumers

The other eight workflows remain on the legacy refresh-token path and must be migrated individually:

1. `spotify-daily-live-preflight.yml`
2. `spotify-daily-midnight-cycle.yml`
3. `spotify-daily-feedback-observation.yml`
4. `tricky-daily-snapshot-refresh.yml`
5. `spotify-reference-library.yml`
6. `spotify-playlist-manager.yml`
7. `great-migration.yml` (each job separately)
8. `update.yml`

The repository inventory test must reject direct references to `SPOTIFY_REFRESH_TOKEN`, direct calls to Spotify's token endpoint, and legacy refresh-token persistence in active workflows. Refresh the inventory whenever workflows are added, renamed, split, or changed.

## Key and Durable Object operations

- The Worker secret `SPOTIFY_CREDENTIAL_ENCRYPTION_KEYS` contains a JSON key-version map of base64-encoded 32-byte AES keys. `SPOTIFY_CREDENTIAL_ACTIVE_KEY_VERSION` selects the active write key.
- Keep historical keys until every credential has been re-encrypted. A missing historical key fails closed. Define secure backup, restore, key-loss, and rotation procedures before production cutover.
- SQLite-backed Durable Object transactions protect reservation, commit, initialization, and same-account reauthorization.
- Spotify network calls happen outside a long-held storage transaction. A unique operation ID and record version protect the final commit from stale operations.
- Do not automatically reclaim an expired or ambiguous operation and retry the old refresh token.
- Bound provider calls, response sizes, and request sizes. Never log tokens, ciphertext, OIDC JWTs, authorization headers, or provider response bodies.

## Authorization and least privilege

- Exact workflow allowlist; no wildcards, forks, pull-request events, feature refs, or caller-supplied identity.
- Separate OIDC audience for broker refresh and any legacy lease-coordinator route.
- The broker GitHub App now needs only repository-scoped Actions: Write to inspect active workflow runs and dispatch the read-only auth-health workflow. It does not need Secrets: write because the callback no longer writes GitHub Actions secrets.
- The Worker encryption key remains a Cloudflare secret and is never exposed to workflows.
- Broker outage fails closed. Migrated workflows must not fall back to a legacy secret.
- Owner OAuth remains explicit; invalid_grant cannot be repaired without fresh owner consent.

## Migration and acceptance sequence

1. Finish source review and passing broker CI for the stacked PRs.
2. Configure the canonical Cloudflare Worker, exact callbacks, required public variables, and encrypted keyring secret.
3. Deploy only after owner approval; run the owner-consented initial OAuth flow and verify the expected Spotify account.
4. Validate real Cloudflare SQLite Durable Object transactions, restarts, concurrency, failed writes, interrupted operations, and same-account recovery.
5. Validate OIDC from the exact main-branch auth-health workflow and obtain two independent successful read-only health checks.
6. Migrate each of the eight remaining consumers. Preserve each workflow's existing playlist locks, preview/confirmation boundaries, snapshots, audits, state persistence, and rollback semantics.
7. Verify the repository-wide inventory contains no direct refresh-token consumers or token-endpoint callers.
8. Test broker outage, rate limiting, invalid_grant, identity mismatch, encryption-key rotation, key loss, and owner reauthorization.
9. Obtain explicit owner approval for production cutover and only then retire the legacy GitHub Actions refresh-token secret.

## Explicit non-goals

- No generic remote shell or arbitrary command execution endpoint.
- No playlist editing, Library writes, playlist unlocking, snapshots, or command generation from the auth broker.
- No token disclosure to ChatGPT, GitHub logs, artifacts, issues, or browser storage.
- No automatic Spotify consent or account replacement.
- No production deployment, production credential migration, or secret deletion without explicit approval.

## Current acceptance status

| Requirement | Status |
|---|---|
| Encrypted credential store | Implemented; Cloudflare integration and key provisioning pending |
| Owner-consented initial credential handoff | Wired in source; live validation pending |
| Same-account recovery | Implemented in store; live validation pending |
| OIDC refresh endpoint and client | Implemented; live OIDC validation pending |
| Auth-health OIDC canary | Migrated in feature branch; CI pending |
| Eight remaining workflow consumers | Not migrated |
| Backup/restore and key-loss recovery | Design pending |
| Production deployment and two independent health checks | Not performed |
| Legacy secret retirement | Blocked pending all consumers and explicit owner approval |
