# Broker-Controlled Spotify Refresh and Credential Persistence

**Status:** Architecture proposal; not implemented or deployed.
**Parent:** Authentication Management & Recovery (PR #185).
**Purpose:** Eliminate cross-workflow refresh-token races by making the broker the sole owner of the rotating Spotify refresh token and the refresh/persistence critical section.

## Why a lease is insufficient

The OIDC Durable Object lease prototype serializes lease acquisition, but the nine existing GitHub Actions workflows still possess a GitHub Secrets API write path. GitHub's Actions Secrets API does not support compare-and-swap or conditional writes tied to a fencing generation. A workflow can lose its lease while a network request is in flight and still finish a secret write after a successor begins. Do not treat a lease as a correctness guarantee for downstream secret persistence.

## Recommended end state

1. The broker becomes the only component allowed to possess and refresh the long-lived Spotify refresh token.
2. The refresh token is stored as authenticated ciphertext in a dedicated SQLite Durable Object. A Worker secret supplies a high-entropy encryption key; plaintext refresh tokens are never stored in Durable Object storage, logs, GitHub Actions outputs, or repository files.
3. A single broker-controlled operation performs the Spotify refresh exchange, validates the resulting access token with `GET /v1/me`, then atomically replaces the encrypted refresh-token record. The old record remains intact if exchange, identity verification, encryption, or the durable write fails.
4. Authorized GitHub Actions jobs authenticate to the broker with short-lived GitHub OIDC tokens. The broker validates signature/JWKS, issuer, audience, exact repository and immutable owner ID, main ref, event, workflow identity, run identity, and allowlist.
5. The broker returns only the short-lived Spotify access token and expiry needed by that authorized job. It never returns the refresh token. The access token must not be written to Actions logs, artifacts, caches, or persistent outputs.
6. All nine existing workflows migrate from reading `SPOTIFY_REFRESH_TOKEN` and refreshing independently to requesting a broker-issued access token. The inventory test must prove no workflow reads or writes the long-lived refresh token directly.
7. OAuth reauthorization writes the newly issued refresh token into the same encrypted credential store only after GitHub owner authentication, Spotify owner identity verification, and required scope checks pass.
8. Once every consumer is migrated and verified, remove the GitHub Actions refresh-token secret and the old secret-write code path. Keep an audited, owner-consented recovery flow.

## Durable storage and cryptography requirements

- Use a dedicated `SpotifyCredentialStore` Durable Object, not the lease coordinator's metadata object.
- Store versioned ciphertext, 96-bit random AES-GCM nonce, key version, and update timestamp. Bind repository/credential purpose and record version as authenticated additional data.
- Use Web Crypto AES-GCM with a key imported from a Worker secret; never hardcode or commit the key. Define a key-rotation procedure before production.
- Ensure every write is transactional and version checked inside the same Durable Object. A single object serializes refresh operations and atomically commits the next ciphertext version.
- Keep Spotify network calls outside a long-held storage transaction. Use an explicit refresh-in-progress record with unique operation ID, short expiry, and recovery rules; commit only if the operation still owns the current record version. Prevent an expired operation from committing after a successor.
- Bound provider calls with timeouts. Treat ambiguous network outcomes conservatively: do not overwrite a known-good token unless the response and identity verification are complete.
- Never log tokens, ciphertext, OIDC JWTs, authorization headers, or provider response bodies. Return generic errors and correlation IDs only.

## Required authorization and abuse controls

- Separate audiences for broker refresh access and lease-coordinator operations.
- Exact allowlist of the nine production workflow identities; no wildcard workflow names, PR/fork contexts, feature refs, or caller-supplied owner identities.
- Rate limits by verified workflow/run identity, bounded request bodies, POST-only routes, HTTPS canonical origin, no-store responses, and strict content type.
- A job receives an access token only after its OIDC identity and workflow authorization are verified. Access token lifetime is dictated by Spotify; never extend it or persist it.
- Broker endpoint failure must fail closed. Workflows must not fall back to an old secret or an independent refresh path after broker failure, because that recreates the race.

## Migration sequence

1. Finish tests/security review of the OIDC coordinator prototype; retain it as a non-production experiment unless it proves useful for other coordination.
2. Implement and test the encrypted credential Durable Object, key-version handling, operation fencing, and failure recovery in isolation.
3. Extend the existing OAuth callback to populate the encrypted store safely while preserving current behavior until owner-reviewed cutover.
4. Implement OIDC-authorized broker refresh endpoint and tests for concurrent callers, token rotation, identity mismatch, failed verification, ambiguous provider outcomes, stale operation commits, and storage failures.
5. Build a shared GitHub Action/client for workflows; migrate one low-risk read-only workflow first, then each remaining workflow.
6. Add a repository-wide inventory test that fails if any production workflow references the long-lived refresh-token secret or directly calls Spotify's token endpoint.
7. Verify all nine workflows against the broker in non-production; then request explicit owner approval for production cutover and secret removal.
8. Only after cutover, remove the GitHub secret refresh-token write path and mark the broker as the sole credential authority.

## Explicit non-goals

- No generic remote shell or arbitrary command execution endpoint.
- No Spotify playlist editing or library writes from the auth broker.
- No token disclosure to ChatGPT or workflow logs.
- No automatic OAuth consent; invalidated/revoked refresh tokens still require the owner's consent through Spotify.
- No production deployment, production secret migration, or deletion of the existing GitHub secret without explicit approval.

## Acceptance criteria

- The broker is the only refresh-token holder and refresher.
- At most one successful refresh operation can commit a newer token version; stale operations cannot commit.
- A successful response returns a valid access token for the expected Spotify owner and never the refresh token.
- All nine workflows use the broker, and a static inventory test prevents regressions.
- OIDC trust, key rotation, concurrency, crash recovery, rate limiting, error redaction, and failure behavior have automated tests.
- Recovery and reauthorization are documented and owner-consented.
- Production cutover is reviewed, approved, and auditable.
