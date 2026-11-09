# Authentication Management & Recovery — Action Log

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


## 2026-11-08 — Broker implementation and security hardening

- Added `auth-broker/src/index.js`, pinned package manifest, Wrangler config, README, unit tests, and owner-triggered Cloudflare deployment workflow. The broker is source code only; it is not deployed.
- Replaced the initial Workers KV design with a SQLite-backed Durable Object. Its strongly consistent transactional storage atomically consumes GitHub/Spotify OAuth state, binds Spotify state to the current session, rejects replay/superseded callbacks, and cleans expired records with an alarm. Cloudflare documents SQLite Durable Objects as available on Free and Paid plans, with plan quotas/storage billing applying: https://developers.cloudflare.com/durable-objects/.
- Consolidated GitHub owner authentication into the same dedicated repository-scoped GitHub App's web authorization flow with PKCE; no separate GitHub OAuth App is required. The App's client ID/client secret are distinct from its numeric App ID/private key. GitHub's current documentation supports PKCE for the GitHub App web flow: https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-user-access-token-for-a-github-app.
- GitHub permission design is grounded in the REST docs: repository secret publication requires `Secrets: write`, while workflow dispatch requires `Actions: write`; the broker requests only those two permissions and scopes the installation token to this repository. References: https://docs.github.com/en/rest/actions/secrets and https://docs.github.com/en/rest/actions/workflows.
- Added three preflight checks for active Spotify-related Actions runs (before Spotify consent, before exchanging the authorization code, and before secret publication). This reduces races but is not an atomic lock against a new workflow starting between checks; final authorization must be tested in a quiet maintenance window.
- Cloudflare Worker rate-limiting bindings are approximate and per-location, not strict global limits; this is only an abuse throttle, not the authentication/replay boundary: https://developers.cloudflare.com/workers/runtime-apis/bindings/rate-limit/.
- Broker unit tests and Wrangler bundle/config dry-run both passed in run #42450723671 (the run checked out the complete broker source and config); GitHub App PKCE owner flow tests passed in #42450626017; earlier Durable Object transaction/replay tests passed in #42450572672 and #42450564312.
- Daily curator tests and workflow-catalogue contract passed in run #42450186954 after adding the two new workflows to the catalogue. Public repository security scan passed in #42450186937 on that earlier commit; a final security scan after all source changes remains to be checked.
- The PR remains #176; no secrets, external account settings, Spotify redirect registrations, GitHub App installations, live OAuth sessions, or playlists have been changed.

- After switching Cloudflare rate-limit keys from client IPs to per-session (post-login) and route-wide (pre-login) identifiers, broker unit tests and Wrangler dry-run passed again in run #42450832707. This avoids false throttling for users behind shared mobile carrier IPs. The latest full-history Gitleaks scan is running as #42450865632.


## 2026-11-08 — Branch-targeting correction

- Detected that three file updates had landed on `main` rather than the feature branch: `auth-broker/README.md`, `auth-broker/src/index.js`, and `auth-broker/wrangler.toml`. No Worker deployment, OAuth credential, GitHub secret, permission change, Spotify setting or playlist operation resulted.
- Opened corrective revert PR [#177](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/177), deleting only those three files from `main`. PR #177 is mergeable; it has not been merged. Owner should merge #177 before the full operational PR #176 is reconciled/rechecked.
- Full-history Gitleaks scan passed on the complete broker source/configuration branch in run [#42450865632](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42450865632). Broker unit tests and Wrangler dry-run passed in [#42450832707](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42450832707).
- PR #176 remains open and not currently mergeable while `main` contains the three prematurely published files. Do not merge #176 until PR #177 is merged and #176 is refreshed/reconciled.


## 2026-11-08 — Concurrency gate and deployment configuration hardening

- Audited the branch's full workflow inventory. The initial classifier could miss active Spotify-using workflows whose filenames did not contain the word Spotify, and it failed open for missing workflow paths.
- Replaced that classifier with a fail-closed allowlist: only six explicitly audited non-Spotify workflows may overlap OAuth; every other or unknown workflow path blocks authorization. Added tests for Spotify playlist, preview, migration and auth workflows plus safe CI/deployment workflows.
- Added the required canonical HTTPS BROKER_BASE_URL to wrangler.toml. Without this value, the Worker would reject all requests; the new configuration test asserts every required public runtime variable is declared.
- Latest changes are on feature/mobile-spotify-reauth-plan. Broker unit tests and Wrangler dry-run were passing on the preceding commit; new classifier/config tests are running now. No deployment or external configuration changes have occurred.


## 2026-11-08 — Cloudflare deployment least-privilege review

- Updated the deployment guide to pre-create the Worker in the Cloudflare dashboard, then deploy updates to that existing Worker. Cloudflare's current Workers authorization guide says deploying an existing Worker needs Workers Editor, while creating a new Worker through Wrangler needs Workers Admin; pre-creation avoids granting Admin to the CI token. Source: https://developers.cloudflare.com/workers/authorization/.
- Cloudflare currently documents SQLite-backed Durable Objects as available on Free and Paid plans. Free-tier limits include 5 million row reads/day, 100,000 row writes/day and 5 GB SQLite storage; usage beyond included allocations may incur charges. Sources: https://developers.cloudflare.com/durable-objects/platform/limits/ and https://developers.cloudflare.com/workers/platform/pricing/.
- Deployment remains disabled until the Worker exists and the user configures a Worker-scoped Cloudflare API token, repository secret CLOUDFLARE_API_TOKEN, repository variable CLOUDFLARE_ACCOUNT_ID, GitHub App secrets in Cloudflare, and exact callback URLs. No Cloudflare account or external setting has been changed.


## 2026-11-08 — Preserve existing SHIT GitHub App permissions

- Inspected the existing Spotify operations guide: the current SHIT manager App is documented as repository-scoped with `Secrets: write` only, used to persist Spotify refresh-token rotations.
- Kept that App unchanged. The mobile broker requires workflow dispatch as well as secret publication, so it will use a separate dedicated broker App with only repository `Actions: write` and `Secrets: write`. This avoids silently broadening the existing operational credential.
- Updated broker setup instructions and roadmap to make the separation explicit. No App, permission, installation, repository secret or external setting has been changed.


## 2026-11-08 — Spotify account identity preflight

- Added a server-side Spotify `GET /v1/me` check immediately after the authorization-code exchange and before writing the refresh token to GitHub. If Spotify identity cannot be verified, secret persistence stops.
- The completion page now displays the authenticated Spotify display name and account ID, allowing the owner to notice if the wrong Spotify account was authorized. No identity is stored in the broker's Durable Object.
- Added unit tests for successful identity retrieval and fail-closed handling of HTTP errors/missing IDs. Updated broker guide and roadmap.


## 2026-11-08 — OAuth callback URL cleanup

- Changed the Spotify callback to redirect immediately to a clean completion URL after the code is exchanged and the secret is saved. The one-time authorization code/state no longer remains in the final browser address bar.
- The completion URL uses a random one-time handle to retrieve a 120-second Durable Object record containing only the Spotify account identity and verification-dispatch status. The record is consumed on first display; it contains no access or refresh token.
- Added tests for completion identity rendering, expiry/replay rejection and one-time consumption. Updated the broker security guide. OAuth code exchange, GitHub secret update and workflow dispatch remain unchanged.


## 2026-11-08 — GitHub App signing test

- Added a cryptographic unit test that generates a temporary RSA keypair, builds a GitHub App JWT using the same PKCS#1 PEM conversion path as production, and verifies the RS256 signature with the public key. The generated key is test-only and never persisted.
- This specifically tests the private-key parsing/signing code rather than relying only on Wrangler bundle validation. Test run is pending on the latest feature-branch commit.


## 2026-11-08 — Restore the mobile-operation documentation contract

- Created PR [#179](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/179) to restore the required goal README after the owner-authored read-only control test (#178) reached the workflow but failed the repository documentation contract. The original failure was the missing `project/goals/mobile-cloud-operation/README.md` on `main`.
- PR #179's first CI run confirmed the README requirement was repaired and all pre-test checks passed, but the 519-test suite found one remaining broken local link: `OPERATIONS.md` is present on the broker feature branch/PR #176, not on `main` yet.
- Corrected the README to describe the guide's actual branch/PR status without creating a broken local link. The follow-up test run must pass before PR #179 is considered merge-ready.
- The full-history Gitleaks check passed on PR #179. No runtime code, credentials, workflow permissions, OAuth settings, playlist locks, snapshots, or playlists were changed.
- PR #179 remains unmerged pending owner approval. Do not merge automatically.


## 2026-11-08 — PR #179 merged; read-only control path retested

- After the owner explicitly approved merge once the security scan passed, merged PR [#179](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/179) as `e8aafccfa5465911d661bb128e13578ed312303b`. The updated 519-test repository suite passed and the full-history Gitleaks scan passed.
- Created owner-authored read-only `status` issue [#180](https://github.com/TrickySturluson/spotify-helper-information-tracker/issues/180). The issue was authored as `TrickySturluson` and triggered the owner-gated workflow [#42458239670](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42458239670). The control channel and test gate are now both proven.
- The manager then attempted Spotify authentication and received `invalid_grant`. This is the known stale/revoked refresh-token blocker. No further Spotify API or playlist-control retries should be made until reauthorization succeeds.
- Workflow backup artifact [#13607684091](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42458239670/artifacts/13607684091) was successfully uploaded; snapshot preservation and state/audit persistence steps completed. No playlist write or unlock occurred. Issue #180 was closed to prevent accidental rerun.
- The old PR #177 branch is now behind/diverged from `main` because #179 merged. Created a fresh cleanup branch `fix/mobile-auth-main-cleanup-and-status-docs` from current `main`, removed only the three accidentally published scaffold files (`auth-broker/README.md`, `auth-broker/src/index.js`, `auth-broker/wrangler.toml`), and updated this goal's README with verified status. This will replace stale PR #177; it is not yet merged.
- PR #176 remains unmerged. Its latest reviewed feature-branch head passed lockfile, test and Gitleaks checks, but must be reconciled with current `main` after the cleanup PR is accepted. No Worker deployment, GitHub App setting, Spotify callback or Actions secret has been changed.


## 2026-11-08 — PR #181 merged; broker branch reconciled from current main

- After explicit owner approval, merged PR [#181](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/181) as `b0b280ff7b0b6d71fcbcf8fa3ded2d0b0f7b8a22`. Both checks passed on its exact head: repository tests 519/519 and full-history Gitleaks. The cleanup removed only the three unreviewed scaffold files and updated the mobile-operation status record. No Spotify or playlist side effects occurred.
- The original broker PR #176 was still 7 commits behind and divergent from the merged `main`. Rather than force-update or merge old history, created `feature/mobile-spotify-reauth-reconciled` directly from the new main commit and copied the reviewed broker source, pinned package/lock files, unit tests, Wrangler config, deployment/test workflows, and the `OPERATIONS.md` guide.
- Updated the broker test workflow's owner-only lockfile-commit branch guard to the reconciled branch name. Expanded the public-repository Gitleaks workflow to scan `feature/**` pushes as well as `main` and pull requests.
- Kept the current-main mobile README/ACTIONS/ROADMAP history instead of importing stale feature-branch versions. Updated the README to identify the reconciliation branch and the still-pending external setup.
- No Worker deployment, Cloudflare account change, GitHub App creation/permission change, Spotify callback change, Actions secret update, playlist unlock or playlist write occurred. The saved Spotify credential remains blocked by the previously verified `invalid_grant`; do not rerun auth/playlist control until reauthorization is completed.
- Next: inspect the reconciled diff and rerun broker tests, dependency audit, Wrangler dry-run, repository tests and full-history Gitleaks. Keep PR merge approval separate from the user's approval to merge PR #181.


## 2026-11-08 — Reconciled broker CI passed on PR #182

- PR [#182](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/182) is based directly on current `main` commit `b0b280ff7b0b6d71fcbcf8fa3ded2d0b0f7b8a22`; its verified head for this run was `e2b941180bf3b187ed13dc6f3a7d2d20e88afcd6` (19 commits ahead, 0 behind; GitHub reports mergeable/clean).
- Broker CI run [#42460672005](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42460672005) passed: `npm audit --audit-level=high`, 24/24 broker security tests, and Wrangler `--dry-run` bundle/config validation. No deployment occurred.
- Repository suite [#42460671975](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42460671975) passed all 519 tests, including the documentation contract, after compile/data/library checks.
- Full-history Gitleaks passed on the PR run [#42460671996](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42460671996) and feature-push run [#42460668354](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42460668354). Each scanned 3,396 commits / about 815.6 MB and reported no leaks.
- The broker lockfile job succeeded/skipped without changing the committed lockfile. All checks above apply to head `e2b9411`; any later commit requires fresh checks.
- PR #182 is still unmerged and awaits separate explicit owner approval. No Worker deployment, Cloudflare/GitHub App configuration, Spotify OAuth, Actions secret update, playlist unlock or playlist write occurred. The saved Spotify refresh token remains rejected with `invalid_grant` until mobile reauthorization is completed.


## 2026-11-08 — Reframe as SHIT-wide Authentication Management & Recovery

- User clarified that this is not merely a mobile feature: SHIT must monitor Spotify authentication health, automatically repair what can be repaired, and request owner consent only when Spotify requires it.
- Renamed the workstream conceptually to **Authentication Management & Recovery**. Phone and desktop are supported clients, not the purpose of the project. GitHub issue-based mobile operation remains a separate control-plane capability.
- Reworked the scope around three components: Authentication Health Monitor, Authorization Broker, and Recovery Coordinator; added a future Central Auth Gate milestone for Spotify-dependent workflows.
- Defined distinct states for healthy, reauthorization-required, rate-limited, provider-unavailable, configuration-error, identity-mismatch, secret-persistence-failed and verification-pending.
- Preserved hard boundaries: no retries of `invalid_grant`; honor Retry-After; do not confuse 429/5xx/network faults with revoked credentials; never expose tokens; no auth recovery path may unlock or modify playlists.
- Confirmed current workflow baseline: `spotify-auth-health-check.yml` is manual-only today, performs token refresh plus `GET /v1/me`, and can persist refresh-token rotation through a narrowly scoped GitHub App. It does not currently provide scheduled monitoring or a durable structured health state.
- Confirmed the broker is not deployed and no fresh Spotify consent has occurred. Existing credential remains blocked by the previously observed `invalid_grant`; no further Spotify status/playlist retries should be attempted until reauthorization.
- Created branch `feature/authentication-management-recovery` from current `main` for this work. No merge, deployment, external account changes, secret changes, OAuth, or playlist operations were performed.
- Next implementation: add conservative scheduled health monitoring and structured failure classification, test rotation/error paths, then design the shared auth preflight to avoid concurrent refresh-token races.


## 2026-11-08 — First scheduled Authentication Health Monitor implementation

- Updated `.github/workflows/spotify-auth-health-check.yml` to run daily at 09:00 UTC as well as on manual dispatch. The workflow remains serialized and makes one refresh attempt per run.
- Added redacted outcome categories: `reauthorization_required` for `invalid_grant`, `rate_limited` with Retry-After, `provider_unavailable` for 5xx/network failures, `configuration_error`, `scope_or_identity_error`, `identity_error`, `provider_error`, `secret_persistence_failed`, and `healthy`.
- The monitor never logs provider response bodies, access tokens or refresh tokens. It masks returned tokens and persists a rotated refresh token only after successful `GET /v1/me` verification.
- No retry loop was added. In particular, the same `invalid_grant` credential is never retried by the workflow; it reports that owner-consented reauthorization is required. Rate limits are reported with Retry-After rather than retried.
- Updated `docs/WORKFLOWS.md`, the goal README and roadmap to reflect the new schedule and current implementation status.
- This change is on `feature/authentication-management-recovery`; it has not yet been validated by GitHub Actions. The workflow's scheduled trigger is not an auth-recovery mechanism for a revoked grant; the broker and owner consent remain required.
- No Spotify request, OAuth, Actions secret change, Cloudflare deployment, playlist operation, Library write or other provider operation was performed in this session.
- Next: validate workflow syntax and behavior, add regression coverage for status classification/redaction/rotation failure, and then design a concurrency-safe shared auth preflight for Spotify-dependent workflows.


## 2026-11-08 — Safety correction: defer scheduled retries until invalid-grant latch exists

- A design review found that a daily schedule would retry the same refresh token after `invalid_grant`, contradicting the no-futile-retry invariant. A schedule alone is not safe monitoring.
- Removed the scheduled trigger. The auth-health workflow remains manual-dispatch only until a durable reauthorization-required latch can make subsequent scheduled runs skip automatically.
- Updated the workflow catalogue, README and roadmap to make this prerequisite explicit.
- The durable latch must be cleared only by a deliberate recovery attempt or confirmed replacement credential; transient 429/5xx/network failures must remain separately classified and eligible for bounded retry after their cooldown.
- This is a deliberate safety gate, not a retreat from automatic monitoring. It prevents SHIT from repeatedly sending a known-invalid credential while the recovery coordinator is still being built.


## 2026-11-08 — Durable auth-state latch enables safe scheduled monitoring

- Added a daily 09:00 UTC schedule back after implementing a durable non-secret repository variable, `SPOTIFY_AUTH_STATE`.
- Every manual or scheduled run writes `pending` before contacting Spotify. If the runner exits unexpectedly or cannot persist a result, the next scheduled run sees the unresolved state and fails closed rather than sending the same credential again.
- Scheduled runs proceed only when the prior state is absent, `healthy`, or a retryable provider/rate-limit state. Permanent blockers and unknown states pause the schedule. Manual dispatch bypasses the latch, writes `pending`, and allows an owner-directed recovery attempt.
- Every classified result is persisted to `SPOTIFY_AUTH_STATE`; only a verified `healthy` run clears a previous blocker. State-write failure fails the run and leaves `pending`.
- The health workflow now requests `variables: write` for its own `GITHUB_TOKEN` to manage this non-secret status. The existing manager GitHub App remains unchanged and retains only its existing Secrets:write purpose; the broker App remains separate.
- Updated the workflow catalogue and roadmap. The scheduled monitor still needs CI/source review and a live dry-run strategy; do not dispatch it against the known-invalid credential just to test the latch.
- Remaining safety nuance: rate-limit retry eligibility must eventually be tied to the actual Retry-After deadline, not merely the next daily run. Add this before broad production reliance.


## 2026-11-08 — Replace repository-variable latch with read-only run-history latch

- Corrected the initial latch design after checking GitHub's current workflow-token permission model: `variables` is not an available `GITHUB_TOKEN` permission. Do not ship a workflow that declares unsupported `variables: write`.
- Removed all repository-variable reads/writes and the proposed `SPOTIFY_AUTH_STATE` variable. The workflow now uses only `contents: read` and `actions: read` for its own `GITHUB_TOKEN`; the existing GitHub App token remains limited to Secrets:write for refresh-token rotation.
- Scheduled runs inspect the most recent completed auth-health run's logs for fixed, non-secret `AUTH_HEALTH_STATUS` and optional `AUTH_HEALTH_RETRY_AFTER` markers. Permanent blockers, unknown states, pending/interrupted runs, and unavailable logs fail closed. Manual dispatch bypasses the prior status latch and records a new pending marker.
- A 429 marker carries an absolute Retry-After deadline; scheduled runs skip until that deadline has elapsed. Missing/unparseable Retry-After is fail-closed until manual dispatch.
- Every health outcome emits a status marker; the workflow never writes repository contents, variables, or playlist state.
- This latch depends on GitHub Actions run-log retention. If the previous run's logs have expired or cannot be inspected, scheduled checks stop and require a manual dispatch rather than assuming health.
- The earlier same-date note describing a repository-variable latch is superseded by this entry. No variable was created or changed, no Spotify request was made, and no secret or playlist was touched.


## 2026-11-08 — Spotify workflow inventory and refresh-token concurrency audit

- Searched the repository workflow sources for `SPOTIFY_REFRESH_TOKEN` and inspected the nine consumers: `update.yml`, `spotify-playlist-manager.yml`, `spotify-reference-library.yml`, `spotify-auth-health-check.yml`, `spotify-daily-midnight-cycle.yml`, `spotify-daily-live-preflight.yml`, `tricky-daily-snapshot-refresh.yml`, `spotify-daily-feedback-observation.yml`, and `great-migration.yml`.
- Most currently use independent concurrency groups; `update.yml` has no concurrency group. This means existing per-workflow serialization does not guarantee single-flight refresh-token rotation across different workflows.
- Do not naively assign every workflow one global group without considering scheduling impact. Great Migration can run for up to six hours, while Tricky Daily has time-sensitive Eastern-midnight delivery. A global queue may serialize safely but delay those operations.
- GitHub's current Actions concurrency model now supports `queue: max` (up to 100 pending runs), which avoids the default one-pending-run replacement behavior, but this alone does not resolve the long-job scheduling tradeoff. Reference: https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency.
- M4 now records the inventory as complete and keeps the single-flight architecture decision open. Next design options: a narrow shared refresh lock around token-exchange only, split auth/operation jobs with safe token handoff, or carefully scoped global serialization that excludes non-Spotify Great Migration operations.
- No workflow concurrency behavior was changed, no Spotify API request was made, and no playlist or credential state was modified.


## 2026-11-08 — First authentication monitor implementation passed repository CI

- PR #183 head `e01bec33c5d8ddb44536078fad684df7eb9db9cb` passed the complete repository workflow: **528 tests passed** in run #42540593870 (workflow run number 2238). The new `test_spotify_auth_health_workflow.py` tests were included and all nine passed.
- The broker test/audit/Wrangler dry-run workflow passed in run #42540593852 (run number 163); `npm audit` reported zero vulnerabilities and Wrangler exited in dry-run mode without deployment.
- Full-history Gitleaks passed in run #42540593842 (run number 2076): **no leaks found**.
- These are source/build/security checks only. No live Spotify refresh, `/v1/me`, OAuth, secret rotation, Worker deployment or playlist operation was run.
- The new auth-health workflow now uses the prior completed Actions run's redacted status markers as its schedule latch, with fail-closed behavior for missing/unreadable logs, permanent blockers and interrupted attempts. It honors Retry-After deadlines for 429 and provides manual-dispatch recovery.
- PR #183 remains draft and unmerged. It is mergeable against current `main`, but requires the user's separate approval before merge. No deployment or external account setup has been performed.
- Next implementation: add an owner-facing reauthorization notification/action, then resolve the cross-workflow refresh-token single-flight design before enabling broad auth preflight.


## 2026-11-08 — Enforce Retry-After for manual recovery too

- Changed the run-history latch to inspect the previous completed auth-health run for both scheduled and manual events.
- Manual recovery bypasses permanent blockers such as `reauthorization_required`, configuration errors and interrupted runs, but it cannot bypass an active 429 cooldown.
- Retry-After accepts either integer seconds or an HTTP date. If Spotify omits or returns an invalid header, the monitor waits a conservative 24 hours before another scheduled or manual attempt.
- Preserved the Retry-After marker when a scheduled run is skipped, so later scheduled runs continue evaluating the same deadline rather than losing it.
- Added a regression assertion for the 24-hour fallback and manual cooldown behavior. Full CI is being rerun for this refinement.

## 2026-11-08 — Correct broker source status and make authorization UI device-neutral

- Re-inspected the current `main` tree and confirmed `auth-broker/src/index.js`, the pinned package/test suite, Wrangler configuration and owner-only deployment workflow are already present on `main`. The broker README also records these source assets as merged. Earlier same-day action-log text saying PR #182 remained unmerged is historical and superseded; the current blocker is external provisioning/deployment and live OAuth, not source merge.
- Updated the goal README and roadmap to reflect that the broker source/tests/deploy workflow are on `main`, while keeping Worker deployment and Spotify consent explicitly incomplete.
- Updated the broker landing page to say it supports a phone or desktop browser; renamed its user-facing title to SHIT Spotify authorization. Updated the broker README and legacy deployment runbook to match.
- Updated the broker landing-page test to assert the device-neutral phone/desktop message and retained the no-third-party-script/no-store checks.
- No Worker deployment, Cloudflare setting, GitHub App permission/installation, Spotify callback, Actions secret, OAuth, or playlist operation occurred. The current `invalid_grant` still requires fresh owner consent.

## 2026-11-08 — Owner-facing reauthorization action in health-check summary

- When the health monitor classifies `invalid_grant`, its run summary now provides a direct link to the configured HTTPS broker root (`BROKER_BASE_URL`) so the owner can start the GitHub-owner then Spotify consent flow from phone or desktop.
- If the broker URL is not configured, the summary links to the owner-only deployment runbook instead of presenting a broken authorization link.
- The broker URL is parsed and accepted only as an HTTPS origin with no credentials, path, query or fragment. The value is a non-secret repository variable.
- Added regression assertions for both the broker action and runbook fallback. This does not create issues, send messages, deploy the broker, or change any credential.

## 2026-11-08 — Replace run-history latch with durable GitHub commit status

- Replaced the previous-run log parser with the GitHub Commit Status API. The workflow reads the latest `spotify-auth-health` context for the current commit SHA and writes `pending` before contacting Spotify.
- The health result is stored as a non-secret commit status: `success/healthy`, `error/provider_unavailable`, or `failure` with the specific status in its description. For 429, the description carries `rate_limited_until:<epoch>`.
- Scheduled runs pause on permanent failure or `pending`; manual dispatch bypasses permanent blockers but still respects an active rate-limit deadline. Missing/invalid Retry-After uses a conservative 24-hour fallback.
- The workflow token now needs only `contents:read` and `statuses:write`. It no longer needs `actions:read`, does not inspect/download logs, and does not write repository variables or files. The separate GitHub App token remains Secrets:write only for refresh-token rotation.
- This supersedes the prior run-history latch design and removes the 90-day log-retention dependency. If the status API cannot be read or the pending/result status cannot be written, the workflow fails closed.
- Added/updated regression tests for the commit-status context, permission boundary, Retry-After state description, and no repository/run-log writes. The commit-status version has not yet received fresh CI; previous 528-test pass applies to the earlier run-history implementation.
- No Spotify API request, secret rotation, OAuth, Cloudflare deployment, playlist write or repository variable change was performed.
## 2026-11-08 — Pin health status to a stable anchor commit

- Found that storing auth status on the latest workflow SHA would reset the latch on every unrelated code/data commit, allowing repeated `invalid_grant` attempts.
- Pinned the `spotify-auth-health` commit-status context to fixed main commit `a4ac9def8be5b6e727b777e2660a7bb027a8e51b`. That commit is the current `main` base and remains reachable as history advances; normal commits no longer reset auth state.
- Restricted the health-check job to `refs/heads/main`, so a manual dispatch from a feature branch cannot overwrite the global auth state.
- The fixed status anchor is non-secret and is intentionally hard-coded in the workflow. If repository history is ever rewritten, update this anchor as a deliberate migration.
- Added regression assertions for the fixed SHA and main-only execution. The latest CI run is still pending; no Spotify request was made.

## 2026-11-09 — SHIT-wide monitoring and recovery hardening

- Reframed the project from a phone-only reauthorization path to **Authentication Management & Recovery**, with phone and desktop as equivalent clients.
- PR #185 (`feature/authentication-management-recovery-final`) contains the auth-health monitor, durable status latch, OAuth broker, tests, and owner-only Worker deployment workflow. It remains open and unmerged; no live Worker deployment or OAuth run was performed.
- Latest confirmed broker CI on commit `49aa94a7fce965d35ccba5f8aa290a529a3dfe66`: broker tests passed; Daily curator tests passed; Gitleaks failed on two known auth-state metadata false positives. The first regex-based allowlist adjustment did not resolve those findings.
- Replaced the broad regex attempt with exact Gitleaks fingerprints for the two audited occurrences and removed the broad auth-state regex. Latest branch commit at this log update: `9398ff2f7ea4bcb76820cbc22c700d9855b9fa46`. Fresh broker, Daily, and full-history Gitleaks runs were triggered; their results must be checked before claiming green.
- Updated the runbook to reflect the actual variable names (`BROKER_GH_APP_*`), owner-reported provisioning, explicit deployment boundary, current PR status, and known cross-workflow race. Updated the source overview and goal documentation to stop describing the feature as mobile-only.
- Security review confirms the broker's GitHub side effects remain limited to repository secret publication and dispatch of the read-only auth-health workflow. It has no playlist endpoint or playlist-write capability.
- Known unresolved design item: active-workflow checks are not an atomic global single-flight lock. A Spotify workflow could start after the broker's check; central coordination remains required before claiming all Spotify-dependent operations are race-safe.
- No secret values were read, copied, logged, or changed. No Spotify API/OAuth call, Cloudflare deployment, GitHub App permission change, or playlist operation was performed.


## 2026-11-09 — Security-scan false-positive remediation and documentation consistency

- Latest completed CI before this revision: broker tests passed and Daily curator tests passed on `f1d0a58d11b3aef60cf51a3e4c0804132bede2df`; full-history Gitleaks failed on exactly two generic-api-key false positives: the auth-state commit-reference environment binding and its regression-test assertion.
- Inspected the actual redacted findings and corrected the allowlist to match the exact source-line shapes, restricted by AND-combined path checks to the auth-health workflow and its test. Earlier fingerprint entries did not suppress the findings and were removed.
- Renamed the runtime environment key from `SPOTIFY_AUTH_STATE_SHA` to `AUTH_STATE_COMMIT` in the health workflow and its regression test so new history no longer repeats the detector-triggering label.
- Updated `auth-broker/README.md` to use the actual `BROKER_GH_APP_*` repository-variable names, describe SHIT-wide phone/desktop support, and reflect owner-reported provisioning without asserting deployment.
- Latest branch head at this log entry: `5ea3ae0adc6e834fa256fa00a8fb656ca04c10ac`. Broker test workflow #42553298788 was pending at the last check; no fresh green status or full-history scan result is yet confirmed for this head.
- Source review confirmed: the Worker has no playlist API; secret persistence is encrypted using GitHub's Actions public key; dispatch occurs only after secret update; GitHub and Spotify identity checks are separate; OAuth state is short-lived and consumed once; the auth-health workflow verifies `/v1/me` before persisting refresh-token rotation.
- Remaining architectural risk: preflight enumerates active workflow runs but is not a globally atomic lock. Do not enable a claim of race-free refresh across all Spotify workflows until a true shared coordination mechanism is designed and tested.
- No OAuth flow, external API call, Worker deployment, secret mutation, or playlist operation was performed.


## 2026-11-09 — Cross-workflow refresh-token coordination design

- Confirmed the race is not safely solved by existing per-workflow concurrency groups or a single global Actions group. Nine workflows consume the same rotating refresh token; a global group risks pending-run replacement and Daily starvation behind long migration work.
- Added `REFRESH_TOKEN_SINGLE_FLIGHT.md` specifying a dedicated Cloudflare Durable Object lease coordinator authenticated with GitHub Actions OIDC.
- The design uses short critical-section leases, atomic storage transactions, renewal, crash expiry, fencing generations, exact repository/workflow identity validation, and fail-closed behavior. The coordinator stores no Spotify credentials and cannot call Spotify, GitHub APIs, modify secrets, or touch playlists.
- Updated M4 in the roadmap. Implementation, JWT verification, lease concurrency tests, workflow rollout and the all-consumer coverage test remain open. No Worker deployment or production workflow change was made.

## 2026-11-09 — Initial OIDC lease coordinator implementation

- Added `auth-broker/src/refresh-lock.js`: GitHub OIDC RS256 verification against GitHub JWKS, exact issuer/audience, time claims, repository and immutable owner ID, main-branch/event restrictions, and exact workflow-ref allowlisting.
- Added the `SpotifyRefreshLease` SQLite Durable Object, bound it in `wrangler.toml`, and added the v2 migration. Lease state is metadata only; no Spotify token or provider secret is stored in the coordinator.
- Added Worker routes `/internal/refresh-lock/acquire`, `renew`, and `release`. The Worker derives owner identity from verified OIDC claims and rate-limits requests.
- Added unit tests for valid and invalid OIDC signatures/claims, exclusive concurrent acquisition, monotonic fencing generations, wrong-owner/stale-owner rejection, renewal, and malformed requests.
- CI exposed and corrected malformed line breaks in the Wrangler TOML and Worker route/module source. The broker test workflow passed on commit `dee009212309b6cbd705da87d8145fa960d8a34a` after the TOML repair; a subsequent JWKS timeout hardening change is being re-tested on the current head.
- Security scan had passed on earlier head `8c60906d6a2b997971a07ca1d1fe999394e15db6`; full-history scan for the latest code remains pending.
- Critical unresolved issue: GitHub Actions Secrets writes cannot be conditionally committed against a fencing generation. A Durable Object lease alone cannot prevent a stale workflow from finishing an already-started secret write. The coordinator is a prototype only and must not be integrated as sufficient protection until refresh and persistence move behind a broker-controlled critical section or another fencing-enforcing downstream store.
- No workflow consumes the new lease yet. The allowlist is not configured, no OIDC claims have been validated from a real non-production Actions job, and no Worker deployment, production secret change, Spotify request, or playlist operation has occurred.

- Added `BROKER_CONTROLLED_REFRESH.md` with the recommended end state: broker-only refresh-token custody, encrypted Durable Object persistence, OIDC-authorized access-token delivery, operation-version fencing, a nine-workflow migration, and explicit production approval gates.
- Updated the roadmap to make broker-owned credential persistence—not a lease-only solution—the next implementation milestone.

## 2026-11-09 — Credential-store test correction and green broker validation

- The first CI run after the refresh-test correction still failed because the replay assertion referenced an undefined shorthand variable (operationId) instead of the fixture's operation value. This was a test-only defect; the refresh implementation was not implicated by that failure.
- Corrected the replay request to use the explicit operation ID fixture in commit `583d48eb669127b6796cafaaa0e0f23c6b78e3d3`.
- Broker test workflow run [#42564037531](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42564037531) passed on that exact commit. All broker security unit tests, dependency audit, Worker bundle validation, and Wrangler configuration dry-run passed.
- Public repository security scan [#42564037488](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42564037488) was still running at the time of this entry; do not mark the commit security-scan complete until its final result is checked.
- This green run validates the isolated prototype only. The credential-store class remains unbound and unreachable from the Worker; no encryption key is configured, no OAuth callback handoff or OIDC credential route exists, and no workflow or production credential has migrated. The in-memory storage adapter is not a substitute for Cloudflare Durable Object integration tests.
## 2026-11-09 — Verified workflow migration inventory

- Inspected the active workflow sources and confirmed nine direct consumers of `SPOTIFY_REFRESH_TOKEN`: `spotify-auth-health-check.yml`, `spotify-daily-live-preflight.yml`, `spotify-daily-midnight-cycle.yml`, `spotify-daily-feedback-observation.yml`, `tricky-daily-snapshot-refresh.yml`, `spotify-reference-library.yml`, `spotify-playlist-manager.yml`, `great-migration.yml`, and `update.yml`.
- Added `WORKFLOW_MIGRATION_INVENTORY.md` with each consumer's role, current credential behavior, proposed migration order, adjacent workflows checked, and a no-fallback migration contract.
- Updated `BROKER_CONTROLLED_REFRESH.md` and `ROADMAP.md`: the encrypted credential store is now accurately marked as an isolated prototype implemented in PR #187, not merely a proposal; Cloudflare Durable Object integration tests and key rotation/recovery remain mandatory before binding or routing it.
- No workflow was modified, no secret was removed or read, and no production credential path was changed. All nine workflows continue using the existing secret until an end-to-end replacement is proven and production cutover is explicitly approved.
## 2026-11-09 — Automated consumer inventory and restart/concurrency coverage

- Added `auth-broker/test/workflow-inventory.test.js`. It asserts that the exact nine documented workflow consumers remain accounted for and that the only workflow definition directly containing the Spotify token endpoint is the existing read-only auth-health checker. This is a baseline guard; it will be tightened to require zero direct consumers after migration.
- The first inventory-test attempt incorrectly assumed zero direct token endpoint callers already existed. CI correctly identified `spotify-auth-health-check.yml` as the remaining explicit workflow-level caller. The test was corrected to encode the verified baseline rather than hide or prematurely change production behavior.
- Added credential-store tests for a refresh reservation surviving store-instance restart and for a stale operation being unable to block a different operation.
- Broker workflow run [#42564440402](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42564440402) passed on commit `df6b2a04b6875225c71568b84e37fb2b3f4749e1`: dependency audit, all broker security unit tests (including the new inventory and restart tests), Worker bundle validation, and Wrangler dry-run.
- Public repository security scan [#42564440515](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42564440515) was still running at this entry; verify its conclusion before marking this commit fully validated.
- The tests still use an in-memory storage adapter. Cloudflare Durable Object restart/transaction integration tests remain a hard gate before the class can be bound or routed.
## 2026-11-09 — OIDC broker refresh route prototype

- Created stacked draft work branch `feature/oidc-broker-refresh-endpoint` from the credential-store work. Added the `SpotifyCredentialStore` SQLite Durable Object binding and migration tag `v3` to Wrangler configuration, and exported the class from the Worker entry point.
- Added `POST /internal/spotify/refresh`. It requires a signed GitHub Actions OIDC token with a dedicated `shit-spotify-refresh` audience, exact configured workflow refs, repository/immutable owner/ref/event/time/run claims, and a bounded JSON body. The Worker ignores caller-supplied owner/account claims, selects the fixed `spotify-primary` Durable Object, and forwards only the operation ID.
- Added distinct OIDC audience support while preserving the existing refresh-lock audience. Added tests for audience separation, exact OIDC-gated route behavior, payload minimization, and rejection before credential storage access.
- Added documentation for the route contract and required future Worker configuration: `SPOTIFY_CREDENTIAL_ENCRYPTION_KEY` secret and exact `SPOTIFY_REFRESH_WORKFLOW_REFS` variable. Neither is configured; the Worker is not deployed.
- The existing OAuth callback still writes the legacy GitHub Actions secret. Initial credential handoff, key rotation/recovery, real Cloudflare DO integration tests, and all nine workflow migrations remain outstanding. The new route is therefore an isolated, disabled prototype and is not used by any workflow.
- Opened stacked draft PR [#188](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/188) for the OIDC refresh-route prototype, based on PR #187. Broker tests passed on the route implementation commit before documentation-only follow-ups; final-head CI and security scan are being verified separately.
## 2026-11-09 — Workflow client and manager broker-only mode

- Added `scripts/spotify/broker_access_token.py`. It obtains a GitHub OIDC JWT with the dedicated audience, requests a broker access token using a random operation ID, bounds and validates responses, rejects any refresh-token field, masks the access token, and writes it only to the ephemeral Actions `GITHUB_ENV`. It never prints the token as ordinary output and has no legacy fallback.
- Updated `scripts/spotify/spotify_playlist_manager.py` to support `SHIT_BROKER_ACCESS_TOKEN` and its expiry. In broker-managed mode it does not read `.spotify_playlist_token.json`, does not need a refresh token or GitHub secret-writer token, and never calls Spotify's token endpoint. If the access token expires, it stops and requires the workflow to request a fresh broker token.
- Added Python tests for the OIDC client and manager tests proving broker mode avoids legacy token-file reads/direct refresh and fails closed after expiry.
- These are client capabilities only. No GitHub Actions workflow has been migrated yet because the broker has no initialized credential in a deployed environment. The existing nine workflows remain on the current secret path until the full migration can be tested safely.
- The broker CI workflow now also runs `tests.test_spotify_broker_access` and `tests.test_spotify_playlist_manager` on changes to the client/manager. The first run exposed a backward-compatibility issue in tests that construct the manager with `__new__`; the broker-mode guard now uses a safe default for legacy instances.
- Broker workflow run [#42565467507](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42565467507) passed on commit `73482d2453b653a4ed5055fa5a76a7f90e926f17`, including Node security tests, Python broker-client/manager tests, dependency audit, Worker bundle validation, and Wrangler dry-run. The public repository security scan was still running at the time of this entry.
## 2026-11-09 — OIDC client validation and credential key-version binding

- The broker client/manager tests are now part of the dedicated broker CI workflow, along with the maintained Python script documentation contract. This caught and corrected the missing test-file overview before final validation.
- Added authenticated `keyVersion` metadata to AES-GCM credential records and included it in the authenticated additional data alongside account ID and credential version. The prototype currently uses key version 1; multi-key rotation/re-encryption is still a production gate.
- Broker workflow run [#42565806213](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42565806213) passed on commit `66ac7921ff885477ec569e70620b8bc40f564e7a`: Node broker tests, Python OIDC client and manager tests, script-layout documentation tests, dependency audit, Worker bundle validation, and Wrangler dry-run.
- Public repository security scan [#42565800935](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42565800935) was still running at this entry. No production deployment, key provisioning, callback cutover, or workflow migration has occurred.
## 2026-11-09 — Keyring rotation, owner recovery, and CI resilience

- Added a versioned AES-GCM keyring. Credential records authenticate the key version; refresh decrypts using the retained record key and commits under the configured active key version. Tests cover rotation from v1 to v2, removing v1 only after successful re-encryption, and failing closed when a historical key is missing.
- Added a same-account owner-reauthorization primitive for credentials blocked after ambiguous refresh outcomes. It requires the store to be in `reauthorization_required`, rejects account changes and ready/in-progress overwrite, increments the credential version, encrypts under the active key, and preserves the blocked operation ID against replay. It is not yet connected to the OAuth callback.
- Removed the single-key compatibility fallback; the credential store now requires the versioned `SPOTIFY_CREDENTIAL_ENCRYPTION_KEYS` keyring. The active version is explicit via `SPOTIFY_CREDENTIAL_ACTIVE_KEY_VERSION` (defaults to v1).
- Broker workflow run [#42566867902](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42566867902) passed on commit `aee1e7c9bc9552abead9032942316f4f5063350c`, including keyring rotation and same-account reauthorization tests. Subsequent documentation/configuration commits also passed broker tests through [#42566933729](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42566933729).
- Public repository security scans intermittently failed before scanning because the Gitleaks release download returned HTTP 504; no secret finding was reported. Added bounded curl retries to the security workflow to tolerate transient release-host failures. Recheck the latest scan before declaring it green.

## 2026-11-09 — Central credential handoff and OIDC canary

- Added `SpotifyCredentialStore.authorize()`: owner-consented authorization initializes an empty encrypted credential record or restores a blocked record for the same verified Spotify account. It cannot overwrite a ready/in-progress credential or silently switch accounts.
- Rewired the Spotify OAuth callback to verify the Spotify account and pass the refresh token directly to the fixed Durable Object. Removed the broker's GitHub Actions refresh-token secret writer.
- Migrated `.github/workflows/spotify-auth-health-check.yml` to request a GitHub OIDC token with audience `shit-spotify-refresh`, call the central broker, and verify `/v1/me`. The existing commit-status latch remains; the workflow no longer reads the refresh-token secret, Spotify client secret, or calls Spotify's token endpoint directly.
- Narrowed the broker GitHub App installation token to repository Actions: Write, which is required for workflow dispatch and active-run inspection. It no longer needs Secrets: write.
- Fixed explicit Spotify 429 handling: release the refresh reservation, preserve the existing ciphertext/version, return HTTP 429 and Retry-After. Ambiguous provider/network outcomes remain blocked and require owner-consented recovery.
- Updated the consumer inventory and regression tests: auth-health is the first canary; eight direct refresh-token consumers remain. Updated broker README, credential-store status, controlled-refresh architecture, and roadmap.
- Changes are on stacked draft PR #188 (base PR #187, itself based on PR #185). CI run #42567648435 was pending at the last check; later commits require fresh CI. No production deployment, Cloudflare key provisioning, live Spotify OAuth, external app permission change, repository secret rotation/deletion, or playlist/Library operation occurred.
- Remaining blockers: passing CI and security review; real Cloudflare Durable Object integration; secure encryption-key provisioning/backup/rotation/recovery; live OIDC claim validation; two independent broker-backed auth-health checks; migration and verification of the remaining eight workflows; explicit owner approval before production cutover.


## 2026-11-09 — All nine Spotify workflows migrated to the broker client

- Migrated Daily live preflight, Daily midnight cycle, Daily feedback observation, Daily snapshot refresh, Spotify Reference Library, owner Playlist Manager, both Great Migration credential-verification jobs, and `update.yml` to obtain short-lived broker access tokens through GitHub OIDC.
- The auth-health workflow remains the only consumer permitted to force a refresh after a cached access token receives an early 401. The broker rejects forced refresh from every other workflow identity.
- Added encrypted access-token caching in the Durable Object. Concurrent workflow jobs wait for one in-flight refresh and reuse the same encrypted cached token; provider 429 cooldowns are persisted and propagated.
- Added fail-closed `SHIT_AUTH_MODE=broker` to the shared Spotify manager. It refuses to read legacy token files or persist rotated refresh tokens when broker mode is active. Daily preflight, Daily snapshot, and Daily cycle no longer seed local refresh-token files in broker mode.
- Reworked Great Migration's provider verifier to request an OIDC broker token and perform read-only `/v1/me`; it no longer contacts Spotify's token endpoint directly.
- Removed all direct `SPOTIFY_REFRESH_TOKEN` inputs, secret-writer App steps, and token-file seeding from the nine workflow definitions. Existing playlist locks, snapshots, confirmation boundaries, audits, and write paths were not intentionally changed.
- OIDC policy now allows `issues` only for the exact Playlist Manager and Great Migration workflow refs, and `issue_comment` only for Playlist Manager. The deployment allowlist is pinned to exactly nine main-branch workflow refs.
- Updated the workflow inventory test to require zero legacy refresh-token workflow consumers and exact broker-client usage in all nine workflows.
- No production deployment, Cloudflare key provisioning, live OAuth, GitHub App permission change, legacy secret deletion, playlist modification, or Library write occurred. Main remains unchanged until the stacked PRs are reviewed/merged and the owner approves coordinated cutover.
- Validation remains pending on the latest branch head. Required before deployment: all CI/security checks, real Durable Object integration tests, exact OIDC claim validation for issue events, two independent read-only health checks, and key backup/rotation/recovery readiness.


## 2026-11-09 — Broker retry and multi-job correctness refinements

- Added an encrypted short-lived access-token cache with a two-minute minimum remaining lifetime before a workflow receives a cached token. This leaves the shared manager's 60-second expiry safety margin intact.
- Changed concurrent refresh handling to return an immediate transient `credential_busy` result from the Durable Object. The Python OIDC client retries with the same operation ID and OIDC identity; after another job commits, the retry receives the cached token. If a forced auth-health refresh collides with another in-flight refresh, the retry drops the force flag and reuses the winning result.
- Made successful refresh operation IDs idempotent while their encrypted cached access token remains valid. This allows a client to recover from a lost broker HTTP response without performing a second refresh-token rotation; expired replays remain rejected.
- Persisted bounded Retry-After cooldowns after Spotify 429 responses and made subsequent broker calls return the remaining cooldown without contacting Spotify.
- Restricted forced refresh to the exact main-branch auth-health workflow. It is used only after Spotify rejects a cached access token with HTTP 401; all other workflow identities are explicitly denied.
- Adjusted Cloudflare Workers SQLite integration coverage to verify encrypted persistence and sequential cache reuse. The Vitest DO harness raised a cross-DO I/O-context error when the test itself held an external MSW response gate across concurrent requests, so concurrent contention is tested in the isolated store/client unit suites instead. Real cross-job concurrency remains a live deployment acceptance check, not a claimed completed integration result.
- Added client tests for busy retry, network-response-loss idempotency, forced-refresh flag handling, and manager broker-only fail-closed behavior.


## 2026-11-09 — Long-running workflow token renewal

- The shared Spotify manager now renews an expiring broker-issued access token in-process by requesting a fresh GitHub OIDC identity and using the central broker. It never calls Spotify's refresh-token endpoint in broker mode.
- The broker helper now persists the validated HTTPS broker origin alongside the ephemeral access token in `GITHUB_ENV`, allowing later manager requests in the same job to renew safely.
- Manager broker mode validates token size/CRLF and requires at least 120 seconds of lifetime, preserving its 60-second request safety margin. Renewed tokens are masked and kept in process memory; they are not written to files or artifacts.
- Added manager tests for successful in-process broker renewal, fail-closed broker outage, and no direct token refresh or legacy secret persistence.
