# SHIT repository instructions

**Documentation system naming:** use **SHIT Documentation & Continuity** as the clear public-facing name. Its internal codename is **Babel**; define it through [docs/BABEL.md](docs/BABEL.md) before using the short name in a fresh session.

This file applies to every assistant, contributor, and automation agent working in this repository.

## Before changing anything
1. Read [project/DOCUMENTATION_RULES.md](project/DOCUMENTATION_RULES.md). It is mandatory.
2. Read [the documentation-system identity and operating guide](docs/BABEL.md) so “Babel” is unambiguous.
3. Read [project/NEXT_WORK.md](project/NEXT_WORK.md), [project/LOOSE_ENDS.md](project/LOOSE_ENDS.md), and [project/PROJECT_LOG.md](project/PROJECT_LOG.md).
4. Find the relevant workstream in [project/goals/README.md](project/goals/README.md). Read its `ROADMAP.md`, `README.md`, and `ACTIONS.md`.
5. Read the relevant source, tests, data contracts, runbooks, workflow definitions, and current GitHub status. Documentation is not a substitute for checking the live implementation.
   Before editing or committing any path, inspect matching workflow `push.paths` filters. Comment-only changes to a listed source or workflow file still trigger its full workflow, including provider calls and repository writes.
6. Confirm the current branch and working tree before editing. Do not overwrite unrelated work.

## Active-session brief — mandatory Buddy context bridge

During every active SHIT work session, ChatGPT must maintain [project/ACTIVE_SESSION_BRIEF.md](project/ACTIVE_SESSION_BRIEF.md) as work proceeds. Update it after every material decision, scope change, implementation change, source finding, test/audit result, failure, uncertainty, or blocker—not only at session end. Update the affected goal ROADMAP.md and ACTIONS.md in the same session, plus NEXT_WORK.md / LOOSE_ENDS.md / PROJECT_LOG.md when cross-project state changes. Buddy must read the brief at the start of every run and reconcile it against checked-out source and evidence. The brief is curated project context, never a raw chat transcript; exclude unrelated personal details and all secret values. It is not real-time messaging: Buddy sees only committed updates on a subsequent run.

## Mandatory daily Buddy check for every SHIT conversation

Whenever ChatGPT is asked to work on, discuss, review, plan, or report on SHIT, Babel, or Buddy, it must perform the Buddy daily-check gate before substantive work:

1. Read the current SHIT Buddy automation status and latest run result using the available automation status source. Use the user's Eastern timezone, `America/New_York`, to determine the current calendar day.
2. If no successful, report-bearing Buddy run has completed for the current Eastern date, state plainly that Buddy is **pending today** (or identify the exact failure/blocker). Do not repeatedly perform a full PR audit while the run is still pending; check again on the next SHIT-related conversation.
3. Once a successful run for today is visible, independently review that run's report, Buddy-owned draft PR, complete changed-file list/diff, read-back evidence, and CI/check state. Verify claims against current source and tests; distinguish draft from merged work. A green check or Buddy's own self-review is not a substitute for independent review.
4. Record a durable review checkpoint in `project/ACTIVE_SESSION_BRIEF.md`: Eastern date, Buddy run ID, reviewed PR/head SHA (or no-PR result), review outcome, and outstanding user action. On later SHIT conversations that same day, a lightweight status check is sufficient; skip the full review if the same run ID and PR head SHA are already recorded as reviewed. Re-review if either changes, a new run appears, or a material failure/check change is reported.
5. A failed/incomplete run does not count as a successful daily completion. Report the blocker and retry the gate on the next SHIT-related conversation. Do not claim continuous background monitoring: checks occur when a SHIT conversation is active.
6. ChatGPT may independently correct documentation within its authorized scope and publish changes only through a reviewable draft PR. Never write directly to `main`, approve, mark ready, close, merge, or self-merge. The user retains final integration authority.

This is a core SHIT operating rule, not an optional reminder. It applies across fresh conversations and assistants; this repository instruction is authoritative over chat habits.

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
