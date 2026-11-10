# Spotify Credential Consumer Inventory

**Status:** All nine inventoried Spotify workflow consumers have been migrated to broker-issued OIDC access tokens on `feature/oidc-broker-refresh-endpoint`. PR #188 latest code-bearing commit `4634c8ae41688665fb16efe9e4b9e3565265f7bb` passed exact-head CI and Cloudflare preview checks on 2026-11-10; the subsequent documentation-only sync `7721ae6b7e6f449253f1adce3e197b019032fecd` also passed (8 successful check runs, 1 skipped on each). PR #188 remains open as a draft and is not merged or deployed; `main` and the production Worker still use the legacy credential path. Live end-to-end validation remains pending.

This inventory is a migration control. The feature branch contains the encrypted credential store, owner-consented initialization/recovery, shared encrypted access-token cache, OIDC client, fail-closed manager mode, and workflow integrations. Read-only Cloudflare metadata confirms the encryption-key secret is present as `secret_text`, but the production `SPOTIFY_CREDENTIAL_STORE` binding/migration is absent. Production invocation logs are enabled with query-string redaction disabled; PR #188 now makes redaction explicit and verifies it after deployment. Do not retire the legacy GitHub Actions refresh-token secret until the branch is merged, the broker is deployed, all nine workflows are verified, and the owner approves cutover.

## All inventoried Spotify workflow consumers

| Workflow | Role | Feature-branch credential behavior | OIDC event policy |
|---|---|---|---|
| `.github/workflows/spotify-auth-health-check.yml` | Scheduled/manual auth health diagnosis | Direct OIDC client call; verifies `/v1/me`; only workflow permitted to request forced refresh after early 401 | `schedule`, `workflow_dispatch` |
| `.github/workflows/spotify-daily-live-preflight.yml` | Daily live preflight | Broker helper; manager is broker-only | `schedule`, `workflow_dispatch`, main push trigger |
| `.github/workflows/spotify-daily-midnight-cycle.yml` | Daily playlist cycle | Broker helper; manager is broker-only; Last.fm remains separate | `schedule`, `workflow_dispatch`, main push trigger |
| `.github/workflows/spotify-daily-feedback-observation.yml` | Daily feedback observation | Broker helper; no token-file seeding or secret rotation | `schedule`, `workflow_dispatch`, main push trigger |
| `.github/workflows/tricky-daily-snapshot-refresh.yml` | Daily snapshot refresh | Broker helper; read-only Spotify operations; no secret rotation | `schedule`, `workflow_dispatch`, main push trigger |
| `.github/workflows/spotify-reference-library.yml` | Spotify reference/library workflow | Broker helper; no token-file seeding or secret rotation | `schedule`, `workflow_dispatch`, main push trigger |
| `.github/workflows/spotify-playlist-manager.yml` | Owner-controlled cloud playlist manager | Broker helper; exact issue/comment workflow identity; existing owner gate and playlist safeguards retained | `issues`, `issue_comment` |
| `.github/workflows/great-migration.yml` | Library operations and daily provider verification | Broker helper in both Spotify-verification jobs; other provider keys remain independent | `schedule`, `workflow_dispatch`, owner issue event |
| `.github/workflows/update.yml` | General update workflow | Broker helper before Spotify Reference Library sync; Last.fm and metadata providers remain independent | `schedule`, `workflow_dispatch`, main push trigger |

## Centralization contract

- Every migrated job obtains a short-lived access token from `scripts/spotify/broker_access_token.py`, or uses the same helper directly in the auth-health workflow.
- The helper writes `SHIT_AUTH_MODE=broker` and the short-lived access token only to the runner's ephemeral `GITHUB_ENV`.
- The shared Spotify manager fails closed when `SHIT_AUTH_MODE=broker` is set but no broker token is present. It does not read a local refresh-token file or run local OAuth. When its short-lived token approaches expiry during a long job, it obtains a new OIDC broker token in-process; it never directly refreshes.
- The broker Durable Object encrypts the short-lived access token and caches it until expiry. Concurrent jobs wait for one refresh and reuse the cached result; they do not race rotating refresh tokens.
- A definite Spotify 429 persists a bounded Retry-After cooldown. An ambiguous provider outcome blocks refresh until owner-consented recovery.
- Only the exact auth-health workflow may request a forced refresh after an early 401. Playlist, Library, Daily, and migration workflows cannot bypass the shared access-token cache or provider cooldown.
- The broker allowlist contains exactly the nine workflow refs above, each pinned to `refs/heads/main`. The owner-only deployment workflow generates this exact list directly from its code; it is not a manually maintained repository variable. Wildcards, forks, pull-request refs, and arbitrary caller-supplied workflow identities are forbidden.
- `issues` events are accepted only for the exact Playlist Manager and Great Migration workflows. `issue_comment` is accepted only for the exact Playlist Manager workflow. Standard workflows accept only `push`, `schedule`, and `workflow_dispatch`.
- The broker GitHub App has repository-scoped Actions: Write only, for active-run inspection and auth-health dispatch. It no longer needs Secrets: Write.

## Migration rules and acceptance

1. Keep the deployed main-branch secret path intact until the broker has an initialized credential and the coordinated cutover is approved.
2. Do not run broker refresh against a production credential while legacy workflows are still active: rotating the broker-held token can invalidate a refresh token still held by an old workflow. Pause legacy schedules/in-flight jobs, initialize the broker store, and enable the broker-backed workflows as one coordinated cutover.
3. Preserve each workflow's playlist lock, preview/confirmation, snapshot, audit, state persistence, data publication, and rollback behavior.
4. Multi-job workflows must obtain a broker token in every job that makes Spotify requests. The encrypted access-token cache makes concurrent job requests share one refresh result.
5. Tests must reject direct `secrets.SPOTIFY_REFRESH_TOKEN` references, legacy token-file seeding, and secret-writer steps in the nine migrated workflows. Local interactive manager mode remains available outside broker-required workflow mode.
6. Test the exact OIDC identity and event rules, including issue/comment command workflows. Do not broaden the allowlist to accommodate test or feature branches.
7. Validate all nine workflows with CI and inspect the exact job logs for credential redaction, broker-only manager mode, and absence of refresh-token material.
8. Verify broker outage, 429 cooldown, concurrent refresh, early access-token 401 recovery, `invalid_grant`, identity mismatch, key rotation, key loss, and same-account owner reauthorization.
9. Obtain two independent successful read-only auth-health checks after deployment. Confirm no playlist locks, playlist contents, snapshots, Library data, or generated repository state changed as a side effect of authentication.
10. Retire the legacy GitHub Actions refresh-token secret only after the full acceptance sequence and explicit owner approval.

## Baseline and current boundary

The feature-branch workflow scan found no direct `SPOTIFY_REFRESH_TOKEN` references, secret-writer steps, or legacy token-file seeding in the nine migrated workflow files. This is source-branch evidence only; the default branch and production Worker remain unchanged until merge/deployment. Refresh this inventory whenever a Spotify workflow is added, renamed, split, or changed.
