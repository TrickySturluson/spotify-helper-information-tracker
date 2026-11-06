# Maintainability & Documentation
> **Roadmap:** [ROADMAP.md](ROADMAP.md) is the durable plan and next-action reference. Read it before work; update it and [ACTIONS.md](ACTIONS.md) in the same session as implementation, testing, decisions, or blockers.

## Goal

Make SHIT understandable, testable, recoverable and straightforward to continue across contributors and fresh assistant sessions.

## Scope, decisions and constraints

Scope: repository architecture/file indexes; per-file overviews; input/output and side-effect contracts; tests/audits/runbooks; goal workspaces and session handoffs.

Each maintained implementation file should explain purpose and supported goal, inputs/outputs/dependencies/data paths, network/write side effects, safety/rate/mutation boundaries, and how to run/test it. Never insert prose into machine-readable JSON; use adjacent docs or supported metadata conventions.

**Status: active repository-wide documentation-only workstream.** All 13 goal workspaces exist with ROADMAP.md, README.md and ACTIONS.md. The repository currently has 21 technical guides, 17 workflows, 55 maintained implementation modules, 40 compatibility launchers and 44 test modules. Thirty-two implementation overviews and 11 previously generic test-module overviews have been rewritten. Daily curator CI [#42158020546](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42158020546) and full-history security scan [#42158020518](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42158020518) passed on intermediate PR head `041bf54da9b25d8269fd193c8f8e1bd1c497d33a`, including compilation, generated-data audit, read-only Library health/confidence/freshness, documentation checks and full unittest discovery. Later documentation-only changes added a Reference Library schedule-alignment test, corrected workflow trigger boundaries, documented the Daily force/idempotency discrepancy, recorded the latest 58-item Daily snapshot and SHITting Grounds role-registry drift, and reconciled stale open-PR bases. The current PR head is `6202fc3fd574a70123d1c73577497b8363c5f2b7`; no workflow run or commit status was returned for that exact head. Exact-head CI/security remains outstanding. The full tracked-file inventory, semantic source/guide review, all goal README/ACTIONS reconciliation and fresh-session simulation remain incomplete. Do not declare completion yet.

**Resume:** continue from [project/NEXT_WORK.md](../../NEXT_WORK.md) and [ROADMAP.md](ROADMAP.md); complete the remaining inventory/semantic audit; keep this as the only active workstream until all acceptance criteria pass.

## Documentation and resume

Read [ACTIONS.md](ACTIONS.md) for dated work and evidence. After each meaningful action, update it with files changed, execution, exact verification and outcome. Update [the central handoff](../../NEXT_WORK.md) when priority or blockers change.
