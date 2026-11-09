# Authentication Management & Recovery — Roadmap

**Status:** Active implementation. Authentication foundation PR #185 and stacked credential-store/OIDC PRs #187/#188 remain open and are not deployed. Central OAuth handoff and the first auth-health OIDC canary are implemented on the feature branch; eight workflow consumers and production acceptance remain outstanding.  
**Priority:** User-authorized on 2026-11-08.  
**Scope:** SHIT-wide authentication health, safe automatic refresh/rotation, diagnosis and consent-based recovery. Phone and desktop are equally supported.

## Problem and target

SHIT currently has refresh-token rotation persistence and a manually dispatched auth-health workflow, but no maintained authentication health service or verified recovery path for an invalid/revoked refresh token. The user wants SHIT to detect auth problems, repair what is safely repairable, and ask for consent only when Spotify requires a new authorization grant.

The desired end state is a system that continuously monitors auth, refreshes and persists rotated credentials, classifies failures accurately, prevents repeated futile calls, and blocks Spotify-dependent work until a read-only verification confirms recovery.

## Required invariants

1. The central broker is the source of truth for migrated workflows; the legacy GitHub Actions secret remains temporarily available only to unmigrated consumers until explicit cutover.
2. Refresh tokens and access tokens are never exposed in logs, artifacts, issues, chat, browser storage, URLs or repository files.
3. Automatic refresh and token rotation are allowed only through existing narrow GitHub App secret-write boundaries.
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
- [x] Earlier broker iteration implemented repository-secret publication; superseded by central encrypted credential ownership and removed from the current OAuth callback.
- [x] Dispatch only read-only auth-health verification after confirmed central credential-store initialization/recovery.
- [x] Add security tests and reproducible deployment configuration.
- [x] Review and merge the reconciled broker source/tests/deployment workflow to `main` (source is present; no Worker deployment is implied).
- [ ] Configure Cloudflare Worker secrets/variables and dedicated repository-scoped GitHub App.
- [ ] Register exact HTTPS callback URLs and deploy the Worker.
- [ ] Complete owner-consented Spotify OAuth from phone and desktop browsers.

### M4 — Central auth gate
- [x] Inventory the nine current workflows that consume `SPOTIFY_REFRESH_TOKEN`; see [WORKFLOW_MIGRATION_INVENTORY.md](WORKFLOW_MIGRATION_INVENTORY.md).
- [ ] Define a reusable workflow/action or shared preflight contract for all Spotify-dependent workflows.
- [x] Define the short critical-section OIDC-authenticated Durable Object lease design; see [REFRESH_TOKEN_SINGLE_FLIGHT.md](REFRESH_TOKEN_SINGLE_FLIGHT.md). No global Actions concurrency group is permitted.
- [x] Add initial OIDC JWT verification, atomic lease acquisition/renewal/release, expiry recovery and fencing generations in `auth-broker/src/refresh-lock.js`; keep isolated because a lease cannot fence GitHub Secrets writes.
- [x] Implement isolated AES-256-GCM credential-store prototype with transactional refresh reservation, identity verification, encrypted rotation commit, replay rejection and fail-closed ambiguous outcomes; PR #187.
- [x] Add OIDC-authenticated `POST /internal/spotify/refresh` route with a dedicated audience, exact workflow allowlist, fixed credential Durable Object identity and minimal operation-ID payload; stacked draft PR #188.
- [x] Add a GitHub Actions OIDC client and broker-only Spotify manager mode; broker sessions do not load refresh-token files or refresh directly, and expired access tokens fail closed.
- [x] Authenticate explicit credential encryption key-version metadata in AES-GCM associated data and support staged multi-key rotation on successful refresh.
- [x] Add same-account owner reauthorization and wire the owner-consented OAuth callback to initialize/recover the encrypted credential store.
- [ ] Add real Cloudflare Durable Object integration tests and key-version rotation/recovery design before enabling the credential store in any environment.
- [ ] Validate real OIDC claims using a harmless non-production workflow before enforcing the workflow allowlist (not yet performed).
- [x] Migrate auth-health first as the read-only OIDC canary in the feature branch; [ ] migrate the remaining eight consumers individually and preserve their operational boundaries.
- [ ] Ensure a single auth check can satisfy multiple jobs in a run without parallel refresh storms.
- [ ] Distinguish authentication from 429, 5xx, network, permission and configuration failures.
- [ ] Block operations on known invalid credentials; do not silently skip the gate.
- [ ] Preserve each workflow's existing authorization and playlist safeguards.
- [ ] Add source-backed tests proving auth preflight itself performs no playlist writes.

### M5 — End-to-end acceptance
- [ ] Verify unauthenticated and non-owner broker requests are denied.
- [ ] Complete Spotify PKCE authorization and confirm expected Spotify identity/scopes.
- [ ] Verify the central Durable Object credential version advances without exposing ciphertext or plaintext secrets.
- [ ] Verify only the read-only auth-health workflow is dispatched.
- [ ] Pass two independent cloud auth-health runs after runner disposal.
- [ ] Verify health state becomes healthy and stale reauthorization status clears.
- [ ] Verify playlist lock/state/audit/snapshots and live playlist contents are unchanged.
- [ ] Verify one Spotify-dependent workflow is blocked before recovery and passes auth preflight after recovery.
- [ ] Test from phone and desktop with the user's PC otherwise off.

## Architecture decisions

- **Authentication Health Monitor:** scheduled and on-demand read-only verification, token refresh, secure rotation persistence, structured diagnosis and durable non-secret status.
- **Authorization Broker:** managed HTTPS owner-consent flow; Cloudflare Worker + SQLite Durable Object; dedicated GitHub App with repository-scoped Actions: write (required only for active-run inspection and auth-health dispatch).
- **Recovery Coordinator:** routes each failure category to bounded automatic repair, deferred retry, configuration correction or owner consent.
- **Central Auth Gate:** shared preflight dependency for Spotify workflows. The broker must become the sole refresh-token holder and refresher; workflows receive only short-lived access tokens after OIDC authorization. No per-job refresh fan-out or direct refresh-token secret reads.
- **Control plane separation:** GitHub issue commands are a separate remote operations interface. They are not the purpose of this auth workstream and must never bypass manager controls.

## Known risks and constraints

- A refresh token rejected with `invalid_grant` cannot be revived by refreshing again; owner consent is mandatory.
- A scheduled monitor against an invalid credential must report reauthorization-required; subsequent scheduled runs inspect the fixed anchor commit's `spotify-auth-health` status and skip until an explicit owner-triggered recovery attempt succeeds. The `pending` status also blocks later scheduled runs if a runner exits before persisting its result. If the commit-status API cannot be read or the pending/result status cannot be written, the workflow fails closed before it can proceed or leaves `pending` to block the next scheduled run.
- Multiple concurrent refreshes previously raced when Spotify rotated refresh tokens. The lease prototype alone cannot fence GitHub Secrets writes; the broker-owned encrypted credential store is now the intended authority. The remaining eight workflows must migrate before the race is fully removed from production.
- The broker's active-workflow check is advisory only and is used to avoid starting owner OAuth during active Spotify work. Refresh serialization and credential commit are enforced inside the single Durable Object.
- Cloudflare quotas/storage billing apply; no zero-cost/unlimited assumption.
- GitHub App private key belongs only in the broker's managed secret store. The broker App remains separate from the existing manager secret-writer App.
- No external account, app, secret, redirect URI or playlist may be changed without the required user-side setup/consent.

## Acceptance criteria

Complete only when SHIT can monitor authentication, automatically refresh and persist rotations, correctly classify and safely handle failures, request owner consent only when necessary, complete OAuth from phone or desktop, pass two independent read-only cloud checks, and gate Spotify-dependent work on verified health—without any authentication path changing playlists or bypassing existing safeguards.

## Next action

Finish CI/source review for the stacked PRs, validate Cloudflare Durable Object integration and key recovery, then deploy only after owner setup/approval. Prove the auth-health OIDC canary with two independent read-only checks, then migrate the remaining eight consumers using `WORKFLOW_MIGRATION_INVENTORY.md` and preserve every existing playlist/snapshot/rollback boundary.


## 2026-11-09 — Central credential ownership and first OIDC canary

- Added a Durable Object `/authorize` operation that initializes an empty credential store or restores a blocked credential for the same verified Spotify account. Ready/in-progress records and account changes are rejected.
- Wired the Spotify OAuth callback to verify `/v1/me` and hand the refresh token directly to the encrypted credential store. The broker no longer writes the long-lived token to GitHub Actions Secrets.
- Migrated `spotify-auth-health-check.yml` to the broker OIDC client and a short-lived access token. The workflow retains the durable commit-status latch, Retry-After handling, and read-only playlist/Library boundary.
- Narrowed the broker GitHub App installation token to repository Actions: Write, the minimum needed both to inspect active runs and dispatch the read-only auth-health workflow; Secrets: write is no longer required.
- Corrected credential-store rate-limit handling: a definite Spotify 429 releases the refresh reservation, preserves the existing encrypted credential, and propagates Retry-After rather than permanently blocking the credential.
- Updated the workflow inventory guard: auth-health is the first migrated canary; eight direct refresh-token consumers remain.
- Source and documentation changes are on stacked draft PR #187/#188. CI is pending. No Cloudflare deployment, encryption-key provisioning, Spotify OAuth, GitHub App configuration, production secret migration, or playlist operation was performed.
