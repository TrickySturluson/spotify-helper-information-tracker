# Cross-Workflow Refresh Token Single-Flight Design

**Status:** Initial Worker/Durable Object implementation added in PR #185 and its automated unit tests pass. It is not integrated into any Actions workflow or deployed; the downstream fencing limitation below still prevents treating the lease as sufficient protection.
**Scope:** Serialize only Spotify refresh-token exchange and rotated-secret persistence across all SHIT workflows.

## Problem

Nine Actions workflows currently read SPOTIFY_REFRESH_TOKEN. Their concurrency groups are independent, and update.yml has none. Spotify may rotate a refresh token during exchange. Two jobs can read the same old token, refresh concurrently, and race to persist different token generations. Per-workflow concurrency does not coordinate them.

A repository-wide Actions concurrency group is not acceptable: GitHub permits only one running and one pending run per group, newer pending runs can replace older pending runs, and long operations such as Great Migration could delay or displace time-sensitive Daily work.

The broker's current active-workflow check is advisory and has a check-then-act race. Its OAuth-state Durable Object does not serialize refreshes initiated by Actions jobs.

## Decision

Use a dedicated Cloudflare Durable Object as a short critical-section lease coordinator authenticated by GitHub Actions OIDC. Do not hold a lease for an entire workflow. Do not send Spotify credentials to the coordinator. Store only opaque lease metadata.

**Critical downstream-fencing limitation:** GitHub's Actions Secrets API does not expose a conditional write keyed by a fencing generation. A lease alone cannot guarantee that an expired workflow will not finish an already-started secret write after a successor acquires the lease. Therefore this coordinator must not be integrated as sufficient protection for token persistence. The next design step must place refresh and rotated-secret persistence behind one broker-controlled operation (or another downstream store that enforces fencing), with bounded provider/API timeouts and ownership checks. The current coordinator is a prototype, not a rollout-ready solution.

## Trust and request validation

1. Each eligible Actions job requests a short-lived GitHub OIDC token with a fixed audience such as shit-spotify-refresh-lock.
2. The Worker validates the JWT signature using GitHub's published JWKS and validates issuer, exact audience, expiry, not-before, and required repository identity.
3. Require repository to equal TrickySturluson/spotify-helper-information-tracker; pin and validate the immutable repository owner ID; require refs/heads/main for production refresh.
4. Validate workflow_ref and job_workflow_ref against a repository-maintained allowlist. Validate event_name against explicitly supported events. Reject pull-request and fork contexts. Never trust caller-supplied claims.
5. Require HTTPS, POST, JSON content type, bounded body size, and rate limits. Never log raw JWTs or request bodies.
6. Return generic errors. Never expose JWT validation detail or lease-owner information to unauthenticated callers.

## Lease protocol

- One Durable Object identity represents the single Spotify refresh-token credential.
- Acquire atomically checks and writes lease state in a storage transaction.
- Lease metadata: random opaque lease ID, hash of GitHub run/job identity, acquisition time, expiry, and monotonically increasing fencing generation.
- Initial TTL: 120 seconds; renew every 30 seconds while the refresh/persist critical section is active. Revisit TTL against real request and secret-persistence timeouts before rollout.
- Acquisition returns either lease token plus expiry/generation or bounded busy response with retry hint. No unbounded queue.
- Renewal and release succeed only for the current lease ID and generation. Stale owners cannot renew or release successor leases.
- Expiry recovers from runner crashes. Durable Object alarm removes expired metadata.
- All state transitions are serialized in Durable Object storage transactions.
- The object never stores access/refresh tokens, client secrets, GitHub App tokens, OAuth codes, or provider responses.
- Hold the lease only from immediately before refresh exchange through account verification and rotated-secret persistence. Release in unconditional cleanup.
- If acquire/renew/release cannot be verified, fail closed before Spotify refresh. If lease ownership is lost after refresh begins, do not persist a rotated token without proving current fencing ownership.
- Busy lock exits with a distinct deferred status; do not wait indefinitely inside a workflow.

## Why OIDC, not a static shared secret

A static Worker bearer secret would be copied to nine workflows and require independent rotation. OIDC provides short-lived signed workload identity. The Worker must validate the signature and enforce repository/workflow allowlists; decoding claims without signature verification is forbidden.

## Integration plan

1. Add a separate Durable Object class, binding, migration, and isolated tests. Keep OAuthStateStore separate.
2. Test valid identity and rejection of wrong issuer/audience, expired/not-yet-valid tokens, wrong repository/owner, PR/fork context, unapproved workflow, malformed JWT, unknown key ID, and JWKS cache/rotation failures.
3. Test simultaneous acquisition (exactly one succeeds), owner renewal/release, stale renewal/release, expiry, reacquisition with higher fencing generation, malformed input, storage failure, and alarm cleanup.
4. Test that no Spotify request occurs when acquisition fails, lease loss prevents secret persistence, and cleanup releases after success/failure/exception.
5. Roll out first to manual auth-health in report-only mode; uncertainty must still prevent Spotify calls.
6. Enforce locking for auth-health and observe multiple independent runs.
7. Migrate each of the nine token-consuming workflows to a shared reusable action/script. Keep lease only around refresh, verification, and persistence; preserve existing workflow concurrency and operational safeguards.
8. Remove advisory active-workflow checks only after all nine callers are verified to use the lock.
9. Add an inventory test that enumerates every workflow reading SPOTIFY_REFRESH_TOKEN and fails if any lacks OIDC permission and lock integration.
10. Only then introduce shared auth preflight to Spotify-dependent operations.

## Failure semantics

| Condition | Required behavior |
|---|---|
| OIDC invalid/untrusted | Reject; no lease |
| Lock service unavailable | Fail closed before Spotify refresh |
| Lease busy | Defer; do not refresh or mutate token state |
| Lease expires before refresh | Reacquire; no provider request occurred |
| Lease lost after refresh request | Do not persist without current fencing ownership; raise recovery incident |
| Spotify invalid_grant | Mark reauthorization required; release; never retry same token |
| Spotify 429 | Persist Retry-After state; release |
| Spotify 5xx/network | Preserve old secret; bounded retry/backoff after release |
| Secret persistence failure | Mark failure; never report healthy; no token in logs/artifacts |
| Runner crash | Lease expires; next run rechecks durable auth health |

## Operational safety

- No global Actions concurrency group.
- No credentials, provider responses, or queued workflow payloads in the Durable Object.
- The lock service grants, renews, and releases leases only; it does not call Spotify or GitHub APIs.
- No playlist, Library, issue-control, secret-write, or deployment capability is added.
- CI is not deployment evidence. Production rollout requires a Worker migration and verified end-to-end tests.
- Never declare this solved until every token consumer is inventoried and the missing-lock test passes.

## Initial implementation in PR #185\n\n- Added `auth-broker/src/refresh-lock.js` with RS256 signature verification against GitHub's OIDC JWKS, strict issuer/audience/time checks, repository and immutable owner-ID checks (`337022631`), `main` branch/event restrictions, and exact `workflow_ref` allowlisting.\n- Added the `SpotifyRefreshLease` SQLite Durable Object with transactional exclusive acquisition, 120-second expiry, renew/release ownership checks, monotonically increasing fencing generations, and expiry alarm cleanup.\n- Added Worker routes `/internal/refresh-lock/acquire`, `/renew`, and `/release`. The Worker derives lease ownership from verified workflow identity; caller-supplied owner claims are ignored. The Worker fails closed when its binding or exact workflow allowlist is absent.\n- Added a separate Durable Object binding/migration and unit tests for signed OIDC trust, invalid claims/signatures, exclusive acquisition, fencing, renewal and malformed requests.\n- **Not complete:** tests are still running/fixing; no workflow currently calls these endpoints; the owner allowlist is not configured; no production Worker deployment or live OIDC claim validation has occurred. The current nine-workflow inventory is not yet protected by the lease.\n\n## Open implementation decisions

- Confirm the immutable GitHub repository owner ID from a trusted GitHub API response and pin it as a non-secret Worker variable.
- Validate real OIDC claims from a harmless non-production test workflow before enforcing workflow allowlists.
- Confirm Durable Object migration syntax supported by the deployed Wrangler version.
- Decide whether reusable workflow or composite action best makes lock integration mandatory without duplicating untrusted scripts.
- Define safe recovery for the case where Spotify rotates a token but GitHub secret persistence is unavailable; no durable plaintext token buffer is permitted.

## Acceptance criteria

The lock is complete only when concurrent tests prove exactly one lease owner, fencing prevents stale persistence, crash expiry recovers, every refresh-token consumer is covered, no global workflow serialization is introduced, and production rollout is verified without exposing tokens or changing playlist behavior.