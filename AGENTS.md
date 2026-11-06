# SHIT repository instructions

**Documentation system naming:** use **SHIT Documentation & Continuity** as the clear public-facing name. Its internal codename is **Babel**; define it through [docs/BABEL.md](docs/BABEL.md) before using the short name in a fresh session.

This file applies to every assistant, contributor, and automation agent working in this repository.

## Before changing anything
1. Read [project/DOCUMENTATION_RULES.md](project/DOCUMENTATION_RULES.md). It is mandatory.
2. Read [the documentation-system identity and operating guide](docs/BABEL.md) so “Babel” is unambiguous.
2. Read [project/NEXT_WORK.md](project/NEXT_WORK.md), [project/LOOSE_ENDS.md](project/LOOSE_ENDS.md), and [project/PROJECT_LOG.md](project/PROJECT_LOG.md).
3. Find the relevant workstream in [project/goals/README.md](project/goals/README.md). Read its `ROADMAP.md`, `README.md`, and `ACTIONS.md`.
4. Read the relevant source, tests, data contracts, runbooks, workflow definitions, and current GitHub status. Documentation is not a substitute for checking the live implementation.
5. Confirm the current branch and working tree before editing. Do not overwrite unrelated work.

## Non-negotiable continuity rule
The repository is the durable source of truth; chat history is not. Every meaningful requirement, decision, implementation, test, failure, blocker, provider limitation, and next action must be recorded in the appropriate documentation during the same session. Never leave important knowledge only in a conversation.

Every major workstream must maintain:
- `ROADMAP.md`: purpose, requirements, constraints, verified status, milestones, open tasks, acceptance criteria, blockers, next action.
- `README.md`: scope, architecture, invariants, dependencies, links, resume instructions.
- `ACTIONS.md`: dated chronological record of changes, commands, tests, outcomes, failures, decisions, and evidence.

Update the relevant roadmap and action log whenever status changes. Update the workstream README when design or operating instructions change. Update `project/NEXT_WORK.md` and `project/LOOSE_ENDS.md` when cross-project priorities or blockers change; add major milestones to `project/PROJECT_LOG.md`.

## Evidence and safety
- Distinguish planned, implemented, merged, deployed, and verified. Never claim verification without exact evidence.
- Record failed attempts and why they failed; do not silently erase useful history.
- Do not mark tasks complete based on a preview, stale snapshot, unverified artifact, or code inspection alone when live verification is required.
- Preserve existing authorization, read-only defaults, playlist locks, blacklists, deduplication, backups, atomic writes, rollback, rate limits, and audit requirements.
- Never expose credentials, tokens, private keys, or secret values in code, docs, logs, issues, or commits.
- Do not manually edit generated data or canonical records outside their documented writers.
- Keep documentation plain and explicit enough for a fresh session with no prior chat context.

## Before ending a work session
Update all affected documentation in the same session. Verify changed links and file paths where practical. Record exact tests and failures, the commit/PR/workflow evidence, whether changes are published, remaining uncertainty, and the next executable action. A task is not complete until its documentation and handoff are current.

See [the documentation index](docs/README.md) for navigation and [the project-wide roadmap](project/ROADMAP.md) for cross-workstream priorities.
