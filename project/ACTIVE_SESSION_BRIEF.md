# Current verified checkpoint — 2026-11-22 (post-CI review)

- **Main:** `deb5a192eda4b8965a4af1110c432db78e7ec11b`.
- **Buddy:** automation `6aed3a70baf88191ab1dbfaa8f7dba91` enabled; next run Nov 23, 9:00 AM Eastern. Latest run `e560322d-6ac8-8332-84aa-98b2b5816aeb` completed before the latest prompt update and omitted the successor-readiness report. Environment selection is inherited; actual environment status is unknown.
- **Jockey:** automation `6af1645551a48191900c77833073fdfd` disabled; latest run `ae49786b-46e0-8321-949d-9f139020df47` disclosed accidental direct-to-main commits `a372f8d49817783a2ba9e9bed0f6b24f071a7cc1` and `649690ce545094cc0f5d19a4a57b17eac20319dd`. Keep disabled pending reviewed recovery.
- **Boots:** automation `Automation_2e1357c87e688191829bd2380047f46b` disabled. Preserve `engineering/general`; do not reset, rebase, force-push, or re-enable before recovery review.
- **PR #201:** open/draft, `babel/chatgpt-buddy-v2`, head `b91254ff1dec0a0e62f1083d82be8877996085eb`, 65 ahead / 14 behind. Known exact-head Daily curator tests #45083951234, Mobile Auth Broker Tests #45083951231, and security scan #45083951241 passed.
- **PR #202:** open/draft, `coordination/trio-readiness-handoffs`, head `f2291b003f459ad4e330a96837f97d3f1cc6f1a1`, 62 ahead / 14 behind. Current-head full tests #45095764686 and full-history secret scan #45095764679 are in progress. Previous head `986bc385946f869cacf655a775ceafcce4cd86cf` passed full tests #45095318314, full-history secret scan #45095318358, and Cloudflare Workers Builds #137434112899; lockfile check skipped.
- **PR #200:** open/draft, `engineering/priority`, head `4f0291b8990987ca5bb84bdea06d6d6bad1113fe`, 67 ahead / 8 behind. Passing historical CI does not resolve the direct-to-main incident or authorize Jockey to resume.
- **Shared-file gate:** #201 and #202 overlap on `docs/BABEL_CHATGPT_BUDDY.md`, `docs/README.md`, `project/ACTIVE_SESSION_BRIEF.md`, and `project/LOOSE_ENDS.md`. Neither PR may merge until these files and merge order are reconciled against current heads.
- **Phase status:** all three saved prompts contain successor mappings and Phase 1 read-only limits, but no complete runtime handoff cycle has been observed. Buddy's next run is the next verification milestone. Phase 2 cross-repair remains disabled and requires separate user authorization.
- **Safety:** no worker was re-enabled; no workflow was manually dispatched; no Spotify/provider, playlist, credential, production, or canonical Library write was performed.

---

# Current trio checkpoint — 2026-11-22 20:33 Eastern

## Verified live checkpoint — 2026-11-22 20:33 Eastern

- **Buddy:** automation `6aed3a70baf88191ab1dbfaa8f7dba91` is enabled; next run Nov 23, 9:00 AM Eastern. Latest recorded run `e560322d-6ac8-8332-84aa-98b2b5816aeb` completed before the latest prompt update and did not contain a successor-readiness handoff. Its report claims Buddy PR head `452a6d3...`, but the live PR API reports #201 head `b91254ff1dec0a0e62f1083d82be8877996085eb`; trust the live GitHub branch/PR metadata and require Buddy to reconcile this discrepancy in its next run. Environment selection is inherited; actual environment details are unavailable, so environment status is unknown.
- **Jockey:** automation `6af1645551a48191900c77833073fdfd` remains disabled. Latest report `ae49786b-46e0-8321-949d-9f139020df47` disclosed accidental direct-to-main commits `a372f8d49817783a2ba9e9bed0f6b24f071a7cc1` and `649690ce545094cc0f5d19a4a57b17eac20319dd`. Keep disabled pending reviewed recovery.
- **Boots:** automation `Automation_2e1357c87e688191829bd2380047f46d` remains disabled. Branch `engineering/general` is 14 ahead / 85 behind current main, with no matching open PR. Preserve it; do not reset/rebase/force-push or re-enable.
- **Main:** `deb5a192eda4b8965a4af1110c432db78e7ec11b`.
- **PR #201:** open/draft, branch `babel/chatgpt-buddy-v2`, head `b91254ff1dec0a0e62f1083d82be8877996085eb`, 65 ahead / 14 behind. Exact-head Daily curator tests #45083951234, Mobile Auth Broker Tests #45083951231, and security scan #45083951241 all passed.
- **PR #202:** open/draft, branch `coordination/trio-readiness-handoffs`, head `9af60ff2d6cd4e7169def18feced445351b9db61`, 48 ahead / 14 behind. Exact-head Daily curator tests #45093806549, Mobile Auth Broker Tests #45093806530, and security scan #45093806533 all passed.
- **PR #200:** open/draft, branch `engineering/priority`, head `4f0291b8990987ca5bb84bdea06d6d6bad1113fe`, 67 ahead / 8 behind. Passing historical exact-head checks do not authorize Jockey to resume or settle the mainline/branch recovery.
- **Shared-file gate:** #201 and #202 overlap on `docs/BABEL_CHATGPT_BUDDY.md`, `docs/README.md`, `project/ACTIVE_SESSION_BRIEF.md`, and `project/LOOSE_ENDS.md`. #202 adds the Trio Protocol navigation and Buddy handoff responsibility that #201 lacks. Neither PR is merged; preserve the deliberate merge-order and full review gate.
- **Phase 1:** saved prompt mappings are configured, but no complete runtime handoff cycle has been observed. Phase 2 cross-repair remains disabled and requires separate authorization.
- **Safety:** no worker was re-enabled, no workflow was manually dispatched, and no Spotify/provider, playlist, credential, production, or canonical Library write was performed.

---

# Current trio and documentation checkpoint — 2026-11-22 20:15 Eastern

## Verified live checkpoint — 2026-11-22 20:15 Eastern

- **Buddy:** automation `6aed3a70baf88191ab1dbfaa8f7dba91` enabled; latest run `e560322d-6ac8-8332-84aa-98b2b5816aeb` completed before the latest prompt update (`2026-11-22T23:41:06Z`). It did not report the required successor check. Next scheduled run: Nov 23, 9:00 AM Eastern. Environment selection is inherited; environment details are unavailable, so status is unknown.
- **Jockey:** automation `6af1645551a48191900c77833073fdfd` disabled; latest run `ae49786b-46e0-8321-949d-9f139020df47` completed with a report disclosing two accidental direct-to-main commits. Next scheduled time while disabled: Nov 23, 11:00 AM Eastern. Keep disabled pending a reviewed branch/mainline recovery plan.
- **Boots:** automation `Automation_2e1357c87e688191829bd2380047f46d` disabled; latest run `a030ee14-e434-832d-a8cc-b462d8e88ed7` completed after safely stopping on its stale branch. Next scheduled time while disabled: Nov 23, 4:30 PM Eastern. Environment details are unavailable. Preserve its branch.
- **PR #201:** `babel/chatgpt-buddy-v2`, head `b91254ff1dec0a0e62f1083d82be8877996085eb`, 65 ahead / 14 behind current main `deb5a192eda4b8965a4af1110c432db78e7ec11b`, open/draft. Exact-head Daily curator tests #45083951234, Mobile Auth Broker Tests #45083951231, and security scan #45083951241 passed.
- **PR #202:** `coordination/trio-readiness-handoffs`, head `9b3fbeed1a0e1569644133984df1ce766e077517`, 43 ahead / 14 behind the same main, open/draft. Exact-head Daily curator tests #45084445454, Mobile Auth Broker Tests #45084445441, and security scan #45084445450 passed.
- **PR #200:** `engineering/priority`, head `4f0291b8990987ca5bb84bdea06d6d6bad1113fe`, 67 ahead / 8 behind, open/draft. Its three exact-head checks passed (#44928121259 broker, #44928121273 Daily, #44928121262 security). This does not resolve its branch recovery or authorize enabling Jockey.
- **Boots branch:** `engineering/general`, 14 ahead / 83 behind, no matching open PR. Do not reset, rebase, force-push, or enable Boots.
- **Shared-file gate:** #201 and #202 overlap on `docs/BABEL_CHATGPT_BUDDY.md`, `docs/README.md`, `project/ACTIVE_SESSION_BRIEF.md`, and `project/LOOSE_ENDS.md`. The coordination branch includes the Trio Protocol link and Buddy handoff section; Buddy's current branch does not yet include those two additions. Do not merge either PR until a deliberate merge order and complete shared-file review are recorded.
- **Phase 1:** prompt text is configured, but runtime handoff behavior is not proven. The latest Buddy run predates the prompt update. Phase 2 cross-repair remains disabled and requires separate authorization.
- No worker was re-enabled, no workflow was manually dispatched, and no Spotify/provider, playlist, credential, production, or canonical Library write was performed in this checkpoint.

---

# Current trio and documentation checkpoint — 2026-11-22

- **User direction:** continue the trio-readiness implementation and repair the identified blockers; the intended handoff is Buddy → Jockey → Boots → Buddy, with read-only successor checks first and bounded cross-repair separately gated.
- **Live automation records:** Buddy `6aed3a70baf88191ab1dbfaa8f7dba91` is enabled; latest run `e560322d-6ac8-8332-84aa-98b2b5816aeb` completed, but its report did not include a successor-readiness handoff. Jockey `6af1645551a48191900c77833073fdfd` is disabled; latest run `ae49786b-46e0-8321-949d-9f139020df47` disclosed two direct-to-main commits. Boots `Automation_2e1357c87e688191829bd2380047f46d` is disabled; latest run `a030ee14-e434-832d-a8cc-b462d8e88ed7` stopped safely on its stale branch.
- **Prompt configuration:** all three saved prompts have been read back and contain the correct successor and fallback mappings plus Phase 1 read-only limits. This proves prompt text, not runtime handoff execution. Phase 1 is not complete.
- **Buddy PR #201:** branch `babel/chatgpt-buddy-v2`, current head `b91254ff1dec0a0e62f1083d82be8877996085eb`, 65 ahead / 12 behind main, open/draft. The missing Tricky Daily recommendation-memory guide link was added to the branch and read back. Exact-head Daily curator tests, Mobile Auth Broker Tests and public repository security scan all passed. The previous two failures had the same single cause: the Python suite's documentation-index assertion; the broker-specific integration tests passed 5/5.
- **Coordination PR #202:** branch `coordination/trio-readiness-handoffs`, current head `5eaf7d57621506ac33862932c74780dace65a9b7`, 34 ahead / 12 behind main, open/draft. Daily curator tests and Mobile Auth Broker Tests passed; security scan was still running at the last query. Its README now also indexes the recommendation-memory guide. The shared files with PR #201 remain overlapping and need a deliberate merge-order/reconciliation.
- **PR overlap:** #201 and #202 share `docs/BABEL_CHATGPT_BUDDY.md`, `docs/README.md`, `project/ACTIVE_SESSION_BRIEF.md`, and `project/LOOSE_ENDS.md`. Do not merge either until those shared files are reconciled. The coordination branch's Buddy guide and index have been reconciled to include the current Buddy branch/policy and the trio handoff link.
- **Jockey:** branch `engineering/priority` is 67 ahead / 6 behind, PR #200 open/draft at head `4f0291b8990987ca5bb84bdea06d6d6bad1113fe`. Two accidental main commits are `a372f8d49817783a2ba9e9bed0f6b24f071a7cc1` (Daily recommendation-memory guide) and `649690ce545094cc0f5d19a4a57b17eac20319dd` (standalone 1,232-line memory module). The module exists on main but is not imported by `spotify_daily_cycle.py` or the midnight workflow; no dedicated memory test file or active JSONL store/manifest was found. Treat it as unvalidated groundwork; do not integrate it or roll it back without a reviewed plan.
- **Boots:** branch `engineering/general` is 14 ahead / 83 behind main and has no matching open PR. Preserve its head; no reset/rebase/force-push.
- **Safety:** no task was re-enabled, no workflow was manually dispatched, and no Spotify/provider, playlist, credential, production, or canonical Library operation was performed.
- **Next:** finish exact-head PR #202 security verification; reconcile the four shared files and merge order; then prepare Jockey's branch/mainline recovery and Boots' archival refresh plan without discarding either worker's work.

---

# Coordination session overlay — 2026-11-20

- User authorized a self-maintaining handoff cycle for the scheduled trio: Buddy → Jockey → Boots → Buddy. The objective is to prevent silent worker failure during extended absences, including roughly two weeks away.
- A new Trio Coordination goal and canonical protocol are proposed in [draft PR #202](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/202), branch `coordination/trio-readiness-handoffs`. Phase 1 is read-only successor-readiness checking; cross-repair is a later, separately gated phase. Do not change another worker's task prompt, schedule, enablement, environment, branch or PR during Phase 1.
- Phase 2 candidates are now documented: restore only a previously approved task enabled/schedule state, restore an approved prompt snapshot, or archive a stale branch with no open PR before refreshing it from current main. These remain disabled until Phase 1 evidence is reviewed and the user authorizes a specific allowlist.
- Added a broken-chain fallback: if the immediate successor has failed or missed its expected run, the outgoing worker also checks the following worker so one failure does not blind the rest of the chain.
- This current overlay supersedes older notes below that the trio remains disabled. Live automation audit: Buddy is enabled; latest run `54ea442a-ca08-8326-b910-2ba2f6a15428` completed with a blocker report referencing obsolete PR #163. Jockey is enabled; latest run `aac1531b-53d0-832f-918c-9e21a3a46772` failed with a generic scheduled-task error. Boots is enabled; latest recorded run `1e3d1069-f10c-8331-9a81-2fb71b707e11` completed on 2026-11-08, with its next scheduled run 2026-11-20 4:30 PM Eastern. These are point-in-time observations; recheck live records before action.
- Branch audit: Buddy `babel/chatgpt-buddy-v2` is 14 ahead/0 behind with open draft PR #201 and all exact-head checks passing. Jockey `engineering/priority` is 40 ahead/2 behind with open draft PR #200, GitHub mergeable/clean and exact-head tests/security/broker checks passing, but its latest scheduled automation failed generically. Boots `engineering/general` is 14 ahead/71 behind and has no matching open PR; its prompt requires stopping on divergent branch state. Do not reset/rebase Boots or edit another worker's branch during Phase 1.
- No automation prompt/schedule/enablement, runtime code, workflow, credential, provider, playlist or canonical Library changes have been made in this coordination batch.
- Next: finish repository navigation and review the protocol diff; open a draft PR; then, after the documentation is merged, add read-only successor checks to all three saved task prompts and observe one full cycle before considering bounded cross-repair.

---

# Verified continuation overlay — 2026-11-20 08:29 UTC

- PR #198 merged as `fbd1b7a7e245479a73742f007ad6d401152f09b9`; exact-head broker tests #44702575255, Daily curator tests #44702575185, and full-history security scan #44702575262 passed. Cloudflare preview build/deployment succeeded (build `fc47ae95-819f-4b34-b672-c686f582e2c0`, deployment `8cd44007-5fb5-4356-b999-1f9afe5914a7`). The correction preserves ordinary whitespace in opaque Spotify account IDs exactly and retains empty/control/length rejection.
- Production is **not** verified: latest read-only deployment remains `8939dbfc-f607-4891-bcfc-d77abd8b7a72`, version `1783d2bb-4fe8-477a-8b4c-df486d92dcb5`, 100% traffic. Do not equate merged code or preview deployment with production activation or successful Spotify auth.
- Cloudflare secret-binding metadata confirms the GitHub App client secret, GitHub App private key, and Spotify credential encryption keyring exist as `secret_text`. No secret values were read. Keyring independent backup and repository variable `SPOTIFY_CREDENTIAL_KEY_BACKUP_CONFIRMED=true` remain unverified.
- Post-merge mainline tests #44702801378 and security scan #44702801377 were still in progress. Auth-health #44581567494 and Daily preflight #44692745648 remain the latest verified operational failures.
- Owner-controlled next step: confirm independent encryption-key backup and required variable; run Actions → Deploy SHIT Auth Broker. Verify 100% traffic, query redaction, and `/ready`; then owner performs fresh consent. Verify encrypted credential persistence without reading it and two independent read-only health successes.
- Buddy/Jockey/Boots remain disabled until the authentication acceptance gate passes; then resume as background lanes with separate scopes.

---

# Current session overlay — 2026-11-20

## Focus: centralized Spotify authentication

- User explicitly authorized continued work to get SHIT's centralized authentication functioning. Keep authentication the sole focused engineering priority until acceptance is met.
- PR #188 is merged. Current main is `2eecf2592c5dec2977277ba9b8880e7ff57d7fe5`. The remaining immediate identity-validation correction was ported cleanly from stale PR #196 to fresh branch `fix/opaque-spotify-account-identifiers-mainline`, PR #198, head `1146b0cc51d855b438c15fa7b4697186bfecbfad`.
- PR #198 changes only `auth-broker/src/credential-store.js` and `auth-broker/test/credential-store.test.js`. It allows ordinary whitespace in opaque provider IDs without normalization; still rejects empty, control-character, and over-256-character values. Exact account ID is preserved for storage and encryption associated data.
- Exact-head checks #44701998659 (broker), #44701998530 (Daily curator), and #44701998525 (security scan) were running at the time of this update. Do not merge until complete and green.
- Read-only Cloudflare deployment metadata: latest production deployment `8939dbfc-f607-4891-bcfc-d77abd8b7a72`, version `1783d2bb-4fe8-477a-8b4c-df486d92dcb5`, 100% traffic, created 2026-11-10 20:12:11 UTC. Integrated v3 credential-store/OIDC production deployment is not yet verified.
- Auth-health run #44581567494 failed on 2026-11-19 at the broker request. Daily preflight #44692745648 failed on 2026-11-20 while obtaining the central access token. No successful credential persistence or two independent health checks are established.
- Updated auth-recovery monitor task `6af195417fe88191859e30f9958dcc02` to track PR #198 and the full production/credential/health acceptance path. It remains read-only.
- Safety: do not read/expose secrets, rotate or delete credentials, initiate OAuth, deploy production, or write to Spotify/Last.fm. Owner-controlled deployment and owner-consented OAuth remain explicit gates. No playlist writes.
- **Trio transition:** Buddy (Babel), Jockey (priority engineering), and Boots (general engineering) remain disabled during focused auth recovery. After credential persistence and two independent auth-health checks pass, resume the three as background lanes with non-overlapping scopes; do not reactivate them early.

## Next executable action

Inspect exact-head checks for PR #198. If all required checks pass, independently review the complete two-file diff and merge. Then prepare the owner-controlled production deployment handoff, verify 100% traffic/readiness/query redaction, and only then ask the owner to perform fresh Spotify consent.

---

# Active SHIT Session Brief

## Current authentication session overlay — 2026-11-10

### Objective
Complete SHIT-wide centralized Spotify authentication. The Cloudflare broker must own the only long-lived refresh credential, serialize refresh/rotation inside its encrypted Durable Object, and issue short-lived access tokens only to the exact allowlisted GitHub Actions workflows through OIDC. Authentication must never modify playlists.

### Decisions and safety boundaries
- Continue the previously authorized Authentication Management & Recovery workstream. Do not reassign or edit Jockey/Tricky Daily work.
- The target is broker-owned encrypted refresh-token custody. Keep the legacy GitHub Actions `SPOTIFY_REFRESH_TOKEN` secret until the new path is deployed and independently verified; no dual-write or silent fallback.
- Production deployment remains owner-controlled. Never read or expose secret values, start Spotify OAuth on the owner's behalf, delete legacy credentials, or modify playlists.
- Spotify PKCE uses `client_id` in the form body and does not require a Spotify client secret or HTTP Basic authentication.
- PR #187 is superseded by #188. PR #189 is closed as a stale deployment-alignment draft.

### Repository / PR state (checked 2026-11-10)
- PR #185 merged the base broker; PR #190 and #191 merged safe diagnostic follow-ups.
- PR #188 (`feature/oidc-broker-refresh-endpoint`) is the integrated draft containing the encrypted credential store, OIDC refresh endpoint, and all nine workflow migrations. It remains open and draft; not merged or deployed.
- Current PR branch head: `cb25552e4578f4dbf35a7a8d8f9a59d5b7870413`. It includes the rate-limit hardening described below.
- GitHub compare at the preceding refresh reported 450 commits ahead, 14 behind, and 42 changed files, with zero changed-path overlap between mainline and PR #188. Subsequent mainline commits in this session have only refreshed this active-session brief; they do not overlap the PR's 42 files. For the live ahead/behind count, use the PR description. Preserve unrelated mainline changes; do not force-push or rewrite branch history.
- Latest exact-head CI is green: Mobile Auth Broker Tests #42861563408 passed (broker security unit tests, Cloudflare SQLite Durable Object integration tests, broker client/manager tests, dependency audit, Python documentation and Wrangler validation); Daily curator tests #42861563244 passed; Public repository security scan #42861563507 passed.
- Cloudflare Workers Builds independently deployed the exact same branch head to its isolated preview: build `195d4c73-69d1-4020-947f-60be95ea4552`, outcome `success`, commit `cb25552e4578f4dbf35a7a8d8f9a59d5b7870413`. Wrangler reported preview URL `https://feature-oidc-broker-refresh-endpoint-shit-auth-broker.trickysturluson.workers.dev` and unique deployment URL `https://d2d2f501-shit-auth-broker.trickysturluson.workers.dev`. The exact-head GitHub check **Verify deployed auth broker preview** #42861546486 passed both steps: it waited for the Cloudflare build for this exact SHA, then successfully probed the preview's non-secret `/health` endpoint.
- No PR review submissions or inline review threads were present at the preceding inspection.

### Authentication implementation / latest hardening
- The integrated broker uses AES-256-GCM encrypted refresh-token and access-token records in a broker-owned SQLite Durable Object, transactional single-flight refresh, idempotent operation IDs, Retry-After cooldowns, and Spotify `/v1/me` identity verification before rotated-token commit.
- GitHub Actions consumers obtain short-lived access tokens via OIDC; no workflow has a direct Spotify refresh-token call or legacy refresh-token fallback. Nine workflow identities are exact-allowlisted on `refs/heads/main`.
- New hardening isolates broker-refresh rate limiting from browser OAuth limits: a dedicated `BROKER_REFRESH_RATE_LIMITER` uses 60 requests/minute with separate preview and production namespaces. Requests are first limited by Cloudflare's `CF-Connecting-IP` before JWKS verification, then by the verified OIDC `workflow_ref`. This avoids a single shared anonymous bucket starving all nine workflows and allows the broker client's bounded busy retries.
- Broker readiness now fails closed if either rate-limit binding, the encryption keyring, OIDC allowlist, Spotify client ID, or credential-store Durable Object is unavailable.
- The deployment workflow remains owner-only, verifies required secret bindings, deploys with Wrangler, and checks live query-string redaction plus `/ready` afterward.

### Cloudflare production state (read-only checked 2026-11-10)
- Worker: `shit-auth-broker`. Production deployment `cc312856-c717-49a1-a20a-45d3ed7950d2` still sends 100% traffic to legacy version `c166ef6f-d7aa-4b8f-951a-fff565636b17`.
- Live bindings include `OAUTH_STATE` and `SPOTIFY_REFRESH_LEASE`, but not `SPOTIFY_CREDENTIAL_STORE`; production does not yet serve `/internal/spotify/refresh`.
- Cloudflare metadata confirms `GITHUB_APP_CLIENT_SECRET`, `GITHUB_APP_PRIVATE_KEY`, and `SPOTIFY_CREDENTIAL_ENCRYPTION_KEYS` are `secret_text` bindings. Values were not read. The owner provisioned the encryption-key secret; independent secure backup remains unverified.
- Production observability still has `redact_query_string = false`. This blocks OAuth because callback URLs contain one-time `code` and `state` parameters. Do not initiate OAuth until the integrated deployment enables and independently verifies query-string redaction.
- PR config adds Durable Object migration v3 / `SPOTIFY_CREDENTIAL_STORE`, `BROKER_REFRESH_RATE_LIMITER`, and `redact_query_string = true`. Workers Builds remains upload-only (`npx wrangler versions upload`) under root `auth-broker`; production traffic promotion is owner-controlled through GitHub Actions.

### Remaining production gates
1. Confirm the encryption keyring has a secure independent backup. Never paste the key into chat, logs, or Git.
2. Keep PR #188 in draft pending an independent review of the integrated diff and a clean reconciliation plan for its 450-ahead/14-behind history. Exact-head broker, Durable Object, Python, Wrangler, Daily and full-history security checks pass; the exact-head Cloudflare preview deployment and `/health` probe both succeed.
3. Reconcile/merge the auth-only PR while preserving unrelated mainline Daily/Library updates; inspect the final combined diff.
4. Run the owner-only deployment workflow. Verify the new credential-store and broker-rate-limit bindings/migrations, live query-string redaction, and `/ready` before Spotify consent.
5. Complete owner-consented PKCE authorization; verify encrypted credential persistence without reading it back, then pass two independent broker-backed read-only auth-health checks.
6. Verify all nine workflows end-to-end while preserving playlist locks, previews/confirmation, snapshots, audits, rollback, and no-playlist-side-effect boundaries.
7. Only after the new path and rollback are verified, retire the legacy GitHub Actions refresh-token secret and remove obsolete App permissions with explicit owner approval.

### Actions in the current continuation
- Refreshed this session brief on `main` and the PR #188 description with verified repository and production state.
- Added per-IP and verified-workflow rate-limit buckets, a dedicated 60/minute broker limiter with isolated preview/production namespaces, readiness enforcement, and regression tests to the PR branch.
- The first CI attempt exposed missing test fixtures for the new binding; those fixtures were corrected. All three latest exact-head workflows subsequently passed.
- No production deployment, Worker setting change, Spotify OAuth exchange, credential-store initialization, GitHub secret mutation, playlist operation, or Library write was performed.

---

> **Purpose:** This is the curated context bridge between active ChatGPT work, the scheduled ChatGPT Buddy task, and the separate repository-hosted Codex experiment. It is not a raw chat transcript, does not contain private conversation material, and is not a real-time message channel.

## Current policy and session overlay — 2026-11-07

- **Daily live-cycle result (2026-11-07 UTC / 2026-11-06 Eastern; supersedes older Daily status entries below):** production workflow #42316296314 completed a real 60-track replacement; 26 prior tracks rotated out neutrally. Stage and recovery backup were committed before mutation; final Spotify read-back confirmed exact order, 60 unique valid URIs, zero blacklist hits, and description `Today's detour starts here.`. Post-cycle verify-only #42316824364 passed. GET-only snapshot refresh #42316906860 now records 60 accessible/unique tracks, baseline 60, blacklist 58, and zero new manual removals. Trigger is left at `action: verify-only`, `force: true`.
- **Daily operational follow-up:** next scheduled automatic rotation after cooldown persistence fix remains unverified; strict cron-to-DST matching and guided resume/rollback/discard remain open. `--verify-only` now bypasses the same-day completion guard and has a regression test; full suite #42316716912 passed 517 tests. Saved-item lookup now respects Spotify's 40-URI maximum; encoded-query feedback observer #42318532288 recorded current liked status for all 60 tracks. Their `liked_at_add` baseline remains unknown for this cycle due to the pre-fix 50-item request returning 400. The corrected helper is covered by the 519-test run #42317712007.
- **Daily recommendation memory is now an approved product requirement:** persist each recommendation event and connect later outcomes across cycles. Keep Spotify playback and Last.fm scrobbles separate; distinguish likes/saves, manual removal/blacklist, retention, ignored/no observed play, not-yet-observed and unknown coverage. Repeated recommendations remain distinct events linked to a track history. High-play-then-remove differs from unplayed-then-remove; track rejection does not automatically reject the artist. Use idempotent/versioned/recoverable/auditable Daily-scoped storage; never invent historical outcomes from null evidence or override exclusions. Design/implement after operational gate.
- **Current coverage:** Last.fm available; liked-song observations present; Spotify playback tracker unknown because `playback_data/segments.jsonl` is absent. Missing tracker coverage must never be interpreted as zero plays.

- Babel remains active, but ChatGPT may continue other explicitly authorized SHIT workstreams in parallel. Buddy remains a documentation-only worker focused on Babel.
- The current Buddy is the scheduled ChatGPT task using the connected GitHub app; the repository-hosted Codex/API workflow is a separate quota-blocked experiment and must not be retried without explicit user reauthorization.
- Today's Buddy run completed: run `a1354400-ad1c-8320-906e-888d071012ee` (scheduled 2026-11-06 09:00 Eastern; completed 15:04 UTC). It updated draft PR [#163](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/163), head `c8e4a2ad74b8c50868a6806abf9869b9da4b5725`, with 13 documentation files. Independent review outcome: **NEEDS CHANGES**. The draft incorrectly says ChatGPT may publish documentation only through a draft PR and must never write to `main`; current mainline `AGENTS.md` and `project/DOCUMENTATION_RULES.md` explicitly authorize independently verified documentation-only publication directly to `main`. No PR reviews or inline threads were present. Do not merge this contradictory draft.
- PR #163 CI evidence reported and independently rechecked: Daily curator tests run [#42239266411](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42239266411) completed successfully; public security scan [#42239266381](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42239266381) completed successfully. The test run reports 478 passing tests in Buddy's report. These checks do not resolve the policy contradiction or establish Babel completion.
- ChatGPT resumed Tricky Daily work in parallel with Babel after explicit user authorization for the force/idempotency and description-readback fixes, safe verification, and a Daily-only GET snapshot refresh. The runtime guard now bypasses only the clock-window check; the same-Eastern-date completion guard remains active for forced runs. The workflow and source overview comments have been aligned with that behavior.
- The Spotify description read-back helper now HTML-unescapes provider text before comparison. Focused regression coverage exists for encoded apostrophes and duplicate forced dispatches exiting before Spotify client construction.
- **Whitelist contract source/test verified:** only an explicit playlist-local whitelist row matching exact Spotify URI or normalized primary-artist/title identity clears that exact removal. Current playlist membership never clears a removal. It does not whitelist the artist or any other playlist. Current Daily whitelist count is zero. Source: `scripts/spotify/spotify_discovery.py`; tests: `tests/test_spotify_discovery.py` (`test_daily_live_reconciliation_records_only_missing_tracks_and_honors_whitelist`, `test_readded_removed_track_remains_blocked_without_explicit_whitelist`, `test_explicit_playlist_whitelist_overrides_removal`).
- **Current Daily snapshot:** snapshot workflow run #42263830309 captured 29 accessible/unique items at 2026-11-06T17:41:02.779553+00:00; baseline 29; blacklist 55; whitelist 0. The reference catalog reports 29 items and track/artist indexes have zero stale or missing Daily memberships. The prior 37-item snapshot is archived. This was GET-only; no playlist tracks or description were changed.
- **Snapshot workflow:** after fixing compatibility import precedence and Daily catalog/index reconciliation, run #42263830309 passed focused tests, credentials, live GET refresh, and publication. It captured 29 accessible/unique tracks; baseline 29; blacklist 55; whitelist 0; all stale/missing Daily track and artist index memberships were removed while preserving other playlists. Full generated-data audit and 481-test suite passed at that point. Later full safe CI run #42268351897 passed 500 tests.
- **CI status:** full safe run #42268351897 passed 500 tests, including generated-data audit and canonical Library health/confidence checks. It covers Daily force/idempotency, exact staging/hash/commit failure, repository-head concurrency, pre-write live snapshot checks, ambiguous write read-back, exact post-write order/count/uniqueness/blacklist checks, pending-stage retry blocking, and stage-only no-write behavior.
- **Publication safeguards:** implemented immutable SHA-256 staging committed before mutation, committed-blob verification, repository-head check, two live pre-write snapshot/policy checks, ambiguous-write read-back reconciliation, exact post-write order/count/uniqueness/blacklist validation, and a same-date pending-stage guard. Guided resume/rollback/discard remains open.
- **Stage-only attempt:** push-triggered run #42268583897 (event `push`; display title “Trigger safe Daily stage-only durability verification”, not a scheduled midnight cycle) authenticated but Spotify returned HTTP 429 QUOTA_EXCEEDED during candidate search with Retry-After 5781 seconds. It failed before stage creation/commit; the workflow log confirms no playlist changes were attempted. The durable deadline in `.github/spotify_api_cooldown.json` is `2026-11-06T19:49:46+00:00` (14:49:46 Eastern). No Spotify requests were made after that failure.
- **Candidate artifact:** 195 historical Spotify-resolved candidate URIs across 105 artists; 134 Daily-source and 61 Booze-preview-source rows. Do not mix the Booze rows into Daily automatically. Saved listening evidence is null, so this is not a freshly scored 60-track stage.
- **Latest documentation CI:** curator tests #42270239847 and security scan #42270239536 passed on main commit `b278da8f4f81bd8202fda50d6ed457e4ccfcb62e`.
- **Cooldown regression coverage restored:** PR #169 merged as `8d0d2d5e8b0448fde64932aced1014ef944e3312`. Final PR CI #42272711018 passed all 512 tests and security scan #42272711156 passed. Post-merge mainline tests #42272911280 passed all 512 tests and post-merge security scan #42272911119 passed. The three tests now cover Retry-After persistence, active-cooldown blocking, and expired-cooldown allowance under normal unittest discovery.
- **Quota-safety improvement:** PR #170 merged as `397218ebf4e397ec4a8fd3a1d1ec6e23aefe8db2`. It parses delta-seconds and HTTP-date Retry-After values; missing/unusable headers persist `manual_clear_required: true`, blocking all Spotify requests until verified manual clearance. PR test #42273342714 passed 514 tests and security scan #42273342665 passed. Post-merge mainline tests #42273509046 and security scan #42273509063 both passed. Manual-clear procedure is documented in `docs/SPOTIFY_API_OPERATIONS.md`.
- **Buddy review checkpoint:** daily Buddy run `a1354400-ad1c-8320-906e-888d071012ee` completed today; PR #163 remains open/draft at head `c8e4a2ad74b8c50868a6806abf9869b9da4b5725`. Current independent review remains **NEEDS CHANGES**: the full 13-file draft contains policy text forbidding ChatGPT direct documentation publication to `main`, contrary to current mainline `AGENTS.md` and `project/DOCUMENTATION_RULES.md`. Do not merge it. No reviews/inline threads are present; its prior reported checks are green but do not cure the policy contradiction.
- **Feedback nuance under review:** artist-level negative feedback currently increments for any removed track with at least one measured post-add play or Last.fm scrobble, even if that track was played many times or is the artist's only removed track. Exact track blocks remain absolute. Do not change scoring weights until a conservative multiple-removal/engagement rule is designed and tested.
- **Next executable action:** after the persisted cooldown expires, re-check current time and cooldown state, then retry only the protected no-write stage-only verification and confirm the GitHub stage commit/read-back path. Do not run a live track cycle or description mutation without separate user authorization.
## Operating rule

During every active SHIT work session, ChatGPT must maintain this file as work proceeds. Update it after each material user decision, scope change, implementation change, source finding, test/audit result, failure, uncertainty, or blocker—not merely at session end. Update the affected goal `ROADMAP.md` and `ACTIONS.md` in the same session; also update `NEXT_WORK.md`, `LOOSE_ENDS.md`, and `PROJECT_LOG.md` when cross-project state or major decisions change.

Buddy must read this file at the start of every run, then reconcile it against the checked-out source, tests, workflow definitions, current branch, and recorded evidence. This brief is a navigation and context aid, not authority to override newer verified source or evidence. If it conflicts with source or fresh evidence, report and resolve the discrepancy rather than repeating stale claims.

Updating this file does not wake Buddy, alter an already-running job, or deliver a live message. Buddy sees committed updates on its next scheduled or manually dispatched run.

## Identity and roles

- Repository/product: **Spotify Helper & Information Tracker (SHIT)**.
- Documentation system: **SHIT Documentation & Continuity**, internal codename **Babel**.
- Documentation worker: **Buddy** in repository documentation and everyday references. Its OpenAI agent identifier is **SHIT-Buddy**, reserved to distinguish it from possible future agents.
- ChatGPT is responsible for active project work, keeping this brief and project records current, and reviewing Buddy's proposals.
- Buddy is a documentation partner only. It may audit and improve documentation, continuity records, roadmaps, action logs, and narrowly scoped documentation-contract tests. It must not perform SHIT runtime/product development or Spotify/Last.fm operations.
- ChatGPT may independently publish verified documentation-only maintenance directly to `main` under `AGENTS.md` and `project/DOCUMENTATION_RULES.md`. Buddy is separate and proposal-only: it may update its dedicated branch and draft PR, but may not write to `main`, approve, mark ready, close, merge, or self-merge.

## Current priority

**Babel remains active, and explicitly authorized SHIT workstreams may proceed in parallel.** ChatGPT may resume bounded SHIT feature work while Buddy remains focused on Babel. Operational/runtime changes, provider operations, generated data, and playlist writes still require specific user authorization and must follow the relevant workstream safeguards.

Success means a new assistant with no prior chat history can identify the repository's goals, current verified state, constraints, evidence, unresolved risks, and next executable action from repository files alone.

## Deferred post-Babel objective — SHIT-wide integrity, diagnostics and recovery

After Babel is judged as complete and realistically as good as it can be, revisit a dedicated SHIT-wide **Integrity, Diagnostics & Recovery** workstream. This is explicitly deferred; it does not expand the current documentation-only priority or authorize runtime implementation now.

The intended design is a coordinated health system: (1) health monitoring across project data, documentation, tests and workflows; (2) diagnostics that trace symptoms to likely root causes; (3) bounded recovery/repair for deterministic, reversible cases; (4) Buddy as the permanent Documentation & Continuity Guardian, checking documentation drift, roadmaps, handoffs and evidence; and (5) an improvement backlog for recurring failures and systemic weaknesses. Buddy contributes evidence and documentation maintenance but is not the sole health authority and must not approve its own risky repairs.

Safety contract to carry forward: observe and diagnose by default; preserve canonical data and provenance; distinguish authoritative Last.fm scrobbles from optional Spotify playback observations; never invent, silently delete, or silently rewrite uncertain records; only allow explicitly scoped, deterministic, backed-up, reversible repairs with audit trail and post-repair verification; require user approval for consequential or ambiguous changes. Revisit and formalize scope, ownership, autonomy levels, health dimensions, audit records and acceptance criteria only after Babel's completion gate and cold-start simulation pass.

## Historical repository-hosted Codex/API experiment (not the current Buddy path)

- Workflow: `.github/workflows/babel-ai-continuation.yml`.
- Instructions: `.github/babel/CONTINUATION_PROMPT.md`.
- Durable worker state: `project/BABEL_AGENT_STATE.md`.
- Proposal branch: `babel/agent-progress`.
- The user has reported adding the OpenAI API key to GitHub repository Actions secrets under the exact name `OPENAI_API_KEY`. Secret values must never be read, printed, copied, or documented.
- The first dispatch run is now verified: run [#42181953313](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42181953313) completed with failure. Preflight passed; Codex failed before prompt execution; validation and publisher were skipped. Do not claim activation.
- The user has now confirmed **Settings → Actions → General → Workflow permissions → Allow GitHub Actions to create and approve pull requests** is enabled.
- Workflow trigger enhancement: `.github/workflows/babel-ai-continuation.yml` listens for a push to a `babel/dispatch-*` branch when `.github/babel/dispatch.json` changes. On 2026-11-06, ChatGPT successfully created `babel/dispatch-20261106-01` from `main` and committed `.github/babel/dispatch.json` in commit `7c1abce763d293992872699146eb7f13d10f9b87`. This is the first successful ChatGPT-initiated GitHub write intended to dispatch Buddy. The dispatch branch is only a trigger; preflight/agent/validation/publisher continue to use `main` or `babel/agent-progress` as before. Manual dispatch and the six-hour schedule remain available.
- The marker push successfully triggered run [#42181953313](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42181953313) on commit `7c1abce763d293992872699146eb7f13d10f9b87`. Preflight passed. Codex failed before prompt execution because `ubuntu-latest` resolved to Ubuntu 26.04 and the action's `drop-sudo` D-Bus socket restriction failed (`runner is not a member of the sudo group` / `Could not restrict access`). This matches upstream [openai/codex-action issue #188](https://github.com/openai/codex-action/issues/188). Validation and publisher were skipped; no Buddy PR was created. The workflow's Codex agent job is pinned to `ubuntu-24.04` as a workaround, retaining `drop-sudo` and all existing permission boundaries.
- Retry marker `75d3102e80ffe4158214114fa90c5979edda14e6` on `babel/dispatch-20261106-02` triggered [run #42183337573](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42183337573). Preflight passed; the Ubuntu 24.04 Codex job completed `drop-sudo` isolation; Codex then returned `Quota exceeded. Check your plan and billing details.` Validation and publisher were skipped; no patch or PR was created. The runner fix is verified; the remaining blocker is API quota/billing. Do not retry until the user confirms quota is available.
- Continuity rule is now propagated into `AGENTS.md`, `project/DOCUMENTATION_RULES.md`, `docs/BABEL_AGENT.md`, `project/BABEL_AGENT_STATE.md`, the Buddy continuation prompt, the Maintainability & Documentation roadmap/action log, `project/NEXT_WORK.md`, and `project/PROJECT_LOG.md`. Latest supporting commits include `675351e` (worker state) and `7770474` (project log).
- Post-quota verification must confirm the Codex job succeeds, independent validation passes path/deletion checks and full unittest discovery, and the publisher creates or updates the isolated proposal branch/PR. No automatic merge.

## Current repository findings and evidence to reconcile

Read `project/NEXT_WORK.md`, `project/LOOSE_ENDS.md`, `project/PROJECT_LOG.md`, and `project/goals/maintainability-documentation/{ROADMAP.md,README.md,ACTIONS.md}` for the full current audit history and evidence. The following are high-priority carry-forward items from the current handoff; re-check them against current source and live GitHub state before relying on them:

1. Finish source-to-document semantic review of maintained implementation modules, compatibility launchers, test modules, workflows, and technical guides. Prioritize high-risk side effects, credentials, provider access, write boundaries, recovery and evidence semantics.
2. Reconcile all goal roadmaps/action logs, workflow permissions/triggers/publication behavior, open PRs/issues, and the loose-ends register.
3. The Tricky Daily `--force`/same-Eastern-date idempotency discrepancy is corrected and CI-verified: force bypasses the clock gate only. Continue to preserve the same-date completion guard.
4. Preserve the distinction between canonical Last.fm scrobbles and optional Spotify playback-tracker observations. A playlist appearance, recommendation, or saved snapshot is not proof of a play, scrobble, like, or listening.
5. Treat stale snapshots, generated reports, open PR branches, and previous CI runs as historical evidence until freshly checked. Do not merge divergent PR #161 wholesale.
6. Complete a cold-start simulation using only repository documentation and record exact results.

Previously observed test evidence: full unittest discovery passed 478 tests in workflow run #42178656402 on commit `69e72829c6cc9e72837025f8c777b4d846c9ba7b`. This is historical evidence for that commit, not proof that the current HEAD or Buddy workflow has passed. Current mainline Daily curator tests #42270239847 and public security scan #42270239536 both passed on `b278da8f4f81bd8202fda50d6ed457e4ccfcb62e`.

## Required update format

Keep this brief concise and current. Use these headings when updating:

- **Current objective and success criteria**
- **Material decisions and authorization boundaries**
- **Current work / affected files / branch / PR**
- **Findings and verification evidence**
- **Failures, uncertainty, and blockers**
- **Buddy's next documentation/audit task**
- **Next executable action**

For each test or workflow claim, include the exact command or run URL/ID, commit/ref, outcome, and what it does—and does not—prove. Preserve failures and uncertainty. Do not invent timestamps, test outcomes, branch state, or completed work.

## Privacy and security

This is a curated project brief, not a chat dump. Include only SHIT project context needed for continuation. Exclude unrelated personal conversations, personal or sensitive details, private messages, API keys, secret values, tokens, credentials, and unnecessary account information. Refer to credentials by variable/secret name only.
