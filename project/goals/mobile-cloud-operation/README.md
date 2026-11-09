# Centralized Authentication & Mobile Cloud Operation

## Purpose

Make SHIT operable from ChatGPT, phone, or desktop without requiring the user to open a local terminal, start a Codespace, or keep a personal computer online. The OAuth broker is a centralized SHIT authentication service; mobile is one convenient owner-facing entry point, not the feature boundary. GitHub remains the source of truth; GitHub Actions remains the controlled execution plane while the broker-owned credential/OIDC migration remains unfinished.

This workstream closes the first-time Spotify authorization gap. Existing playlist control already runs in GitHub Actions, and the manager already persists rotated refresh tokens through a narrowly scoped GitHub App token. Initial recovery still starts a local HTTP callback server on port 8888, writes a local token cache, and asks the user to copy the refresh token into GitHub Actions Secrets.

## User-facing target

From a mobile browser, the owner opens a trusted SHIT authorization page, authenticates as the expected GitHub owner, approves Spotify access, and finishes with the refresh token saved directly to the repository Actions secret. The page must never display, return, log, or ask the user to copy the token. After saving, the service starts a read-only cloud credential verification; it must not unlock or edit any playlist.

Codespaces and local checkouts become optional developer tools, not requirements for Spotify recovery or playlist operations.

## Verified baseline

- The playlist-control workflow is the remote issue-command control plane. It serializes commands and preserves manager state/audit, snapshots and explicit confirmation safeguards.
- The playlist manager uses Spotify Authorization Code with PKCE. Its callback server binds port 8888 and is tied to a local/Codespaces runtime.
- SPOTIFY_REFRESH_TOKEN is the cloud credential source of truth. Automatic refresh-token rotation is already persisted through a GitHub App token.
- The manual Spotify auth-health workflow performs a read-only authentication check and can persist a rotated token.
- Playlist-control run [#42448656654](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42448656654) and the post-documentation-fix read-only status run [#42458239670](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42458239670) both reached Spotify and were rejected with `invalid_grant`. Repeated retries cannot repair this credential; complete the mobile reauthorization path before any playlist operation.
- The GitHub connector can create owner-authored control issues as `TrickySturluson` and trigger the owner-gated workflow without Codespaces. Issue #178 first proved the identity/trigger path but hit a documentation test failure. After PR #179 restored the README and all 519 repository tests passed, issue #180 reached the manager; its read-only status command then failed only because Spotify rejected the stored refresh token.

## Proposed architecture

Use the existing Cloudflare Worker `shit-auth-broker` at `https://shit-auth-broker.trickysturluson.workers.dev` as a narrow managed HTTPS bridge between the owner-facing browser, Spotify PKCE, and GitHub Actions Secrets. It uses a SQLite-backed Durable Object for transactional one-time state. Broker source and tests were merged in PR #182; PR #189 aligns the Wrangler target and deployment documentation with the existing Worker. Production deployment and OAuth acceptance remain pending.

The broker must:

1. Require the dedicated broker GitHub App's user-authorization flow and accept only the repository owner account TrickySturluson.
2. Start Spotify Authorization Code with PKCE, store the verifier and one-time state server-side with a short TTL, and use an exact registered HTTPS redirect URI.
3. Validate state, session binding, expiry, callback errors, and required scopes.
4. Exchange the authorization code server-side. The refresh token must never reach browser JavaScript, HTML, a URL, ChatGPT, or logs.
5. Use a dedicated broker GitHub App, separate from the existing SHIT manager secret-writer App, with only repository Actions: write and Secrets: write. Narrow its short-lived installation token to this repository, encrypt and write only SPOTIFY_REFRESH_TOKEN, and keep the App private key only in the broker's managed secret store.
6. Dispatch only the existing read-only Spotify auth-health workflow after confirmed secret persistence.
7. Verify Spotify `/v1/me`, then redirect to a clean one-time completion URL that displays the Spotify account name/ID, status and a link to the verification run. Never return tokens, codes, verifiers, session tokens, private keys, or provider response bodies.
8. Use HTTPS, secure HttpOnly SameSite cookies, CSRF protection, origin validation, rate limits, bounded state/session TTLs, no third-party scripts, and redacted logs.
9. Fail closed if secret persistence cannot be confirmed.
10. Never call playlist modification endpoints or unlock playlists.

## Security boundaries

- The broker is SHIT's centralized owner-reauthorization entry point, not a second playlist manager. It currently writes only the `SPOTIFY_REFRESH_TOKEN` Actions secret; the in-progress broker-owned credential/OIDC work is a separate migration and must not be described as live until deployed and verified.
- The existing GitHub issue-command workflow is the mobile control plane for playlist operations. It accepts owner-authored JSON in an open issue titled `SHIT — Playlist Control`; ChatGPT can create/update the issue and inspect Actions runs through the GitHub connector. This was verified on 2026-11-08: issue #178 proved owner identity and trigger; after PR #179 merged, issue #180 reached the manager and executed the read-only status path until Spotify returned `invalid_grant`. See the action log. The user does not need Codespaces or a local terminal.
- GitHub identity and Spotify identity are distinct; verify both and report the authenticated Spotify account through the read-only workflow.
- Use PKCE; do not introduce a Spotify client secret if the app is a public client.
- Restrict the GitHub App to this repository. Request only Secrets: write and Actions: write for the broker; do not request Contents, Administration, or broad account permissions.
- Do not persist the Spotify refresh token in the broker's Durable Object state store after writing it to GitHub. Only short-lived PKCE/state/session records may be stored.
- Never put credentials in issue bodies/comments, workflow inputs, query strings, commits, artifacts, ChatGPT messages, browser storage, or logs.
- Preserve every existing playlist lock, ownership check, allowlist, blacklist, preview/confirmation, snapshot, audit, rollback and live read-back gate.
- OAuth completion must never trigger a playlist write.

## Deployment dependencies

Initial provisioning still requires owner configuration; routine reauthorization should then require only the owner to open the broker and approve the two identity/consent steps:

- A managed HTTPS runtime such as Cloudflare Workers.
- A dedicated repository-scoped GitHub App with minimal Secrets: write and Actions: write permissions, separate from the existing manager App.
- The dedicated broker GitHub App's user-authorization flow for owner authentication; no separate GitHub OAuth App is required.
- Exact HTTPS callback registration in Spotify Developer Dashboard.
- Runtime secrets for the GitHub App client secret and private key, plus non-secret App/client IDs.
- A deployment credential in GitHub Actions if deployment is automated.

Do not claim phone operation is available until the broker is deployed, secrets are configured, owner-only access is tested, OAuth completes, the GitHub secret is updated, and read-only verification succeeds.

## Non-goals

- Giving ChatGPT direct access to Spotify refresh tokens or GitHub secret values.
- Running an interactive terminal or remote desktop inside ChatGPT.
- Replacing GitHub Actions with an unrestricted always-on server.
- Browser-based playlist writes outside the SHIT manager.
- Removing explicit playlist unlock, preview, confirmation, backup, audit, or read-back gates.

## Resume instructions

Read ROADMAP.md and ACTIONS.md. Inspect the OAuth implementation, auth-health workflow, playlist-control workflow, GitHub App permissions, repository rules and Spotify redirect configuration before changing runtime code. Update the roadmap and action log in the same session. Never ask the user to paste a token into chat.
## Mobile issue-control workflow

The existing owner-only issue workflow already allows ChatGPT to operate SHIT from the ChatGPT mobile app without Codespaces:

- Exact issue title: `SHIT — Playlist Control`.
- The open issue body contains one exact JSON command object; sender must be `TrickySturluson`.
- The workflow runs remotely in GitHub Actions, serializes control commands, persists state/audit, and comments the result.
- The supported command list and procedure are documented in [OPERATIONS.md](OPERATIONS.md), added alongside the broker reconciliation for review.
- ChatGPT can use GitHub issue/file/workflow tools to prepare, stage, inspect and verify. It cannot access an interactive Codespaces terminal or read Actions secret values.
- Playlist mutations still require the manager's lock/unlock, preview, explicit confirmation, snapshot, audit and live read-back safeguards.

## Current implementation status

- PR #179 merged on 2026-11-08 (merge commit `e8aafcc`), restoring this required README. The updated repository test run passed all 519 tests; the full-history Gitleaks scan also passed.
- PR #181 was merged after explicit approval as `b0b280ff7b0b6d71fcbcf8fa3ded2d0b0f7b8a22`; it removed the three accidental scaffold files and recorded the verified control-channel status.
- The original broker PR #176 was 7 commits behind and divergent from the new `main`, so its source and tests have been copied to a fresh branch from current `main` rather than force-merging old history. The reconciled branch is `feature/mobile-spotify-reauth-reconciled`.
- The broker remains source-only and undeployed. Reconciled PR #182 passed 24 broker tests, dependency audit, Wrangler dry-run, 519 repository tests and full-history Gitleaks; see ACTIONS.md for exact runs. Any subsequent change requires fresh checks.
- No Cloudflare Worker, dedicated GitHub App, Spotify callback, Actions secret or playlist has been changed. Phone OAuth is not available until the external setup and end-to-end checks are complete.

## Latest mobile control verification — 2026-11-08

- PR #179 was merged after explicit owner approval. Merge commit: `e8aafccfa5465911d661bb128e13578ed312303b`.
- Its updated repository test workflow passed all 519 tests; its full-history Gitleaks scan passed.
- A new read-only `status` control issue (#180) was created by the GitHub connector as `TrickySturluson`, and the owner-gated workflow reached the manager. The manager's Spotify API preflight failed with `invalid_grant`; this confirms the stored refresh token is still expired/revoked/invalid after rotation. Do not repeat status or playlist commands until reauthorization succeeds.
- The workflow preserved a backup artifact and completed its state/audit persistence steps. No playlist mutation, unlock, or Spotify playlist write occurred. Issue #180 was closed after the run to prevent accidental retriggering.
- The broker is still undeployed and no Spotify secret was changed. Next steps remain: finish review and CI on the reconciled broker PR, obtain separate merge approval, complete the external Cloudflare/GitHub App/Spotify setup, authorize on phone, and pass read-only auth-health verification before any playlist write.
