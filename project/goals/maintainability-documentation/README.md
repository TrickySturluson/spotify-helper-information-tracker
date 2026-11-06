# Maintainability & Documentation
> **Roadmap:** [ROADMAP.md](ROADMAP.md) is the durable plan and next-action reference. Read it before work; update it and [ACTIONS.md](ACTIONS.md) in the same session as implementation, testing, decisions, or blockers.

## Goal

Make SHIT understandable, testable, recoverable and straightforward to continue across contributors and fresh assistant sessions.

## Scope, decisions and constraints

Scope: repository architecture/file indexes; per-file overviews; input/output and side-effect contracts; tests/audits/runbooks; goal workspaces and session handoffs.

Each maintained implementation file should explain purpose and supported goal, inputs/outputs/dependencies/data paths, network/write side effects, safety/rate/mutation boundaries, and how to run/test it. Never insert prose into machine-readable JSON; use adjacent docs or supported metadata conventions.

**Status: active repository-wide documentation-only workstream.** All 13 goal workspaces have ROADMAP.md, README.md and ACTIONS.md. The repository has 21 technical guides, 17 workflows, 55 maintained implementation modules, 40 compatibility launchers and 44 test modules. **35 of 55 implementation-module overviews**, three compatibility-launcher overviews and 11 test-module overviews have been rewritten with source-specific contracts; 11 workflow YAML overviews are now specific. All 17 workflow trigger/schedule and permission blocks have been cross-checked against source. The complete committed-tree inventory is verified at audit commit `7cc839f3f00eeb026cd898099654eea8f9a79497`: 28,161 file/blob entries, including 27,902 under `assistant_data/`; every directory-scoped tree query returned `truncated=false`. See `docs/REPOSITORY_FILE_INDEX.md`.

The last completed code/test head is `dfbefffe7fd4f5fa81d8d227a9dd1f8e71143049`. Daily curator CI [#42164423132](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42164423132) passed compilation, generated-data audit, full read-only Library health/confidence/freshness, maintained-file documentation checks and full unittest discovery. Full-history Gitleaks [#42164422940](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42164422940) passed. Later commits updated only documentation/handoff counts and the action log; no runtime logic, tests, workflow logic or generated data changed after that verified code/test head.

The active delivery is draft PR [#161](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/161), branch `docs/semantic-documentation-audit`. Latest observed metadata: open/draft and mergeable=true; re-fetch live comparison before any merge decision. The first fresh-session simulation passed; a second exposed stale handoff-status statements, which have been corrected. The final cold-start simulation remains required.

**Remaining work:** finish semantic review of the remaining 20 implementation modules and all technical guides; audit workflow job steps, credentials, writes and recovery paths beyond the completed trigger/schedule pass; reconcile current-status claims in all 13 goal ACTIONS logs; repeat the cold-start simulation. Keep documentation as the only active workstream until every acceptance gate passes. Do not declare completion or merge yet.

**Resume:** continue from [project/NEXT_WORK.md](../../NEXT_WORK.md) and [ROADMAP.md](ROADMAP.md); complete the remaining inventory/semantic audit; keep this as the only active workstream until all acceptance criteria pass.

## Documentation and resume

Read [ACTIONS.md](ACTIONS.md) for dated work and evidence. After each meaningful action, update it with files changed, execution, exact verification and outcome. Update [the central handoff](../../NEXT_WORK.md) when priority or blockers change.
