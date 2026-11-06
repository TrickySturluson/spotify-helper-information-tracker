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

## Workflow catalogue and documentation guardrails

- `docs/WORKFLOWS.md` summarizes all 17 workflow files, triggers, permissions, credential names, major steps and side effects. The documentation contract fails if a workflow filename is missing from the catalogue.
- Nine workflow YAML bottom overviews were rewritten with their actual triggers, credentials, repository writes, playlist-write boundaries and related implementation.
- Workflow YAML comment-only changes can trigger push-path workflows. This operational hazard is now documented; see the incident entry in ACTIONS.md and docs/WORKFLOWS.md.
- Draft PR #161 adds complete technical-guide indexing, repository-wide Markdown local-path checks, specific workflow overview checks, implementation/test overview anti-boilerplate checks and compatibility-to-source references. The corrected test-overview guard and full unittest discovery passed on commit `9cbf695291fa073f96669f20e83404eccba4e45e` in run #42152796114; full-history security scan #42152796120 also passed on that commit. Later commits changed only documentation/handoff files and `tests/README.md`; exact latest-head verification remains unconfirmed. See the current status section below and re-fetch live PR metadata before acting.

## Current status — 2026-11-06

- Documentation remains the only active workstream by explicit user direction. All 12 other goal roadmaps are paused, with their plans preserved.
- The repository currently has 13 goal workspaces, 17 workflow YAMLs, 21 technical guides plus the docs index, 55 maintained implementation modules, 40 compatibility launchers and 44 test modules. The directory-scoped counts are documented in `docs/REPOSITORY_FILE_INDEX.md`; they are not a complete `git ls-files` inventory because the recursive Git tree response was truncated by generated Library records.
- Draft PR [#161](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/161) contains 32 source overview rewrites, three compatibility overview corrections, 11 test overview rewrites, complete technical guide indexing, all-Markdown local-path link checks, workflow overview quality checks, and implementation/test overview boilerplate guards. It remains draft and unmerged.
- The test-overview guard initially failed because its generic-rejection fixture accidentally contained the layout test's own newly specific scope sentence. The fixture was corrected in commit `9cbf695291fa073f96669f20e83404eccba4e45e`.
- Latest available Daily curator CI [#42154433350](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42154433350) passed on commit `adce63e1f17bb2bb13a26944b7b5917c3506a714`, including compilation, generated-data audit, full read-only Library health/confidence/freshness checks, all documentation checks and full unittest discovery. The Great Migration issue/manual-dispatch/runbook allowlist test and canonical Library guide safety clarification were included. Full-history security scan [#42154433307](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42154433307) also passed on that commit.
- After `adce63e`, only documentation files changed: lyrics-provider setup, goal roadmap status/date reconciliation, action-log chronology, and current Library health/confidence/freshness baselines. No implementation source, test logic or workflow YAML changed. Exact latest-head CI/security remains outstanding.
- Latest live PR inspection reported mergeable true, draft/unmerged; branch comparison showed 0 commits behind main. Re-fetch PR metadata and compare status before any merge decision.
- The workflow YAML comment-only push incident and its three failed publication attempts remain documented. Do not run enrichment, data publication or playlist operations during the documentation pause.

## Remaining acceptance work

1. **Tracked-file inventory:** obtain a complete checkout and reconcile `git ls-files` against the maintained-file index and documentation contract. Keep generated per-record data documented by family/schema/owner rather than adding thousands of prose entries. The recursive Git tree API response was truncated and cannot be treated as complete.
2. **Semantic source audit:** manually inspect every maintained implementation overview, compatibility launcher, test-module overview and workflow overview against actual inputs, outputs, state paths, network calls, permissions, side effects, retries and safety behavior. Automated anti-boilerplate tests prove specificity patterns, not factual accuracy.
3. **Technical-guide audit:** reconcile all 21 technical guides and operational runbooks against current source, tests, schemas and workflow definitions. Correct stale commands, paths, schedules, permissions, ownership boundaries, recovery procedures and evidence claims.
4. **Goal audit:** reconcile all 13 goal ROADMAP/README/ACTIONS sets against current main, the open PRs/issues and latest workflow evidence. Preserve proposals as proposals; distinguish planned, implemented, merged, deployed and verified.
5. **Cross-document consistency:** remove contradictory historical checkpoints from current handoff sections; ensure NEXT_WORK, LOOSE_ENDS, project ROADMAP, goal ROADMAP and ACTIONS logs agree on current status and next action. Historical records may remain when clearly dated and labelled.
6. **Fresh-session simulation:** start only from `AGENTS.md`, `project/DOCUMENTATION_RULES.md`, `project/NEXT_WORK.md`, `project/LOOSE_ENDS.md` and the goal index. Verify that a new session can identify the active task, constraints, evidence, blockers and next executable step without chat history.
7. **Final verification:** run documentation contract tests, layout tests, full unittest discovery and full-history security scan on the final PR head; inspect results and confirm the PR is mergeable before seeking merge authorization. Do not declare completion or merge based on older-head checks.

## Next action

Continue the cross-document consistency audit. The project handoff had accumulated stale PR checkpoints; the top-level NEXT_WORK section has now been consolidated. Inspect and reconcile remaining duplicated/stale checkpoint sections in this roadmap, LOOSE_ENDS and PROJECT_LOG, then perform the fresh-session simulation. Keep documentation as the only active priority until every acceptance criterion above has current evidence.

## Related records
[README](README.md) · [ACTIONS](ACTIONS.md) · [Documentation rules](../../DOCUMENTATION_RULES.md) · [Documentation index](../../../docs/README.md)
