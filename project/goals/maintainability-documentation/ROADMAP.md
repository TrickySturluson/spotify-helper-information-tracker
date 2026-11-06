# Maintainability & Documentation — Roadmap

**Last reviewed:** 2026-11-05  
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

## Workflow catalogue and local-link checks — CI-verified\n- `docs/WORKFLOWS.md` summarizes all 17 current workflow files, triggers, permissions, credential names, major steps and side effects. `tests/test_documentation_contract.py` fails if a workflow filename is missing from the catalogue.\n- The same test parses and validates local links from the primary entry points. Its Markdown-link regex was corrected and verified in run #42144349548 (commit 9a624875).\n\n## 2026-11-05 repository audit checkpoint

- Confirmed current default branch `main` at `b542ceab2c40f6910a91ea3fcb84c204fc412c2d`.
- Confirmed 13 goal workspaces, each with ROADMAP.md, README.md and ACTIONS.md.
- Confirmed 17 GitHub Actions workflow YAML files and a workflow catalogue that the documentation contract test checks dynamically.
- Confirmed maintained implementation directories: `scripts/analytics/` (7 Python modules), `scripts/lastfm/` (1), `scripts/music/` (24), and `scripts/spotify/` (19); `compat/`, `tests/`, and `.github/workflows/` are included in the FILE OVERVIEW presence check.
- Latest observed full Daily curator test run #42144512658 and full-history public-repository security scan #42144512423 succeeded on the current main SHA. This is evidence for the automated checks on that commit, not semantic correctness of documentation.
- The recursive Git tree API result was truncated by the large generated per-record Library tree. It is explicitly not accepted as a complete inventory. Directory-scoped listings were used for maintained code and goal workspaces.
- Three open Daily PRs were observed (#158, #159, #160); their proposed behavior is not treated as merged implementation.

## Current gaps / uncertainty
- The full tracked-file inventory has not yet been compared programmatically with documentation coverage; a complete checkout and `git ls-files` are still needed for authoritative whole-repository coverage.
- Goal status and cross-project loose ends need reconciliation against current main, open PRs/issues and latest workflow runs.
- Link integrity and whether every referenced guide still exists have not yet been exhaustively checked.
- Existing per-file overview claims in the repository README are not yet independently audited.

## Next action
Continue with a directory-by-directory maintained-file audit, obtain a complete checkout/`git ls-files` inventory when available, compare it with file overviews and docs/REPOSITORY_FILE_INDEX.md, then record a categorized gap list. Audit semantic accuracy—not just marker presence—starting with write-capable Spotify tools, scheduled workflows, authentication, shared generated-state writers and recovery paths. Reconcile the 13 goal roadmaps and open PRs/issues. Keep documentation as the only active project priority until the fresh-session acceptance test passes.

## Related records
[README](README.md) · [ACTIONS](ACTIONS.md) · [Documentation rules](../../DOCUMENTATION_RULES.md) · [Documentation index](../../../docs/README.md)
