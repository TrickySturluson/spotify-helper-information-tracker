# Maintainability & Documentation
> **Roadmap:** [ROADMAP.md](ROADMAP.md) is the durable plan and next-action reference. Read it before work; update it and [ACTIONS.md](ACTIONS.md) in the same session as implementation, testing, decisions, or blockers.

## Goal

The documentation system is publicly named **SHIT Documentation & Continuity** and internally codenamed **Babel**. Its name, scope, and operating contract are defined in [docs/BABEL.md](../../../docs/BABEL.md). Use the descriptive name for first-contact clarity and the codename only after it has been introduced.

Make SHIT understandable, testable, recoverable and straightforward to continue across contributors and fresh assistant sessions.

## Scope, decisions and constraints

Scope: repository architecture/file indexes; per-file overviews; input/output and side-effect contracts; tests/audits/runbooks; goal workspaces and session handoffs.

Each maintained implementation file should explain purpose and supported goal, inputs/outputs/dependencies/data paths, network/write side effects, safety/rate/mutation boundaries, and how to run/test it. Never insert prose into machine-readable JSON; use adjacent docs or supported metadata conventions.

**Status:** the repository file index and per-file overview system exist. All 14 goal workspaces now have ROADMAP.md, README.md, and ACTIONS.md; semantic accuracy and current-state reconciliation remain under audit. The 28 known generic or underspecified module overviews have been replaced, and automated tests now reject known generic placeholders across maintained Python implementations, compatibility launchers, test modules and GitHub Actions workflow YAML files.

**Resume:** use the verified committed-tree inventory and source-specific checks to audit the remaining implementation overviews, compatibility launchers, test modules, workflow contracts, technical guides and all goal workspaces. Babel continues alongside other explicitly authorized SHIT workstreams; keep this roadmap and ACTIONS current, and complete the fresh-session simulation before declaring Babel complete.

## Documentation and resume

Read [ACTIONS.md](ACTIONS.md) for dated work and evidence. After each meaningful action, update it with files changed, execution, exact verification and outcome. Update [the central handoff](../../NEXT_WORK.md) when priority or blockers change.

## Scheduled ChatGPT Buddy — current continuation worker

Babel's active recurring documentation worker is the scheduled ChatGPT task using the connected GitHub app. It works from repository state, makes bounded documentation-only changes, and publishes through a single draft PR. It does not require a local PC, repository-hosted Codex execution, or an OpenAI API key. Its operating rules and current branch/PR status are documented in [docs/BABEL_CHATGPT_BUDDY.md](../../../docs/BABEL_CHATGPT_BUDDY.md).

## Separate Codex/API experiment — quota-blocked; workflow enablement unverified

The repository-hosted Codex workflow is separate from the current ChatGPT Buddy. Its last verified attempt was blocked by API quota before validation or publication. The workflow YAML still declares a six-hour schedule, manual dispatch, and a push trigger; the repository-level enabled/disabled state was not confirmed in this audit. Do not manually dispatch, retry, or assume it is disabled without explicit user reauthorization. If no scheduled Codex execution is wanted, the repository owner must disable the workflow in GitHub Actions or separately authorize a workflow change. Buddy must not change workflow logic/settings; see [docs/BABEL_AGENT.md](../../../docs/BABEL_AGENT.md).
