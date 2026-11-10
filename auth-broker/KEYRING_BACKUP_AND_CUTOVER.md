# Keyring Backup and Production Cutover

## Purpose

This runbook defines the owner-controlled steps required before the central Spotify authentication broker can safely replace the legacy refresh-token secret path. The encryption keyring is the only way to decrypt credentials already stored in the broker Durable Object. Losing it makes those credentials unrecoverable.

This runbook does not authorize deployment or Spotify consent by itself. Production promotion remains an owner-only action.

## 1. Independently back up the encryption keyring

Before initializing the production credential store:

1. Locate the original keyring JSON used to provision the Cloudflare Worker secret `SPOTIFY_CREDENTIAL_ENCRYPTION_KEYS`.
2. Confirm the backup contains the same complete JSON keyring, including the active key version and every retained historical key version.
3. Store the backup in an encrypted password manager or encrypted offline backup that is independent of this Cloudflare account and this repository.
4. Confirm that the backup can be retrieved by the owner. Do not paste the key or keyring JSON into ChatGPT, GitHub issues, pull requests, workflow logs, or repository files.
5. Do not rotate, replace, or delete the Cloudflare secret during this verification.

The secret's presence in Cloudflare is not proof of a backup. The deployment workflow intentionally requires the owner to attest to the independent backup.

After completing these steps, set the repository Actions variable:

- `SPOTIFY_CREDENTIAL_KEY_BACKUP_CONFIRMED=true`

Set it to `true` only after the independent backup has been checked. If the backup is not ready, leave the variable unset or set it to `false`; production deployment will stop before publishing.

## 2. Verify owner-controlled configuration

Before dispatching production deployment, verify the following repository Actions variables are configured:

- `CLOUDFLARE_ACCOUNT_ID`
- `BROKER_BASE_URL` — canonical HTTPS origin, with no path or trailing slash
- `BROKER_GH_APP_CLIENT_ID`
- `BROKER_GH_APP_ID`
- `BROKER_GH_APP_REDIRECT_URI` — exactly `<BROKER_BASE_URL>/auth/github/callback`
- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_REDIRECT_URI` — exactly `<BROKER_BASE_URL>/spotify/callback`
- `SPOTIFY_CREDENTIAL_ACTIVE_KEY_VERSION` — defaults to `1` if unset
- `SPOTIFY_CREDENTIAL_KEY_BACKUP_CONFIRMED` — must be `true` after step 1

Verify these Worker secrets are present as Cloudflare `secret_text` bindings:

- `GITHUB_APP_CLIENT_SECRET`
- `GITHUB_APP_PRIVATE_KEY`
- `SPOTIFY_CREDENTIAL_ENCRYPTION_KEYS`

Never read a secret value merely to confirm its presence. The deployment preflight checks binding names and types without printing values.

The GitHub App must be installed on this repository with the Actions permission required to inspect workflow runs and dispatch the read-only auth-health workflow. Its client ID, App ID, private key, client secret, and callback URL must all belong to the same intended App.

Register the exact GitHub and Spotify callback URLs with their respective applications before attempting owner authorization.

## 3. Review and merge the broker implementation

1. Review PR #188 and its exact-head checks.
2. Confirm the PR is based on the intended repository history and has no unresolved review threads.
3. Merge only through the repository's normal owner-controlled review process. Do not force-push or rewrite the feature branch to catch up with unrelated mainline changes.
4. Confirm `main` contains the broker source, Durable Object migration, deployment workflow, all nine migrated workflow clients, and the updated tests.

A green branch preview is not a production deployment. The preview `/health` endpoint proves only that the Worker responds; it does not prove production bindings, secrets, credential persistence, or Spotify OAuth.

## 4. Deploy and verify readiness

From the default branch, the repository owner manually dispatches `.github/workflows/deploy-mobile-auth-broker.yml`.

The workflow must pass all preflight gates before deployment:

- Stable owner account ID check
- Independent key backup attestation
- Required non-secret variables and exact callback URL checks
- Required Cloudflare secret binding names and `secret_text` types

After deployment it verifies query-string redaction and polls `/ready`. Readiness must return HTTP 200 with `status: ready`. The readiness probe checks OAuth configuration, GitHub App private-key parseability, both rate limiters, OIDC allowlist, encryption keyring import, and the credential-store Durable Object. It does not create or read a Spotify credential.

If deployment or readiness fails, stop. Do not begin Spotify OAuth or remove legacy credentials. Inspect the fixed diagnostic stage and Worker configuration without exposing secret values.

## 5. Owner-consented Spotify authorization

Only after production readiness passes:

1. Ensure no Spotify-related GitHub Actions workflow is queued or running.
2. Open the canonical broker URL in a browser.
3. Sign in with the authorized GitHub owner account.
4. Complete Spotify PKCE consent for the intended Spotify account.
5. Confirm the broker verifies Spotify `/v1/me` and writes the refresh credential directly to the encrypted Durable Object.
6. Confirm the browser receives the accurate saved-state message and the read-only auth-health workflow is dispatched.

The broker does not unlock or edit playlists. The refresh token must never be returned to the browser, written to a GitHub Actions secret, or printed to logs.

## 6. Verify every consumer before retiring legacy auth

Keep the existing legacy refresh-token secret until all nine migrated workflows have passed broker-backed tests on `main` and live read-only verification:

1. Spotify auth-health check
2. Daily live preflight
3. Daily midnight cycle
4. Daily feedback observation
5. Daily snapshot refresh
6. Reference Library
7. Playlist manager
8. Great Migration
9. Update/enrichment workflow

Verify each workflow obtains only a short-lived access token through GitHub Actions OIDC, uses the expected repository/workflow identity, and preserves its existing locks, snapshots, audit records, rollback protections, and playlist side-effect rules.

Run at least two independent broker-backed read-only auth-health checks. Confirm refresh-token rotation, encrypted persistence, same-account recovery, cached access-token reuse, and fail-closed handling of interrupted or ambiguous refresh operations.

Only after those checks pass should the owner approve a separate change to retire the legacy credential path. Do not combine credential retirement with the initial broker deployment.

## 7. Rollback and recovery boundaries

- Keep the legacy refresh-token secret available until the new path is verified across all consumers.
- Do not delete or replace the encryption keyring while encrypted credential records exist.
- Rolling back Worker code does not roll back Durable Object data. Treat code rollback and credential-store recovery as separate operations.
- If a refresh outcome is ambiguous, the broker blocks automatic reuse of the old token and requires owner-consented same-account recovery.
- If a different Spotify account is presented, stop for separate owner review; never silently replace the stored identity.
- Preserve workflow snapshots, audit/state files, and existing playlist locks. The auth broker must not perform playlist writes.

## Current known blockers (2026-11-10)

- The production Worker still lacks the new credential-store Durable Object binding/migration and dedicated broker refresh rate limiter.
- Production query-string redaction is currently disabled and must be enabled by the guarded deployment before OAuth callbacks are used.
- The Cloudflare keyring secret exists, but its independent backup has not been verified.
- Production centralization and live Spotify OAuth have not been demonstrated. The PR preview has passed its non-secret health check only.
