# Active SHIT Session Brief

## Current authentication session overlay — 2026-11-09

### Current objective and success criteria
Finish SHIT-wide centralized Spotify authentication: the broker owns the only long-lived refresh credential, performs serialized refresh/rotation inside its encrypted Durable Object, and gives authorized GitHub Actions jobs only short-lived access tokens through OIDC. Complete fresh owner consent only after the integrated Worker is deployed and verified. Authentication must never modify playlists.

### Material decisions and boundaries
- Continue the previously user-authorized auth implementation in parallel with the Jockey's Tricky Daily priority; do not reassign or edit Jockey work.
- Target architecture is broker-owned encrypted refresh-token custody, not a permanent GitHub Actions `SPOTIFY_REFRESH_TOKEN` secret. The secret remains legacy on current `main` until the migration is merged and verified; no dual-write or fallback.
- Keep production release owner-controlled. Do not read or change secret values, initiate consent on the user's behalf, or touch Spotify playlists.
- PR #189 belongs to the separate `engineering/general` branch; leave it untouched.

### Current work / branch / PR
- Current main: `50202a4a394ea68582f02a4ab18ce9091f7f3e4b`.
- PR #185 merged `8cd28530081c519112fd947ac7bb05edc0ce7b04`; PR #190 merged `0266b0f124c67fdecae8b83ef89ffe0c6aa478b3`; PR #191 merged `50202a4a394ea68582f02a4ab18ce9091f7f3e4b`.
- PR #187 branch `feature/broker-owned-spotify-credential-store`, head `1c8e6b46c292525c3a13019325a270d91f97a84d`, draft/unmergeable. Broker tests and Wrangler dry-run passed in #42598447923; security scan #42598447639 was pending at last check.
- PR #188 branch `feature/oidc-broker-refresh-endpoint`, head `5e39177daeb0695d7230b199c9c37f6edc6999f2`, draft/unmergeable, stacked on PR #187. Previous head `f4889ae4ef37b6e1aeaff5d25cb04fe0b99bef45` passed broker tests, SQLite Durable Object integration, Python regression suite, documentation checks, dependency audit and Wrangler dry-run in #42598096634; security scan #42598096535 passed. New callback-stage diagnostics/tests are awaiting fresh CI.
- PR #187 is 130 ahead / 3 behind main; PR #188 is 267 ahead / 5 behind its PR #187 base. Resolve ancestry and conflicts before merge. Do not force-update.
- PR #189 is a separate `engineering/general` draft and remains untouched.

### Production / provider findings
- Cloudflare Worker `shit-auth-broker` version 14 (`06bb7f3a-da70-449f-9f51-72423c693fa1`) is active at 100% traffic; created 2026-11-09 09:46:17 UTC.
- Active version metadata shows migration tag v2 and only `OAUTH_STATE` and `SPOTIFY_REFRESH_LEASE`; no `SPOTIFY_CREDENTIAL_STORE`, encryption keyring, active key version, or Spotify client-secret binding.
- Cloudflare metadata confirms `GITHUB_APP_CLIENT_SECRET` and `GITHUB_APP_PRIVATE_KEY` are `secret_text`; values were not read.
- Cloudflare Workers Builds config: root `auth-broker`, no build command, production upload `npx wrangler versions upload`, preview `npx wrangler preview`; auto-build/previews enabled. Production promotion remains owner-controlled.
- Redacted Workers Observability query for the prior 24 hours (ending 2026-11-09 10:08 UTC) found six callback failures: four on version 13 at `broker.base_url_configuration`, two on version 14 at `broker.route_dispatch` (`UnexpectedError`). No exception contents, OAuth codes, tokens, cookies, state values or secret values were retrieved.
- PR #188 adds safe fixed-stage callback instrumentation through GitHub App JWT/installation, concurrent-workflow check, Spotify exchange/scope/identity, encrypted store write, health dispatch, completion-state storage and redirect. Wait for fresh checks before another consent attempt.
- No successful credential persistence, auth-health result, or playlist operation has been verified.

### Buddy daily-check gate
- Automation `SHIT Buddy — Babel documentation only` is disabled.
- Latest successful report-bearing Buddy result: 2026-11-07.
- 2026-11-08 run recorded failed; no successful report-bearing run exists for 2026-11-09.
- Status: **Buddy pending today — disabled**. Do not enable it or modify its branch/PR without user direction.

### Next executable action
1. Check fresh CI for PR #187/#188 latest heads.
2. Reconcile the stacked branches with current main and independently inspect the combined diff; keep both drafts until mergeability and all checks are clean.
3. Add fail-closed deployment checks for the missing encryption keyring, active key version, Spotify client secret and exact OIDC workflow allowlist.
4. After owner-controlled deployment, verify the integrated version receives 100% traffic, then ask the user to complete a fresh OAuth flow.
5. Verify encrypted credential persistence and two independent read-only auth-health runs; keep all playlists untouched.

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
