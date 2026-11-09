# Broker-Owned Credential Store Prototype

Status: isolated draft prototype; not deployed or connected to production workflows.

## Purpose

This module explores moving the long-lived Spotify refresh token out of GitHub Actions secrets and into a broker-controlled Durable Object. The broker would be the only component allowed to decrypt and use that token. Workflows would receive short-lived access tokens only.

## Current behavior

- AES-256-GCM encrypts the refresh token before it is written to Durable Object storage.
- A fresh 96-bit nonce is generated for every encryption.
- Authenticated additional data binds ciphertext to the record version, explicit encryption key version, and Spotify account ID. Current prototype supports a versioned keyring. On a successful refresh, it decrypts with the record's retained key version and re-encrypts under the active key version before commit. Retain old keys until every credential record has moved to the new version; missing historical keys fail closed. Backup/restore and emergency key-loss recovery remain unresolved.
- The object reserves a refresh operation durably before calling Spotify.
- Concurrent operations are rejected while a refresh is in progress.
- The Spotify account identity is checked through `/v1/me` before a rotated credential is committed.
- The credential version increments only after identity verification and encrypted persistence.
- The long-lived refresh token is never included in the response.
- A committed operation ID cannot be replayed.
- Provider errors, timeouts, invalid identity, corrupted ciphertext, or ambiguous outcomes fail closed and require owner reauthorization rather than retrying a possibly invalidated refresh token.

## Important limitations

This is not a production implementation yet:

- The class and SQLite migration are declared in `wrangler.toml` on stacked draft PR #188, and an OIDC-gated Worker refresh route is present. Neither has been deployed or enabled; the encryption key and exact workflow allowlist are not configured.
- No encryption key has been provisioned; no production secrets or credentials were changed.
- The existing OAuth callback does not yet hand off an initial token to this store.
- GitHub Actions workflows still use the existing refresh-token secret path.
- The OIDC refresh route has unit-tested identity/audience gates, but no live GitHub OIDC request or Cloudflare Durable Object integration has been exercised.
- An interrupted operation intentionally remains blocked. Recovery and reauthorization UX still need implementation and tests.
- Multi-key rotation/re-encryption, backup/restore, disaster recovery, account replacement, and operational monitoring still need design and validation. The `keyVersion` field is authenticated metadata, not a completed rotation system.
- Unit tests use an in-memory storage adapter; they do not replace Cloudflare Durable Object integration tests.

## Safety requirements before integration

1. Authenticate every broker request using GitHub OIDC with exact repository owner ID, repository, workflow file, ref, event, run identity, audience, and time claims.
2. Keep the encryption key in Worker secret storage and never expose it to workflows.
3. Bind the store to a single expected Spotify account and verify identity on every refresh.
4. Use one serialized Durable Object per Spotify account and transactionally protect reservation, commit, and operation replay checks.
5. Never automatically reclaim an expired or ambiguous refresh operation and retry its old refresh token.
6. Return access tokens only to authenticated, allowlisted workflow callers, with no refresh token or credential-store metadata that reveals secrets.
7. Add Cloudflare integration tests for restart, concurrent requests, storage transaction semantics, timeout ambiguity, and failed writes.
8. Migrate all workflows away from direct refresh-token access before removing the old secret path.
9. Keep the existing recovery path until the replacement is tested end-to-end and an owner explicitly approves production cutover.

## Related design

See `project/goals/mobile-cloud-operation/BROKER_CONTROLLED_REFRESH.md` for the target architecture, migration sequence, and acceptance criteria.
