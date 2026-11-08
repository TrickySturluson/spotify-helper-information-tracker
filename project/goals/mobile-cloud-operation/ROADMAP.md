# Mobile Cloud Operation & Spotify Reauthorization — Roadmap

**Status:** Broker source implementation is complete in review PR #182; reconciled-branch CI passed on head `e2b941180bf3b187ed13dc6f3a7d2d20e88afcd6`. No broker is deployed.  
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
- [x] Implement Spotify authorization-code exchange, exact scope validation and pre-save `/v1/me` identity verification (display the account name/ID on completion).
- [x] Implement GitHub App JWT, installation discovery and short-lived repository-scoped installation-token handling.
- [x] Encrypt the refresh token with GitHub's Actions secret public key and update only SPOTIFY_REFRESH_TOKEN.
- [x] Dispatch only spotify-auth-health-check.yml after confirmed secret persistence.
- [x] Implement owner allowlisting, one-time state/replay protection, preflight checks for active Spotify workflows, rate limiting, secure cookies, security headers and strict log redaction.
- [x] Add unit tests for owner allow/deny, scopes, cookies, HTML escaping, PKCE, canonical host, fail-closed workflow concurrency classification, Durable Object replay/expiry and required runtime configuration.
- [x] Add mocked integration/failure tests for provider token exchange, GitHub encryption/API errors, fail-closed persistence and dispatch outcomes (24 broker tests on the previously reviewed head; rerun on PR #182).

### M2 — Deployment pipeline and setup

- [x] Add infrastructure configuration and reproducible deployment workflow.
- [x] Document external secret/variable names only; keep values out of repository documentation.
- [ ] Deploy to a managed HTTPS runtime and register the exact Spotify callback URI.
- [ ] Install the minimal repository-scoped GitHub App.
- [ ] Configure GitHub App web authorization and runtime secrets.
- [x] Confirm no persistent Spotify refresh-token storage exists in the broker through source review and regression tests.
- [x] Add a mobile-first authorization page with clear account/permission explanation and no third-party scripts.

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

- [x] Provide a simple mobile entry point for supported SHIT operations using the existing GitHub issue/workflow control plane.
- [x] Verify ChatGPT can prepare, stage, inspect and verify through supported GitHub tools without terminal access; owner-authored read-only status reached the manager in issue #180.
- [ ] Keep explicit user confirmation for every consequential playlist write.
- [x] Document operations ChatGPT can execute through connected GitHub capabilities versus steps requiring a user tap in GitHub in OPERATIONS.md.
- [ ] Test the full flow with the user's PC off.

## Implementation notes

- Cloudflare Workers is the selected deployment target. SQLite-backed Durable Objects were chosen instead of ordinary Workers KV because OAuth state consumption and the active-flow marker need strongly consistent transactional behavior. Cloudflare documents SQLite Durable Objects on Free and Paid plans, subject to plan quotas and storage billing; do not assume unlimited zero-cost usage.
- The rate-limiting binding is an approximate per-location abuse throttle, not a security boundary. Owner authentication, PKCE, session binding and transactional one-time state provide the actual controls.
- A dedicated broker GitHub App, separate from the existing SHIT manager secret-writer App, is required. Install it only on this repository with Actions: write and Secrets: write; do not broaden the existing manager App's Secrets: write-only permissions. The app's web authorization flow (with PKCE) verifies the GitHub owner; the installation token is separately narrowed to this repository and those two permissions.
- The broker checks for active Spotify-related Actions runs before consent, before code exchange and before secret publication. This reduces token-rotation races but is not an atomic lock against a new workflow starting between checks; complete live testing in a quiet maintenance window.
- The previous reviewed broker head `1d38979a801ae3b5a8b635537f46f931f7048c9e` passed the 24-test broker suite, `npm audit --audit-level=high`, Wrangler dry-run, lockfile verification and full-history Gitleaks. PR #182 is rerunning the broker suite, dependency audit, Wrangler dry-run, 519-test repository suite and full-history Gitleaks after reconciliation. Passing unit/CI checks do not prove external OAuth or deployment.
- No external account, app, secret, redirect URI or playlist has been changed.

## Acceptance criteria

Complete only when a user can reauthorize from a phone browser without Codespaces/PC; GitHub owner and OAuth state are validated; PKCE is used; the token goes directly to the repository secret and is never exposed to browser/ChatGPT/issues/artifacts/logs; two independent cloud auth checks pass; OAuth does not unlock or modify playlists; existing safeguards remain unchanged; setup is reproducible; and end-to-end mobile verification succeeds with the PC off.

## Risks and open decisions

- A managed broker needs an external deployment account and initial configuration. Static GitHub Pages alone cannot securely write repository Actions Secrets.
- GitHub App private-key custody is critical; it belongs only in the broker's managed secret store. The app must be restricted to one repository.
- Verify GitHub App installation permission requirements and Spotify redirect URI rules before deployment.
- Spotify may invalidate the prior refresh token during reauthorization/rotation. Avoid concurrent token refreshes during bootstrap and use the new token only after secret persistence is confirmed.
- ChatGPT's GitHub connector does not expose Codespaces terminal execution or direct Actions-secret read/write. The broker is a secure bridge, not a claim that those capabilities already exist.

## Next action

Complete review/CI for PR #182, obtain separate explicit approval before merging it, then perform the owner-side Cloudflare/GitHub App/Spotify setup and deploy only after a separate readiness review. Complete mobile OAuth and two independent read-only auth-health checks before any playlist command. Do not retry the invalid Spotify credential until the broker is deployed and the new token is securely installed.

## Reconciliation status — 2026-11-08

- PR #181 was merged as `b0b280ff7b0b6d71fcbcf8fa3ded2d0b0f7b8a22` after explicit approval; its 519-test suite and full-history Gitleaks scan passed.
- The old broker PR #176 was 7 commits behind/divergent. Its reviewed broker implementation was copied onto a fresh branch based on the new `main`; PR [#182](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/182) is open, ahead 17 commits and behind 0 at the latest recorded comparison. Do not merge without separate explicit owner approval.
- CI on the reconciled PR passed on the recorded head. The workflow catalogue, docs index, goal index and current-main mobile operation history are included; the prior PR #176 docs were not blindly copied over the newer PR #181 status. Any new commit requires fresh checks.
- Known design limitation: active Spotify workflow checks are repeated but are not an atomic lock against a new workflow starting after the final check. Schedule first OAuth in a quiet maintenance window; do not weaken fail-closed behavior.
- No Worker deployment, external app configuration, callback registration, credential change or playlist operation has occurred. Spotify `invalid_grant` remains the live blocker.
