# Maintainability & Documentation
> **Roadmap:** [ROADMAP.md](ROADMAP.md) is the durable plan and next-action reference. Read it before work; update it and [ACTIONS.md](ACTIONS.md) in the same session as implementation, testing, decisions, or blockers.

## Goal

The documentation system is publicly named **SHIT Documentation & Continuity** and internally codenamed **Babel**. Its name, scope, and operating contract are defined in [docs/BABEL.md](../../../docs/BABEL.md). Use the descriptive name for first-contact clarity and the codename only after it has been introduced.

Make SHIT understandable, testable, recoverable and straightforward to continue across contributors and fresh assistant sessions.

## Scope, decisions and constraints

Scope: repository architecture/file indexes; per-file overviews; input/output and side-effect contracts; tests/audits/runbooks; goal workspaces and session handoffs.

Each maintained implementation file should explain purpose and supported goal, inputs/outputs/dependencies/data paths, network/write side effects, safety/rate/mutation boundaries, and how to run/test it. Never insert prose into machine-readable JSON; use adjacent docs or supported metadata conventions.

**Status:** the repository file index and per-file overview system exist. All 13 goal workspaces now have ROADMAP.md, README.md, and ACTIONS.md; semantic accuracy and current-state reconciliation remain under audit. The 28 known generic or underspecified module overviews have been replaced, and automated tests now reject known generic placeholders across maintained Python implementations, compatibility launchers, test modules and GitHub Actions workflow YAML files.

**Resume:** use the verified committed-tree inventory and source-specific checks to audit the remaining implementation overviews, compatibility launchers, test modules, workflow contracts, technical guides and all goal workspaces. Keep documentation as the sole active workstream until a fresh-session simulation passes.

## Documentation and resume

Read [ACTIONS.md](ACTIONS.md) for dated work and evidence. After each meaningful action, update it with files changed, execution, exact verification and outcome. Update [the central handoff](../../NEXT_WORK.md) when priority or blockers change.

## Scheduled ChatGPT Buddy — current continuation path

The current recurring documentation worker is the scheduled ChatGPT task **SHIT Buddy — daily Babel continuation**, using the connected GitHub app. It works from repository state, makes bounded documentation-only changes, and publishes to the persistent `babel/chatgpt-buddy` branch through one draft pull request. It does not require the repository-hosted Codex workflow or an OpenAI API key. See [docs/BABEL_CHATGPT_BUDDY.md](../../../docs/BABEL_CHATGPT_BUDDY.md) for its operating model, mandatory daily verification gate, scope, and review boundary.

As of 2026-11-06, the worker's proposed guide and daily-check rule are in [draft PR #163](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/163). They are not merged mainline policy until the user reviews and merges that PR. Keep it as a draft; never approve or merge it automatically.

## Separate repository-hosted Codex/API experiment

The repository-hosted OpenAI Codex worker remains documented in [docs/BABEL_AGENT.md](../../../docs/BABEL_AGENT.md) and tracked by [project/BABEL_AGENT_STATE.md](../../BABEL_AGENT_STATE.md). Its runner compatibility workaround is verified, but the latest Codex attempt was blocked by API quota before validation or publication. It is not the current ChatGPT Buddy execution path. Do not trigger it or ask the user to fund API usage unless the user explicitly reauthorizes that separate experiment.
