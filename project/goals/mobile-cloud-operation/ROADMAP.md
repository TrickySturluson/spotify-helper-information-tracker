# Mobile Cloud Operation & Spotify Reauthorization — Roadmap

**Status:** Broker source implementation and automated tests underway; no broker deployed.  
**Priority:** Active, explicitly authorized by the user on 2026-11-08.

## Problem

SHIT already runs playlist operations in GitHub Actions, but recovery from an invalid/revoked Spotify refresh token still requires a local process to receive the OAuth callback on port 8888, followed by manual token transfer into GitHub Actions Secrets. The user wants mobile operation without Codespaces or a personal computer, while retaining all playlist security rules.

## Required invariants

1. GitHub remains the source of truth for code, durable workflow state, audit and operational records.
2. Spotify refresh tokens remain in GitHub Actions Secrets; never in repository files, issues, artifacts, chat, browser storage or logs.
3. The broker is owner-authenticated, repository-scoped, minimal, short-lived and fail-closed.
4. Spotify OAuth uses Authorization Code with PKCE and an exact registered HTTPS callback.
5. Successful authorization writes the token directly to the repository secret store, then runs read-only auth verification.
6. OAuth never unlocks a playlist or triggers a playlist write.
7. Playlist modifications continue through the existing SHIT manager with exact owner checks, managed-playlist authorization, explicit unlock, fresh preview, confirmation, snapshot, audit, rollback and live read-back.
8. Codespaces and personal computers are optional; no always-on user device is required.
9. ChatGPT never claims terminal access, direct secret access, or successful Spotify changes without supported evidence.
10. External infrastructure must be deployed and verified before describing the feature as available.

## Milestones

### M0 — Baseline and threat model

- [x] Inspect current Spotify manager OAuth implementation.
- [x] Inspect playlist-control and auth-health workflows.
- [x] Confirm local callback binds port 8888 and uses PKCE.
- [x] Confirm cloud refresh-token rotation persistence exists.
- [x] Record invalid_grant blocker; avoid repeated retries.
- [ ] Inspect repository rules, GitHub App installation/permissions, and Spotify redirect settings without exposing secret values.
- [ ] Confirm deployment provider/account; prefer free tier and no local PC requirement.

### M1 — Broker implementation

- [x] Implement HTTPS broker source with GitHub App web authorization + PKCE owner authentication.
- [x] Implement short-lived server-side OAuth state and PKCE verifier storage in a strongly consistent SQLite-backed Durable Object.
- [x] Implement Spotify authorization-code exchange and exact scope validation.
- [x] Implement GitHub App JWT, installation discovery and short-lived repository-scoped installation-token handling.
- [x] Encrypt the refresh token with GitHub's Actions secret public key and update only SPOTIFY_REFRESH_TOKEN.
- [x] Dispatch only spotify-auth-health-check.yml after confirmed secret persistence.
- [x] Implement owner allowlisting, one-time state/replay protection, preflight checks for active Spotify workflows, rate limiting, secure cookies, security headers and strict log redaction.
- [x] Add unit tests for owner allow/deny, scopes, cookies, HTML escaping, PKCE, canonical host, concurrency classification and Durable Object replay/expiry.
- [ ] Add integration/failure tests for provider token exchange, GitHub encryption/API errors, fail-closed persistence and dispatch outcomes.

### M2 — Deployment pipeline and setup

- [ ] Add infrastructure configuration and reproducible deployment workflow.
- [ ] Document external secret/variable names only.
- [ ] Deploy to a managed HTTPS runtime and register the exact Spotify callback URI.
- [ ] Install the minimal repository-scoped GitHub App.
- [ ] Configure GitHub App web authorization and runtime secrets.
- [ ] Confirm no persistent Spotify refresh-token storage exists in the broker.
- [ ] Add a mobile-first authorization page with clear account/permission explanation and no third-party scripts.

### M3 — Verification and integration

- [ ] Test unauthenticated and non-owner denial.
- [ ] Test successful Spotify PKCE authorization from a mobile browser.
- [ ] Verify the token is written directly to the GitHub repository secret; inspect only secret metadata, never its value.
- [ ] Verify only the read-only auth-health workflow is dispatched.
- [ ] Confirm /v1/me and required scopes through the health workflow.
- [ ] Confirm a second independent cloud run succeeds after runner disposal.
- [ ] Verify playlist state/audit/lock are unchanged and no playlist write occurred.
- [ ] Update operational guide and workflow catalogue with deployed state and evidence.

### M4 — Mobile SHIT operation quality

- [ ] Provide a simple mobile entry point for supported SHIT operations using the existing GitHub issue/workflow control plane.
- [ ] Ensure ChatGPT can prepare, stage, inspect and verify through supported GitHub tools without terminal access.
- [ ] Keep explicit user confirmation for every consequential playlist write.
- [ ] Document operations ChatGPT can execute through connected GitHub capabilities versus steps requiring a user tap in GitHub.
- [ ] Test the full flow with the user's PC off.

## Implementation notes

- Cloudflare Workers is the selected deployment target. SQLite-backed Durable Objects were chosen instead of ordinary Workers KV because OAuth state consumption and the active-flow marker need strongly consistent transactional behavior. Cloudflare documents SQLite Durable Objects on Free and Paid plans, subject to plan quotas and storage billing; do not assume unlimited zero-cost usage.
- The rate-limiting binding is an approximate per-location abuse throttle, not a security boundary. Owner authentication, PKCE, session binding and transactional one-time state provide the actual controls.
- A dedicated broker GitHub App is expected, installed only on this repository with Actions: write and Secrets: write. The app's web authorization flow (with PKCE) verifies the GitHub owner; the installation token is separately narrowed to this repository and those two permissions.
- The broker checks for active Spotify-related Actions runs before consent, before code exchange and before secret publication. This reduces token-rotation races but is not an atomic lock against a new workflow starting between checks; complete live testing in a quiet maintenance window.
- Automated unit tests and Wrangler dry-run validation are being added to the PR. No external account, app, secret, redirect URI or playlist has been changed.

## Acceptance criteria

Complete only when a user can reauthorize from a phone browser without Codespaces/PC; GitHub owner and OAuth state are validated; PKCE is used; the token goes directly to the repository secret and is never exposed to browser/ChatGPT/issues/artifacts/logs; two independent cloud auth checks pass; OAuth does not unlock or modify playlists; existing safeguards remain unchanged; setup is reproducible; and end-to-end mobile verification succeeds with the PC off.

## Risks and open decisions

- A managed broker needs an external deployment account and initial configuration. Static GitHub Pages alone cannot securely write repository Actions Secrets.
- GitHub App private-key custody is critical; it belongs only in the broker's managed secret store. The app must be restricted to one repository.
- Verify GitHub App installation permission requirements and Spotify redirect URI rules before deployment.
- Spotify may invalidate the prior refresh token during reauthorization/rotation. Avoid concurrent token refreshes during bootstrap and use the new token only after secret persistence is confirmed.
- ChatGPT's GitHub connector does not expose Codespaces terminal execution or direct Actions-secret read/write. The broker is a secure bridge, not a claim that those capabilities already exist.

## Next action

Complete M0 by verifying repository security/branch rules and selecting the least-privilege managed deployment path. Then implement and test the broker on a feature branch. Do not retry the invalid Spotify credential until a new token has been securely installed.