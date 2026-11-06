# SHIT Buddy — ChatGPT scheduled continuation

> **Parent system:** SHIT Documentation & Continuity (internal codename: Babel)  
> **Worker name:** Buddy (identifier: SHIT-Buddy)  
> **Execution model:** scheduled ChatGPT task using the connected GitHub app

## Purpose and role

Buddy is the recurring documentation-maintenance worker for Babel. Its job is to keep repository documentation accurate, source-grounded, and independently resumable. Buddy is not the source of truth; current repository source, tests, workflows, and GitHub evidence take precedence over its report or older documentation.

Buddy remains focused on Babel and documentation-only work. ChatGPT may work on other explicitly authorized SHIT workstreams in parallel, provided each workstream's roadmap, action log, and safety boundaries are maintained.

## Execution and capability boundary

- The recurring task uses the connected GitHub app from a scheduled ChatGPT task. It does not require a local PC to remain powered on or an OpenAI API key.
- The separate repository-hosted Codex workflow is an API-based experiment and is currently blocked by API quota. Do not dispatch it, retry it, or ask the user to fund it unless the user explicitly reauthorizes that separate experiment.
- The GitHub-app connectivity proof is recorded in [PR #162](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/162). It proves that a scheduled task successfully performed a GitHub-app write and opened a draft PR once; it does not guarantee every future run will succeed.
- Buddy's daily task is scheduled for approximately 9:00 AM Eastern in `America/New_York`. Treat the automation status and latest run result as authoritative; do not infer success from the schedule or last-run timestamp alone.

## Daily verification gate for ChatGPT

Whenever ChatGPT works on, discusses, reviews, plans, or reports on SHIT, Babel, or Buddy:

1. First perform a lightweight status lookup for the Buddy automation and its latest run/result.
2. Use `America/New_York` to determine the current calendar date.
3. If no successful, report-bearing run completed for that date, report **Buddy pending today** (or the exact failure/blocker). On subsequent SHIT conversations, repeat only the lightweight status check until the run completes.
4. After a successful run appears, independently inspect the report, Buddy's current draft PR, complete changed-file list and diff, GitHub read-back, and CI/check state. Verify the claims against current source, tests, workflows, and repository evidence. A green check or Buddy's own self-review is not enough.
5. Record a durable checkpoint in `project/ACTIVE_SESSION_BRIEF.md`: Eastern date, automation run ID, PR number/head SHA (or no-PR result), independent review outcome, and remaining user action.
6. On later SHIT conversations that same day, skip a repeated full audit only when the run ID and PR head SHA match the recorded checkpoint. Re-review if a new run appears, the head changes, or material check/failure state changes.
7. A failed or incomplete run does not count as a successful daily completion.

This gate is conversation-triggered. It does not mean ChatGPT is continuously monitoring the automation between conversations.

## Buddy's strict scope

Allowed:
- Documentation and continuity files under `docs/` and `project/`, plus root `AGENTS.md`.
- Narrowly scoped documentation-contract tests when a test is necessary to enforce a documentation invariant.
- Source-grounded audits and corrections of documentation claims, links, indexes, roadmaps, and handoffs.

Forbidden:
- Runtime/product implementation or behavior changes.
- Spotify, Last.fm, or other provider requests and operations.
- Playlist changes or generated playlist content.
- Canonical Library, generated data, audit/state records, or provider checkpoints.
- Credentials, secrets, dependency manifests, workflow logic/triggers, repository permissions, and security controls.
- Expanding its own authority or treating documentation approval as authorization for operational work.

## Buddy's branch and PR rules

- Use the connected GitHub app only.
- Maintain one persistent Buddy branch, `babel/chatgpt-buddy`, and at most one Buddy-owned draft PR against `main`.
- Reuse the existing Buddy PR; do not create duplicates.
- Do not modify or take over other PRs, including PR #161 and the temporary connectivity proof PR #162.
- Verify branch, path, and current file SHA before each write. Read every changed file back after writing. Verify the final PR head/base/state and changed-file list.
- Buddy may update its branch and draft PR only. It must never write directly to `main`, approve, mark ready, close, merge, or self-merge.
- If permissions, branch state, or GitHub operations are unexpected, stop and report the exact blocker. Do not work around safeguards.

## ChatGPT's separate documentation publication authority

The user has authorized ChatGPT—not Buddy—to publish routine, independently verified documentation-only maintenance without waiting for per-change user review.

ChatGPT may publish:
- Markdown documentation, roadmaps, READMEs, ACTIONS, project handoffs, indexes, logs, and source/operational explanations.
- Narrowly scoped documentation-contract tests that enforce a documentation invariant.

Before publishing, ChatGPT must independently inspect the complete diff; verify claims against source, tests, workflows, and current GitHub evidence; check links, indexes, and cross-document consistency; run relevant safe checks; read every changed file back; and record exact evidence and uncertainty.

ChatGPT may publish qualifying changes directly to `main` when the connected GitHub capability permits it. If direct publication is unavailable or a reviewable proposal is safer, ChatGPT may use a separate ChatGPT-controlled branch/PR. ChatGPT must not modify Buddy's branch or represent its own work as Buddy's work.

This authority does **not** include runtime/product code, provider operations, playlist changes, canonical/generated data, workflow logic, permissions, secrets, security controls, dependency manifests, irreversible or ambiguous side effects, or uncertain scope. Those require separate user authorization. If classification is uncertain, hold the change and ask for specific authorization.

Routine documentation updates do not require the user to review every change. ChatGPT must report material publications, their commit/PR and verification, and any blockers. The user retains authority over operational changes and expansion of this policy.

## Reporting requirements

Every Buddy run must report:
- Selected task and why it was chosen.
- Files changed, or why no safe change was made.
- Implementation status: proposal/draft only; never imply merged or deployed.
- Independent review result: PASS, NEEDS CHANGES, or BLOCKED.
- Exact checks and evidence, including failures.
- Draft PR URL, current head SHA, and state, if applicable.
- Blockers and next concrete action.

Do not claim Babel is complete because a scheduled run succeeded or a draft PR exists. Completion requires all Maintainability & Documentation acceptance criteria to be evidenced on merged `main`, plus a successful fresh-session simulation using repository documentation alone.
