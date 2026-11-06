# Maintainability & Documentation
> **Roadmap:** [ROADMAP.md](ROADMAP.md) is the durable plan and next-action reference. Read it before work; update it and [ACTIONS.md](ACTIONS.md) in the same session as implementation, testing, decisions, or blockers.

## Goal

The documentation system is publicly named **SHIT Documentation & Continuity** and internally codenamed **Babel**. Its name, scope, and operating contract are defined in [docs/BABEL.md](../../../docs/BABEL.md). Use the descriptive name for first-contact clarity and the codename only after it has been introduced.

Make SHIT understandable, testable, recoverable and straightforward to continue across contributors and fresh assistant sessions.

## Scope, decisions and constraints

Scope: repository architecture/file indexes; per-file overviews; input/output and side-effect contracts; tests/audits/runbooks; goal workspaces and session handoffs.

Each maintained implementation file should explain purpose and supported goal, inputs/outputs/dependencies/data paths, network/write side effects, safety/rate/mutation boundaries, and how to run/test it. Never insert prose into machine-readable JSON; use adjacent docs or supported metadata conventions.

**Status: repository file index and file-overview work already exist; coverage must be verified rather than assumed. Goal workspaces are being introduced.**

**Resume:** review README/index; identify undocumented or stale modules/workflows; add concise overviews without runtime changes; run relevant tests/index checks; update this workspace and central handoff.

## Documentation and resume

Read [ACTIONS.md](ACTIONS.md) for dated work and evidence. After each meaningful action, update it with files changed, execution, exact verification and outcome. Update [the central handoff](../../NEXT_WORK.md) when priority or blockers change.
