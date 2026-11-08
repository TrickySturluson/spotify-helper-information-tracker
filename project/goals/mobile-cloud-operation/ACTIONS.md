# Mobile Cloud Operation & Spotify Reauthorization — Action Log

## 2026-11-08 — Initial baseline audit and architecture

**User authorization:** The user explicitly requested that ChatGPT be able to reauthorize Spotify and build a way to operate SHIT without depending on Codespaces.

### Source inspected

- .github/workflows/spotify-playlist-manager.yml
- .github/workflows/spotify-auth-health-check.yml
- scripts/spotify/spotify_playlist_manager.py
- scripts/spotify/spotify_playlist_cloud.py
- docs/SPOTIFY_API_OPERATIONS.md
- docs/WORKFLOWS.md
- project/NEXT_WORK.md, project/LOOSE_ENDS.md and project goal index.

### Verified findings

- The manager's authorize() implements Spotify Authorization Code with PKCE, creates an HTTP server bound to CALLBACK_HOST:8888, and writes the resulting token response to .spotify_playlist_token.json.
- The manager defaults to http://127.0.0.1:8888/callback; Codespaces recovery requires port forwarding and an exact forwarded HTTPS redirect URI.
- The cloud playlist-control workflow already runs remotely, is serialized, and executes the manager's command handler. It maintains snapshots/artifacts, state/audit persistence, and existing manager authorization checks.
- The cloud manager uses SPOTIFY_REFRESH_TOKEN from repository Actions Secrets. When Spotify rotates a refresh token, the manager persists the replacement through a narrowly scoped GitHub App token.
- The manual spotify-auth-health-check.yml workflow performs token refresh and GET /v1/me; it does not edit playlists. It can persist a rotated token.
- Playlist-control run [#42448656654](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42448656654) failed with Spotify invalid_grant. Repeated retries are not a recovery strategy.
- The connected GitHub integration does not expose an interactive Codespaces terminal or direct repository-secret values. A supported mobile flow needs a managed HTTPS callback service with server-side credential handling.

### Design decision proposed

A managed OAuth broker, with Cloudflare Workers as the leading candidate, can receive the Spotify PKCE callback from a phone browser, authenticate the GitHub owner, and write the refresh token directly to the repository secret using a repository-scoped GitHub App. After confirmed persistence it should dispatch only the existing read-only auth-health workflow.

The broker must not persist the Spotify refresh token, return it to browser/ChatGPT, create playlist commands, unlock playlists, or write playlist contents. A static GitHub Pages page is insufficient because it cannot safely hold the GitHub App private key or update Actions Secrets.

### Status

- Documentation and workstream plan drafted on branch feature/mobile-spotify-reauth-plan.
- No OAuth broker code has been deployed.
- No secrets, GitHub App permissions, Spotify developer settings, workflows, or playlists were changed.
- Buddy's latest recorded run is from 2026-11-07; today's run (2026-11-08 Eastern) is pending and has not been independently reviewed.
- Current next action: complete the infrastructure permission/redirect audit and implement the broker with automated tests.

### Follow-up security/deployment audit

- GitHub repository rulesets endpoint returned an empty list. The connected integration could not read branch protection (HTTP 403), so branch protection requirements remain unverified.
- No supported connector endpoint exposes GitHub App private-key values, installation secrets, or Spotify Developer Dashboard redirect configuration. Those values/settings must be checked in their respective dashboards without disclosing secret values.
- Added an initial Cloudflare Worker implementation, pinned package manifest, Durable Object/rate-limiter configuration template, and isolated Node security-test workflow on this branch. These are implementation-in-progress, not deployed or end-to-end verified.
- The broker's only intended GitHub side effects are updating the single `SPOTIFY_REFRESH_TOKEN` Actions secret and dispatching the read-only `spotify-auth-health-check.yml` workflow after the secret update succeeds. It does not have playlist endpoints or command-generation logic.
- Current PR CI: Daily curator tests passed on the documentation-only commit; public repository security scan was still in progress at the last check. The dedicated broker test workflow is expected to run for the implementation changes.
