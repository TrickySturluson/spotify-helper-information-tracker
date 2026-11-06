# Maintainability & Documentation
> **Roadmap:** [ROADMAP.md](ROADMAP.md) is the durable plan and next-action reference. Read it before work; update it and [ACTIONS.md](ACTIONS.md) in the same session as implementation, testing, decisions, or blockers.

## Goal

Make SHIT understandable, testable, recoverable and straightforward to continue across contributors and fresh assistant sessions.

## Scope, decisions and constraints

Scope: repository architecture/file indexes; per-file overviews; input/output and side-effect contracts; tests/audits/runbooks; goal workspaces and session handoffs.

Each maintained implementation file should explain purpose and supported goal, inputs/outputs/dependencies/data paths, network/write side effects, safety/rate/mutation boundaries, and how to run/test it. Never insert prose into machine-readable JSON; use adjacent docs or supported metadata conventions.

**Status: active repository-wide documentation-only workstream.** All 13 goal workspaces exist with ROADMAP.md, README.md and ACTIONS.md. The repository currently has 21 technical guides, 17 workflows, 55 maintained implementation modules, 40 compatibility launchers and 44 test modules. Thirty-two implementation overviews and 11 previously generic test-module overviews have been rewritten. Daily curator CI [#42159891531](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42159891531) and full-history security scan [#42159891537](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42159891537) both passed on PR head `6261439b2f3095d8d4844c27bfbf4075c3bea5c0`. Daily CI included compilation, generated-data audit, read-only Library health/confidence/freshness, documentation checks and full unittest discovery, including the 12-roadmap next-action guard. A subsequent 19/19 manual assertion pass on `abc644dc9cac05fdd1868886823f7b54951f1a6e` verified the root README/Reference Library schedule, Daily force semantics and all 12 paused-roadmap next-action sections. Later documentation-only status commits advanced the branch; re-fetch current head and require exact-head CI/security before merge. The full tracked-file inventory, semantic source/guide review, all goal README/ACTIONS reconciliation and fresh-session simulation remain incomplete. Do not declare completion yet.

**Resume:** continue from [project/NEXT_WORK.md](../../NEXT_WORK.md) and [ROADMAP.md](ROADMAP.md); complete the remaining inventory/semantic audit; keep this as the only active workstream until all acceptance criteria pass.

## Documentation and resume

Read [ACTIONS.md](ACTIONS.md) for dated work and evidence. After each meaningful action, update it with files changed, execution, exact verification and outcome. Update [the central handoff](../../NEXT_WORK.md) when priority or blockers change.
