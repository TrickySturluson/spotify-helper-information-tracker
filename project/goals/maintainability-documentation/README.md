# Maintainability & Documentation
> **Roadmap:** [ROADMAP.md](ROADMAP.md) is the durable plan and next-action reference. Read it before work; update it and [ACTIONS.md](ACTIONS.md) in the same session as implementation, testing, decisions, or blockers.

## Goal

Make SHIT understandable, testable, recoverable and straightforward to continue across contributors and fresh assistant sessions.

## Scope, decisions and constraints

Scope: repository architecture/file indexes; per-file overviews; input/output and side-effect contracts; tests/audits/runbooks; goal workspaces and session handoffs.

Each maintained implementation file should explain purpose and supported goal, inputs/outputs/dependencies/data paths, network/write side effects, safety/rate/mutation boundaries, and how to run/test it. Never insert prose into machine-readable JSON; use adjacent docs or supported metadata conventions.

**Status: active repository-wide documentation-only workstream.** All 13 goal workspaces exist with ROADMAP.md, README.md and ACTIONS.md. The repository currently has 21 technical guides, 17 workflows, 55 maintained implementation modules, 40 compatibility launchers and 44 test modules. Thirty-two implementation overviews and 11 previously generic test-module overviews have been rewritten. Daily curator CI [#42158995339](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42158995339) passed on PR head `7cc3497075d47bfb3ef2f35dcf7d89a04e33ecab`, including compilation, generated-data audit, read-only Library health/confidence/freshness, documentation checks and full unittest discovery. This run includes the Reference Library schedule test, Daily force/idempotency discrepancy test and sensitive workflow trigger-boundary test. Full-history security scan [#42158995392](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42158995392) is still in progress. This status update moves the branch head, so recheck exact-head CI/security after commit. The full tracked-file inventory, semantic source/guide review, all goal README/ACTIONS reconciliation and fresh-session simulation remain incomplete. Do not declare completion yet.

**Resume:** continue from [project/NEXT_WORK.md](../../NEXT_WORK.md) and [ROADMAP.md](ROADMAP.md); complete the remaining inventory/semantic audit; keep this as the only active workstream until all acceptance criteria pass.

## Documentation and resume

Read [ACTIONS.md](ACTIONS.md) for dated work and evidence. After each meaningful action, update it with files changed, execution, exact verification and outcome. Update [the central handoff](../../NEXT_WORK.md) when priority or blockers change.
