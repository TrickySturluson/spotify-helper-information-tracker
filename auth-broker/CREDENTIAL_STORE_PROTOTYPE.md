# Broker-Owned Credential Store

Status: central credential ownership and first OIDC consumer are implemented on stacked draft PR #188; not deployed or production-verified.

## Purpose

Move the long-lived Spotify refresh token out of GitHub Actions and into a single encrypted, broker-controlled SQLite Durable Object. The Worker/credential object is the only component allowed to possess or refresh that token. Authorized workflows receive short-lived Spotify access tokens only.

## Implemented behavior

- AES-256-GCM encrypts the refresh token before Durable Object persistence, with a fresh 96-bit nonce for every write.
- Authenticated additional data binds ciphertext to key version, credential version, and Spotify account ID.
- A versioned keyring decrypts with retained historical keys and re-encrypts under the active key version during a successful refresh. Retain old keys until every record has moved to the new version.
- The owner-consented Spotify OAuth callback verifies `/v1/me` and passes the new refresh token directly to the fixed credential Durable Object's `/authorize` operation.
- `/authorize` initializes an empty store or recovers a blocked credential for the same verified Spotify account. It refuses to overwrite a ready/in-progress credential and rejects silent account replacement.
- The object durably reserves refresh operations before contacting Spotify. Concurrent operations are rejected.
- Spotify `/v1/me` identity is checked against the stored account ID before a rotated credential is committed.
- A verified short-lived access token is encrypted under the same versioned keyring and cached until its expiry. Concurrent authorized workflows wait for the in-flight refresh and reuse that cached token, avoiding competing rotations. Only the short-lived access token, expiry, account ID, and credential version are returned; the refresh token is never returned.
- Operation IDs cannot be replayed after a successful commit.
- A definite Spotify 429 releases the reservation, preserves the existing encrypted credential, persists a bounded cooldown, and propagates Retry-After. Ambiguous network/provider outcomes, invalid identity, corrupted ciphertext, and uncertain commits block refresh and require owner-consented recovery.

## First workflow integration

`.github/workflows/spotify-auth-health-check.yml` is the first OIDC canary on the feature branch. It requests the dedicated audience `shit-spotify-refresh`, is restricted to its exact main-branch workflow identity, obtains a broker access token, verifies Spotify `/v1/me`, and records the existing non-secret commit-status health latch. It does not read the old refresh-token secret or call Spotify's token endpoint directly.

Eight other workflows remain on the legacy refresh-token path. They must be migrated one at a time with their existing workflow, playlist, snapshot, audit, and rollback boundaries preserved.

## Outstanding production requirements

- Cloudflare Worker deployment and real SQLite Durable Object integration tests.
- Provisioning and controlled backup/rotation of `SPOTIFY_CREDENTIAL_ENCRYPTION_KEYS`; key loss can make the credential unrecoverable.
- Exact repository variable `SPOTIFY_REFRESH_WORKFLOW_REFS` configured for the initial canary and expanded only as each workflow is migrated.
- Live GitHub OIDC validation from the exact main-branch auth-health workflow.
- Real owner-consented initial OAuth handoff and same-account recovery validation.
- Migration and testing of the remaining eight workflows.
- Two independent post-deployment auth-health checks and a rollback/recovery exercise.
- Explicit owner approval before production cutover or removal of the legacy GitHub Actions refresh-token secret.

## Safety boundaries

- No refresh token or encryption key in GitHub Actions environment, output, artifact, issue, logs, repository files, or ChatGPT.
- No refresh-token fallback for a broker-enabled workflow.
- No automatic retry of a token after an ambiguous provider outcome.
- No credential overwrite when the store is ready or a refresh is in progress.
- No automatic Spotify account replacement.
- No playlist, Library, snapshot, unlock, preview, or audit operations in the broker.
- No production deployment or credential migration as part of pull-request CI.

## Related design

See `project/goals/mobile-cloud-operation/BROKER_CONTROLLED_REFRESH.md` and `WORKFLOW_MIGRATION_INVENTORY.md`.
