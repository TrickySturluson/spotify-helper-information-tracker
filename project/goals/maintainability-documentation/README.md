# Maintainability & Documentation
> **Roadmap:** [ROADMAP.md](ROADMAP.md) is the durable plan and next-action reference. Read it before work; update it and [ACTIONS.md](ACTIONS.md) in the same session as implementation, testing, decisions, or blockers.

## Goal

Make SHIT understandable, testable, recoverable and straightforward to continue across contributors and fresh assistant sessions.

## Scope, decisions and constraints

Scope: repository architecture/file indexes; per-file overviews; input/output and side-effect contracts; tests/audits/runbooks; goal workspaces and session handoffs.

Each maintained implementation file should explain purpose and supported goal, inputs/outputs/dependencies/data paths, network/write side effects, safety/rate/mutation boundaries, and how to run/test it. Never insert prose into machine-readable JSON; use adjacent docs or supported metadata conventions.

**Status: active repository-wide documentation-only workstream.** All 13 goal workspaces exist with ROADMAP.md, README.md and ACTIONS.md. The repository currently has 21 technical guides, 17 workflows, 55 maintained implementation modules, 40 compatibility launchers and 44 test modules. Thirty-two implementation overviews and 11 previously generic test-module overviews have been rewritten. The active delivery is draft PR [#161](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/161), branch `docs/semantic-documentation-audit`. Latest inspected PR head `32751b5ae645c3d4eb18f15cad983b7b42794fcc` has both exact-commit checks passing: Daily curator CI [#42160249966](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42160249966) passed compilation, generated-data audit, read-only full Library health/confidence/freshness, maintained-file documentation checks and full unittest discovery; full-history security scan [#42160248763](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42160248763) passed all Gitleaks steps. This supersedes the older `6261439`/`abc644` checkpoints for the current PR tip. A first fresh-session simulation passed for resuming the documentation workstream, but it must be repeated after the remaining audit. The complete tracked-file inventory, full semantic source/guide review, and cross-goal README/ACTIONS reconciliation remain incomplete. Do not declare completion or merge yet.

**Resume:** continue from [project/NEXT_WORK.md](../../NEXT_WORK.md) and [ROADMAP.md](ROADMAP.md); complete the remaining inventory/semantic audit; keep this as the only active workstream until all acceptance criteria pass.

## Documentation and resume

Read [ACTIONS.md](ACTIONS.md) for dated work and evidence. After each meaningful action, update it with files changed, execution, exact verification and outcome. Update [the central handoff](../../NEXT_WORK.md) when priority or blockers change.
