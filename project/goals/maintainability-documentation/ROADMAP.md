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

## Automated guardrails — implemented; corrected core checks CI-verified
- Added `tests/test_documentation_contract.py` to enforce required control documents, all goal workspaces' ROADMAP/README/ACTIONS files, AGENTS continuity requirements, major documentation-domain coverage, and local links from the primary entry points.
- Existing `tests/test_script_layout.py` checks bottom `FILE OVERVIEW` coverage across maintained Python implementation, compatibility, tests and GitHub Actions workflow files.
- The repository's standard unittest discovery includes both tests; `.github/workflows/update.yml` runs the full suite before data publishing. The corrected layout guard and full unittest suite passed Daily curator CI run #42152796114 on commit `9cbf695291fa073f96669f20e83404eccba4e45e`. The full-history security scan #42152796120 also passed on that commit. Later documentation-only commits have not been shown with a fresh exact-head run; see the current status below.

## Repository inventory correction — implemented
- Replaced the stale exhaustive file snapshot with a maintained source and data-family index. The previous snapshot incorrectly implied a small, static `assistant_data` file count despite the expanded per-record canonical music Library.
- The new index distinguishes canonical Last.fm scrobbles, canonical structured music Library records, generated analytics/profiles, optional playback observations, Spotify playlist state/feedback, source code, tests, and GitHub automation.
- It documents commands for retrieving the exact current tracked path inventory instead of embedding a stale generated-record listing.

## Complete committed-tree inventory — verified 2026-11-06

- The single recursive root-tree request was truncated by the large generated Library subtree, so it was not used as evidence.
- Replaced that incomplete approach with the root Contents listing plus separate recursive Git Trees requests for every top-level directory. The `assistant_data/` directory was split into its nine immediate child subtrees plus its root-level files.
- All queried directory trees returned `truncated=false`; all root and immediate `assistant_data/` entries were included.
- Counted 28,161 committed file/blob entries at audit commit `7cc839f3f00eeb026cd898099654eea8f9a79497`: 9 root files, 23 `.github/`, 42 `compat/`, 4 `data/`, 22 `docs/`, 2 `playback_data/`, 50 `project/`, 61 `scripts/`, 46 `tests/`, and 27,902 `assistant_data/`.
- Maintained-code totals reconcile: 55 implementation modules, 40 compatibility launchers, 44 test modules, 17 workflows, 21 technical guides, and 13 goal workspaces.
- The complete snapshot replaces the prior assumption that a local checkout was required to get a defensible committed-tree inventory. A local `git ls-files` remains the easiest repeatable refresh method when a checkout is available.
- Generated records remain family/schema-documented rather than individually enumerated in prose. The file index now records counts and family distribution.
- **Outcome:** tracked committed-tree inventory acceptance item satisfied for the audited commit; refresh after future structural changes.

## Workflow catalogue and documentation guardrails

- `docs/WORKFLOWS.md` summarizes all 17 workflow files, triggers, permissions, credential names, major steps and side effects. The documentation contract fails if a workflow filename is missing from the catalogue.
- Nine workflow YAML bottom overviews were rewritten with their actual triggers, credentials, repository writes, playlist-write boundaries and related implementation.
- Workflow YAML comment-only changes can trigger push-path workflows. This operational hazard is now documented; see the incident entry in ACTIONS.md and docs/WORKFLOWS.md.
- Draft PR #161 adds complete technical-guide indexing, repository-wide Markdown local-path checks, specific workflow overview checks, implementation/test overview anti-boilerplate checks and compatibility-to-source references. The corrected test-overview guard and full unittest discovery passed on commit `9cbf695291fa073f96669f20e83404eccba4e45e` in run #42152796114; full-history security scan #42152796120 also passed on that commit. Later commits changed only documentation/handoff files and `tests/README.md`; exact latest-head verification remains unconfirmed. See the current status section below and re-fetch live PR metadata before acting.

## Current status — 2026-11-06

- Documentation remains the only active workstream by explicit user direction. All 12 other goal roadmaps are paused, with their plans preserved.
- The repository currently has 13 goal workspaces, 17 workflow YAMLs, 21 technical guides plus the docs index, 55 maintained implementation modules, 40 compatibility launchers and 44 test modules.
- All 12 non-documentation goal roadmaps now separate `Next action (documentation-only priority)` from `Next feature action after documentation pause`; original feature tasks are preserved but no longer appear to be immediate authorization. The documentation contract test enforces both headings and the explicit no-provider/no-data/no-playlist/no-feature instruction. A complete committed-tree inventory was subsequently verified at `7cc839f3f00eeb026cd898099654eea8f9a79497`: 28,161 file/blob entries, with every directory-scoped tree query non-truncated. See `docs/REPOSITORY_FILE_INDEX.md`.
- Draft PR [#161](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/161) contains 35 source overview rewrites, three compatibility overview corrections, 11 test overview rewrites, complete technical guide indexing, all-Markdown local-path link checks, workflow overview quality checks, and implementation/test overview boilerplate guards. It remains draft and unmerged.
- The test-overview guard initially failed because its generic-rejection fixture accidentally contained the layout test's own newly specific scope sentence. The fixture was corrected in commit `9cbf695291fa073f96669f20e83404eccba4e45e`.
- Latest available Daily curator CI [#42154433350](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42154433350) passed on commit `adce63e1f17bb2bb13a26944b7b5917c3506a714`, including compilation, generated-data audit, full read-only Library health/confidence/freshness checks, all documentation checks and full unittest discovery. The Great Migration issue/manual-dispatch/runbook allowlist test and canonical Library guide safety clarification were included. Full-history security scan [#42154433307](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42154433307) also passed on that commit.
- After `adce63e`, the metadata-enrichment budget regression test and further guide/goal/handoff updates were added. Exact-head verification is now complete: Daily curator CI [#42157311583](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42157311583) and full-history security scan [#42157311623](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42157311623) both passed on PR head `2ac590af9d8dbc85ebf5a81bc951f4190695906a`. The CI run included compile, generated-data audit, read-only Library health/confidence/freshness, documentation checks and full unittest discovery.
- PR #161 remains open and draft. The last completed code/test head `dfbefffe7fd4f5fa81d8d227a9dd1f8e71143049` passed Daily curator CI #42164423132 and full-history security scan #42164422940. CI passed compilation, generated-data audit, full read-only Library health/confidence/freshness, maintained-file documentation checks and full unittest discovery; Gitleaks passed. Subsequent branch commits changed only handoff/overview-count/action-log documentation. Latest observed PR metadata reported open/draft, `mergeable=true`, 547 commits ahead / 0 behind. Re-fetch live metadata on resume; do not merge until semantic/fresh-session gates pass.
- PR head `6261439b2f3095d8d4844c27bfbf4075c3bea5c0` passed Daily curator CI [#42159891531](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42159891531) and full-history security scan [#42159891537](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42159891537). Daily CI included the 12-roadmap next-action guard, Reference Library guide schedule check, Daily force/idempotency guard, workflow trigger-boundary test, compilation, generated-data audit, read-only Library diagnostics and full unittest discovery. On the subsequent tip `abc644dc9cac05fdd1868886823f7b54951f1a6e`, 19/19 manual assertions passed for the latest root README/guide/workflow/roadmap assertions. Later documentation-only status commits advanced the branch; re-fetch current head and require exact-head checks before merge.
- The workflow YAML comment-only push incident and its three failed publication attempts remain documented. Do not run enrichment, data publication or playlist operations during the documentation pause.

## Last completed exact-head verification — 2026-11-06

- PR #161 code/test head: `dfbefffe7fd4f5fa81d8d227a9dd1f8e71143049`.
- Daily curator CI #42164423132: success; compile, generated-data audit, full read-only Library health/confidence/freshness checks, maintained-file documentation checks and full unittest discovery all passed.
- Full-history public repository security scan #42164422940: success.
- Subsequent commits updated only handoff/status/overview-count/action-log documentation; no runtime logic, test logic, workflow logic or generated data changed after the verified code/test head. Latest observed PR metadata was open/draft, `mergeable=true`, 547 commits ahead / 0 behind. Re-fetch current metadata before any merge decision.

## Fresh-session resume simulation — initial pass completed 2026-11-06

A cold-start review was performed using only `AGENTS.md`, `project/DOCUMENTATION_RULES.md`, `NEXT_WORK.md`, `LOOSE_ENDS.md`, `PROJECT_LOG.md`, the goal index, and the relevant Maintainability and Tricky Daily roadmap/README/ACTIONS files. The first pass established that the repository entry points could resume the documentation workstream. A second cold-start pass exposed stale current-status statements (old PR head/ahead-behind counts and an inventory still marked incomplete); those contradictions were corrected in the roadmap, README, NEXT_WORK and LOOSE_ENDS. **Result: partial pass, with handoff corrections applied.** A final cold-start simulation is still required after the remaining audit; this does not satisfy the semantic-accuracy gate.

## Remaining acceptance work

1. **Inventory maintenance:** the complete committed-tree inventory is verified for audit commit `7cc839f3f00eeb026cd898099654eea8f9a79497`. Refresh it after future structural/data-family changes; use local `git ls-files` when a checkout is available. Keep generated per-record data documented by family/schema/owner rather than adding thousands of prose entries.
2. **Semantic source audit:** manually inspect every maintained implementation overview, compatibility launcher, test-module overview and workflow overview against actual inputs, outputs, state paths, network calls, permissions, side effects, retries and safety behavior. Automated anti-boilerplate tests prove specificity patterns, not factual accuracy.
3. **Technical-guide audit:** reconcile all 21 technical guides and operational runbooks against current source, tests, schemas and workflow definitions. Correct stale commands, paths, schedules, permissions, ownership boundaries, recovery procedures and evidence claims.
4. **Goal audit:** reconcile all 13 goal ROADMAP/README/ACTIONS sets against current main, the open PRs/issues and latest workflow evidence. Preserve proposals as proposals; distinguish planned, implemented, merged, deployed and verified.
5. **Cross-document consistency:** remove contradictory historical checkpoints from current handoff sections; ensure NEXT_WORK, LOOSE_ENDS, project ROADMAP, goal ROADMAP and ACTIONS logs agree on current status and next action. Historical records may remain when clearly dated and labelled.
6. **Fresh-session simulation:** initial pass completed for the current documentation workstream on 2026-11-06 using the repository entry points and relevant goal docs. Repeat after the remaining guide/inventory audit and final verification; verify that all active goals remain resumable without chat history.
7. **Final verification:** run documentation contract tests, layout tests, full unittest discovery and full-history security scan on the final PR head; inspect results and confirm the PR is mergeable before seeking merge authorization. Do not declare completion or merge based on older-head checks.

## Next action

Continue semantic review of the remaining 20 implementation modules, all 21 technical guides and workflow job-step/credential/write behavior; reconcile the current-status entries in all 13 goal ACTIONS logs. The complete committed-tree inventory is already recorded for `7cc839f`; refresh only if structure or generated family counts change. The first fresh-session simulation passed for the current documentation workstream; repeat it after the remaining audit and final exact-head verification. Keep documentation as the only active priority until every acceptance criterion above has current evidence.

## Related records
[README](README.md) · [ACTIONS](ACTIONS.md) · [Documentation rules](../../DOCUMENTATION_RULES.md) · [Documentation index](../../../docs/README.md)
