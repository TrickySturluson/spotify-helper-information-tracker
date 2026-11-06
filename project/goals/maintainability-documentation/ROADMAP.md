## Current operating-policy overlay — 2026-11-06

Babel remains an active workstream, but it is no longer a gate that blocks all other SHIT work. The user explicitly authorized ChatGPT to continue other SHIT workstreams in parallel while Buddy continues documentation maintenance. Each workstream must keep its roadmap and ACTIONS current and preserve its own safety boundaries.

ChatGPT may independently publish routine, verified documentation-only changes directly to `main` when the connected GitHub capability permits. Independent review is mandatory: inspect the complete diff, verify claims against current source/tests/workflows/evidence, check links and cross-document consistency, run relevant safe checks, and read every changed file back. Routine documentation changes do not require per-change user review.

Buddy remains proposal-only on `babel/chatgpt-buddy` and its draft PR. It must not write to `main`, approve, mark ready, close, merge, or self-merge. Runtime/product changes, provider operations, playlists, canonical/generated data, workflow logic, permissions, secrets, security controls, dependency manifests, and ambiguous side effects remain outside ChatGPT's documentation authority and require separate user authorization.

See [AGENTS.md](../../../AGENTS.md), [documentation rules](../../DOCUMENTATION_RULES.md), and [the ChatGPT Buddy policy](../../../docs/BABEL_CHATGPT_BUDDY.md). This overlay supersedes older statements below that call documentation the sole active SHIT workstream or require user review/merge for every documentation change.

# Maintainability & Documentation — Roadmap

**Last reviewed:** 2026-11-06  
**Status:** In progress. The documentation control structure is established; the full file-level coverage and freshness audit remains open.

## Purpose
Make SHIT understandable, maintainable, and recoverable by a contributor or assistant with no access to prior chat history. Repository documentation—not chat memory—is the durable source of truth.

## Established structure
- Public-facing identity: **SHIT Documentation & Continuity**; internal codename: **Babel**. The naming convention and system contract are defined in [docs/BABEL.md](../../../docs/BABEL.md).
- Root [AGENTS.md](../../../AGENTS.md): mandatory instructions for every assistant/contributor session.
- [Documentation rules](../../DOCUMENTATION_RULES.md): required reading, same-session updates, evidence vocabulary and completion checklist.
- [Documentation index](../../../docs/README.md): navigation to technical references and workstreams.
- [Project roadmap](../../ROADMAP.md): cross-workstream priorities and dependencies.
- [NEXT_WORK.md](../../NEXT_WORK.md), [LOOSE_ENDS.md](../../LOOSE_ENDS.md), and [PROJECT_LOG.md](../../PROJECT_LOG.md): current handoff, unresolved work, and chronology.
- [Goal index](../README.md): 13 goal workspaces, each expected to contain ROADMAP, README and ACTIONS.
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

## Controlled ChatGPT dispatch

- [x] Add a narrowly scoped `push` trigger for fresh `babel/dispatch-*` branches, filtered to `.github/babel/dispatch.json`; retain manual dispatch and the six-hour schedule.
- [x] Ensure the dispatch branch is only an event trigger: preflight and all work jobs continue to select `main` or `babel/agent-progress`, never treating the marker branch as a work base.
- [ ] Execute the first ChatGPT-triggered run and verify Codex, independent validation, and isolated PR publication.

## Deferred successor: SHIT-wide Integrity, Diagnostics & Recovery

Once this roadmap's acceptance criteria pass **and** the fresh-session simulation succeeds, revisit a separate cross-project workstream tentatively titled **Integrity, Diagnostics & Recovery**. This is a future design checkpoint only; it is not part of Babel's current implementation scope and must not interrupt documentation completion.

The intended system should monitor integrity and operational health across canonical data, derived data, documentation, tests and workflows; diagnose root causes; maintain a prioritized improvement backlog; and support carefully bounded recovery. Buddy should continue as the permanent **Documentation & Continuity Guardian**, checking documentation drift, roadmap/action-log freshness, handoff accuracy and evidence quality as one contributor to overall health—not as the sole authority over health or repair approval.

Preserve strict safety boundaries: canonical data/provenance remain authoritative; Last.fm scrobbles are not conflated with optional Spotify playback observations; no fabricated or silently discarded records; deterministic repairs only, with explicit scope, backups, reversibility, audit trails and post-repair verification; user approval for consequential or ambiguous mutations. At the revisit, establish a dedicated goal workspace, ownership, severity model, autonomy levels, repair policy, reporting cadence and acceptance tests before implementation.

## Buddy activation test — first attempt diagnosed

- First ChatGPT-triggered run [#42181953313](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42181953313) was received; preflight passed, but Codex failed before prompt execution on Ubuntu 26.04 during `drop-sudo` D-Bus socket restriction. Validation and publication were skipped.
- The failure matches [upstream openai/codex-action issue #188](https://github.com/openai/codex-action/issues/188). The Codex agent job is pinned to `ubuntu-24.04` as a compatibility workaround, without changing the security strategy or permission separation.
- Activation remains open until a new run proves Codex execution, allowlist/deletion checks, full unittest discovery, and isolated PR publication.

## Buddy activation retest — runner fixed; API quota remains blocked

- Retry [#42183337573](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42183337573) ran the Codex job on Ubuntu 24.04. Preflight and `drop-sudo` isolation succeeded, confirming the Ubuntu 26.04 compatibility workaround.
- Codex then returned `Quota exceeded. Check your plan and billing details.` Validation and publication were skipped; no candidate patch or PR was produced. The worker is not yet operationally verified.
- The repository owner must ensure the OpenAI API project/organization has available quota/credits and a usable billing limit. Do not retry until quota is confirmed. Keep `drop-sudo`, workspace restrictions, read-only validation and isolated publisher unchanged.
- Daily curator run [#42183307146](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42183307146) passed all 478 tests and security scan [#42183307047](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42183307047) passed on commit `ffc75f5796d422d6f3bcd889465a00f0c613a57e`.

## Acceptance criteria
- Every indexed goal has ROADMAP, README and ACTIONS with current links.
- Every maintained executable file has a useful overview or an explicit adjacent-documentation entry; no file is falsely marked covered.
- File index matches the tracked repository inventory and identifies generated versus canonical data.
- Operational docs identify inputs, outputs, side effects, permissions, safety boundaries, failure/retry behavior and verification.
- A fresh session can resume each active goal without chat history.
- Meaningful work updates relevant documentation in the same session; status claims cite exact evidence.

## Automated guardrails — core checks implemented and CI-verified
- `tests/test_documentation_contract.py` enforces required control documents, all 13 goal workspaces' ROADMAP/README/ACTIONS files, AGENTS continuity requirements, major documentation-domain coverage, Babel identity and local links from primary entry points.
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

**Current count note:** the committed-tree snapshot above recorded 17 workflow YAMLs. The live repository now contains 18 after the Babel AI continuation workflow was added; the inventory snapshot remains historical until refreshed.

## Workflow catalogue and local-link checks — CI-verified

- `docs/WORKFLOWS.md` summarizes all 18 current workflow files, triggers, permissions, credential names, major steps and side effects. The documentation contract fails if a workflow filename is missing from the catalogue.
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
- Structural inventory is complete for the stated commit; semantic accuracy of all 55 implementation overviews, 40 compatibility launchers, 44 test modules and 17 workflow overviews remains under review.
- The 21 technical guides and 13 goal workspaces still require a source-to-document freshness pass, including exact inputs/outputs, provider budgets, credentials, permissions, publication behavior and recovery paths.
- All-Markdown local-link validation and comprehensive workflow/goal cross-contract tests are not yet on main; the draft PR #161 contains candidate implementations that must be reconciled rather than blindly merged.
- The current open PR/issue set and domain-specific loose ends must be rechecked against live GitHub state; old historical checkpoints are not current evidence.

## AI continuation infrastructure — implemented; activation pending

- Added the repository-hosted Codex worker in .github/workflows/babel-ai-continuation.yml, with its task contract in .github/babel/CONTINUATION_PROMPT.md and durable stop/recovery state in project/BABEL_AGENT_STATE.md.
- The worker runs every six hours or by manual dispatch, resumes from the dedicated babel/agent-progress branch, and is designed to create/update one review PR rather than commit to main.
- The agent job is read-only at the GitHub API level and workspace-scoped for local edits. A separate read-only validation job enforces the strict documentation/test allowlist, rejects deletions/out-of-scope paths, and runs full unittest discovery without the API key or write-capable GitHub token. The final publisher alone receives contents:write / pull-requests:write and does not execute candidate code.
- The workflow has no music-provider or Spotify credentials and is forbidden from feature implementation, generated-data changes, playlist operations, or provider calls.
- **Status distinction:** workflow/prompt/state/docs are committed; successful execution is not yet verified. Activation requires the repository secret OPENAI_API_KEY. API usage is billed separately from a ChatGPT subscription. Configure the repository setting that allows GitHub Actions to create pull requests if it is currently disabled.
- Guide: docs/BABEL_AGENT.md. Do not mark the worker operational until the first Actions run passes and its branch/PR is inspected.


**2026-11-06 dispatch milestone:** ChatGPT successfully created `babel/dispatch-20261106-01` and committed `.github/babel/dispatch.json` (`7c1abce763d293992872699146eb7f13d10f9b87`), proving the connected GitHub integration can emit the configured push trigger. First workflow execution and all job outcomes remain unverified; inspect the Actions run before marking activation complete.

## Next action
Continue the semantic audit of all 55 maintained implementation modules, 40 compatibility launchers, 44 test modules and 17 workflow overviews. Prioritize write-capable Spotify tools, scheduled workflows, authentication/secret rotation, shared generated-state writers, migration/recovery paths and data provenance. Reconcile all 21 technical guides, all 13 goal workspaces, open PRs/issues and the cross-project loose-ends register. Add targeted regression checks for real operational contracts, then complete a fresh-session resume simulation. Keep documentation as the only active project priority until that acceptance test passes.

## Related records
[README](README.md) · [ACTIONS](ACTIONS.md) · [Documentation rules](../../DOCUMENTATION_RULES.md) · [Documentation index](../../../docs/README.md)
