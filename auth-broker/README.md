# SHIT Mobile Spotify Authorization Broker

This Worker is the planned mobile replacement for the local port-8888 OAuth callback used by the Spotify playlist manager. It is an authentication bootstrap only. It does not read or modify playlists.

## Flow

1. The browser starts the GitHub App web authorization flow with PKCE and the broker verifies the returned GitHub identity is exactly the repository owner.
2. The broker creates a short-lived session and redirects to Spotify Authorization Code with PKCE.
3. The broker validates one-time OAuth state and session binding, exchanges the code server-side, requires all scopes used by the existing SHIT manager, and verifies Spotify `/v1/me` before saving. The completion page displays the Spotify account name and ID so the owner can spot an account mix-up.
4. The broker obtains a short-lived installation token from a GitHub App restricted to this repository. It checks for active Spotify-related Actions runs before replacing the credential and refuses to race an in-flight Spotify job.
5. The broker encrypts the Spotify refresh token using GitHub's repository Actions secret public key and updates only SPOTIFY_REFRESH_TOKEN.
6. Only after the secret update succeeds does it dispatch spotify-auth-health-check.yml. This workflow verifies authentication and does not edit playlists.
7. The browser receives only status and a link to the auth-health workflow. The callback immediately redirects to a clean, one-time completion URL; only a short-lived non-secret account/status summary is stored in the Durable Object. The refresh token is never returned or stored in the Durable Object state store.

## Required Worker bindings and configuration

The Worker declares a SQLite-backed Durable Object binding named OAUTH_STATE. Cloudflare creates its namespace through the first deployment migration; no separate KV namespace is needed. SQLite-backed Durable Objects are currently available on Cloudflare's Free plan, with published daily read/write and storage limits; usage beyond included limits or plan changes may incur charges. See [Durable Objects limits](https://developers.cloudflare.com/durable-objects/platform/limits/) and [Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/). Configure the canonical Worker URL in BROKER_BASE_URL; requests arriving through a different host are rejected. Configure the rate-limiter binding AUTH_RATE_LIMITER as shown in wrangler.toml. Cloudflare's Worker rate-limit API is approximate and per location; it is an abuse throttle, not the owner-authentication or replay-protection boundary. Replace the canonical Worker host and both callback host placeholders before deployment.

Non-secret GitHub repository Actions variables (injected by the deployment workflow using Wrangler `--var`):

- BROKER_BASE_URL (canonical HTTPS Worker origin)
- GITHUB_APP_CLIENT_ID
- GITHUB_APP_REDIRECT_URI (exact Worker URL plus /auth/github/callback)
- SPOTIFY_CLIENT_ID
- SPOTIFY_REDIRECT_URI (exact Worker URL plus /spotify/callback)
- GITHUB_APP_ID

Worker secrets (set with Cloudflare's secret-management interface or Wrangler secrets; never commit them):

- GITHUB_APP_CLIENT_SECRET
- GITHUB_APP_PRIVATE_KEY

The dedicated broker GitHub App must be installed only on this repository and grant only Actions: write and Secrets: write. Keep it separate from the existing SHIT manager App, which is documented as Secrets: write only; do not widen that operational App's permissions. The installation token request further narrows the token to this one repository and those two permissions. Use this same App's web authorization flow for owner identity; no separate GitHub OAuth App is needed. Do not grant Contents, Administration, Issues, or account-wide permissions.

## GitHub App and Spotify app setup

- Create a **dedicated broker GitHub App** separate from the existing SHIT manager secret-writer App. Set its user-authorization callback URL to the exact HTTPS Worker URL plus /auth/github/callback, enable the user authorization flow, and install it only on this repository. Grant only repository `Actions: write` and `Secrets: write`; do not broaden the existing manager App's permissions.
- Use the App's client ID/client secret for the browser web-authorization flow and App ID/private key for installation tokens. Do not enable automatic user authorization during installation; the broker starts the flow explicitly with state and PKCE.
- Register both exact HTTPS callback URLs in Spotify Developer Dashboard. Use the same Spotify app/client ID already used by SHIT. Do not configure a Spotify client secret for the public PKCE client.
- Use separate callback URLs for GitHub and Spotify as shown above.
- The Worker URL must be HTTPS. Do not use a preview URL that changes between deployments.

## Deployment

From Cloudflare and GitHub dashboards (no local PC is required):

1. Use the existing Cloudflare Worker named `shit-auth-broker`; do not create a duplicate. The first Wrangler deployment then updates this existing Worker and applies the SQLite Durable Object migration.
2. Enable its `workers.dev` hostname and note the exact HTTPS URL.
3. Add these non-secret GitHub repository Actions variables: `CLOUDFLARE_ACCOUNT_ID`, `BROKER_BASE_URL`, `GITHUB_APP_CLIENT_ID`, `GITHUB_APP_ID`, `GITHUB_APP_REDIRECT_URI` and `SPOTIFY_CLIENT_ID`, `SPOTIFY_REDIRECT_URI`. The callback URLs must use the exact `BROKER_BASE_URL` host and end in `/auth/github/callback` and `/spotify/callback` respectively.
4. Create a Cloudflare API token scoped to this existing Worker with the Workers product `Editor` permission. Creating a brand-new Worker by API requires broader `Admin`; pre-creating it allows the narrower existing-Worker permission. Add the token as GitHub Actions secret `CLOUDFLARE_API_TOKEN`.
5. Set the two Worker secrets `GITHUB_APP_CLIENT_SECRET` and `GITHUB_APP_PRIVATE_KEY` in Cloudflare. Keep the GitHub App private key and client secret out of GitHub repository files and out of this deployment workflow.
6. Run the owner-only `Deploy SHIT Mobile Auth Broker` workflow from the repository's Actions tab. It injects the repository variables into Wrangler and deploys the existing Worker plus its Durable Object migration; it does not contact Spotify or modify playlists.
7. Register the exact Spotify callback URI and GitHub App user-authorization callback URI in their respective dashboards.
8. Open the Worker root URL on a phone and complete GitHub then Spotify authorization.
9. Confirm the repository Actions secret metadata has been updated without retrieving its value.
10. Confirm the triggered Spotify Auth Health Check succeeds. If automatic dispatch fails after secret storage, the page reports that the secret was saved and provides the workflow link for manual read-only verification.

## Security contract

- GitHub App user access tokens are used only in memory to verify the GitHub identity; they are not stored. Only short-lived state, PKCE verifier and session metadata are stored in the strongly consistent Durable Object.
- GitHub and Spotify state values, session IDs and PKCE verifiers are short-lived Durable Object records and are consumed transactionally on callback. Expired records are removed by the Durable Object alarm. The final completion summary is also one-time and contains only the Spotify account display name/ID and whether the read-only workflow dispatch started.
- The Spotify callback redirects away from the query string containing the one-time authorization code before displaying the result.
- The Spotify refresh token is held only in memory between token exchange and GitHub's encrypted secret update.
- No token, code, verifier, session ID, private key, request URL, or provider response body is logged or returned. Worker observability is explicitly disabled in Wrangler because OAuth callbacks carry authorization codes in query parameters.
- Cookies are Secure, HttpOnly, SameSite=Lax and host-only.
- Responses use no-store, no-referrer, frame-denial, content-type and CSP headers.
- GitHub secret persistence failure stops the flow; the broker does not claim success or dispatch verification.
- Verification dispatch failure is reported separately because the secret may already have been saved.
- OAuth completion never unlocks or edits a playlist. All playlist actions remain under the existing SHIT manager.

## Tests

Run `npm ci` and `npm test` in this directory. The manifest pins `libsodium-wrappers` 0.8.4 and Wrangler 4.158.0. The committed `package-lock.json` is installed with `npm ci`; owner-push CI regenerates and commits it only after the broker tests, high-severity audit and Wrangler dry-run all pass. These 24 tests cover owner matching, scope enforcement, cookie parsing, HTML escaping, PKCE challenge generation, canonical-host enforcement, fail-closed workflow concurrency classification, transactional Durable Object replay/expiry, required runtime configuration, playlist-isolation boundaries, Spotify identity verification, one-time clean completion-page behavior, GitHub App JWT signature validation, OAuth provider exchange, encrypted GitHub secret publication and dispatch/persistence failure behavior. They are unit tests only; deployment, OAuth provider integration, GitHub secret publication and end-to-end mobile verification remain separate acceptance gates.

## Status

The broker source, automated security tests, and owner-only deployment workflow are merged to `main`. The existing Worker is named `shit-auth-broker`; live deployment and authorization still require the external configuration and verification steps below. Deployment is blocked on external account provisioning, not unfinished broker code:

- Create the Cloudflare Worker and configure its canonical `workers.dev` URL.
- Create and install the dedicated broker GitHub App with only repository Actions:write and Secrets:write.
- Register the exact GitHub and Spotify callback URLs.
- Add the required repository Actions variables and the Cloudflare deployment token.
- Set the GitHub App client secret and private key as Cloudflare Worker secrets.
- Run the owner-only deployment workflow, then complete mobile OAuth and verify the read-only auth health check.

No Spotify refresh token has been replaced by this broker until its OAuth flow succeeds. Do not use it for live authorization until deployment and the end-to-end acceptance checks above pass. The broker never unlocks or edits playlists.
