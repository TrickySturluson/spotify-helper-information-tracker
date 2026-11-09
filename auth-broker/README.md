# SHIT Authentication Management & Recovery Broker

This Worker is SHIT's managed, owner-consented recovery path for Spotify authentication. It supports phone and desktop browsers equally; device type is not a system dependency. It is an authentication service only. It does not read or modify playlists.

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

Non-secret GitHub repository Actions variables (the deployment workflow maps these to the Worker runtime names using Wrangler `--var`):

- `CLOUDFLARE_ACCOUNT_ID`
- `BROKER_BASE_URL` (canonical HTTPS Worker origin)
- `BROKER_GH_APP_CLIENT_ID` (mapped to runtime `GITHUB_APP_CLIENT_ID`)
- `BROKER_GH_APP_ID` (mapped to runtime `GITHUB_APP_ID`)
- `BROKER_GH_APP_REDIRECT_URI` (mapped to runtime `GITHUB_APP_REDIRECT_URI`; exact Worker URL plus `/auth/github/callback`)
- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_REDIRECT_URI` (exact Worker URL plus `/spotify/callback`)

Do not create repository variables named `GITHUB_APP_CLIENT_ID`, `GITHUB_APP_ID`, or `GITHUB_APP_REDIRECT_URI` for this broker deployment; those are Worker runtime names populated by the workflow. The `BROKER_GH_APP_*` prefix keeps these settings distinct from the existing SHIT manager GitHub App configuration.

Worker secrets (set with Cloudflare's secret-management interface or Wrangler secrets; never commit them):

- GITHUB_APP_CLIENT_SECRET
- GITHUB_APP_PRIVATE_KEY

The dedicated broker GitHub App must be installed only on this repository. In the GitHub App settings UI, grant **Actions: Read and write** and **Secrets: Read and write**; GitHub's installation-token API represents these as `actions: write` and `secrets: write` (write includes the read operations the broker needs to list active workflow runs and fetch the repository secret public key). The broker requests only those two write-level permissions and only this repository. Keep it separate from the existing SHIT manager App, which remains Secrets: write only; do not widen that operational App's permissions. Use this same App's web authorization flow for owner identity; no separate GitHub OAuth App is needed. Do not grant Contents, Administration, Issues, or account-wide permissions.

## GitHub App and Spotify app setup

- Create a **dedicated broker GitHub App** separate from the existing SHIT manager secret-writer App. Set its user-authorization callback URL to the exact HTTPS Worker URL plus /auth/github/callback, enable the user authorization flow, and install it only on this repository. Grant only repository `Actions: write` and `Secrets: write`; do not broaden the existing manager App's permissions.
- Use the App's client ID/client secret for the browser web-authorization flow and App ID/private key for installation tokens. Do not enable automatic user authorization during installation; the broker starts the flow explicitly with state and PKCE.
- Register both exact HTTPS callback URLs in Spotify Developer Dashboard. Use the same Spotify app/client ID already used by SHIT. Do not configure a Spotify client secret for the public PKCE client.
- Use separate callback URLs for GitHub and Spotify as shown above.
- The Worker URL must be HTTPS. Do not use a preview URL that changes between deployments.

## Cloudflare Workers Builds configuration

This repository is a monorepo: the Worker project is in `auth-broker/`. The verified Cloudflare Workers Builds settings are:

- **Production root directory:** `/auth-broker`
- **Production build command:** empty
- **Production deploy command:** `npx wrangler deploy`
- **Preview root directory:** `/auth-broker`
- **Preview build command:** empty
- **Preview deploy command:** `npx wrangler preview`

The root directory must contain `wrangler.toml`, `package.json`, and `package-lock.json`. Wrangler resolves `main = "src/index.js"` relative to this project directory and uses the pinned Wrangler version from the package manifest. Do not add `--config auth-broker/wrangler.toml` when the build root is already `/auth-broker`; that would resolve the config path incorrectly.

The Wrangler config includes the required `previews` bindings for isolated Durable Object state and a separate preview rate-limit namespace. The Cloudflare Worker subdomain setting must also have **Preview URLs enabled**; the preview builds can succeed without producing a routable URL if `previews_enabled` is false. The production Worker URL and production settings are not changed by preview builds. The broker exposes a non-secret `GET /health` liveness endpoint; it deliberately does not report credentials or configuration values.

Workers Builds preview deployments and the owner-only `Deploy SHIT Auth Broker` workflow are separate paths. A successful preview/build check is not proof that the production Worker was deployed or that OAuth works. Production deployment and end-to-end authorization remain explicit acceptance gates.

## Deployment

From Cloudflare and GitHub dashboards (no local PC is required):

1. Use the pre-created Cloudflare Worker `shit-auth-broker` in the dashboard. The first Wrangler deployment then updates this existing Worker and applies the SQLite Durable Object migration.
2. Enable its `workers.dev` hostname and note the exact HTTPS URL.
3. Add these non-secret GitHub repository Actions variables: `CLOUDFLARE_ACCOUNT_ID`, `BROKER_BASE_URL`, `BROKER_GH_APP_CLIENT_ID`, `BROKER_GH_APP_ID`, `BROKER_GH_APP_REDIRECT_URI`, `SPOTIFY_CLIENT_ID`, and `SPOTIFY_REDIRECT_URI`. The callback URLs must use the exact `BROKER_BASE_URL` host and end in `/auth/github/callback` and `/spotify/callback` respectively.
4. Create a Cloudflare API token scoped to this existing Worker with the Workers product `Editor` permission. Creating a brand-new Worker by API requires broader `Admin`; pre-creating it allows the narrower existing-Worker permission. Add the token as GitHub Actions secret `CLOUDFLARE_API_TOKEN`.
5. Set the two Worker secrets `GITHUB_APP_CLIENT_SECRET` and `GITHUB_APP_PRIVATE_KEY` in Cloudflare. Keep the GitHub App private key and client secret out of GitHub repository files and out of this deployment workflow.
6. Run the owner-only `Deploy SHIT Auth Broker` workflow from the repository's Actions tab. It injects the repository variables into Wrangler and deploys the existing Worker plus its Durable Object migration; it does not contact Spotify or modify playlists.
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

Run `npm ci` and `npm test` in this directory. The manifest pins `libsodium-wrappers` 0.8.4 and Wrangler 4.158.0. The committed `package-lock.json` is installed with `npm ci`; owner-push CI regenerates and commits it only after the broker tests, high-severity audit and Wrangler dry-run all pass. The tests cover owner matching, scope enforcement, cookie parsing, HTML escaping, PKCE challenge generation, canonical-host enforcement, fail-closed workflow concurrency classification, transactional Durable Object replay/expiry, required runtime configuration, playlist-isolation boundaries, Spotify identity verification, one-time clean completion-page behavior, GitHub App JWT signature validation, OAuth provider exchange, encrypted GitHub secret publication and dispatch/persistence failure behavior. They are unit tests only; deployment, OAuth provider integration, GitHub secret publication and end-to-end mobile verification remain separate acceptance gates.

## Status

The broker source, automated security tests, and owner-only deployment workflow are in PR #185. The centralized Worker preview for code commit `828f3606b64c571837576378a45ab47f0d717057` completed successfully after correcting dependency discovery, preview configuration, and Cloudflare Preview URL routing. The automated broker tests passed, and a separate GitHub Actions smoke test made an HTTP request to the deployed preview's `/health` endpoint and verified `{ "status": "ok", "service": "shit-auth-broker" }`. This is preview-only: production deployment and live browser-based authorization have not been verified. Owner-reported provisioning is recorded in `project/goals/mobile-cloud-operation/README.md`; do not ask for secret values. Remaining gates:

- Verify the pre-created Cloudflare Worker's canonical `workers.dev` URL and configured secret names.
- Verify the dedicated broker GitHub App is installed only on this repository with Actions:write and Secrets:write.
- Verify the exact GitHub and Spotify callback URLs.
- Verify the required repository Actions variables and Cloudflare deployment token are configured.
- Verify the GitHub App client secret and private key exist as Cloudflare Worker secrets; never retrieve or disclose their values.
- Run the owner-only deployment workflow, then complete owner-consented OAuth from a phone or desktop browser and verify the read-only auth health check.

No Spotify refresh token has been replaced by this broker. Do not use it for live authorization until deployment and end-to-end acceptance checks above pass. The broker never unlocks or edits playlists.
