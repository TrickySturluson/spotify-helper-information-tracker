# Maintainability & Documentation — Roadmap

**Last reviewed:** 2026-11-05  
**Status:** Ongoing; repository indexes and goal workspaces exist, but documentation coverage and freshness must be continuously verified.

## Purpose
Make the repository understandable and maintainable by a contributor or assistant with no access to prior chat history.

## Required per-file documentation
Every maintained script/module/workflow should state its purpose, supported goal, inputs/outputs, dependencies/data paths, network and write side effects, safety/rate/mutation boundaries, and how to run/test it. Do not put prose into machine-readable JSON; use adjacent documentation or supported metadata.

## Roadmap
1. **Adopt mandatory documentation standard — next.** Add [project documentation rules](../../DOCUMENTATION_RULES.md) and require every workstream to maintain ROADMAP, README and ACTIONS.
2. **Audit documentation coverage.** Compare scripts, modules, workflows, schemas and tests with the repository file index and per-file overview requirements.
3. **Repair gaps and stale docs.** Prioritize operational entry points, write-capable tools, scheduled workflows, and shared data contracts.
4. **Automate checks where practical.** Add link/path checks and documentation coverage checks without making brittle requirements that encourage meaningless boilerplate.
5. **Maintain continuity.** Keep NEXT_WORK, LOOSE_ENDS, PROJECT_LOG and all goal roadmaps synchronized as work changes.
6. **Fresh-session test.** Periodically verify a new assistant can identify the active task, safety boundaries, exact next action and verification commands using repository docs alone.

## Acceptance criteria
A fresh session can resume each goal without chat history; file indexes/overviews accurately reflect code; status labels distinguish implemented/merged/verified; docs are updated in the same session as code changes.

## Next action
Audit all goal folders for ROADMAP/README/ACTIONS, then compare per-file docs against current scripts and workflows; record gaps and fix high-risk omissions first.

## Related records
[README](README.md) · [ACTIONS](ACTIONS.md) · [Documentation rules](../../DOCUMENTATION_RULES.md)
