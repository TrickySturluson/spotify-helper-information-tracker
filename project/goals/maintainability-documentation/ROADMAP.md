## 2026-11-24 — Reconciled Buddy-owned shared handoff and refreshed successor evidence (09:35 Eastern)

- **Current `main`:** `862e9662a6f2e6b583ef21b5d303134d68205874`.
- **Buddy automation:** `6aed3a70baf88191ab1dbfaa8f7dba91` is enabled. Current run `bbd06c35-1e78-832a-9d0f-ab71ba014848` is `in_progress`, scheduled 09:00 and started 09:35:37 Eastern; latest result `1fc98dce-5084-8324-8cb7-7b32344cc84d` is from Nov 23 and does not match. Environment is unknown.
- **Jockey readiness: BLOCKED.** Automation `6af1645551a48191900c77833073fdfd` is disabled; completed run/result `ae49786b-46e0-8321-949d-9f139020df47` match and the non-truncated report discloses accidental direct-to-main writes followed by a safe stop. PR #200 head `4f0291b8990987ca5bb84bdea06d6d6bad1113fe` is 67 ahead / 16 behind; exact-head Daily #44928121273, broker #44928121259, and security #44928121262 passed. Environment is unknown.
- **Boots fallback readiness: BLOCKED.** Automation `Automation_2e1357c87e688191829bd2380047f46d` is disabled; completed run/result `a030ee14-e434-832d-a8cc-b462d8e88ed7` match but the report is truncated. `engineering/general` head `a58e6b7d953428adf9932499a79234fc2ed06150` is 14 ahead / 93 behind, has no PR, and exact-head Daily #42578252673/security #42578252818 failed while broker #42578252704 passed. Environment is unknown.
- **Buddy PR #201:** pre-change head `045187191d79dbedae48d6735e918512f350a2cd`, 89 ahead / 22 behind; open/draft, 12 changed files. Exact-head Daily #45415263443, broker #45415263474, and security #45415263509 passed on this pre-change head. This documentation batch creates a new head; fresh exact-head CI is required.
- **Trio PR #202:** head `8d4a25e2516d404610fdf6cd9e1e9c55f062b6e0`, 68 ahead / 22 behind; open/draft, 12 changed files. Exact-head broker #45097778021, Daily #45097778095, and security #45097778028 passed.
- **Jockey PR #200:** head `4f0291b8990987ca5bb84bdea06d6d6bad1113fe`, 67 ahead / 16 behind; open/draft, 14 changed files. Exact-head broker #44928121259, Daily #44928121273, and security #44928121262 passed; task/branch recovery remains blocked.
- **Boots:** `engineering/general` is 14 ahead / 93 behind with no matching open PR. Exact-head Daily/security failed and broker passed. Do not reset, rebase, force-push, or enable it.
- **Shared-file reconciliation:** the four #201/#202 paths are the Buddy guide, docs index, active-session brief, and loose-ends register. Both guide versions include v2 branch/PR rules, Codex/API history, and Trio responsibility; #201's fallback/read-only text is more detailed. Both index versions include Trio Start here, Daily recommendation-memory guide, and 22 workflows. The protocol file is on #202's branch but absent from `main`, so #201's direct branch URL is retained. The #202 handoff snapshots are stale; PR #200 also overlaps both handoff files.
- **Merge gate:** no merge order is approved. Do not merge #201 or #202 until all four shared files and the order are reconciled, including #200's two-file overlap. #202-first is a proposal, not authorization.
- **Completed in this batch:** verified the live #201/#202 versions of all four shared paths; retained the already-correct Buddy guide and docs index; refreshed the Buddy-owned active-session brief and loose-ends overlay; independently compared the complete #201 diff and checked source/test claims. All other worker branches, PRs, task settings, prompts, schedules, and environments remained read-only.
- [x] Verify pre-change exact-head CI on Buddy head `045187191d79dbedae48d6735e918512f350a2cd`: Daily #45415263443, broker #45415263474, and security #45415263509 passed.
- [ ] Verify exact-head CI on the new Buddy commit created by this batch; record its final head and checks in PR #201's description without a status-only branch commit.
- [ ] Obtain an owner-approved merge order across #201/#202/#200; keep all PRs draft until the shared-file state and merge order are reconciled.
- [ ] Complete maintained-file/technical-guide semantic coverage, all-goal semantic review, operational safety-contract audit, and fresh-session simulation using repository docs alone.

---

## Historical checkpoint — 2026-11-23 Buddy/Trio shared handoff and successor evidence (superseded by 2026-11-24)

- Current `main` at audit start: `f3387a29ad2a97017a80968ec1a047a97118c618`. The Buddy automation is enabled, but its Nov 23 run `1fc98dce-5084-8324-8cb7-7b32344cc84d` remains `in_progress`; the latest completed result is prior run `e560322d-6ac8-8332-84aa-98b2b5816aeb`. Environment status is unknown.
- Jockey is disabled and **BLOCKED**. Its last run `ae49786b-46e0-8321-949d-9f139020df47` is recorded completed and reports accidental direct-to-main writes followed by a stop. PR #200 head `4f0291b8990987ca5bb84bdea06d6d6bad1113fe` is 67 ahead / 10 behind; exact-head Daily, broker, and security Actions passed. Its branch remains diverged and the task remains disabled.
- Boots is disabled and **BLOCKED**. Its last run `a030ee14-e434-832d-a8cc-b462d8e88ed7` is recorded completed, but its result is truncated. `engineering/general` head `a58e6b7d953428adf9932499a79234fc2ed06150` is 14 ahead / 87 behind, has no matching open PR, and exact-head Daily/security checks failed while broker tests passed. Environment status is unknown.
- Buddy PR #201 was open/draft at pre-update head `cfa7af161d0bf2d27e59f184403663e232c4e0a3`, 80 ahead / 16 behind, with 12 changed files. Exact-head Daily #45207916219, broker #45207915676, and security #45207915681 passed. This shared-handoff commit creates a new head and requires fresh exact-head checks; no separate Workers Builds result was surfaced.
- PR #202 is open/draft at `8d4a25e2516d404610fdf6cd9e1e9c55f062b6e0`, 68 ahead / 16 behind; exact-head full tests, additional tests, and security passed. Its description reports Workers preview job #137441608988 success, not independently re-fetched. PR #201/#202 share four files; PR #200 additionally touches ACTIVE_SESSION_BRIEF.md and LOOSE_ENDS.md.
- The Buddy guide and docs index on this branch already satisfy their side of the four-file reconciliation: v2 branch/PR rules, historical Codex/API status, Buddy → Jockey → Boots → Buddy responsibility, Trio Protocol in Start here, Daily recommendation-memory guide entry, and 22-workflow count. The protocol file remains only on PR #202's branch, so its link remains a temporary direct branch URL.
- [x] Refresh the active-session brief and loose-ends register with current worker/run/branch/PR/CI evidence and explicitly preserve the #201/#202 merge gate.
- [ ] Recheck exact-head CI on the new Buddy PR head created by this checkpoint; the #452079 and earlier checks do not transfer to a later commit.
- [ ] Obtain an owner-approved merge order for PR #201/#202 that also accounts for PR #200's overlap. The #202-first sequence in its description is a proposal, not authorization; keep all PRs draft.
- [ ] Observe a complete Phase 1 Buddy → Jockey → Boots → Buddy runtime cycle. Jockey and Boots are disabled/BLOCKED. Phase 2 cross-repair remains disabled and unauthorized.

## Current operating-policy overlay — 2026-11-06

Babel remains an active workstream, but it is no longer a gate that blocks all other SHIT work. The user explicitly authorized ChatGPT to continue other SHIT workstreams in parallel while Buddy continues documentation maintenance. Each workstream must keep its roadmap and ACTIONS current and preserve its own safety boundaries.

ChatGPT may independently publish routine, verified documentation-only changes directly to `main` when the connected GitHub capability permits. Independent review is mandatory: inspect the complete diff, verify claims against current source/tests/workflows/evidence, check links and cross-document consistency, run relevant safe checks, and read every changed file back. Routine documentation changes do not require per-change user review.

Buddy remains proposal-only on `babel/chatgpt-buddy-v2` and its draft PR. It must not write to `main`, approve, mark ready, close, merge, or self-merge. Runtime/product changes, provider operations, playlists, canonical/generated data, workflow logic, permissions, secrets, security controls, dependency manifests, and ambiguous side effects remain outside ChatGPT's documentation authority and require separate user authorization.

See [AGENTS.md](../../../AGENTS.md), [documentation rules](../../DOCUMENTATION_RULES.md), and [the ChatGPT Buddy policy](../../../docs/BABEL_CHATGPT_BUDDY.md). This overlay supersedes older statements below that call documentation the sole active SHIT workstream or require user review/merge for every documentation change.

# Maintainability & Documentation — Roadmap

**Last reviewed:** 2026-11-24 09:35 Eastern
**Status:** In progress. The four shared files are reconciled on Buddy's branch: the Buddy guide and docs index already satisfied the requirements and were retained; the active-session brief and loose-ends register now carry a 2026-11-24 09:35 Eastern overlay. Exact-head GitHub Actions passed on pre-change Buddy head `045187191d79dbedae48d6735e918512f350a2cd`; this batch advances the branch and requires fresh checks. Owner-approved merge order across PRs #201/#202/#200, maintained-file/guide semantic coverage, all-goal review, operational safety-contract audit, and fresh-session simulation remain open.

## Purpose
Make SHIT understandable, maintainable, and recoverable by a contributor or assistant with no access to prior chat history. Repository documentation—not chat memory—is the durable source of truth.

## Established structure
- Public-facing identity: **SHIT Documentation & Continuity**; internal codename: **Babel**. The naming convention and system contract are defined in [docs/BABEL.md](../../../docs/BABEL.md).
- Root [AGENTS.md](../../../AGENTS.md): mandatory instructions for every assistant/contributor session.
- [Documentation rules](../../DOCUMENTATION_RULES.md): required reading, same-session updates, evidence vocabulary and completion checklist.
- [Documentation index](../../../docs/README.md): navigation to technical references and workstreams.
- [Project roadmap](../../ROADMAP.md): cross-workstream priorities and dependencies.
- [NEXT_WORK.md](../../NEXT_WORK.md), [LOOSE_ENDS.md](../../LOOSE_ENDS.md), and [PROJECT_LOG.md](../../PROJECT_LOG.md): current handoff, unresolved work, and chronology.
- [Goal index](../README.md): 14 goal workspaces, each expected to contain ROADMAP, README and ACTIONS.
- [Repository file index](../../../docs/REPOSITORY_FILE_INDEX.md): tracked file and directory inventory.

## Required per-file documentation
Every maintained script/module/workflow should state its purpose, supported goal, inputs/outputs, dependencies/data paths, network and write side effects, safety/rate/mutation boundaries, and how to run/test it. Tests and schemas should have clear scope and ownership. Do not put prose into machine-readable JSON; use adjacent documentation or supported metadata.

## Naming convention
The documentation system is publicly named **SHIT Documentation & Continuity** and internally codenamed **Babel**. The naming contract is documented in [docs/BABEL.md](../../../docs/BABEL.md) and surfaced from the repository's first-contact entry points.

## Roadmap
1. **Mandatory continuity rules and navigation — implemented.** Root instructions, documentation rules, docs index, project roadmap and README links now exist on main.
2. **Verify all goal workspaces.** Confirm every indexed goal has ROADMAP, README and ACTIONS; inspect links and reconcile current status.
3. **Audit file-level coverage.** Compare all tracked scripts, modules, compatibility launchers, tests, workflows, schemas and data contracts with the file index and per-file overview requirements.
4. **Repair high-risk documentation gaps.** Prioritize write-capable tools, scheduled workflows, authentication, shared generated-state writers, safety policies and recovery paths.
5. **Automate checks.** Add maintainable link/path checks and meaningful documentation coverage checks; avoid brittle boilerplate-only checks.
6. **Reconcile cross-project records.** Keep NEXT_WORK, LOOSE_ENDS, PROJECT_LOG, project roadmap and goal roadmaps synchronized with current GitHub evidence.
7. **Fresh-session test.** Verify a new assistant can identify priorities, constraints, exact next actions and verification commands from repository docs alone.

## Active-session continuity bridge

- [x] Create `project/ACTIVE_SESSION_BRIEF.md` as a curated, privacy-safe bridge between active ChatGPT work and Buddy. Created on main in commit `55f1403c8feb614b1b6763ce8873499bdcbe4c86`.
- [x] Update Buddy's continuation prompt to read the active brief first and reconcile it against checked-out source/evidence. Prompt update commit: `bad03f65cbe92690718278440886a84014fd79a1`.
- [x] Make the brief a mandatory same-session operating rule in first-contact and documentation guidance (`AGENTS.md`, `project/DOCUMENTATION_RULES.md`, `docs/BABEL_AGENT.md`, Buddy continuation prompt, roadmap and action history). Commits: `798674d`, `e9339c7`, `991b1ff`, `bad03f6`, `01ee1d2`, `5899053`.
- [ ] Verify Buddy reads the brief in its first successful run and reports reconciliation with live repository state.
- [ ] Perform a cold-start simulation proving the brief and repository docs are sufficient without prior chat history.
- [ ] Confirm privacy boundaries: curated SHIT context only; no raw chat dumps, unrelated personal context, or secret values.

## Scheduled ChatGPT Buddy — current continuation path

- [x] Establish the daily scheduled ChatGPT/GitHub-app task with documentation-only scope and a draft-PR publication boundary.
- [x] Repair the stale Buddy branch safely: retain the former `babel/chatgpt-buddy` branch for reference, close obsolete draft PR #163 without merging, and create `babel/chatgpt-buddy-v2` from current `main`.
- [x] Reconcile the active-worker guides and goal handoff with the scheduled ChatGPT Buddy path; document the Codex/API workflow as a separate quota-blocked experiment, while keeping its repository-level enabled/disabled state explicitly unverified.
- [x] Re-enable the daily Buddy automation and request an immediate run on 2026-11-20.
- [x] Independently reviewed Buddy PR #201 at audit-start head `67df681f8227b04b4cfe6137a7fcfce544fb25cb`; its exact-head test, security, and Workers Builds checks passed. The review found stale Codex/activation wording and workflow counts corrected in this batch.
- [x] Exact-head Daily curator tests, Mobile Auth Broker Tests, and public repository security scan passed on post-checkpoint head `7c7da5c7f6199070161672e1c57f43cb3e29517d` (runs #45207299259, #45207299393, and #45207299147). The final action-log/roadmap checkpoint commits create a new head and require fresh exact-head checks; no separate Workers Builds result was exposed.
- [x] Reconcile the four shared PR #201/#202 files on Buddy's own branch; the protocol link temporarily targets PR #202's branch because the file is not on main.
- [ ] Finalize an owner-approved merge order for #201/#202, also accounting for PR #200's overlap on ACTIVE_SESSION_BRIEF.md and LOOSE_ENDS.md. The #202-first sequence in its description is a proposal, not authorization.
- [ ] Perform the fresh-session simulation using merged repository documentation.

## Legacy Codex/API workflow — execution-state safety

- [x] Reconcile the Codex experiment's documentation with the current workflow source: the YAML still declares a six-hour schedule, manual dispatch, and push trigger.
- [x] Preserve the distinction between the current scheduled ChatGPT Buddy and the separate repository-hosted Codex/API experiment.
- [x] Document that the repository-level workflow enabled/disabled state is not confirmed by the available read-only GitHub access. Do not call the workflow disabled or guaranteed dormant.
- [ ] Repository owner confirms the legacy Codex workflow is disabled in GitHub Actions if no scheduled API execution is wanted, or explicitly reauthorizes a separate workflow change. Buddy must not change workflow logic/settings or dispatch it.
- **Safety invariant:** keep `project/BABEL_AGENT_STATE.md` at `status: active` while Babel acceptance remains open. The workflow's `status: complete` sentinel is not a pause switch and must not be used to suppress API execution; preflight also skips the agent when `OPENAI_API_KEY` is absent, but this audit did not inspect or verify that secret.

## Deferred successor: SHIT-wide Integrity, Diagnostics & Recovery

Once this roadmap's acceptance criteria pass **and** the fresh-session simulation succeeds, revisit a separate cross-project workstream tentatively titled **Integrity, Diagnostics & Recovery**. This is a future design checkpoint only; it is not part of Babel's current implementation scope and must not interrupt documentation completion.

The intended system should monitor integrity and operational health across canonical data, derived data, documentation, tests and workflows; diagnose root causes; maintain a prioritized improvement backlog; and support carefully bounded recovery. Buddy should continue as the permanent **Documentation & Continuity Guardian**, checking documentation drift, roadmap/action-log freshness, handoff accuracy and evidence quality as one contributor to overall health—not as the sole authority over health or repair approval.

Preserve strict safety boundaries: canonical data/provenance remain authoritative; Last.fm scrobbles are not conflated with optional Spotify playback observations; no fabricated or silently discarded records; deterministic repairs only, with explicit scope, backups, reversibility, audit trails and post-repair verification; user approval for consequential or ambiguous mutations. At the revisit, establish a dedicated goal workspace, ownership, severity model, autonomy levels, repair policy, reporting cadence and acceptance tests before implementation.

## Historical Codex/API experiment — first attempt diagnosed

- First ChatGPT-triggered run [#42181953313](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42181953313) was received; preflight passed, but Codex failed before prompt execution on Ubuntu 26.04 during `drop-sudo` D-Bus socket restriction. Validation and publication were skipped.
- The failure matches [upstream openai/codex-action issue #188](https://github.com/openai/codex-action/issues/188). The Codex agent job is pinned to `ubuntu-24.04` as a compatibility workaround, without changing the security strategy or permission separation.
- This historical Codex/API experiment is not the active Buddy path and is not authorized for retry. Its runner compatibility workaround is verified; successful Codex execution, independent validation, and isolated PR publication remain unverified.

## Historical Codex/API experiment — retry reached Codex; API quota blocked

- Retry [#42183337573](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42183337573) ran the Codex job on Ubuntu 24.04. Preflight and `drop-sudo` isolation succeeded, confirming the Ubuntu 26.04 compatibility workaround.
- Codex then returned `Quota exceeded. Check your plan and billing details.` Validation and publication were skipped; no candidate patch or PR was produced. The worker is not yet operationally verified.
- No retry is currently authorized. Do not ask the user to fund API quota or re-enable the experiment. Any future activation requires explicit user reauthorization and owner-controlled GitHub Actions configuration. Preserve the historical runner/sandbox evidence; never weaken `drop-sudo` or workspace restrictions.
- Daily curator run [#42183307146](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42183307146) passed all 478 tests and security scan [#42183307047](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42183307047) passed on commit `ffc75f5796d422d6f3bcd889465a00f0c613a57e`.

## Acceptance criteria
- Every indexed goal has ROADMAP, README and ACTIONS with current links.
- Every maintained executable file has a useful overview or an explicit adjacent-documentation entry; no file is falsely marked covered.
- File index matches the tracked repository inventory and identifies generated versus canonical data.
- Operational docs identify inputs, outputs, side effects, permissions, safety boundaries, failure/retry behavior and verification.
- A fresh session can resume each active goal without chat history.
- Meaningful work updates relevant documentation in the same session; status claims cite exact evidence.

## Automated guardrails — core checks implemented and CI-verified
- `tests/test_documentation_contract.py` dynamically enforces ROADMAP/README/ACTIONS coverage for every goal workspace, AGENTS continuity requirements, major documentation-domain coverage, Babel identity and local links from primary entry points.
- `tests/test_script_layout.py` checks compatibility delegation, package layout, and bottom `FILE OVERVIEW` presence across maintained Python implementations, compatibility launchers, test modules and workflow YAMLs. Its known-placeholder guard scans those same maintained file families.
- Daily curator run #42168520574 passed all 460 tests on commit `8153028e4123d2be9307983b0eccff47fcaf07f9`; public repository security scan #42168520598 also passed on that commit. The later metadata-enrichment publication is separately validated by run #42166959478 and the post-enrichment integrity audit.

## Repository inventory correction — implemented
- Replaced the stale exhaustive file snapshot with a maintained source and data-family index. The previous snapshot incorrectly implied a small, static `assistant_data` file count despite the expanded per-record canonical music Library.
- The new index distinguishes canonical Last.fm scrobbles, canonical structured music Library records, generated analytics/profiles, optional playback observations, Spotify playlist state/feedback, source code, tests, and GitHub automation.
- It documents commands for retrieving the exact current tracked path inventory instead of embedding a stale generated-record listing.

## Complete committed-tree inventory — verified 2026-11-06

- Snapshot commit: `3d2c1ded8dfb44b92e6e0c086673c69350200edc`.
- A non-recursive root Git Tree plus separate recursive requests for each of the nine top-level directories produced **28,241 file/blob entries**. Every directory-scoped result returned `truncated=false`; the root recursive response was not used because it was truncated.
- Breakdown: root 9; `.github/` 23; `assistant_data/` 27,981; `compat/` 42; `data/` 4; `docs/` 23; `playback_data/` 2; `project/` 50; `scripts/` 61; `tests/` 46.
- Maintained files: 55 Python implementation modules (60 files including five package initializers), 40 compatibility launchers (41 Python files including initializer), 44 test modules (45 Python files including initializer), 17 workflow YAMLs, 21 technical guides and 13 goal workspaces.
- **Outcome:** committed-tree inventory acceptance item is satisfied for this snapshot. Refresh after structural/generated-data changes. See `docs/REPOSITORY_FILE_INDEX.md`.

**Current count note — 2026-11-21:** the current source tree contains 22 workflow YAMLs, and `docs/WORKFLOWS.md` catalogs all 22. The current goal index lists 14 workspaces, and a recursive tree check confirmed every one has `ROADMAP.md`, `README.md`, and `ACTIONS.md`. The `docs/` tree contains 26 Markdown files including `README.md` (25 other Markdown documents). These are structural counts, not proof of semantic completeness. The 2026-11-06 inventory snapshot remains historical; a fresh maintained-file inventory is still required.

## Workflow catalogue and local-link checks — CI-verified

- `docs/WORKFLOWS.md` summarizes all 22 current workflow files, triggers, permissions, credential names, major steps and side effects. The documentation contract fails if a workflow filename is missing from the catalogue.
- The current mainline test validates local links from the primary entry points. A repository-wide all-Markdown local-link check remains a candidate guardrail from draft PR #161 and must be ported/adapted before being treated as implemented.

## 2026-11-06 — Module overview semantic correction

- Replaced generic or underspecified overviews in 28 maintained implementation modules across Spotify operations, music enrichment, Last.fm import, and analytics with module-specific contracts for actual inputs, outputs, providers, limits, provenance, safety boundaries, and invocation.
- The first seven high-risk Spotify modules were committed together; the remaining 17 generic overviews were replaced in two grouped commits. These are documentation/comment-only changes; runtime logic was not changed.
- Added an anti-placeholder regression check in `tests/test_script_layout.py` so known generic fallback phrases cannot silently return to maintained `scripts/` overviews.
- The full 460-test suite passed on commit `da3be75844e3ce28eacd46ce8d87960493402503` (Daily curator run #42167849568), including the anti-placeholder assertion scanning all maintained Python modules under `scripts/` and the explicit Babel identity/link contract. Public repository security scan #42167849588 also passed.
- **Operational side effect:** the source path `scripts/music/enrich_musicbrainz_recording_ids.py` is included in the push filter for Enrich Music Metadata. The documentation-only comment update triggered run #42166959478, which has contents:write and provider-enrichment steps. It completed successfully and published generated metadata as commit `3d2c1ded8dfb44b92e6e0c086673c69350200edc`. The run merged 195 discovery candidates into the canonical Library, audited 13,239 songs, and rebuilt summaries/analytics. Post-enrichment integrity audit: 9 checks, 18 warnings, 0 errors. The warnings were a missing measured-playback capture and 16 Spotify playlist snapshots with inaccessible item contents; preserved snapshot data may be stale. No Spotify playlist write is part of that workflow.
- **Process correction:** future source-overview edits must inspect all matching workflow path filters first, batch related changes into one commit, and record any unavoidable provider/write side effects. Prefer documentation-only paths when the same contract can be maintained adjacent to source without weakening the required in-file overview standard.

## 2026-11-05 repository audit checkpoint

- Confirmed current default branch `main` at `b542ceab2c40f6910a91ea3fcb84c204fc412c2d`.
- Confirmed 13 goal workspaces, each with ROADMAP.md, README.md and ACTIONS.md.
- Confirmed 17 GitHub Actions workflow YAML files and a workflow catalogue that the documentation contract test checks dynamically.
- Confirmed maintained implementation directories: `scripts/analytics/` (7 Python modules), `scripts/lastfm/` (1), `scripts/music/` (24), and `scripts/spotify/` (19); `compat/`, `tests/`, and `.github/workflows/` are included in the FILE OVERVIEW presence check.
- Latest observed full Daily curator test run #42144512658 and full-history public-repository security scan #42144512423 succeeded on the current main SHA. This is evidence for the automated checks on that commit, not semantic correctness of documentation.
- The recursive Git tree API result was truncated by the large generated per-record Library tree. It is explicitly not accepted as a complete inventory. Directory-scoped listings were used for maintained code and goal workspaces.
- Three open Daily PRs were observed (#158, #159, #160); their proposed behavior is not treated as merged implementation.

## Source-audit evidence added — 2026-11-06

- Great Migration `preview` and `prepare-preview` were traced through the workflow, preparation script, CLI dispatcher, and full migrator. The dry-run path returns before resolver construction, backup creation, or canonical Library writes; no provider requests or Spotify playlist writes occur. A regression test now guards this call chain. The new test is pending CI execution.

## Current gaps / uncertainty
- The 2026-11-06 inventory counts (55 implementation modules, 40 compatibility launchers, 44 test modules, 17 workflows, 21 guides, and 13 goal workspaces) are historical. The 2026-11-21 structural check confirms 22 workflow YAMLs, 14 goal workspaces with all required files, and 26 Markdown files under `docs/` including the index; the broader maintained-file inventory still needs a fresh tree-based refresh.
- Semantic accuracy remains under review across maintained implementations, compatibility launchers, tests, all 22 workflow overviews, and 25 non-index Markdown documents. Do not treat the historical module/launcher/test counts as current until the inventory is refreshed.
- All-Markdown local-link validation and comprehensive workflow/goal cross-contract tests are not yet on main; the draft PR #161 contains candidate implementations that must be reconciled rather than blindly merged.
- The current open PR/issue set and domain-specific loose ends must be rechecked against live GitHub state. Buddy PR #201 and the separate trio-coordination PR #202 are both open drafts and overlap on shared index/handoff files; keep ownership separate and reconcile their merge order before changing additional overlapping files.

## Historical repository-hosted Codex/API workflow — source committed; execution quota-blocked

- The source remains committed at `.github/workflows/babel-ai-continuation.yml` with a six-hour schedule, manual dispatch, and a push trigger for `babel/dispatch-*`. This is a separate historical Codex/API experiment, not the current scheduled ChatGPT Buddy.
- The latest observed scheduled runs [#44808721608](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/44808721608) (2026-11-20 20:09 UTC) and [#44878119328](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/44878119328) (2026-11-21 06:59 UTC) both passed preflight, then failed in the Codex agent with an explicit API quota-exceeded response. Validation and publishing were skipped; no candidate patch or Codex PR was produced. The initial #42181953313/#42183337573 attempts remain historical runner/quota diagnostics. These recent runs prove the schedule triggered at those times; the available read-only API did not expose the workflow's current enabled/disabled setting.
- Workflow preflight stops when `project/BABEL_AGENT_STATE.md` contains the exact `status: complete` sentinel and also skips the agent when `OPENAI_API_KEY` is absent. The state remains `status: active` because Babel acceptance is open. The secret's presence/value was not inspected.
- Repository-level workflow enablement is unverified. Do not describe the workflow as disabled or dormant. Do not dispatch, retry, request API funding, or change workflow settings without explicit user reauthorization. If no scheduled Codex execution is wanted, the repository owner must disable it in GitHub Actions; Buddy must not change workflow logic/settings.
- The historical workflow was designed with a read-only Codex job, isolated validation, and a separate publisher. This is source-configuration evidence, not proof of a successful recent Codex run.
- The current continuation worker is the scheduled ChatGPT Buddy using the connected GitHub app and the `babel/chatgpt-buddy-v2` branch; see [docs/BABEL_CHATGPT_BUDDY.md](../../../docs/BABEL_CHATGPT_BUDDY.md).

## Next action

1. Re-fetch PR #201's live head and exact-head CI after any subsequent documentation commit; the checks recorded above apply to `c741846e84b40c962552f347bf42e7c4d8825d6c` and do not transfer to a later commit.
2. Keep PR #201 draft. Obtain an owner-approved merge order across #201/#202/#200; reconcile the four #201/#202 shared files and #200's additional handoff overlap before any merge.
3. After the Trio Protocol reaches `main`, replace the temporary branch URL in the Buddy guide and docs index with a repository-relative link, then rerun documentation checks.
4. Continue the maintained-file and technical-guide semantic audit, all-goal semantic review, operational safety-contract audit, and fresh-session simulation using repository documentation alone.

## Related records
[README](README.md) · [ACTIONS](ACTIONS.md) · [Documentation rules](../../DOCUMENTATION_RULES.md) · [Documentation index](../../../docs/README.md)
