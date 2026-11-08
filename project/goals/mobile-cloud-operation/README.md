# Mobile Cloud Operation & Spotify Reauthorization

## Purpose

Make SHIT operable from ChatGPT and a phone without requiring the user to open a local terminal, start a Codespace, or keep a personal computer online. GitHub remains the source of truth; GitHub Actions remains the controlled execution plane.

This workstream closes the first-time Spotify authorization gap. Existing playlist control already runs in GitHub Actions, and the manager already persists rotated refresh tokens through a narrowly scoped GitHub App token. Initial recovery still starts a local HTTP callback server on port 8888, writes a local token cache, and asks the user to copy the refresh token into GitHub Actions Secrets.

## User-facing target

From a mobile browser, the owner opens a trusted SHIT authorization page, authenticates as the expected GitHub owner, approves Spotify access, and finishes with the refresh token saved directly to the repository Actions secret. The page must never display, return, log, or ask the user to copy the token. After saving, the service starts a read-only cloud credential verification; it must not unlock or edit any playlist.

Codespaces and local checkouts become optional developer tools, not requirements for Spotify recovery or playlist operations.

## Verified baseline

- The playlist-control workflow is the remote issue-command control plane. It serializes commands and preserves manager state/audit, snapshots and explicit confirmation safeguards.
- The playlist manager uses Spotify Authorization Code with PKCE. Its callback server binds port 8888 and is tied to a local/Codespaces runtime.
- SPOTIFY_REFRESH_TOKEN is the cloud credential source of truth. Automatic refresh-token rotation is already persisted through a GitHub App token.
- The manual Spotify auth-health workflow performs a read-only authentication check and can persist a rotated token.
- Playlist-control run [#42448656654](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42448656654) failed because Spotify rejected the stored credential with invalid_grant. Repeated retries cannot repair it.
- The GitHub connector does not provide an interactive Codespaces terminal or direct Actions-secret access to ChatGPT.

## Proposed architecture

Use a small managed HTTPS OAuth broker, deployed from this repository, as a narrow bridge between the phone browser, Spotify PKCE, and GitHub Actions Secrets. Cloudflare Workers is the leading candidate, subject to deployment/security validation.

The broker must:

1. Require GitHub authentication and accept only the repository owner account TrickySturluson.
2. Start Spotify Authorization Code with PKCE, store the verifier and one-time state server-side with a short TTL, and use an exact registered HTTPS redirect URI.
3. Validate state, session binding, expiry, callback errors, and required scopes.
4. Exchange the authorization code server-side. The refresh token must never reach browser JavaScript, HTML, a URL, ChatGPT, or logs.
5. Use a repository-scoped GitHub App installation token to encrypt and write only SPOTIFY_REFRESH_TOKEN to repository Actions Secrets. Keep the App private key only in the broker's managed secret store.
6. Dispatch only the existing read-only Spotify auth-health workflow after confirmed secret persistence.
7. Return only status and a link to the verification run. Never return tokens, codes, verifiers, session tokens, private keys, or provider response bodies.
8. Use HTTPS, secure HttpOnly SameSite cookies, CSRF protection, origin validation, rate limits, bounded state/session TTLs, no third-party scripts, and redacted logs.
9. Fail closed if secret persistence cannot be confirmed.
10. Never call playlist modification endpoints or unlock playlists.

## Security boundaries

- The broker is an authentication bootstrap, not a second playlist manager.
- GitHub identity and Spotify identity are distinct; verify both and report the authenticated Spotify account through the read-only workflow.
- Use PKCE; do not introduce a Spotify client secret if the app is a public client.
- Restrict the GitHub App to this repository. Request only Secrets: write and Actions: write for the broker; do not request Contents, Administration, or broad account permissions.
- Do not persist the Spotify refresh token in the broker's Durable Object state store after writing it to GitHub. Only short-lived PKCE/state/session records may be stored.
- Never put credentials in issue bodies/comments, workflow inputs, query strings, commits, artifacts, ChatGPT messages, browser storage, or logs.
- Preserve every existing playlist lock, ownership check, allowlist, blacklist, preview/confirmation, snapshot, audit, rollback and live read-back gate.
- OAuth completion must never trigger a playlist write.

## Deployment dependencies

A phone-only setup after initial infrastructure bootstrap still requires owner configuration:

- A managed HTTPS runtime such as Cloudflare Workers.
- A repository-scoped GitHub App with minimal Secrets: write and Actions: write permissions.
- The same repository-scoped GitHub App's web authorization flow for owner authentication; no separate OAuth App is required.
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