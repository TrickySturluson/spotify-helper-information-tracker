# SHIT Authentication Management & Recovery Broker

The Cloudflare Worker is SHIT's central, owner-consented Spotify authentication authority. It supports phone and desktop browsers equally and has no dependency on a local PC or Codespace. It is an authentication service only: it never unlocks, edits, snapshots, or otherwise operates Spotify playlists.

## Central architecture

The intended production path is:

1. The owner completes GitHub identity verification and Spotify PKCE consent in the broker's browser flow.
2. The Worker verifies the Spotify account through `/v1/me`.
3. The Worker passes the refresh token directly to the fixed `SpotifyCredentialStore` Durable Object. The object encrypts it with AES-256-GCM and stores only ciphertext plus account/version metadata.
4. Initial authorization initializes the store. A later owner-consented authorization can recover a blocked credential only for the same Spotify account. A ready or in-progress credential cannot be overwritten, and changing Spotify accounts requires separate owner review.
5. The auth-health workflow obtains a short-lived access token using GitHub Actions OIDC. The broker verifies the signed token, exact repository owner ID, repository, main ref, allowed event, audience, workflow file, run identity, and time claims.
6. The Durable Object serializes refresh, verifies the account identity after refresh, commits rotated credentials only after verification, and returns only the short-lived access token.
7. The health workflow independently calls Spotify `/v1/me` and persists a non-secret health status. It never receives or stores the refresh token.

The credential store is keyed to one fixed Durable Object identity (`spotify-primary`); caller-supplied account IDs are not accepted on the refresh route. A verified short-lived access token is also encrypted in the object until expiry so multiple jobs can reuse one refresh result without racing Spotify's rotating refresh token. Concurrent callers wait for the in-flight operation and receive the cached token; a durable Retry-After cooldown prevents repeated requests after a 429. The refresh-token secret path is removed from the broker callback. There is no automatic fallback to GitHub Actions secrets or local token files.

## Current implementation and rollout boundary

The first broker consumer is `.github/workflows/spotify-auth-health-check.yml`. Its feature-branch implementation requests OIDC with audience `shit-spotify-refresh`, calls the central broker, verifies `/v1/me`, and retains the durable commit-status latch and Retry-After behavior.

All nine inventoried Spotify workflow consumers have now been migrated to the broker client on the stacked feature branch. Each job obtains its own OIDC token; the encrypted access-token cache lets concurrent jobs share one serialized refresh result. The existing playlist locks, snapshots, audits, rollback behavior, and side effects are preserved. The deployed main branch still uses the legacy secret until the stacked PRs are merged and the broker is deployed; do not remove that secret before live end-to-end verification and explicit owner approval.

The central callback, credential-store initialization/recovery, and auth-health OIDC canary are implemented on the stacked feature branch PRs #187/#188. They are not merged or deployed. The Cloudflare encryption key and exact OIDC workflow allowlist are not yet provisioned. Do not claim production centralization until deployment and end-to-end verification pass.

## Durable Object bindings and configuration

The Worker uses SQLite-backed Durable Objects:

- `OAUTH_STATE`: short-lived GitHub/Spotify PKCE state, sessions, and one-time completion summaries.
- `SPOTIFY_REFRESH_LEASE`: existing cross-workflow refresh lease prototype; retain until its consumers are audited and removed.
- `SPOTIFY_CREDENTIAL_STORE`: encrypted long-lived Spotify credential, refresh reservation, rotation, and recovery.

Non-secret GitHub repository Actions variables injected by the deployment workflow:

- `CLOUDFLARE_ACCOUNT_ID`
- `BROKER_BASE_URL` — canonical HTTPS Worker origin
- `BROKER_GH_APP_CLIENT_ID`
- `BROKER_GH_APP_ID`
- `BROKER_GH_APP_REDIRECT_URI` — exact Worker URL plus `/auth/github/callback`
- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_REDIRECT_URI` — exact Worker URL plus `/spotify/callback`
- `SPOTIFY_CREDENTIAL_ACTIVE_KEY_VERSION` — positive integer
- `SPOTIFY_REFRESH_WORKFLOW_REFS` — exact comma-separated allowlist of all nine migrated main-branch workflow refs: auth-health, Daily preflight, Daily midnight cycle, Daily feedback observation, Daily snapshot refresh, Reference Library, Playlist Manager, Great Migration, and `update.yml`. The deployment workflow rejects wildcards, missing refs, and extra refs.

The Spotify integration uses Authorization Code with PKCE as a public client. Do not configure or require a Spotify client secret: refresh requests send `client_id` in the form body and do not use HTTP Basic authentication, matching Spotify's PKCE refresh contract.

Cloudflare Worker secrets (never commit or copy into GitHub Actions):

- `GITHUB_APP_CLIENT_SECRET`
- `GITHUB_APP_PRIVATE_KEY`
- `SPOTIFY_CREDENTIAL_ENCRYPTION_KEYS` — JSON map of key-version strings to base64-encoded 32-byte AES keys. Keep old key versions until every credential has been re-encrypted. Loss of the active/historical key can make the stored credential unrecoverable.

The dedicated broker GitHub App is separate from SHIT's existing operational manager App. The broker App now needs only repository-scoped **Actions: Write** permission to inspect active workflow runs; it does not need Secrets, Contents, Administration, Issues, or account-wide permissions. Its client secret/private key remain Cloudflare Worker secrets. The OAuth callback no longer writes GitHub repository secrets.

## Deployment and owner setup

No deployment or external account changes are performed by PR CI. Before the owner-only deployment workflow can run:

1. Confirm the pre-created Cloudflare Worker `shit-auth-broker` and its canonical `workers.dev` HTTPS URL.
2. Install the dedicated broker GitHub App only on this repository with repository-scoped Actions: Write. Enable its user authorization flow and register the exact `/auth/github/callback` URI.
3. Register the exact `/spotify/callback` URI in the Spotify Developer Dashboard.
4. Set the public GitHub repository variables listed above. The deployment workflow validates that the OIDC allowlist exactly matches the nine migrated main-branch workflows.
5. Generate a cryptographically random 32-byte AES key, base64 encode it, and configure `SPOTIFY_CREDENTIAL_ENCRYPTION_KEYS` as a Cloudflare Worker secret, for example a JSON object with key version `1`. Set `SPOTIFY_CREDENTIAL_ACTIVE_KEY_VERSION=1`. Never paste the key into chat, source control, or a workflow log.
6. Add the scoped Cloudflare API token as GitHub Actions secret `CLOUDFLARE_API_TOKEN`. It should update only the existing Worker and its declared Durable Object migration.
7. Run the owner-only `Deploy SHIT Auth Broker` workflow from the repository's Actions tab.
8. Complete the owner-consented GitHub then Spotify browser flow from a phone or desktop. The callback verifies identity and initializes the encrypted credential store; it does not write `SPOTIFY_REFRESH_TOKEN` to GitHub.
9. Verify that the read-only auth-health workflow obtains an OIDC access token, successfully calls `/v1/me`, and records a healthy commit status.
10. Confirm that no playlist lock, playlist, snapshot, Library, or generated repository state changed.

Do not share secret values with ChatGPT or put them in issues, PRs, logs, or workflow artifacts. Verify secret names and configuration without retrieving secret contents.

## Failure and recovery semantics

Worker observability remains enabled for operational diagnosis. Broker logs may contain only fixed diagnostic stage names and error classes; never log exception contents, OAuth codes, tokens, cookies, state values, or credential material.


- OIDC identity, audience, workflow, repository, owner, ref, event, run, and timestamp checks fail closed.
- The credential object reserves a refresh operation transactionally before contacting Spotify. Concurrent callers wait for the result and reuse the encrypted access-token cache rather than starting competing refreshes.
- Concurrent refresh attempts are rejected. The refresh token is never returned to a workflow.
- A successful refresh verifies `/v1/me` against the stored account ID before committing the rotated refresh token.
- An explicit Spotify 429 releases the reservation without changing the credential and propagates `Retry-After`; it does not permanently block the credential.
- Ambiguous network/provider outcomes, invalid identity, corrupted ciphertext, or uncertain commits block further refresh and require owner-consented recovery. The old token is never blindly retried.
- Owner reauthorization can initialize an empty store or recover a blocked credential for the same verified Spotify account. A different account cannot silently replace the stored identity.
- Broker outage fails closed. Migrated workflows must not fall back to the old secret or refresh independently.
- OAuth completion never unlocks or edits a playlist.

## Tests and acceptance

Run `npm ci` and `npm test` in this directory. Run the Cloudflare SQLite Durable Object integration suite with `npm run test:durable-objects`. The broker CI also tests the Python OIDC client, manager broker-only mode, auth-health workflow contract, documentation layout, dependency audit, and a non-deploying Wrangler dry run.

Unit tests do not prove production readiness. Required end-to-end evidence includes real Cloudflare Durable Object transactions, owner-consented initial credential handoff, same-account recovery, OIDC verification from the exact main workflow, real Spotify refresh/identity verification, refresh-token rotation persistence, and fail-closed recovery after interrupted operations. All nine migrated workflows must pass CI and end-to-end verification before retiring the legacy secret.

## Current status

- Central encrypted credential store and versioned keyring: implemented in the stacked draft branch; Cloudflare integration and key provisioning remain.
- Owner-consented initial credential handoff and same-account recovery: wired in the stacked draft branch; not deployed or exercised with real credentials.
- OIDC-authenticated refresh endpoint and Python client: implemented and unit-tested; exact allowlist/configuration and live GitHub OIDC validation remain.
- Auth-health workflow: first OIDC consumer migrated in the feature branch; CI validation is pending.
- All nine workflow consumers: migrated to broker-only authentication on the stacked feature branch; live validation pending.
- Production deployment, owner OAuth, and end-to-end verification: not performed.
- Legacy GitHub Actions refresh-token secret: retained on the deployed main branch until merge, deployment, two independent broker-backed health checks, and production cutover approval; the broker callback no longer writes it.

The broker never unlocks or edits playlists. Do not merge, deploy, or perform production cutover until the staged PRs have passing validation, the owner has completed the external setup, and the remaining consumer migration and rollback plan are reviewed.
