## 2026-11-23 — Final post-checkpoint head verification

- **Verified PR head:** `7c7da5c7f6199070161672e1c57f43cb3e29517d`, branch `babel/chatgpt-buddy-v2`, 78 ahead / 16 behind current `main`, open/draft, 12 changed files.
- **Exact-head CI:** Daily curator tests [#45207299259](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/45207299259), Mobile Auth Broker Tests [#45207299393](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/45207299393), and public repository security scan [#45207299147](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/45207299147) all completed successfully on this exact head.
- **Relevant job steps:** the Daily job passed compilation, generated-data audit, read-only canonical Library checks, maintained-file documentation check, and unit tests. The broker job passed broker security tests, Cloudflare SQLite Durable Object integration tests, maintained Python documentation checks, and Worker bundle/Wrangler validation without deploying; `commit-lockfile` was skipped. The full-history security scan passed.
- **Independent diff review:** PASS for the complete 12-file PR diff. The six-file documentation batch is within the allowed Markdown/goal scope; all six changed files were read back. The external Trio Protocol link intentionally targets PR #202's branch because the file is not on main, and the branch-local link test skips external URLs.
- **Remaining merge gate:** PR #201 remains draft. The four #201/#202 shared files have been reconciled on Buddy's branch, but no merge order is approved. PR #200 also overlaps the active-session brief and loose-ends register. Do not merge #201/#202 until the shared-file state and merge order are explicitly reconciled.
- **Successor readiness:** Jockey and Boots remain BLOCKED (both automations disabled). Jockey's PR #200 exact-head checks pass, but its branch is 10 behind and its run report records accidental direct-to-main writes. Boots is 87 behind, has no PR, and has no exact-head CI. Buddy's current run `1fc98dce-5084-8324-8cb7-7b32344cc84d` remains in progress; its latest completed result is still the prior Nov 22 run `e560322d-6ac8-8332-84aa-98b2b5816aeb`. Environment details remain unknown for all three.
- **Workers Builds:** no separate exact-head Workers Builds result was surfaced; the broker job's Worker bundle validation explicitly ran without deploying.
- **Checkpoint boundary:** this action-log update changes the Buddy PR head. The checks above apply to `7c7da5c`, not the new head created by this entry. Re-fetch and verify exact-head CI on the resulting head before treating the PR as check-clean.
- **Next:** verify the new head, keep PR #201 draft, obtain an owner-approved merge order, and continue the maintained-file/source-guide semantic audit and fresh-session simulation. No other worker's branch, PR, task, prompt, schedule, environment, workflow, provider, playlist, or canonical Library was changed.

## 2026-11-23 — Post-reconciliation diff review and exact-head CI

- **Verified PR head:** `b0a67d3ccdcc462da35cefe8c8a614586bd66f3a`, branch `babel/chatgpt-buddy-v2`, 73 ahead / 16 behind current `main`, open/draft, 12 changed files.
- **Independent diff review:** PASS. Re-read all six files changed in the shared-handoff batch and reviewed the complete 12-file PR patch. The four #201/#202 shared files now preserve the Buddy v2 policy and Trio handoff responsibilities; the protocol link targets PR #202's review branch because the file is not on `main`. PR #200's additional overlap on the active-session brief and loose-ends register is documented. No out-of-scope paths were changed.
- **Exact-head CI on `b0a67d3`:** Daily curator tests [#45206108429](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/45206108429) passed, including compilation, generated-data audit, read-only canonical Library checks, maintained-file documentation check, and unit tests. Mobile Auth Broker Tests [#45206108450](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/45206108450) passed, including broker security tests, Cloudflare SQLite Durable Object integration tests, and non-deploying Worker bundle/Wrangler validation; `commit-lockfile` was skipped. Public repository security scan [#45206108650](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/45206108650) passed.
- **Workers Builds:** no separate exact-head Workers Builds result was exposed by the available read-only workflow-run query. Do not claim a preview build or deployment for PR #201.
- **Merge gate:** PR #201 remains draft. PR #202 remains separately open/draft; no merge order is approved. PR #202's proposed #202-first sequence is not authorization, and PR #200 also overlaps the active-session brief and loose-ends register. Do not merge #201/#202 until all shared files and the order are reconciled.
- **Successor readiness:** Jockey and Boots remain BLOCKED because both automations are disabled; Jockey's PR #200 exact-head CI passed but its branch is diverged, while Boots has no PR and no exact-head CI acceptance. Buddy's current scheduled run remains in progress with no result for today's run yet. Environments for all three tasks remain unknown because selection is inherited and no environment details were returned.
- **Checkpoint boundary:** this action-log update is another documentation-only commit and changes the Buddy PR head. The passing checks above apply to `b0a67d3`, not the new head created by this entry. Re-fetch the resulting head and verify its exact-head CI before reporting review-clean status.
- **Next:** verify the final post-checkpoint head, keep PR #201 draft, obtain an owner-approved merge order, and continue the semantic coverage/cold-start audit. No other worker's task, prompt, schedule, environment, branch, PR, workflow, provider, playlist, or canonical Library data was changed.

## 2026-11-23 — Reconciled Buddy/Trio shared handoff files; successor checks BLOCKED

- **Selected task:** complete the Buddy-owned PR #201 / PR #202 shared-file reconciliation after performing the mandatory read-only successor-readiness check.
- **Current main:** `f3387a29ad2a97017a80968ec1a047a97118c618`. The open-PR inventory was refreshed; PRs #201/#202/#200 are open/draft. PRs #161/#162 were inspected read-only and left untouched.
- **Buddy automation:** `6aed3a70baf88191ab1dbfaa8f7dba91` enabled. Current run `1fc98dce-5084-8324-8cb7-7b32344cc84d` is in progress (scheduled 09:00, started 10:17 Eastern); latest completed result still belongs to prior run `e560322d-6ac8-8332-84aa-98b2b5816aeb`. Today's report is pending. Environment selection is inherited and actual status is unknown.
- **Jockey readiness: BLOCKED.** Automation `6af1645551a48191900c77833073fdfd` is disabled. Last run `ae49786b-46e0-8321-949d-9f139020df47` is recorded completed and its matching result reports accidental direct-to-main writes followed by a stop. Branch `engineering/priority` / PR #200 head `4f0291b8990987ca5bb84bdea06d6d6bad1113fe` is 67 ahead / 10 behind; exact-head Daily #44928121273, broker #44928121259, and security #44928121262 passed. Environment status is unknown. The task remains disabled and the branch diverged; no repair or enablement was attempted.
- **Boots fallback readiness: BLOCKED.** Automation `Automation_2e1357c87e688191829bd2380047f46d` is disabled. Last run `a030ee14-e434-832d-a8cc-b462d8e88ed7` is recorded completed and its matching result reports a safe stop on the stale branch. `engineering/general` head `a58e6b7d953428adf9932499a79234fc2ed06150` is 14 ahead / 87 behind, with no matching open PR or exact-head CI acceptance. Environment status is unknown. No repair or enablement was attempted.
- **Buddy/Trio PR evidence:** PR #201 at pre-batch head `b91254ff1dec0a0e62f1083d82be8877996085eb` was 65 ahead / 16 behind; its exact-head Daily #45083951234, broker #45083951231, and security #45083951241 passed. PR #202 head `8d4a25e2516d404610fdf6cd9e1e9c55f062b6e0` was 68 ahead / 16 behind; exact-head additional tests #45097778021, full tests #45097778095, and security #45097778028 passed. These are pre-reconciliation heads, not evidence for the new Buddy head.
- **Shared-file findings:** #201 and #202 overlap on `docs/BABEL_CHATGPT_BUDDY.md`, `docs/README.md`, `project/ACTIVE_SESSION_BRIEF.md`, and `project/LOOSE_ENDS.md`. PR #200 also changes the last two handoff files. The Trio Protocol file exists on PR #202's branch but not on main, so Buddy's links target that review branch until #202 is merged. PR #202's description proposes #202 first, then Buddy reconciles #201; this is not an approved merge order. **Do not merge #201 or #202 until shared files and merge order are reconciled.**
- **Files changed in this batch:** the four shared Buddy-owned files above plus this goal's `ROADMAP.md` and `ACTIONS.md`. The Buddy guide now documents Buddy → Jockey → Boots → Buddy, including the disabled/failed/incomplete/missed-window/blocked-branch fallback to Boots. The docs index now includes the protocol in Start here while preserving the Daily recommendation-memory entry and 22-workflow count. The active-session brief and loose-ends register now contain current automation/run/branch/PR/CI evidence and label older snapshots as historical.
- **Link handling:** current main returns 404 for `project/TRIO_COORDINATION_PROTOCOL.md`; the file is proposed on PR #202 only. A direct GitHub URL to that branch is used so the all-Markdown local-link test will not see a broken local path. Convert it to a relative link after PR #202 merges.
- **Scope and verification boundary:** no other worker's branch/PR, task, prompt, schedule, environment, workflow, production setting, secret, provider, playlist, or canonical Library data was changed. No workflow was manually dispatched and no tests were run manually. The six-file documentation batch was published as sequential commits; its resulting PR #201 head must be checked anew. Fresh exact-head CI and complete-diff/read-back review are required before the draft is considered review-clean.
- **Next:** re-fetch PR #201's final head and complete changed-file list; verify its exact-head tests/security checks; keep #201 draft; leave #202/#200 and their owners' work untouched. No full runtime Phase 1 cycle has been observed; Phase 2 cross-repair remains disabled.

## 2026-11-22 — Rechecked Buddy draft diff and exact-head CI

- **Selected task:** independently review the existing Buddy proposal after the prior report left final-head CI and changed-file accounting unresolved.
- **Repository/PR state:** current `main` was `dc27f576b5d4657a34f56ec8174b4a5fb7b8f1c2` at the pre-checkpoint read. PR [#201](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/201) was open/draft from `babel/chatgpt-buddy-v2`, pre-checkpoint head `af9b7bc4f2a49525b7bb90c998e32239e8fec038`, 62 commits ahead / 12 behind; GitHub reported mergeable. Its exact changed-file list is 12 paths: 11 Markdown files and one `tests/test_documentation_contract.py` file. All paths are within Buddy's allowlist.
- **Independent diff review:** reviewed all 12 file patches, including the follow-up roadmap/action-log changes. The worker identity, v2 branch reference, historical Codex/API boundary, 22-workflow and 14-goal structural counts, and documentation-contract assertions are internally consistent with the checked source/evidence available for this batch. No runtime/product implementation, workflow logic, permissions, secrets, provider, playlist, canonical Library, generated-data, or unrelated engineering paths are changed.
- **Previous-head CI:** Daily curator tests [#44919616098](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/44919616098), Mobile Auth Broker Tests [#44919616118](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/44919616118), and public repository security scan [#44919616125](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/44919616125) all completed successfully on head `396597c`.
- **Intermediate-head CI:** on head `02739f3`, Daily curator tests [#45034570073](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/45034570073), Mobile Auth Broker Tests [#45034570048](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/45034570048), and public repository security scan [#45034570070](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/45034570070) were in progress at the last query. The subsequent documentation-only checkpoint commits require fresh exact-head CI; their result was not available in this run.
- **PR description correction:** the existing PR body said “Six Markdown documents and one” test, but the complete changed-file list shows 11 Markdown files plus one documentation-contract test. The PR body was corrected to match the actual 12-file diff, distinguish previous-head passes from newer checks, and state the unavailable Workers Builds result.
- **Cross-PR coordination:** separate draft PR [#202](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/202) remains untouched. Its changed-file list overlaps PR #201 on `docs/BABEL_CHATGPT_BUDDY.md`, `docs/README.md`, `project/ACTIVE_SESSION_BRIEF.md`, and `project/LOOSE_ENDS.md`. Preserve both branches; reconcile the shared-file merge order before any merge.
- **Verification boundary:** the new roadmap/action-log commits are documentation-only and cause another PR head; fresh exact-head CI must be checked before review can pass. No tests were run manually, no workflows were dispatched, and no provider or playlist operations occurred.
- **Next:** inspect fresh checks on the resulting PR head, obtain the exact-head Workers Builds result if available, then reconcile shared-file overlap with PR #202 without modifying its branch. Keep the semantic audit and cold-start simulation open; Babel remains in progress.


## 2026-11-21 — Reconciled latest scheduled Codex/API failures

- **Selected task:** verify whether the historical Codex/API workflow had run after the earlier quota report, then reconcile its execution status across Babel guides and state.
- **New evidence:** GitHub recorded scheduled workflow run [#44808721608](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/44808721608) on 2026-11-20 20:09 UTC and [#44878119328](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/44878119328) on 2026-11-21 06:59 UTC. Both were `event: schedule`, both had successful preflight, both failed in the Codex agent with the exact response `Quota exceeded. Check your plan and billing details.`, and both skipped validation and publication. No candidate patch or PR was produced.
- **Interpretation:** these runs prove the scheduled workflow triggered at those times and reached the Codex API; they do not expose the workflow's current enabled/disabled setting. The available read-only GitHub API did not provide that setting. No secret value or credential was inspected.
- **Safety:** Buddy did not manually dispatch, retry, disable, or change the Codex workflow. Do not request API funding or retry it. If scheduled Codex execution is unwanted, the repository owner must disable the workflow in GitHub Actions or separately authorize a workflow change. Buddy must not change workflow logic/settings.
- **Files reconciled:** `docs/BABEL.md`, `docs/BABEL_AGENT.md`, `docs/BABEL_CHATGPT_BUDDY.md`, `docs/WORKFLOWS.md`, `project/BABEL_AGENT_STATE.md`, `project/LOOSE_ENDS.md`, and the Maintainability & Documentation README/ROADMAP/ACTIONS now distinguish these scheduled failures from the active ChatGPT Buddy.
- **Handoff coordination:** updated `project/LOOSE_ENDS.md` with the latest scheduled Codex failures and live worker-status evidence. `project/ACTIVE_SESSION_BRIEF.md` and `project/NEXT_WORK.md` remain untouched because separate draft PR #202 modifies those files and carries stale live-status claims; reconcile them after its owner refreshes the proposal. PR #202 and all other user-owned branches/PRs remain unmodified.
- **Verification:** workflow run job records show preflight success, agent failure, validate/publish skipped; agent logs were inspected only for the quota error and no secret values were exposed. No workflow was manually dispatched and no tests were run manually. The documentation changes require fresh PR #201 CI and complete-diff/read-back verification.
- **Next:** re-read the updated files, inspect the final PR #201 head/checks, then reconcile the overlapping handoff files without modifying PR #202. Babel remains in progress.

## 2026-11-21 — Independently reviewed Buddy repair proposal and corrected stale roadmap claims

- **Selected task:** independently review the existing Buddy draft PR and reconcile the Maintainability & Documentation roadmap's remaining Codex/activation and inventory-count contradictions.
- **Audit baseline:** current `main` was `602b2848ea29653dc3c28eb9e10950ef0e75bf0f`. PR [#201](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/201) was open/draft from `babel/chatgpt-buddy-v2`, head `67df681f8227b04b4cfe6137a7fcfce544fb25cb`, 39 commits ahead / 4 behind main, and GitHub reported mergeable/clean. It contained 12 changed files, all under `docs/` and `project/` plus `tests/test_documentation_contract.py`; no runtime, workflow, secret, permission, provider, playlist, canonical Library, or generated-data paths were changed.
- **Exact-head CI at audit start:** test job [#44917313328](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/44917313328), second test job [#44917313386](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/44917313386), full-history security scan [#44917313377](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/44917313377), and Workers Builds check [#136886054340](https://github.com/TrickySturluson/spotify-helper-information-tracker/runs/136886054340) all completed successfully. `commit-lockfile` was skipped. No PR review submissions or inline review threads existed.
- **Independent review finding:** the PR's documentation changes correctly distinguish the scheduled ChatGPT Buddy from the separate historical Codex/API experiment, but the Maintainability roadmap still mislabeled Codex failures as Buddy activation, retained stale 18-workflow/13-goal/21-guide counts as current, and the docs index still said 21 workflows. The workflow catalogue also retained generic API activation wording. These are corrected in this batch.
- **Current structural evidence:** a non-truncated recursive `.github` tree contained 22 workflow YAMLs; the catalogue contained 22 matching workflow rows. A non-truncated recursive `project/goals` tree contained 14 goal directories, each with `ROADMAP.md`, `README.md`, and `ACTIONS.md`. The `docs/` tree contained 26 Markdown files including `README.md` (25 non-index documents). These counts do not complete the semantic audit or replace a refreshed full maintained-file inventory.
- **Cross-PR coordination:** PR #202 is a separate open draft and modifies `docs/README.md`, `project/NEXT_WORK.md`, `project/ACTIVE_SESSION_BRIEF.md`, `project/LOOSE_ENDS.md`, `project/PROJECT_LOG.md`, `AGENTS.md`, and other coordination files. It overlaps PR #201 on the documentation index and several handoff surfaces. PR #202, PR #161, PR #162, and legacy PR #163 were not modified. Keep the Buddy and coordination branches separate and recheck mergeability after this batch.
- **Changes in this batch:** corrected the workflow count in `docs/README.md`; labeled Codex API activation details in `docs/WORKFLOWS.md` as historical and unauthorized without explicit reauthorization; replaced the roadmap's stale Buddy/Codex activation narrative, refreshed current structural counts, and made the next action reflect the PR #201/#202 overlap.
- **Verification boundary:** the checks above apply to the audit-start head `67df681f`. This documentation batch creates a new PR head and requires fresh exact-head checks plus a final diff/read-back review. No tests were run manually and no workflow was manually dispatched.
- **Next:** inspect the final PR #201 head and complete changed-file list, verify fresh CI, then reconcile overlapping handoff/index changes with PR #202 without modifying its branch. Keep the fresh-session simulation and full semantic audit open; Babel remains in progress.

# Maintainability & Documentation — Actions & Evidence

## 2026-11-21 — Corrected legacy Codex workflow execution-state documentation

- **Selected task:** reconcile the historical Codex/API experiment's documented "dormant" status with the actual workflow source and the current scheduled ChatGPT Buddy.
- **Source evidence:** `.github/workflows/babel-ai-continuation.yml` still declares a six-hour cron schedule, manual `workflow_dispatch`, and a push trigger for `babel/dispatch-*`. Its preflight sets `enabled=false` when `project/BABEL_AGENT_STATE.md` contains the exact `status: complete` sentinel or when `OPENAI_API_KEY` is absent. The state file remains `status: active` because Babel acceptance is not complete. The secret's presence/value was not inspected or verified.
- **Uncertainty:** the available read-only GitHub endpoint did not expose the repository-level workflow enabled/disabled state. Therefore the Codex workflow cannot be described as disabled or guaranteed dormant. No Codex workflow was dispatched or retried.
- **Safety correction:** clarified that the current worker is the scheduled ChatGPT task using the connected GitHub app; the Codex workflow is a separate quota-blocked experiment. The owner must disable the workflow in GitHub Actions if no scheduled API execution is wanted, or separately authorize a workflow change. Buddy will not change workflow logic/settings or use `status: complete` as a pause switch.
- **Current Buddy evidence at audit start:** the scheduled ChatGPT Buddy automation was enabled; its current execution was marked in progress, with no completed result available. Draft PR [#201](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/201) was open at head `6028a605fe75bf40446b20760d409a61f7898e83`, 14 commits ahead / 3 behind main, with GitHub reporting mergeable/clean. Exact-head test, security, and Workers Builds checks were successful; no review submissions or threads existed.
- **Other PRs:** legacy PR #163 is closed; user-owned documentation PR #161 and connectivity proof PR #162 remain open/draft and were inspected read-only, with no submitted reviews or inline threads. Neither was modified.
- **Scope:** documentation and one documentation-contract assertion only. No workflow YAML, runtime code, secrets, permissions, provider, playlist, canonical Library, or generated data was changed.
- **Verification:** each changed file was read back from GitHub after its update. Fresh exact-head checks and a complete diff review are required after this batch; prior green checks are not a substitute.
- **Next:** confirm repository-level Codex workflow disablement or obtain explicit owner authorization before any Codex API execution. Continue the source-to-guide audit and fresh-session simulation; Babel remains in progress.


## 2026-11-06 — Buddy retry verified sandbox; API quota blocker isolated

- **Run:** [Babel AI continuation #42183337573](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42183337573), triggered by marker commit `75d3102e80ffe4158214114fa90c5979edda14e6` on `babel/dispatch-20261106-02`.
- **Verified:** preflight succeeded; agent job ran on `ubuntu-24.04`; `drop-sudo` successfully restricted `/run/snapd-snap.socket`. The first-run Ubuntu 26.04 sandbox compatibility problem is resolved by the narrow runner pin.
- **Failure:** Codex returned `Quota exceeded. Check your plan and billing details.` after launch. Agent job failed; validation and publisher were skipped. No candidate patch, `babel/agent-progress` branch, or Buddy PR was produced.
- **Next blocker:** user must check OpenAI API project/organization billing and usage limits to ensure available quota/credits. ChatGPT subscription access does not provide API credits. Do not retry until quota is confirmed; never weaken `drop-sudo` or use `unsafe`.
- **Independent repository checks:** Daily curator run [#42183307146](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42183307146) passed all 478 tests on `ffc75f5796d422d6f3bcd889465a00f0c613a57e`; public security scan [#42183307047](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42183307047) passed on the same commit.
- **Status:** GitHub dispatch, preflight, Ubuntu 24.04 runner, and sandbox isolation are verified. Buddy's actual documentation task, independent validation and PR publication remain unverified.


## 2026-11-06 — Buddy first dispatch run diagnosed; runner compatibility fix

- **Run:** [Babel AI continuation #42181953313](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42181953313), triggered by marker commit `7c1abce763d293992872699146eb7f13d10f9b87` on `babel/dispatch-20261106-01`.
- **Verified:** push trigger worked; preflight completed successfully; workflow found the configured continuation prompt and launched the Codex action.
- **Failure:** Codex action failed before executing the prompt. Runner `ubuntu-latest` was Ubuntu 26.04; `drop-sudo` could not restrict `/run/dbus/system_bus_socket` and reported `runner is not a member of the sudo group`. This matches [upstream openai/codex-action issue #188](https://github.com/openai/codex-action/issues/188).
- **Downstream effect:** validation and publisher were skipped; no candidate patch, `babel/agent-progress` branch, or Buddy PR was created. No SHIT data or Spotify state was changed.
- **Remediation:** pin only the Codex agent job to `ubuntu-24.04`. Keep `drop-sudo`, the `:workspace` profile, read-only agent/validation permissions, separate publisher, allowlist and human review gate unchanged. Trigger a fresh run from a branch based on the updated main and verify every stage.
- **Status:** first dispatch mechanism proven; Buddy itself is not yet operationally verified.


## 2026-11-06 — Deferred post-Babel health-system direction recorded

- **User direction:** after Babel is considered realistically as complete as it can be, revisit making Buddy part of SHIT's overall health system.
- **Recorded future direction:** a cross-project Integrity, Diagnostics & Recovery workstream covering health monitoring, root-cause diagnosis, bounded recovery/repair, documentation continuity and a systemic improvement backlog. Buddy's enduring role would be Documentation & Continuity Guardian, contributing evidence and drift checks without becoming the sole health authority or approving risky repairs.
- **Gate:** do not begin this work until the Maintainability & Documentation roadmap acceptance criteria pass and the fresh-session cold-start simulation succeeds. Babel remains the sole active SHIT workstream.
- **Safety constraints:** preserve canonical data/provenance, distinguish Last.fm scrobbles from optional Spotify playback observations, never invent or silently discard uncertain records, and require deterministic, backed-up, reversible, audited, post-verified repairs; consequential/ambiguous changes require user approval.
- **Outcome:** future goal recorded, not implemented. At the revisit, create a dedicated goal workspace and define ownership, health dimensions, autonomy boundaries and acceptance criteria.

Newest entries first. Record verified outcomes separately from plans, assumptions and unverified artifacts.

## 2026-11-06 — First ChatGPT-initiated Buddy dispatch trigger committed

- **Purpose:** test whether ChatGPT can initiate the repository-hosted Buddy workflow through the connected GitHub integration, a prerequisite for using ChatGPT as SHIT's front-end interface.
- **Execution:** successfully created branch `babel/dispatch-20261106-01` from `main`, then committed `.github/babel/dispatch.json` on that branch. Commit: `7c1abce763d293992872699146eb7f13d10f9b87`.
- **Trigger contract:** `.github/workflows/babel-ai-continuation.yml` listens for a push to `babel/dispatch-*` when `.github/babel/dispatch.json` changes. The marker branch is only a trigger; the worker continues to select `main` or `babel/agent-progress` as its source.
- **Verified:** GitHub accepted the branch creation and marker commit. This proves ChatGPT can perform the narrow GitHub write needed to emit the trigger event.
- **Not yet verified:** no workflow run URL/ID or job status is available from the connected GitHub actions in this session. Do not claim the workflow started, completed, or published a PR until the Actions run is inspected.
- **Next:** inspect the `Babel AI continuation` workflow run associated with the marker push; verify preflight, Codex, independent path/test validation, and publisher; then record the run ID, commit/ref and outcomes. If no run appears, diagnose the event/filter/permissions before changing the design.


## 2026-11-06 — Repository-hosted AI continuation worker integrated

- **Purpose:** let Babel continue its documentation audit from GitHub checkpoints when a ChatGPT conversation ends, without depending on chat history.
- **Files:** added .github/workflows/babel-ai-continuation.yml, .github/babel/CONTINUATION_PROMPT.md, project/BABEL_AGENT_STATE.md, and docs/BABEL_AGENT.md. Updated docs/BABEL.md, docs/README.md, docs/WORKFLOWS.md, and the Maintainability & Documentation roadmap/README.
- **Architecture:** scheduled every six hours and manually dispatchable; Codex resumes from babel/agent-progress; a separate publisher validates allowed documentation/test paths, rejects deletions and out-of-scope changes, validates and runs full unittest discovery in a read-only job without write credentials, then a separate publisher rechecks paths and pushes the dedicated branch/PR without executing candidate code. It never auto-merges.
- **Safety:** agent job has contents:read and workspace-scoped editing; publisher alone receives contents:write and pull-requests:write. No Spotify/provider credentials are passed. Prompt forbids runtime features, provider calls, playlist changes, generated data and workflow edits.
- **Activation blocker:** the repository-file integration cannot provision GitHub Actions secrets. Repository owner must create an OpenAI API key and add it as the repository Actions secret OPENAI_API_KEY. ChatGPT subscription access is not an API key; API usage is billed separately. The repository setting allowing GitHub Actions to create pull requests may also need to be enabled.
- **Verification:** Daily curator tests run [#42178656402](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42178656402) passed full unittest discovery (**478 tests**) on commit `69e72829c6cc9e72837025f8c777b4d846c9ba7b`; this verifies the repository baseline and documentation contract, not the Codex worker. No successful Babel AI continuation run has yet been observed. Do not call the worker active until the secret is configured, the first worker run succeeds, its validation job passes, and the branch/PR is inspected.
- **Next:** configure the secret and required repository Actions setting, manually dispatch the workflow once, inspect logs, Codex output, and PR, then leave the six-hour continuation schedule enabled until the explicit completion sentinel is set.

## 2026-11-06 — Great Migration preview side-effect contract source-audited

- **Scope:** traced the `prepare-preview` and `preview` paths across `.github/workflows/great-migration.yml`, `scripts/music/prepare_music_library.py`, `scripts/music/library_cli.py`, and `scripts/music/migrate_full_music_library.py`.
- **Verified behavior:** `prepare-preview` calls the preparation script without `--execute`; that script invokes `python shit.py library preview`; the CLI dispatches to the full migrator with `--dry-run`. The full migrator's dry-run branch reads the saved inputs/index and returns before constructing `MusicLibrary`, creating a backup, or calling `put_catalogue`. The preflight makes no provider requests and no Spotify playlist writes. This confirms the documented zero-write preflight contract for the current source.
- **Guardrail:** added a focused documentation-contract test tying the guide's read-only claim to the actual call chain and ensuring the dry-run branch returns before resolver construction or canonical Library writes.
- **Runtime/data impact:** none. No provider calls, generated-data changes, Spotify operations, or runtime code changes were made.
- **Verification status:** source-level control-flow review complete; the new regression test has not yet been run in CI. Do not describe the new test as passing until a workflow run confirms it.
- **Next:** continue the source-to-document audit with other write-capable workflow/CLI paths, then run the full documentation/test suite on the final audit batch.


## 2026-11-06 — High-risk operational contracts source-audited and documented

- **Daily:** verified that `--force` bypasses both the clock gate and same-Eastern-date completion guard; current test asserts it. The saved reference snapshot has 58 accessible unique URIs, below the 60-track target. Documented the P0 mismatch and the narrower-than-required post-write verification in Daily guide/TODO/roadmap/workflow catalogue. No runtime behavior changed.
- **Library:** verified `MusicLibrary()` can rebuild/write the derived index; read-only health avoids the resolver. Great Migration audit/verify-catalogue therefore are not strict zero-write scans. Credential verification can persist rotated Spotify refresh tokens in cloud runs through the scoped GitHub App. Documented backup limitations of legacy migrator paths.
- **Evidence semantics:** Reference Library sync writes canonical repository-side Library context but never changes Spotify playlists; playlist membership is not listening evidence. Track-profile builder can include priority-playlist-only candidates with zero scrobbles and writes them to canonical Library records.
- **Freshness corrections:** corrected Reference Library daily schedule to 06:13 UTC, enriched the workflow catalogue with exact path/trigger boundaries, and updated metadata budgets (scheduled: 300 duration, 100 artist, 200 track, 200 recording-ID, 100 album; manual choices documented separately).
- **Library report mismatch:** current canonical audit reports 13,239 songs; the committed migration_report.json still contains the earlier 13,005-song migration snapshot. The README now labels it historical; no generated data was edited.
- **Tests:** expanded documentation-contract and script-layout tests with workflow/guide allowlist and budget checks, all-Markdown local-link validation, all-goal pause checks, Daily force/idempotency, resolver write-boundary and snapshot/listening evidence assertions. CI verification is pending for this new test set.


## 2026-11-06 — Inventory verified; enrichment workflow reconciled; 12 goal pauses recorded

- **Committed-tree inventory:** main commit `3d2c1ded8dfb44b92e6e0c086673c69350200edc` contains 28,241 file/blob entries. A non-recursive root tree plus nine recursive directory-scoped Git Trees requests were used; every subtree returned `truncated=false`. `assistant_data/` contains 27,981 files. Exact breakdown is in `docs/REPOSITORY_FILE_INDEX.md`.
- **Maintained-code inventory:** 55 Python implementation modules, 40 compatibility launchers, 44 test modules, 17 workflow YAML files, 21 technical guides and 13 goal workspaces. 28 known generic/underspecified implementation overviews have been corrected.
- **Goal continuity:** all 12 non-documentation roadmaps now separate the active documentation-only next action from the preserved next feature action; each corresponding ACTIONS file records the pause.
- **CI/security:** Daily curator run #42168520574 passed 460 tests on `8153028e`; full-history security scan #42168520598 passed on the same commit.
- **Enrichment reconciliation:** run #42166959478 completed successfully and published `3d2c1ded`. It merged 195 discovery candidates, audited 13,239 canonical songs, reached 8,254/11,130 tracks with sourced durations and 139,758/152,005 duration-covered scrobbles (91.9%). Artist profiles: 3,373 matched; track profiles with sourced tags: 229; matched album profiles: 905. Final audit: 9 checks, 18 warnings, 0 errors. Warnings were no captured playback intervals and 16 inaccessible Spotify playlist item snapshots. No Spotify playlist writes occurred.
- **PR #161:** open/draft, 117 files changed; branch diverges from current main by 571 commits ahead and 29 behind. Do not merge blindly. Review and port individual tests/docs only after source verification.
- **Next:** audit high-risk Daily force/idempotency, Library resolver write boundaries, Spotify snapshot evidence semantics, Great Migration secret rotation/backup behavior, and workflow schedule/budget alignment. Then extend documentation contract tests and perform fresh-session acceptance.


## 2026-11-06 — Four analytics overviews corrected; broad placeholder guard passed

- **Additional source documentation:** replaced vague fallback overviews in `scripts/analytics/build_advanced_analytics.py`, `build_assistant_data.py`, `build_listening_time_summary.py`, and `build_music_analytics.py` with concrete inputs, outputs, identity/time semantics, baseline/verified-duration distinctions, and read/write behavior.
- **Total corrected in this pass:** 28 implementation overviews: `scripts/spotify/spotify_playlist_manager.py`, `spotify_daily_playlist.py`, `spotify_playlist_cloud.py`, `spotify_reference_library.py`, `spotify_daily_feedback.py`, `spotify_discovery.py`, `track_playlist_removals.py`; `scripts/lastfm/update_lastfm.py`; `scripts/music/build_music_metadata.py`, `build_music_profiles.py`, `build_track_profiles.py`, `enrich_musicbrainz_durations.py`, `enrich_musicbrainz_recording_ids.py`, `enrich_acousticbrainz.py`, `enrich_getsongbpm.py`, `enrich_recommendation_lyrics.py`, `audio_analysis.py`, `lyrics_library.py`, `mood_inference.py`; `scripts/analytics/build_stats.py`, `build_playback_analytics.py`, `build_advanced_analytics.py`, `build_assistant_data.py`, `build_listening_time_summary.py`, `build_music_analytics.py`; `scripts/spotify/playlist_intelligence.py`, `playlist_metadata.py`, `spotify_playback_tracker.py`.
- **Guardrail expansion:** anti-placeholder coverage now scans Python files under `scripts/`, `compat/`, and `tests/`, plus YAML workflows. This is broader than only modules with compatibility launchers.
- **Verification:** Daily curator run #42168360237 passed **460 tests** on `8fb80589968a7868fd50bba5e13af7f787ed5c15`; the broad maintained-overview placeholder check passed. Public security scan #42168221944 passed for the preceding analytics-overview commit; scan #42168360298 for the expanded guard was still running at the last check.
- **Operational side effect:** Enrich Music Metadata run #42166959478 remains active. Duration, artist-profile, and recording-ID steps succeeded; track-tag enrichment was active. Later workflow steps may enrich albums, optionally call Discogs, merge candidates into the canonical Library, rebuild analytics, audit, and publish generated data. It has no Spotify playlist-write step.
- **Next:** reconcile the Enrich workflow's terminal status and any bot data commit; verify the latest security scan; continue semantic audit of remaining non-placeholder modules and guides, all goal workspaces, workflow details, open PRs/issues, and the complete tracked-file inventory.

## 2026-11-06 — Full documentation guardrails and public security scan passed

- **CI:** Daily curator run #42167849568 completed successfully on `da3be75844e3ce28eacd46ce8d87960493402503`. The maintained-file documentation check passed, including scanning all Python files under `scripts/` for generic overview placeholders; full unittest discovery passed **460 tests**.
- **Security:** Public repository security scan #42167849588 completed successfully on the same commit.
- **Fresh-session entry:** Babel identity and local-link checks passed; the guide is the first item in the docs index start path.
- **Still open:** Enrich Music Metadata run #42166959478 remains active at the MusicBrainz duration step after the comment-only source documentation commit triggered its path filter. Its terminal result and any generated-data commit must be reconciled.
- **Next:** finish workflow reconciliation, update the consolidated loose-ends register, and continue semantic review beyond the 24 corrected placeholders. Do not resume feature or playlist work.

## 2026-11-06 — Babel identity and all-module overview guardrails CI-verified

- **Changes:** the documentation contract now requires `docs/BABEL.md`, checks that first-contact entry points consistently define SHIT Documentation & Continuity / Babel, and validates local links from the Babel guide. The documentation index now places the Babel guide first in its start path.
- **Coverage:** the anti-placeholder check now scans every maintained Python module under `scripts/`, not only modules with compatibility shims.
- **Verification:** Daily curator run #42167694048 completed successfully on `deb653a2528ee7d9969296048582fb9764e7d908`: maintained-file documentation check passed; full unittest discovery passed **460 tests**. The explicit identity test and all-module placeholder test both passed. Public repository security scan #42167694030 was still in progress at the latest inspection.
- **Status:** naming contract and automated documentation guardrails are implemented and CI-verified. The semantic source-to-document audit and fresh-session simulation remain incomplete.
- **Next:** reconcile the Enrich Music Metadata run #42166959478 and security scan #42167694030; update current data-state evidence; continue manual audit of remaining implementation overviews, technical guides, goal roadmaps, workflow contracts, open PRs/issues, and complete tracked-file inventory.

## 2026-11-06 — Twenty-four implementation overviews made specific; workflow side effect under review

- **Work:** replaced generic fallback `FILE OVERVIEW` blocks in 24 maintained modules: seven high-risk Spotify modules, eight Last.fm/music enrichment modules, five lyrics/audio/core analytics modules, and four playback/playlist-intelligence modules. Each now names concrete data paths, provider behavior, outputs, safety boundaries, limits, or its explicit caller.
- **Commits:** `f58de19` (seven Spotify modules), `69fcdd5` (eight Last.fm/music enrichment modules), `68a9d55` (five lyrics/audio/core analytics modules), and `0c05557` (four playback/playlist-intelligence modules).
- **Verification:** Daily curator tests run #42167054690 passed on `0c055578` (458 tests; includes maintained-file documentation/layout checks). Public repository security scan #42166959368 passed on `69fcdd58`; the security scan for `0c055578` was still in progress at the last check. A new anti-placeholder test was added after run #42167054690 and still needs CI verification.
- **Unintended workflow trigger:** changing `scripts/music/enrich_musicbrainz_recording_ids.py` comments matched the Enrich Music Metadata push path filter. Run #42166959478 started with `contents:write` and provider calls; at the last inspection it was still executing “Fill missing durations from MusicBrainz”. Its workflow also enriches artist/track/album metadata, merges into the canonical Library, rebuilds summaries, audits, and may commit generated data. The available GitHub connection exposed no cancellation action. No Spotify playlist writes are included in this workflow. Record its final result and any generated-data commit before proceeding.
- **Other CI evidence:** run #42167011344 passed on `68a9d55d`; run #42167054690 passed on `0c055578`. The earlier naming sequence had temporary intermediate failures because a commit referenced `docs/BABEL.md` before that file existed; the completed naming state passed on `9f2c788a` (run #42166506128), and the public-repository security scan also passed on that commit (run #42166506118).
- **Outcome:** 24 overview corrections published; automated tests passed before the new anti-placeholder assertion; semantic review and current-workflow reconciliation remain open.
- **Next:** verify the new anti-placeholder test in CI; monitor #42166959478 to terminal state and reconcile any resulting data commit; continue manual source-to-overview review and the remaining goal/runbook audit. Keep documentation as the only active priority.

## 2026-11-06 — Documentation system named SHIT Documentation & Continuity (codename Babel)

- **User decision:** use **SHIT Documentation & Continuity** as the descriptive public-facing name and **Babel** as an internal codename introduced only after its meaning is clear. Do not call the parent SHIT product or repository Babel.
- **Changes published to `main`:** added [docs/BABEL.md](../../../docs/BABEL.md) as the canonical identity, scope, naming, operating-contract and completion-standard guide. Updated the root README, AGENTS.md, documentation index, mandatory documentation rules, current handoff, project-wide roadmap, and this workstream's README/ROADMAP to establish the convention.
- **Naming rule:** first reference is “SHIT Documentation & Continuity (internal codename: Babel)”; later references may use “Babel”. First-contact headings and navigation retain the descriptive name.
- **Verification:** GitHub contents API accepted the file creation and sequential updates. Commits: `2afbc25`, `25dec1a`, `a02f668`, `d1841c2`, `2173d83`, `022f5b2`, `b906de5`, `4bdafe0`, `be34f0c`; this action-log update follows them. No application code, generated data, provider state, listening history, or Spotify playlists were changed.
- **Limit:** naming propagation and Markdown publication are verified; repository-wide link/test/CI verification after these edits has not yet been run. Documentation audit remains in progress.
- **Next:** verify every naming link and entry point, inspect current main/CI after the documentation commits, then continue the semantic file-overview and operational-contract audit. Keep documentation as the only active workstream.
- **Outcome:** naming decision documented and published; validation pending.

## 2026-11-05 — Workflow overview audit found boilerplate; push-trigger side effects recorded

- **Finding:** all 17 workflow files are listed in `docs/WORKFLOWS.md`, but nine workflow YAMLs had generic bottom overviews that did not describe their actual triggers, credentials, writes or safety boundaries. This passed the existing FILE OVERVIEW presence test but failed the intended documentation-quality standard.
- **Changes:** replaced the generic overview blocks in `acoustic-metadata-enrichment.yml`, `backfill-music-durations.yml`, `daily-curator-tests.yml`, `enrich-music-metadata.yml`, `playlist-manager-check.yml`, `spotify-daily-feedback-observation.yml`, `spotify-playlist-manager.yml`, `spotify-reference-library.yml`, and `update.yml` with workflow-specific contracts. Added a warning to `docs/WORKFLOWS.md` that comment-only edits to workflow YAMLs can trigger path-filtered workflows.
- **Verification:** Daily curator tests and public-repository security scans passed on the workflow-overview commits through `217bb36049a1791f467c2ed9fbcda34c36daf602`; examples include run #42146153109 and #42146153169.
- **Operational side effect:** editing workflow YAML files on `main` triggered configured push workflows. Reference-library run #42146148971 completed successfully and produced commit `3e989e33282efab6cc1416e35970e7c59af5f056`: 249 files changed (184 canonical Library records, 63 Spotify reference/history files, and 2 removal-state files), 4,445 additions and 644 deletions. It refreshed snapshots and removal feedback; it did **not** write to Spotify playlists.
- **Other triggered jobs:** Update Last.fm History run #42146153098, Enrich Music Metadata run #42146121471, and Acoustic Metadata Enrichment run #42146097964 were still in progress at the latest check. Their completed steps included Last.fm import/artist enrichment, MusicBrainz duration/recording-ID lookups, and strict MusicBrainz ID resolution respectively; track-tag/AcousticBrainz enrichment was still running. These runs were not part of the requested documentation-only scope. The available GitHub connection did not expose a workflow-cancellation action, so they could not be stopped from this session.
- **Lesson / prevention:** inspect all workflow push-path filters before committing workflow documentation. A comment-only change is still a triggering file change. Future overview edits should be staged and reviewed with their trigger consequences understood; do not repeat this side effect.
- **Separate code-documentation audit:** inspection of maintained source overviews found further generic fallback text in analytics, Last.fm, music and Spotify modules. Marker presence is not proof of a useful overview; continue semantic review and repair those files.
- **Outcome:** nine workflow overviews improved and tested; workflow audit remains incomplete; provider refresh side effects are being monitored and must be reconciled in the handoff.
- **Next:** monitor the three remaining runs to terminal state and inspect any resulting commits; then improve the source-module overview quality and strengthen tests so generic fallback boilerplate is rejected.

## 2026-11-05 — Live repository inventory and documentation audit resumed

- **Purpose:** continue the user-directed documentation-only phase and verify the current repository rather than relying on prior chat summaries.
- **Repository:** canonical `TrickySturluson/spotify-helper-information-tracker`, default branch `main`, inspected tree SHA `b542ceab2c40f6910a91ea3fcb84c204fc412c2d`.
- **Inventory evidence:** 13 goal directories were listed individually; all 13 contain ROADMAP.md, README.md and ACTIONS.md. The current workflow directory contains 17 YAML files. Maintained implementation directories list 7 analytics modules, 1 Last.fm module, 24 music modules and 19 Spotify modules. The repository also contains compatibility launchers, tests, canonical data, generated analytics/Library records, playback observations, playlist state and the CLI.
- **Automated verification:** latest observed Daily curator run #42144512658 and public repository security scan #42144512423 both succeeded on the inspected main SHA. Existing tests check goal workspace structure, selected local links, workflow catalogue coverage and bottom FILE OVERVIEW marker presence across maintained Python/workflow files.
- **Important limitation:** the recursive Git tree API response was truncated by the very large generated per-record Library tree. It is not a complete inventory. Directory-scoped listings are adequate for the maintained code/workflow/goal counts above, but a full checkout plus `git ls-files` is still needed for exhaustive tracked-path reconciliation.
- **Accuracy finding:** passing marker/link tests do not prove that every FILE OVERVIEW, workflow summary, technical guide, or roadmap remains semantically accurate. Manual source-to-document review remains required.
- **Open work observed:** Daily PRs #158 (Discover Weekly exposure/feedback), #159 (DST schedule gating), and #160 (exposure-aware discovery) were open at audit time. They must remain clearly distinguished from merged mainline behavior until reviewed and merged.
- **Changes:** updated `project/NEXT_WORK.md` to make documentation the sole active priority and record the verified baseline/next actions; updated this roadmap and action history. No application code, data, provider state, or Spotify playlists were changed.
- **Outcome:** audit resumed; documentation remains in progress and is not declared complete.
- **Next:** obtain a complete tracked-file inventory; audit all maintained file overviews and operational guides against source; reconcile all goal workspaces, open PRs/issues and current workflow evidence; add targeted checks for actual gaps; complete the fresh-session simulation.

## 2026-11-05 — Playlist Sequencing split into an independently resumable workstream

- **Reason:** the ordering engine has distinct user requirements (smooth transitions first, configurable energy journey/peak, sections, track-level evidence) and safety requirements (preview, explicit confirmation, stale-preview rejection, live read-back). It should not be buried inside the broader recommendation/fit-model workspace.
- **Changes:** added project/goals/playlist-sequencing/ROADMAP.md, README.md and ACTIONS.md; linked the workspace from the goal index, project-wide roadmap and docs index.
- **Boundary preserved:** the five-axis playlist-fit model remains a separate preview-only system and is not wired into the sequencer.
- **Verification:** documentation paths and stated behavior were cross-checked against the transition-scoring guide, Booze preset guide and existing playlist-intelligence roadmap. A fresh CI run is required to verify the dynamic goal-directory check.
- **Outcome:** dedicated workstream documentation created; runtime behavior unchanged.
- **Next action:** inspect CI and audit sequencer implementation/tests against this roadmap.

## 2026-11-05 — Tricky Daily split into an independently resumable workstream

- **Reason:** Daily is an active, safety-sensitive system with its own 60-track product contract, forced-run parity, feedback model, schedule, recovery and live-verification requirements. Keeping it only as a subsection of Playlist Intelligence made its own roadmap less discoverable.
- **Changes:** added project/goals/tricky-daily/ROADMAP.md, README.md and ACTIONS.md; linked the new workspace from the goal index, project-wide roadmap and docs index. The existing Daily TODO and cycle guide remain detailed technical references.
- **Guardrail:** the documentation contract test discovers every goal directory dynamically and requires ROADMAP/README/ACTIONS, so the new goal is automatically included in CI coverage.
- **Verification:** GitHub file creation succeeded. A new CI run is required to verify the dynamic goal check after this workspace was added. No code, playlist, Library data or provider state was changed.
- **Outcome:** dedicated workstream documentation created; CI verification pending.
- **Next action:** inspect the latest CI run, then audit Daily implementation and workflow evidence against the new P0 roadmap without assuming unchecked backlog items are complete.

## 2026-11-05 — Repository index corrected and test-suite guide added

- **CI verification:** Daily curator tests run #42143513931 passed on commit 7d23db6a12ec80eb0830a84738dab3c856ef8dff after the directory-guide additions and index correction. The run completed successfully, including the documentation-layout step and full unittest discovery. A later run #42143770161 also passed on commit 79af1f93756878d27a40a02c3a2abc4b627643ce after the dedicated Tricky Daily workspace was added. The new Playlist Sequencing workspace is newer and awaits its own run.

- **Finding:** the previous `docs/REPOSITORY_FILE_INDEX.md` described itself as a complete tracked-file catalogue and listed only 239 assistant_data files, while the current canonical music Library contains a much larger per-record tree. The recursive Git tree API also reported `truncated: true`, so it was not safe to claim a complete recursive inventory from that response.
- **Changes:** replaced the stale exhaustive snapshot with a source and data-family index. It documents code/workflow/test ownership, canonical Last.fm data, canonical structured Library records, generated analytics, optional playback observations, Spotify state/feedback, and commands to inspect the exact current Git inventory. Added `tests/README.md` and linked it from the documentation index.
- **Verification:** repository directories and goal workspaces were inspected through GitHub contents listings. The previous docs contract test passed on commit `38ad97e`; the new directory-guide requirement and corrected index have not yet had a fresh CI run.
- **Outcome:** index scope corrected; further CI verification pending.
- **Next action:** inspect the new test run after the latest commits, fix any failures, then audit source/workflow file overviews against the actual tree and stale operational descriptions.

## 2026-11-05 — Automated documentation contract checks added

- **Purpose:** catch missing documentation foundations and broken navigation before future changes can quietly erode continuity.
- **Changes:** added `tests/test_documentation_contract.py`. It checks repository control documents, every goal folder's ROADMAP/README/ACTIONS, root assistant instructions, coverage of major repository domains in the docs index, and local links from the main fresh-session entry points. Updated `docs/README.md` and `docs/CODE_DOCUMENTATION.md` to explain the checks.
- **Execution:** test is included in standard unittest discovery; the existing `.github/workflows/update.yml` runs full unittest discovery before publishing refreshed data. No workflow YAML change was required.
- **Verification:** file creation succeeded. The new test has not yet been executed in GitHub Actions; do not mark the guardrail verified until a successful run is inspected.
- **Outcome:** implemented; CI verification pending.
- **Next action:** inspect the latest workflow run after this commit. If tests fail, diagnose and fix only the actual broken paths/contract assumptions, then add coverage for source inventory and stale file-index detection.

## 2026-11-05 — Repository navigation and mandatory agent instructions added

- **Purpose:** make the documentation system discoverable and enforceable from the repository root, not dependent on a chat summary.
- **Changes:** added root AGENTS.md; added docs/README.md as the cross-cutting documentation index; added project/ROADMAP.md as the cross-workstream roadmap; linked all three from the repository README and documented the expansion in project/NEXT_WORK.md.
- **Existing foundation verified:** project/DOCUMENTATION_RULES.md, project/NEXT_WORK.md, project/LOOSE_ENDS.md, project/PROJECT_LOG.md, the goal index and 11 goal workspaces already exist on main. Each goal is intended to have ROADMAP/README/ACTIONS.
- **Verification:** fetched and inspected the existing root README, documentation rules, project handoff/log/index, loose-ends register, maintainability workspace, playlist-intelligence workspace, Tricky Daily backlog/cycle guide and privacy/description guides. New files were created successfully on the repository default branch. No code, Library data, provider state, listening history or Spotify playlists were changed.
- **Limitation:** this is not yet a full tracked-file inventory audit. The complete file-index accuracy, per-file overview coverage, link integrity, goal-file completeness and current GitHub run/PR status remain to be verified.
- **Outcome:** navigation/control structure expanded; documentation coverage audit still in progress.
- **Next action:** obtain the complete tracked-file tree, compare all scripts/modules/workflows/tests/schemas/data contracts with documentation, fix the highest-risk gaps, then add automated checks and perform a fresh-session resume test.

## 2026-11-05 — Mandatory project roadmaps and same-session documentation rule

- **User direction:** every project/workstream must have a durable roadmap so future assistant sessions can continue without previous chat knowledge; documentation must explicitly require ongoing maintenance.
- **Changes:** added `project/DOCUMENTATION_RULES.md`; created `ROADMAP.md` for all 11 goal workspaces; linked each goal README to its roadmap; updated the goal index, repository README, project control-centre README, NEXT_WORK handoff, and PROJECT_LOG.
- **Required structure:** each goal has a roadmap for plan/status/acceptance/next action, a README for scope/design/invariants, and ACTIONS for dated implementation and verification evidence.
- **Verification:** all 11 indexed goal workspaces received a roadmap. Changes are documentation-only; no code, Library records, provider state, listening history, or Spotify playlists were changed.
- **Outcome:** complete for the currently indexed goal workspaces.
- **Next action:** audit roadmap accuracy against latest main, PRs, issues and workflow runs; audit per-file documentation coverage and keep this standard for all new workstreams.


## 2026-11-01 — Goal workspace initialized

- **Action:** established this goal's dedicated documentation and action-history location.
- **Context:** 2026-11-01: Added the goal-based workspace design on branch `codex/goal-workspaces`. This folder's README and ACTIONS are part of that proposed structure. Next: finish all goal folders, update central index/handoff, verify links, and merge.
- **Outcome:** documentation initialized; no runtime implementation or data mutation implied unless explicitly stated above.

## 2026-11-01 — Per-goal workspaces merged; repository-wide documentation audit opened

- **PR:** #67 https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/67
- **Merge:** squash merge succeeded as `4ad701c2c4f36b9f6f73926e83db1f84cbfbcc2c`.
- **Verification:** PR checks `tests` and `Scan complete Git history for secrets` both completed successfully. The merge was documentation-only; no Library records, provider checkpoints, listening history or Spotify playlists were changed.
- **Audit scope:** reviewed repository directory/workflow inventory, open issues/PRs, and prior SHIT conversation decisions. Added `project/LOOSE_ENDS.md` as a cross-project index; detailed findings are logged in each goal history.
- **Loose ends:** audit every maintained Python script and workflow for concise in-file purpose, inputs/outputs, side effects, data paths, safety boundaries and run/test guidance. Existing `scripts/README.md` is a directory overview, not proof every file has its own overview. Add automated documentation coverage checks.
- **Failed experiments / lessons policy:** action histories must record failed tests, failed workflow steps, rejected/abandoned approaches, performance/rate-limit problems, root-cause findings and why a decision changed—not only successful work. Never expose credentials or raw secret values in logs.
- **Outcome:** goal workspace foundation merged; broader documentation audit remains in progress.
- **Next action:** use the loose-ends register to work through each goal and verify per-file documentation coverage.

## Entry template

### YYYY-MM-DD — Action
- **Purpose:**
- **Changes / files:**
- **Execution:** command, workflow run, PR, commit
- **Verification:** exact tests/audits, including failing steps and diagnostic evidence
- **Outcome:** complete / partial / blocked / deferred
- **Failed or abandoned approaches:** what was tried/rejected and why; never omit meaningful failures
- **Performance / provider limits:** latency, request volume, cooldowns, quotas, caching, or inefficiencies observed
- **Lessons learned / decision changes:**
- **Next action:**
- **References:**

## 2026-11-05 — All 13 goal workspaces pass documentation contract CI

- **Verification:** Daily curator run #42143913729 completed successfully on commit ec05a646db68e9931c5562f34124e1c8998c6997 after the Playlist Sequencing workspace was added. The workflow completed generated-data audit, read-only full Library health/confidence checks, bounded freshness planning, maintained-file documentation checks, and full unittest discovery. Earlier run #42143770161 passed after Tricky Daily was added.
- **Result:** dynamic goal discovery now verifies all 13 goal folders have ROADMAP.md, README.md and ACTIONS.md. The new documentation contract and directory-guide checks are included in the full unittest suite.
- **Limit:** these checks verify navigation and required structures; they do not yet prove every Markdown statement matches live implementation or every workflow overview accurately describes permissions and side effects.
- **Next:** audit every maintained Python/workflow overview against source and add a read-only report for stale links, missing technical contracts and generated-data ownership.
\n## 2026-11-05 — Workflow catalogue and working Markdown-link audit verified\n\n- **Changes:** added docs/WORKFLOWS.md with the 17 workflow names, triggers, permission boundaries, credential variable names, primary actions and side effects. Added a dynamic test requiring every .github/workflows/*.yml file to appear in the catalogue.\n- **Audit correction:** inspection found the Markdown-link test regex was over-escaped and therefore did not reliably capture ordinary links. Corrected it in commit 9a62487581afcb3116fa21a1a42ea39c9a5b9c18 so primary control-document links are actually parsed and checked. Earlier passing runs verified other contract checks but must not be cited as proof of link validation.\n- **Verification:** Daily curator run #42144349548 passed on commit 9a62487581afcb3116fa21a1a42ea39c9a5b9c18. Compile, generated-data audit, full Library health/confidence, bounded freshness planning, maintained-file documentation check and full unittest discovery all completed successfully. This run includes the corrected link regex and workflow catalogue coverage.\n- **Outcome:** workflow inventory and primary-link contract checks implemented and CI-verified. Full semantic accuracy of every workflow summary and every implementation overview remains a manual audit task.\n- **Next:** audit per-file overview accuracy and cross-reference technical documentation against current source; record gaps by risk rather than treating presence of an overview as proof of correctness.\n

## 2026-11-06 — Active-session brief established for Buddy continuity

- **User requirement:** ChatGPT must keep Buddy informed of active SHIT work, decisions, findings, verification, failures, and next actions throughout each work session. A curated repository brief is preferred over copying raw chat logs.
- **Created:** `project/ACTIVE_SESSION_BRIEF.md` on main, commit `55f1403c8feb614b1b6763ce8873499bdcbe4c86`. It records the current objective, role boundaries, activation state, carry-forward risks/evidence, required update format, and privacy rules.
- **Buddy prompt:** `.github/babel/CONTINUATION_PROMPT.md` now requires the worker to read the active brief first and reconcile it against the checked-out source/evidence. Commit `bad03f65cbe92690718278440886a84014fd79a1`.
- **Important limitation:** this is not real-time messaging. Buddy sees only committed changes on a later scheduled/manual run; it cannot interrupt or message the active ChatGPT conversation.
- **Verification:** GitHub contents API confirmed both commits. Buddy has not yet had a successful run; its state file still records `last_result: not yet run`. No test or workflow run has been claimed for these documentation edits.
- **Next:** confirm the repository Actions PR-creation permission, manually dispatch Buddy on `main`, and inspect the actual worker output, validation result, and proposal PR; then complete the cold-start simulation.

## 2026-11-06 — Buddy activation prerequisites confirmed; first dispatch pending

- **User-confirmed setup:** GitHub repository Actions secret `OPENAI_API_KEY` has been added, and **Allow GitHub Actions to create and approve pull requests** is now enabled.
- **Remaining action:** manually run **Actions → Babel AI continuation → Run workflow** on `main`.
- **Tool limitation:** connected GitHub integration supports repository reads and content/PR operations but exposes no workflow-dispatch action. The user must click the dispatch control in GitHub's Actions UI.
- **Verification status:** no first-run result is claimed yet. After dispatch, inspect all jobs, the independent validation result, and any `babel/agent-progress` PR before marking Buddy operational.

## 2026-11-06 — Added ChatGPT-controlled Buddy trigger; execution attempt blocked

- **User request:** enable ChatGPT to start Buddy directly.
- **Workflow change:** `.github/workflows/babel-ai-continuation.yml` now accepts a push to a fresh `babel/dispatch-*` branch only when `.github/babel/dispatch.json` changes. Commit: `1edb00e583ee28301a490d1a1039827882752608`.
- **Execution design:** ChatGPT creates a fresh dispatch branch from `main`, then commits the marker. The workflow's preflight still selects `main` or `babel/agent-progress` as the actual work base; the dispatch branch is not used as source material. Manual dispatch and six-hour schedule remain available.
- **Safety:** the trigger is constrained by branch pattern and exact path; no secret or executable instruction is placed in the marker. Existing read-only agent/validation and separate allowlisted publisher architecture is unchanged.
- **Attempt:** the connected GitHub branch-creation action was blocked by the platform's safety checks before a dispatch branch was created. Therefore no workflow run has been triggered or verified by this attempt.
- **Next:** use the Actions UI for this first run, or establish an approved GitHub action/connection that permits ChatGPT to create the dispatch branch. Do not mark Buddy active until a successful run and proposal review are confirmed.


## 2026-11-20 — Scheduled ChatGPT Buddy repaired and reactivated

- **User request:** make sure the SHIT workers are working; repair Buddy now and revisit Boots later.
- **Diagnosis:** the scheduled ChatGPT Buddy automation was disabled. Its former persistent branch `babel/chatgpt-buddy` was 46 commits ahead and 349 commits behind current `main`; draft PR #163 was unmergeable and contained stale worker-model guidance.
- **Recovery:** preserved the old branch for historical reference, closed draft PR #163 without merging, and created `babel/chatgpt-buddy-v2` from current `main` at `3b7f9fe830bfc67dc8263518defb47b32377bbc7`. Updated the scheduled task instructions to use the replacement branch and re-enabled the daily automation.
- **Documentation batch:** reconcile the current worker identity across this goal README, `docs/BABEL_AGENT.md`, `docs/BABEL_CHATGPT_BUDDY.md`, and this roadmap/action history. Mark the Codex/API workflow as a separate dormant experiment; it must not be retried without explicit user reauthorization.
- **Execution:** an immediate Buddy run was requested after reactivation. Its result and any draft PR/CI evidence must be checked separately; automation acceptance is not proof of completion.
- **Verification:** all five changed files were read back from GitHub. The branch compares as 5 commits ahead and 0 behind `main`; the complete PR diff contains only the five allowlisted Markdown files and 30 additions/14 deletions. Draft PR [#201](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/201) is open and mergeable. The public security scan and Daily curator tests were triggered by the PR and were still in progress at the last status check. No runtime, workflow, credential, provider, Library, or Spotify changes were made.
- **Next:** wait for both PR #201 checks to finish, independently review their results and the final PR head, and keep the PR draft pending that review. Verify the Buddy automation's next scheduled execution separately. Boots is intentionally deferred.
