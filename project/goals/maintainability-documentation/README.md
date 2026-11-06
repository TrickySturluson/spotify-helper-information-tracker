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

## AI continuation worker

Babel includes a repository-hosted OpenAI Codex worker to continue documentation work from durable GitHub state. It is scheduled every six hours and can also be started manually. It resumes from the dedicated babel/agent-progress branch, makes documentation-only changes, and publishes through a review PR after path validation and full unittest discovery. It cannot perform Spotify/provider operations or change runtime implementation. Setup, permissions, recovery and limitations are in [docs/BABEL_AGENT.md](../../../docs/BABEL_AGENT.md).

**Activation is pending:** the repository owner must add the OPENAI_API_KEY Actions secret and verify the first run. The ChatGPT subscription does not itself provide API credentials; API usage is billed separately.
