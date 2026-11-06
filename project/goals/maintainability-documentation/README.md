# Maintainability & Documentation
> **Roadmap:** [ROADMAP.md](ROADMAP.md) is the durable plan and next-action reference. Read it before work; update it and [ACTIONS.md](ACTIONS.md) in the same session as implementation, testing, decisions, or blockers.

## Goal

Make SHIT understandable, testable, recoverable and straightforward to continue across contributors and fresh assistant sessions.

## Scope, decisions and constraints

Scope: repository architecture/file indexes; per-file overviews; input/output and side-effect contracts; tests/audits/runbooks; goal workspaces and session handoffs.

Each maintained implementation file should explain purpose and supported goal, inputs/outputs/dependencies/data paths, network/write side effects, safety/rate/mutation boundaries, and how to run/test it. Never insert prose into machine-readable JSON; use adjacent docs or supported metadata conventions.

**Status: active repository-wide documentation-only workstream.** All 13 goal workspaces exist with ROADMAP.md, README.md and ACTIONS.md. The repository currently has 21 technical guides, 17 workflows, 55 maintained implementation modules, 40 compatibility launchers and 44 test modules. Thirty-two implementation overviews and 11 previously generic test-module overviews have been rewritten. The active delivery is draft PR [#161](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/161), branch `docs/semantic-documentation-audit`. The last completed exact-head pair is PR commit `7cc839f3f00eeb026cd898099654eea8f9a79497`: Daily curator CI [#42160249966](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42160249966) passed compilation, generated-data audit, read-only full Library health/confidence/freshness, maintained-file documentation checks and full unittest discovery; full-history security scan [#42160248763](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42160248763) passed all Gitleaks steps. Current PR head `54c318789a29817453366953f891a3431ea79fa8` has exact-head Daily curator CI [#42162264872](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42162264872) and security scan [#42162264795](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42162264795) in progress at latest inspection; recheck terminal results before relying on them. A first fresh-session simulation passed for resuming the documentation workstream, but it must be repeated after the remaining audit. The complete committed-tree inventory is now verified for audit commit `7cc839f3f00eeb026cd898099654eea8f9a79497`: 28,161 file/blob entries, with every directory-scoped tree query non-truncated; see `docs/REPOSITORY_FILE_INDEX.md`. All 13 goal READMEs have had their pause/resume instructions checked for conflicting immediate feature actions. The full semantic source/guide review, goal ACTIONS freshness reconciliation, cross-document status consistency and final repeat cold-start simulation remain incomplete. The complete committed-tree inventory is verified at `7cc839f3f00eeb026cd898099654eea8f9a79497` (28,161 file/blob entries; see `docs/REPOSITORY_FILE_INDEX.md`). The current exact-head CI/security runs are newer than that inventory snapshot and remain in progress. Do not declare completion or merge yet.

**Resume:** continue from [project/NEXT_WORK.md](../../NEXT_WORK.md) and [ROADMAP.md](ROADMAP.md); complete the remaining inventory/semantic audit; keep this as the only active workstream until all acceptance criteria pass.

## Documentation and resume

Read [ACTIONS.md](ACTIONS.md) for dated work and evidence. After each meaningful action, update it with files changed, execution, exact verification and outcome. Update [the central handoff](../../NEXT_WORK.md) when priority or blockers change.
