# Maintainability & Documentation — Actions & Evidence

Newest entries first. Record verified outcomes separately from plans, assumptions and unverified artifacts.

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
