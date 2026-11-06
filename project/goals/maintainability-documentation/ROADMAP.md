# Maintainability & Documentation — Roadmap

**Last reviewed:** 2026-11-06  
**Status:** In progress. The documentation control structure is established; the full file-level coverage and freshness audit remains open.

## Purpose
Make SHIT understandable, maintainable, and recoverable by a contributor or assistant with no access to prior chat history. Repository documentation—not chat memory—is the durable source of truth.

## Established structure
- Root [AGENTS.md](../../../AGENTS.md): mandatory instructions for every assistant/contributor session.
- [Documentation rules](../../DOCUMENTATION_RULES.md): required reading, same-session updates, evidence vocabulary and completion checklist.
- [Documentation index](../../../docs/README.md): navigation to technical references and workstreams.
- [Project roadmap](../../ROADMAP.md): cross-workstream priorities and dependencies.
- [NEXT_WORK.md](../../NEXT_WORK.md), [LOOSE_ENDS.md](../../LOOSE_ENDS.md), and [PROJECT_LOG.md](../../PROJECT_LOG.md): current handoff, unresolved work, and chronology.
- [Goal index](../README.md): 13 goal workspaces, each expected to contain ROADMAP, README and ACTIONS.
- [Repository file index](../../../docs/REPOSITORY_FILE_INDEX.md): tracked file and directory inventory.

## Required per-file documentation
Every maintained script/module/workflow should state its purpose, supported goal, inputs/outputs, dependencies/data paths, network and write side effects, safety/rate/mutation boundaries, and how to run/test it. Tests and schemas should have clear scope and ownership. Do not put prose into machine-readable JSON; use adjacent documentation or supported metadata.

## Roadmap
1. **Mandatory continuity rules and navigation — implemented.** Root instructions, documentation rules, docs index, project roadmap and README links now exist on main.
2. **Verify all goal workspaces.** Confirm every indexed goal has ROADMAP, README and ACTIONS; inspect links and reconcile current status.
3. **Audit file-level coverage.** Compare all tracked scripts, modules, compatibility launchers, tests, workflows, schemas and data contracts with the file index and per-file overview requirements.
4. **Repair high-risk documentation gaps.** Prioritize write-capable tools, scheduled workflows, authentication, shared generated-state writers, safety policies and recovery paths.
5. **Automate checks.** Add maintainable link/path checks and meaningful documentation coverage checks; avoid brittle boilerplate-only checks.
6. **Reconcile cross-project records.** Keep NEXT_WORK, LOOSE_ENDS, PROJECT_LOG, project roadmap and goal roadmaps synchronized with current GitHub evidence.
7. **Fresh-session test.** Verify a new assistant can identify priorities, constraints, exact next actions and verification commands from repository docs alone.

## Acceptance criteria
- Every indexed goal has ROADMAP, README and ACTIONS with current links.
- Every maintained executable file has a useful overview or an explicit adjacent-documentation entry; no file is falsely marked covered.
- File index matches the tracked repository inventory and identifies generated versus canonical data.
- Operational docs identify inputs, outputs, side effects, permissions, safety boundaries, failure/retry behavior and verification.
- A fresh session can resume each active goal without chat history.
- Meaningful work updates relevant documentation in the same session; status claims cite exact evidence.

## Automated guardrails — implemented and CI-verified for current core contract
- Added `tests/test_documentation_contract.py` to enforce required control documents, all goal workspaces' ROADMAP/README/ACTIONS files, AGENTS continuity requirements, major documentation-domain coverage, and local links from the primary entry points.
- Existing `tests/test_script_layout.py` checks bottom `FILE OVERVIEW` coverage across maintained Python implementation, compatibility, tests and GitHub Actions workflow files.
- The repository's standard unittest discovery includes both tests; `.github/workflows/update.yml` runs the full suite before data publishing. A successful CI run after this new test is required before calling the guardrail verified.

## Repository inventory correction — implemented
- Replaced the stale exhaustive file snapshot with a maintained source and data-family index. The previous snapshot incorrectly implied a small, static `assistant_data` file count despite the expanded per-record canonical music Library.
- The new index distinguishes canonical Last.fm scrobbles, canonical structured music Library records, generated analytics/profiles, optional playback observations, Spotify playlist state/feedback, source code, tests, and GitHub automation.
- It documents commands for retrieving the exact current tracked path inventory instead of embedding a stale generated-record listing.

## Workflow catalogue and documentation guardrails

- `docs/WORKFLOWS.md` summarizes all 17 workflow files, triggers, permissions, credential names, major steps and side effects. The documentation contract fails if a workflow filename is missing from the catalogue.
- Nine workflow YAML bottom overviews were rewritten with their actual triggers, credentials, repository writes, playlist-write boundaries and related implementation.
- Workflow YAML comment-only changes can trigger push-path workflows. This operational hazard is now documented; see the incident entry in ACTIONS.md and docs/WORKFLOWS.md.
- The draft documentation PR #161 expands the contract to index every technical guide, validate local links across all Markdown files, reject generic workflow overviews, reject generic implementation boilerplate and require compatibility overviews to name maintained source modules. These new checks are pending CI verification; do not call them implemented/verified until the PR's current head passes.

## 2026-11-06 documentation audit progress

- Confirmed all 13 goal workspaces contain ROADMAP.md, README.md and ACTIONS.md; all 17 workflow YAMLs are catalogued.
- Updated the docs index to list all 21 technical guides, corrected a duplicated paragraph in the goal index, and expanded repository-wide Markdown-link and workflow-overview checks in draft PR #161.
- Replaced generic source overviews with module-specific purpose, input/output, evidence, side-effect and safety descriptions across analytics, Last.fm, music and Spotify implementation modules (32 maintained modules updated in the current draft).
- Current source audit found that marker presence alone had allowed generic boilerplate to pass; the new PR checks aim to prevent this recurring.
- Current main has the documented workflow incident: reference snapshot refresh published, two enrichment publication steps failed, and one broad update workflow remained under observation at the latest check. See ACTIONS.md and NEXT_WORK.md for exact evidence.

\n\n## 2026-11-05 repository audit checkpoint

- Structural audit began at `b542ceab2c40f6910a91ea3fcb84c204fc412c2d`; current default branch `main` was rechecked at `a5fe4de6398e2a3d6651fa7e439d2cb898f4fe0a`.
- Confirmed 13 goal workspaces, each with ROADMAP.md, README.md and ACTIONS.md.
- Confirmed 17 GitHub Actions workflow YAML files and a workflow catalogue that the documentation contract test checks dynamically.
- Confirmed maintained implementation directories: `scripts/analytics/` (7 Python modules), `scripts/lastfm/` (1), `scripts/music/` (24), and `scripts/spotify/` (19); `compat/`, `tests/`, and `.github/workflows/` are included in the FILE OVERVIEW presence check.
- Latest observed full Daily curator test run #42144512658 and full-history public-repository security scan #42144512423 succeeded on the current main SHA. This is evidence for the automated checks on that commit, not semantic correctness of documentation.
- The recursive Git tree API result was truncated by the large generated per-record Library tree. It is explicitly not accepted as a complete inventory. Directory-scoped listings were used for maintained code and goal workspaces.
- Three open Daily PRs were observed (#158, #159, #160); their proposed behavior is not treated as merged implementation.

## PR #161 verification update — 2026-11-06

- First validation failed only because three compatibility wrappers did not name their maintained `scripts/music/` implementation. Those three overviews were corrected.
- The next Daily curator tests run (#42149783445) passed on PR head `5b8bfab94064e74100c6b3ac183817b6a3f4d4bd`. It passed compile, generated-data audit, full Library health/confidence checks, bounded freshness planning, maintained-file documentation checks and full unit tests.
- The new all-Markdown local-link, full guide-index, source overview quality, compatibility reference and workflow overview tests therefore passed on that head.
- The complete-history public security scan (#42149783463) was still in progress at the last check. Recheck it and confirm the PR head has not advanced before considering the PR verified.

## Latest workstream status — 2026-11-06

- All 12 non-documentation goal roadmaps now contain an explicit documentation-only pause; the goal index explains the same priority. The workstream plans are preserved, not discarded.
- Draft PR #161 contains 32 source overview rewrites, a complete 21-guide docs index, repository-wide Markdown-link checks and stronger file-overview quality tests. Latest PR CI must be checked before merge.
- The source inventory and semantic audit remain incomplete; do not declare the acceptance criteria met based only on structural tests or the current PR.
- Exact workflow publication failures from the accidental YAML push triggers are documented in library-enrichment, listening-analytics, this workstream's ACTIONS, NEXT_WORK and LOOSE_ENDS.

## Current gaps / uncertainty
- The full tracked-file inventory has not yet been compared programmatically with documentation coverage; a complete checkout and `git ls-files` are still needed for authoritative whole-repository coverage.
- Goal status and cross-project loose ends still need a complete semantic reconciliation against current main, all seven pre-existing open PRs, current issues and latest workflow runs.
- Repository-wide local-link validation and new overview-quality tests are pending PR #161 CI; any failures must be fixed before merge.
- The source overview audit is improved but not complete; compatibility shims, test overviews, all module docstrings, workflow semantics and data-schema references still need a structured review.

## Next action
Finish PR #161 CI and repair every link/overview-quality failure; review the remaining compatibility and test overviews; obtain a complete checkout/`git ls-files` inventory and compare it with docs/REPOSITORY_FILE_INDEX.md; semantically reconcile all 13 goal roadmaps, seven pre-existing open PRs, workflow side effects and operational runbooks; then complete the fresh-session acceptance simulation. Keep documentation as the only active project priority until every acceptance criterion passes.

## Related records
[README](README.md) · [ACTIONS](ACTIONS.md) · [Documentation rules](../../DOCUMENTATION_RULES.md) · [Documentation index](../../../docs/README.md)
