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
