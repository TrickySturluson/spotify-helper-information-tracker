# SHIT Mobile Spotify Authorization Broker

This Worker is the planned mobile replacement for the local port-8888 OAuth callback used by the Spotify playlist manager. It is an authentication bootstrap only. It does not read or modify playlists.

## Flow

1. The browser starts the GitHub App web authorization flow with PKCE and the broker verifies the returned GitHub identity is exactly the repository owner.
2. The broker creates a short-lived session and redirects to Spotify Authorization Code with PKCE.
3. The broker validates one-time OAuth state and session binding, exchanges the code server-side, and requires all scopes used by the existing SHIT manager.
4. The broker obtains a short-lived installation token from a GitHub App restricted to this repository. It checks for active Spotify-related Actions runs before replacing the credential and refuses to race an in-flight Spotify job.
5. The broker encrypts the Spotify refresh token using GitHub's repository Actions secret public key and updates only SPOTIFY_REFRESH_TOKEN.
6. Only after the secret update succeeds does it dispatch spotify-auth-health-check.yml. This workflow verifies authentication and does not edit playlists.
7. The browser receives only status and a link to the auth-health workflow. The refresh token is never returned or stored in the Durable Object state store.

## Required Worker bindings and configuration

The Worker declares a SQLite-backed Durable Object binding named OAUTH_STATE. Cloudflare creates its namespace through the first deployment migration; no separate KV namespace is needed. Configure the canonical Worker URL in BROKER_BASE_URL; requests arriving through a different host are rejected. Configure the rate-limiter binding AUTH_RATE_LIMITER as shown in wrangler.toml. Cloudflare's Worker rate-limit API is approximate and per location; it is an abuse throttle, not the owner-authentication or replay-protection boundary. Replace the canonical Worker host and both callback host placeholders before deployment.

Non-secret Worker variables:

- GITHUB_OWNER=TrickySturluson
- BROKER_BASE_URL (canonical HTTPS Worker origin)
- GITHUB_APP_CLIENT_ID
- GITHUB_APP_REDIRECT_URI (exact Worker URL plus /auth/github/callback)
- SPOTIFY_CLIENT_ID
- SPOTIFY_REDIRECT_URI (exact Worker URL plus /spotify/callback)
- GITHUB_APP_ID

Worker secrets (set with Cloudflare's secret-management interface or Wrangler secrets; never commit them):

- GITHUB_APP_CLIENT_SECRET
- GITHUB_APP_PRIVATE_KEY

The GitHub App must be installed only on this repository and grant only Actions: write and Secrets: write to the broker. The installation token request further narrows the token to this one repository and those two permissions. Use this same App's web authorization flow for owner identity; no separate GitHub OAuth App is needed. Do not grant Contents, Administration, Issues, or account-wide permissions.

## GitHub App and Spotify app setup

- Create one GitHub App, set its user-authorization callback URL to the exact HTTPS Worker URL plus /auth/github/callback, and install it only on this repository.
- Use the App's client ID/client secret for the browser web-authorization flow and App ID/private key for installation tokens. Do not enable automatic user authorization during installation; the broker starts the flow explicitly with state and PKCE.
- Register both exact HTTPS callback URLs in Spotify Developer Dashboard. Use the same Spotify app/client ID already used by SHIT. Do not configure a Spotify client secret for the public PKCE client.
- Use separate callback URLs for GitHub and Spotify as shown above.
- The Worker URL must be HTTPS. Do not use a preview URL that changes between deployments.

## Deployment

From a trusted development environment or Cloudflare's Git-connected deployment flow:

1. Create the Worker. Its SQLite-backed Durable Object namespace is created automatically by the Wrangler migration.
2. Replace the Worker host placeholders with the final HTTPS hostname.
3. Set the non-secret variables and Worker secrets listed above.
4. Deploy the Worker.
5. Register the exact Spotify callback URI and GitHub App user-authorization callback URI.
6. Open the Worker root URL on a phone and complete GitHub then Spotify authorization.
7. Confirm the repository Actions secret metadata has been updated without retrieving its value.
8. Confirm the triggered Spotify Auth Health Check succeeds. If automatic dispatch fails after secret storage, the page reports that the secret was saved and provides the workflow link for manual read-only verification.

## Security contract

- GitHub App user access tokens are used only in memory to verify the GitHub identity; they are not stored. Only short-lived state, PKCE verifier and session metadata are stored in the strongly consistent Durable Object.
- GitHub and Spotify state values, session IDs and PKCE verifiers are short-lived Durable Object records and are consumed transactionally on callback. Expired records are removed by the Durable Object alarm.
- The Spotify refresh token is held only in memory between token exchange and GitHub's encrypted secret update.
- No token, code, verifier, session ID, private key, request URL, or provider response body is logged or returned. Worker observability is explicitly disabled in Wrangler because OAuth callbacks carry authorization codes in query parameters.
- Cookies are Secure, HttpOnly, SameSite=Lax and host-only.
- Responses use no-store, no-referrer, frame-denial, content-type and CSP headers.
- GitHub secret persistence failure stops the flow; the broker does not claim success or dispatch verification.
- Verification dispatch failure is reported separately because the secret may already have been saved.
- OAuth completion never unlocks or edits a playlist. All playlist actions remain under the existing SHIT manager.

## Tests

Run `npm install` and `npm test` in this directory. These tests cover owner matching, scope enforcement, cookie parsing, HTML escaping, PKCE challenge generation, canonical-host enforcement, workflow concurrency classification, and transactional Durable Object replay/expiry behavior. They are unit tests only; deployment, OAuth provider integration, GitHub secret publication and end-to-end mobile verification remain separate acceptance gates.

## Status

The broker implementation is under development and is not deployed. Do not use it for live authorization until the full security review, tests, external app configuration and deployment verification are complete.
