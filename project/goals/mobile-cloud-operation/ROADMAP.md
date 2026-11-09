# Authentication Management & Recovery — Roadmap

**Status:** Active implementation. Broker source exists in an unmerged/reviewable feature line; external deployment and real Spotify reauthorization are not complete.  
**Priority:** User-authorized on 2026-11-08.  
**Scope:** SHIT-wide authentication health, safe automatic refresh/rotation, diagnosis and consent-based recovery. Phone and desktop are equally supported.

## Problem and target

SHIT currently has refresh-token rotation persistence and a manually dispatched auth-health workflow, but no maintained authentication health service or verified recovery path for an invalid/revoked refresh token. The user wants SHIT to detect auth problems, repair what is safely repairable, and ask for consent only when Spotify requires a new authorization grant.

The desired end state is a system that continuously monitors auth, refreshes and persists rotated credentials, classifies failures accurately, prevents repeated futile calls, and blocks Spotify-dependent work until a read-only verification confirms recovery.

## Required invariants

1. GitHub Actions Secrets remains the source of truth for `SPOTIFY_REFRESH_TOKEN`.
2. Refresh tokens and access tokens are never exposed in logs, artifacts, issues, chat, browser storage, URLs or repository files.
3. Automatic refresh and token rotation are allowed only through existing narrow GitHub App secret-write boundaries.
4. A replacement refresh token is persisted before the old value is discarded; persistence failure is a hard failure.
5. `invalid_grant` means reauthorization is required; do not retry the same credential.
6. 429 honors Retry-After; 5xx/network failures use bounded backoff and remain distinct from auth failures.
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
- [ ] Persist a non-secret health record with timestamps, category and workflow-run evidence.
- [x] Ensure one attempt per run: no retry for `invalid_grant`; report Retry-After for 429; classify transient failures without retry loops.
- [ ] Add a durable reauthorization-required latch and owner notification/action; scheduled checks must skip while latched until an explicit reauthorization or manual recovery attempt.
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
- [x] Implement repository-scoped secret encryption/update of only `SPOTIFY_REFRESH_TOKEN`.
- [x] Dispatch only read-only auth-health verification after confirmed secret persistence.
- [x] Add security tests and reproducible deployment configuration.
- [ ] Review and approve the reconciled broker PR; do not merge without explicit approval.
- [ ] Configure Cloudflare Worker secrets/variables and dedicated repository-scoped GitHub App.
- [ ] Register exact HTTPS callback URLs and deploy the Worker.
- [ ] Complete owner-consented Spotify OAuth from phone and desktop browsers.

### M4 — Central auth gate
- [ ] Define reusable workflow/action or shared preflight contract for all Spotify-dependent workflows.
- [ ] Ensure a single auth check can satisfy multiple jobs in a run without parallel refresh storms.
- [ ] Distinguish authentication from 429, 5xx, network, permission and configuration failures.
- [ ] Block operations on known invalid credentials; do not silently skip the gate.
- [ ] Preserve each workflow's existing authorization and playlist safeguards.
- [ ] Add source-backed tests proving auth preflight itself performs no playlist writes.

### M5 — End-to-end acceptance
- [ ] Verify unauthenticated and non-owner broker requests are denied.
- [ ] Complete Spotify PKCE authorization and confirm expected Spotify identity/scopes.
- [ ] Verify secret metadata changed without reading or exposing the secret value.
- [ ] Verify only the read-only auth-health workflow is dispatched.
- [ ] Pass two independent cloud auth-health runs after runner disposal.
- [ ] Verify health state becomes healthy and stale reauthorization status clears.
- [ ] Verify playlist lock/state/audit/snapshots and live playlist contents are unchanged.
- [ ] Verify one Spotify-dependent workflow is blocked before recovery and passes auth preflight after recovery.
- [ ] Test from phone and desktop with the user's PC otherwise off.

## Architecture decisions

- **Authentication Health Monitor:** scheduled and on-demand read-only verification, token refresh, secure rotation persistence, structured diagnosis and durable non-secret status.
- **Authorization Broker:** managed HTTPS owner-consent flow; Cloudflare Worker + SQLite Durable Object; dedicated GitHub App with only Actions: write and Secrets: write.
- **Recovery Coordinator:** routes each failure category to bounded automatic repair, deferred retry, configuration correction or owner consent.
- **Central Auth Gate:** shared preflight dependency for Spotify workflows. Design must account for concurrent Actions jobs and rotating refresh tokens; no naive per-job refresh fan-out.
- **Control plane separation:** GitHub issue commands are a separate remote operations interface. They are not the purpose of this auth workstream and must never bypass manager controls.

## Known risks and constraints

- A refresh token rejected with `invalid_grant` cannot be revived by refreshing again; owner consent is mandatory.
- A scheduled monitor against an invalid credential must report reauthorization-required and latch that state; subsequent scheduled runs skip until an explicit owner-triggered recovery attempt succeeds. The `pending` marker also blocks later scheduled runs if a runner exits before persisting its result. If previous run logs are unavailable/expired or cannot be inspected, the schedule fails closed and requires manual dispatch.
- Multiple concurrent refreshes can race when Spotify rotates refresh tokens. Single-flight/concurrency coordination is a prerequisite for broad preflight rollout.
- The broker's active-workflow checks reduce but do not eliminate races with newly started workflows; complete live testing in a quiet maintenance window.
- Cloudflare quotas/storage billing apply; no zero-cost/unlimited assumption.
- GitHub App private key belongs only in the broker's managed secret store. The broker App remains separate from the existing manager secret-writer App.
- No external account, app, secret, redirect URI or playlist may be changed without the required user-side setup/consent.

## Acceptance criteria

Complete only when SHIT can monitor authentication, automatically refresh and persist rotations, correctly classify and safely handle failures, request owner consent only when necessary, complete OAuth from phone or desktop, pass two independent read-only cloud checks, and gate Spotify-dependent work on verified health—without any authentication path changing playlists or bypassing existing safeguards.

## Next action

Add regression tests and workflow-level verification for the latch and scheduled skip behavior, then design the shared auth preflight before rolling the gate out to other Spotify workflows.
