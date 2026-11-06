# SHIT Project Documentation Rules

**This file is mandatory operating guidance for every future assistant, contributor, and automation session working in this repository.** It exists so work can be resumed accurately without access to previous chat history. The repository documentation—not chat memory—is the durable source of truth.

## Documentation system identity

The documentation system's public-facing name is **SHIT Documentation & Continuity**. Its internal codename is **Babel**. Use the descriptive name in first-contact navigation, headings, and explanations; after defining the relationship, “Babel” is an acceptable concise reference. Never assume a fresh contributor or assistant knows what Babel means. The canonical explanation and scope live in [docs/BABEL.md](../docs/BABEL.md).

## Non-negotiable rule

Every substantial project/workstream must have a maintained roadmap. Every meaningful implementation, test, failure, decision, blocker, or change of direction must be reflected in the documentation during the same work session. Do not leave important project knowledge only in chat.

## Required reading before work

At the start of a new task or resumed session:

1. Read [project/NEXT_WORK.md](NEXT_WORK.md).
2. Read [project/LOOSE_ENDS.md](LOOSE_ENDS.md) for cross-workstream blockers and unresolved verification.
3. Identify the relevant goal folder in [project/goals/](goals/README.md).
4. Read that goal's `ROADMAP.md`, `README.md`, and `ACTIONS.md`.
5. Read any linked technical contracts, runbooks, workflow documentation, and the relevant source/tests.
6. Inspect the current branch, open PRs/issues, and latest relevant workflow runs before assuming a documented status is still current.

For a focused component with its own dedicated roadmap (for example Tricky Daily), read that roadmap too. Do not assume a prior assistant's summary is more current than the repository.

## Required documentation structure

Each major goal/workstream must have:

- `ROADMAP.md` — durable plan: purpose, user requirements, non-negotiable constraints, current verified state, milestones, outstanding tasks, acceptance criteria, blockers, and next concrete action.
- `README.md` — scope, architecture, design decisions, invariants, component links, and how to resume.
- `ACTIONS.md` — dated chronological record of meaningful work, implementation changes, tests, failures, decisions, and evidence.

The repository-level control centre must retain:

- `NEXT_WORK.md` — authoritative current handoff and next action across the whole repository.
- `LOOSE_ENDS.md` — cross-workstream unresolved items, dependencies, and verification blockers.
- `PROJECT_LOG.md` — chronological record of major project milestones and cross-cutting decisions.
- This file — the mandatory documentation process.

A small task may use an existing workstream roadmap rather than creating a new folder. A genuinely independent new project must get its own goal folder and the three required files before or as implementation begins.

## Update requirements — do this as part of the work

Update documentation whenever any of these happens:

- A task starts and changes the active priority or next action.
- Code, tests, workflows, schemas, configuration, or data contracts change.
- A test, audit, workflow, preview, live operation, or deployment is run.
- A test fails, a provider/API blocks work, a workflow is cancelled, or an assumption is disproved.
- A feature becomes implemented, partially implemented, merged, deployed, verified, deferred, or abandoned.
- A user states a new requirement, preference, constraint, or authorization boundary.
- A dependency, risk, blocker, or next step changes.

At minimum, update the relevant `ROADMAP.md` and `ACTIONS.md`. Also update `README.md` if scope, architecture, decisions, commands, or resume instructions changed. Update `NEXT_WORK.md` and `LOOSE_ENDS.md` when cross-project priority, blockers, dependencies, or status change. Add a `PROJECT_LOG.md` entry for significant milestones or cross-cutting decisions.

Do not defer these updates to a later chat. Documentation is part of completing the task, not optional cleanup.

## How to write it so a fresh assistant can continue

Use plain, explicit language. Spell out project-specific names and paths. Record:

- What the user is trying to achieve and what success looks like.
- Exact user requirements and hard constraints; distinguish preferences from invariants.
- What is implemented, where it lives, and how it is invoked.
- What is only proposed, prototyped, in a branch, in a PR, in an artifact, merged, deployed, or independently verified.
- Exact tests/audits/workflow runs and their results, including failures.
- Known gaps, risks, provider limits, credentials/configuration dependencies (never credential values), and data coverage limitations.
- The next action in executable terms, including prerequisites and what result to inspect.
- Links to source files, tests, PRs, commits, issues, and workflow runs.

Never describe a plan as implemented. Never describe a branch or artifact as published. Never call something verified without naming the evidence. Put dates and timestamps on changing measurements. Label stale measurements as historical. Record failed attempts because they prevent repeated wasted work.

## Roadmap status vocabulary

Use explicit states such as: `not started`, `planned`, `in progress`, `implemented`, `merged`, `deployed`, `verified`, `blocked`, `deferred`, and `retired`. These are not interchangeable. A merged change is not necessarily operationally verified. A successful preview is not a live write.

Use checkboxes for actionable tasks. Mark an item complete only after its acceptance criteria are met and evidence is recorded. If the implementation already exists, verify it before checking the item off.

## Completion / handoff checklist

Before ending a meaningful work session:

- [ ] Relevant roadmap reflects the current state and next action.
- [ ] Relevant action log records files, decisions, tests, exact results, failures, and links.
- [ ] README/design docs updated if the architecture or operating instructions changed.
- [ ] Cross-project handoff and loose-ends register updated if priorities/blockers changed.
- [ ] No plan is presented as completed without evidence.
- [ ] A fresh assistant can resume by reading the documented next action without asking the user to reconstruct the conversation.

## Rule for future assistants

If documentation is missing, incomplete, contradictory, or stale, repair it before or while proceeding. Do not silently ignore this standard. When the user gives a new requirement, preserve it in the appropriate roadmap and related contract. The user's explicit direction overrides an older plan; record the change and its implications.

**This standard applies to every current and future workstream in SHIT, including Tricky Daily, playlist intelligence/sorting, playlist management and safety, discovery/recommendations, playback tracking, Last.fm analytics, Library migration/enrichment, metadata retries/freshness, playability, health/maintenance, confidence verification, and documentation/maintainability.**
