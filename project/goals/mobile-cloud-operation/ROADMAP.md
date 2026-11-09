# Authentication Management & Recovery — Roadmap

**Last reviewed:** 2026-11-09

**Status:** Active integration and recovery work. Base broker PR #185 merged at `8cd28530081c519112fd947ac7bb05edc0ce7b04`; diagnostic follow-ups #190 and #191 merged at `0266b0f124c67fdecae8b83ef89ffe0c6aa478b3` and `50202a4a394ea68582f02a4ab18ce9091f7f3e4b`. The production Worker `shit-auth-broker` is deployed at 100% traffic on version 14 (`06bb7f3a-da70-449f-9f51-72423c693fa1`, 2026-11-09 09:46 UTC). This is the base OAuth broker with Durable Object migration v2; it does **not** yet have the broker-owned `SPOTIFY_CREDENTIAL_STORE` binding or encryption keyring. GitHub App secret metadata now reports both app credentials as `secret_text`. Live Spotify authorization is still failing in the callback and is not complete.

**Active implementation PRs:** PR #187 (`feature/broker-owned-spotify-credential-store`) and PR #188 (`feature/oidc-broker-refresh-endpoint`) remain drafts and are not mergeable against their current bases. PR #187's latest head is `1b55214b4b8362ee90f155e937e3252a9dd513ae`; its fresh broker tests #42599358532 and security scan #42599358504 are in progress. The prior head `1c8e6b46c292525c3a13019325a270d91f97a84d` passed broker tests/Wrangler dry-run #42598447923 and security scan #42598447639. PR #188's callback-diagnostic head `5e39177daeb0695d7230b199c9c37f6edc6999f2` passed broker tests #42598778973 and security scan #42598778904. Latest PKCE-corrected head `6e269154ea2ba8454857efecfd985f6abd541d9e` has security scan #42599375645 in progress and broker tests #42599375698 pending. PR #187 is 130 commits ahead / 3 behind main; PR #188 is 267 ahead / 5 behind PR #187's base. Resolve the stacked branch divergence before merge. PR #189 is a separate engineering/general draft and must not be modified by this workstream.

## Latest production and diagnostic evidence (2026-11-09)

- Cloudflare Workers Builds configuration: root `auth-broker`, empty build command, production upload command `npx wrangler versions upload`, preview command `npx wrangler preview`; automatic builds and previews are enabled. Production promotion remains a separate owner-controlled action.
- Active production Worker version 14 is 100% of traffic and has only `OAUTH_STATE` and `SPOTIFY_REFRESH_LEASE` Durable Object bindings (migration tag v2). It has no `SPOTIFY_CREDENTIAL_STORE`, `SPOTIFY_CREDENTIAL_ENCRYPTION_KEYS`, `SPOTIFY_CREDENTIAL_ACTIVE_KEY_VERSION`,  Do not attempt the new broker-owned refresh path until these are provisioned and the integrated version is deployed.
- The Cloudflare Secrets metadata endpoint confirms `GITHUB_APP_CLIENT_SECRET` and `GITHUB_APP_PRIVATE_KEY` are both `secret_text`; values were not read.
- The Spotify app remains a public Authorization Code with PKCE client. Spotify's refresh guide requires `client_id` in the refresh form body for PKCE and reserves HTTP Basic client-secret authentication for the Authorization Code flow; do **not** provision a Spotify client secret. See [Spotify PKCE refresh requirements](https://developer.spotify.com/documentation/web-api/tutorials/refreshing-tokens) and [PKCE flow](https://developer.spotify.com/documentation/web-api/tutorials/code-pkce-flow).
- A redacted Workers Observability query for the prior 24 hours found six `shit_auth_broker_request_failed` events, all on `GET /spotify/callback`: four on version 13 at `broker.base_url_configuration` (two `BrokerError`, two `UnexpectedError`), and two on version 14 at `broker.route_dispatch` (`UnexpectedError`). No exception text, OAuth codes, tokens, cookies, or state were retrieved.
- PR #188 now adds fixed callback-stage diagnostics (GitHub App JWT, installation lookup/token, concurrent-workflow check, Spotify code exchange, scope/identity verification, encrypted credential write, health dispatch, completion-state write and redirect). The test commit and current CI must pass before another consent attempt. The latest production callback failure is not yet localized beyond route dispatch. The branch refresh implementation has now been corrected to follow Spotify's PKCE contract: `client_id` in the form body, no Basic header and no Spotify client secret.
- No Spotify credential was successfully saved, no auth-health workflow success was verified, and no playlist operation was performed.

## Problem and target

SHIT currently has refresh-token rotation persistence and a manually dispatched auth-health workflow, but no maintained authentication health service or verified recovery path for an invalid/revoked refresh token. The user wants SHIT to detect auth problems, repair what is safely repairable, and ask for consent only when Spotify requires a new authorization grant.

The desired end state is a system that continuously monitors auth, refreshes and persists rotated credentials, classifies failures accurately, prevents repeated futile calls, and blocks Spotify-dependent work until a read-only verification confirms recovery.

## Required invariants

1. Transitional credential ownership is explicit: `SPOTIFY_REFRESH_TOKEN` in GitHub Actions Secrets remains the legacy source on current `main`; after the broker-owned cutover, the encrypted SQLite Durable Object is the sole long-lived refresh-token store. Do not dual-write or silently fall back. Workflows receive only short-lived access tokens through OIDC.
2. Refresh tokens and access tokens are never exposed in logs, artifacts, issues, chat, browser storage, URLs or repository files.
3. After cutover, automatic refresh and rotation occur only inside the broker-owned Durable Object critical section. The existing GitHub App secret-write path is legacy and must not remain as a parallel refresh writer.
4. A replacement refresh token is persisted before the old value is discarded; persistence failure is a hard failure.
5. `invalid_grant` means reauthorization is required; do not retry the same credential.
6. 429 honors Retry-After for both scheduled and manual attempts; missing/invalid headers use a conservative 24-hour fallback. 5xx/network failures remain distinct from auth failures.
7. Missing configuration, insufficient scopes, wrong Spotify identity and secret-write failures have distinct statuses.
8. Health checks are read-only with respect to playlists, Library data and user-facing content.
9. OAuth uses Authorization Code + PKCE, owner authentication, exact HTTPS callbacks, one-time state and replay protection.
10. The broker has no playlist endpoint and cannot unlock, preview, confirm or modify playlists.
11. GitHub owner identity and Spotify account identity are verified independently.
12. Every Spotify-dependent workflow must eventually use a shared auth preflight or equivalent centralized health gate without causing refresh storms or race conditions.
13. No normal Spotify-dependent workflow may proceed on a known reauthorization-required state.
14. Phone and desktop are both supported; no local PC, terminal or Codespace is a runtime dependency.
15. Never claim healthy/deployed/recovered without fresh evidence.

## Status model

| State | Meaning | Automatic action |
|---|---|---|
| healthy | Refresh and `/v1/me` succeeded | Continue; persist rotation if returned |
| reauthorization_required | Spotify rejected refresh with `invalid_grant` or required consent/scopes are absent | Stop Spotify work; request owner consent |
| rate_limited | Spotify returned 429 | Defer until Retry-After; no rapid retry |
| provider_unavailable | Spotify 5xx or network failure | Bounded retry/backoff; preserve prior credential |
| configuration_error | Missing/invalid client configuration or workflow setup | Fail closed; report non-secret configuration |
| identity_mismatch | `/v1/me` does not match the authorized expected account | Stop; require owner review |
| secret_persistence_failed | Refresh succeeded but rotation could not be stored | Stop; never claim healthy; recover without losing the returned token |
| verification_pending | OAuth completed and secret write confirmed, but independent cloud verification is outstanding | Do not resume Spotify operations |

## Milestones

### M0 — Baseline and threat model
- [x] Inspect manager OAuth and cloud token-rotation persistence.
- [x] Inspect playlist-control and auth-health workflows.
- [x] Confirm prior `invalid_grant` blocker and stop futile retries.
- [ ] Audit every Spotify-dependent workflow for a consistent auth preflight integration point.
- [ ] Inspect repository rules, GitHub App installation/permissions and Spotify redirect settings without exposing secret values.
- [ ] Confirm deployment provider/account and cost limits.

### M1 — Automatic health monitoring
- [x] Add daily scheduled and manual auth-health checks with structured diagnosis.
- [x] Emit structured redacted status categories without provider response bodies or credentials.
- [x] Persist non-secret health state in the `spotify-auth-health` commit status on fixed anchor commit `a4ac9def8be5b6e727b777e2660a7bb027a8e51b`, so ordinary commits do not reset the latch; run only on `main`.
- [x] Ensure one attempt per run: no retry for `invalid_grant`; report Retry-After for 429; classify transient failures without retry loops.
- [x] Add a fail-closed GitHub commit-status latch: scheduled checks skip permanent blockers/interrupted attempts, respect Retry-After deadlines and resume after a deliberate manual recovery attempt. Manual dispatch bypasses permanent blockers only.
- [x] Add an owner-facing reauthorization action to the failed health-check summary: link to the HTTPS broker root when configured, otherwise link to the deployment runbook. GitHub's normal workflow-failure notification remains the alert channel.
- [ ] Ensure monitoring cannot trigger playlist operations or generated-data writes.

### M2 — Safe refresh and token rotation
- [x] Existing manager refresh-token rotation persistence inspected.
- [x] Existing auth-health workflow can refresh and persist a rotated token.
- [ ] Add regression tests for rotation persistence, missing rotation, persistence failure and redaction.
- [ ] Verify refresh-token replacement is atomic from the operational perspective and never lose the only valid token.
- [ ] Ensure all refresh-capable workflows share concurrency coordination or a safe single-flight policy.

### M3 — Authorization broker
- [x] Implement HTTPS broker source with GitHub App web authorization + Spotify PKCE.
- [x] Implement short-lived transactional Durable Object state, owner checks, replay/expiry protection and active-workflow checks.
- [x] Implement the temporary base-broker GitHub Actions secret write path for `SPOTIFY_REFRESH_TOKEN` (PR #185); this is legacy-only and must be removed after broker-owned storage is live.
- [x] Base broker dispatches read-only auth-health after confirmed legacy secret persistence; target PR #188 dispatches only after encrypted Durable Object persistence.
- [x] Add security tests and reproducible deployment configuration.
- [x] Merge the base broker source/tests/owner-only deployment workflow (#185); merge safe diagnostic follow-ups (#190 and #191). The base Worker is deployed as version 14 at 100% traffic, but this does not mean broker-owned credential storage or Spotify authorization is complete.
- [ ] Reconcile and merge the encrypted credential store and OIDC refresh integration in PRs #187/#188; both remain drafts and their branches are divergent.
- [ ] Retire the legacy Actions-secret writer at cutover; the target broker GitHub App must need only Actions: write, not Secrets: write.
- [x] Verify GitHub App client secret/private key metadata as Cloudflare `secret_text` bindings; never retrieve values.
- [ ] Provision the versioned Spotify credential encryption keyring for the broker-owned store, plus active-key version and exact OIDC workflow allowlist. Confirm required metadata before deployment.
- [x] Deploy the base Worker and verify version 14 receives 100% production traffic.
- [ ] Deploy the integrated v3 credential-store/OIDC version after key provisioning and owner-controlled promotion; then retest the exact HTTPS callbacks.
- [ ] Complete a fresh owner-consented Spotify OAuth flow only after the integrated credential-store version is active; verify from phone and desktop browsers.

### M4 — Central auth gate
- [x] Inventory the nine current workflows that consume `SPOTIFY_REFRESH_TOKEN`.
- [ ] Merge/deploy the shared OIDC broker access-token client and nine-workflow migration implemented in PR #188; it remains draft and not active on `main`.
- [x] Define the short critical-section OIDC-authenticated Durable Object lease design; see [REFRESH_TOKEN_SINGLE_FLIGHT.md](REFRESH_TOKEN_SINGLE_FLIGHT.md). No global Actions concurrency group is permitted.
- [x] Add initial OIDC JWT verification, atomic lease acquisition/renewal/release, expiry recovery and fencing generations in `auth-broker/src/refresh-lock.js`; automated unit tests pass, but no Actions workflow is integrated and the lease is not sufficient to fence GitHub Secrets API writes.
- [ ] Validate real OIDC claims using a harmless non-production workflow before enforcing the workflow allowlist (not yet performed).
- [ ] Enable the broker-owned single-flight refresh path for auth-health first, then all nine consumers; add an inventory test that rejects any direct refresh-token consumer or legacy fallback.
- [ ] Ensure a single auth check can satisfy multiple jobs in a run without parallel refresh storms.
- [ ] Distinguish authentication from 429, 5xx, network, permission and configuration failures.
- [ ] Block operations on known invalid credentials; do not silently skip the gate.
- [ ] Preserve each workflow's existing authorization and playlist safeguards.
- [ ] Add source-backed tests proving auth preflight itself performs no playlist writes.

### M5 — End-to-end acceptance
- [ ] Verify unauthenticated and non-owner broker requests are denied.
- [ ] Complete Spotify PKCE authorization and confirm expected Spotify identity/scopes.
- [ ] Verify encrypted Durable Object credential persistence and key version without reading or exposing the credential; verify the broker no longer writes GitHub Actions secrets.
- [ ] Verify only the read-only auth-health workflow is dispatched.
- [ ] Pass two independent cloud auth-health runs after runner disposal.
- [ ] Verify health state becomes healthy and stale reauthorization status clears.
- [ ] Verify playlist lock/state/audit/snapshots and live playlist contents are unchanged.
- [ ] Verify one Spotify-dependent workflow is blocked before recovery and passes auth preflight after recovery.
- [ ] Test from phone and desktop with the user's PC otherwise off.

## Architecture decisions

- **Authentication Health Monitor:** scheduled and on-demand read-only verification, token refresh, secure rotation persistence, structured diagnosis and durable non-secret status.
- **Authorization Broker:** managed HTTPS owner-consent flow; Cloudflare Worker + SQLite Durable Object. The merged base broker currently has a legacy Actions-secret writer (Actions: write + Secrets: write); the target broker-owned design in PR #188 removes Secrets: write and retains only repository-scoped Actions: write.
- **Recovery Coordinator:** routes each failure category to bounded automatic repair, deferred retry, configuration correction or owner consent.
- **Central Auth Gate:** shared preflight dependency for Spotify workflows. The broker must become the sole refresh-token holder and refresher; workflows receive only short-lived access tokens after OIDC authorization. No per-job refresh fan-out or direct refresh-token secret reads.
- **Control plane separation:** GitHub issue commands are a separate remote operations interface. They are not the purpose of this auth workstream and must never bypass manager controls.

## Known risks and constraints

- A refresh token rejected with `invalid_grant` cannot be revived by refreshing again; owner consent is mandatory.
- A scheduled monitor against an invalid credential must report reauthorization-required; subsequent scheduled runs inspect the fixed anchor commit's `spotify-auth-health` status and skip until an explicit owner-triggered recovery attempt succeeds. The `pending` status also blocks later scheduled runs if a runner exits before persisting its result. If the commit-status API cannot be read or the pending/result status cannot be written, the workflow fails closed before it can proceed or leaves `pending` to block the next scheduled run.
- Multiple concurrent refreshes can race when Spotify rotates refresh tokens. The OIDC Durable Object lease prototype does not fence GitHub Secrets writes and is not sufficient for production. Broker-controlled encrypted credential persistence is the recommended end state.
- The broker's active-workflow check is advisory only and must not be represented as a global lock. Replace it with the broker-owned refresh/persistence critical section before production rollout.
- Cloudflare quotas/storage billing apply; no zero-cost/unlimited assumption.
- GitHub App private key belongs only in the broker's managed secret store. The broker App remains separate from the existing manager secret-writer App.
- No external account, app, secret, redirect URI or playlist may be changed without the required user-side setup/consent.

## Acceptance criteria

Complete only when SHIT can monitor authentication, automatically refresh and persist rotations, correctly classify and safely handle failures, request owner consent only when necessary, complete OAuth from phone or desktop, pass two independent read-only cloud checks, and gate Spotify-dependent work on verified health—without any authentication path changing playlists or bypassing existing safeguards.

## Next action

Finish the current callback-stage diagnostics on PR #188 and verify fresh CI. Resolve PR #187's divergence against current `main`, then reconcile the stacked PR #188 branch without losing its nine-workflow OIDC migration. Independently review the full combined diff and rerun broker security tests, Durable Object integration tests, all Python regressions, dependency audit, Wrangler dry-run and full-history secret scan. Only then provision the missing encryption keyring and use the owner-only deployment path. Do not ask the user to retry Spotify consent until the integrated Worker version is confirmed active at 100% traffic.
