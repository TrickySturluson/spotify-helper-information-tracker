# SHIT Buddy — ChatGPT scheduled continuation

> **Parent system:** SHIT Documentation & Continuity (internal codename: Babel)  
> **Worker name:** Buddy (identifier: SHIT-Buddy)  
> **Execution model:** scheduled ChatGPT task using the connected GitHub app

## Purpose

This guide documents the ChatGPT-hosted Buddy path. It is separate from the repository-hosted OpenAI Codex worker described in [BABEL_AGENT.md](BABEL_AGENT.md). The ChatGPT path is intended to provide bounded, recurring documentation continuation without an OpenAI API key, paid API calls, a local computer, or a continuously running personal PC.

The GitHub repository remains the durable source of truth. A scheduled task is an execution trigger and worker, not a replacement for repository documentation, tests, source review, or human approval.

## Capability evidence

On 2026-11-06, a scheduled ChatGPT task used the connected GitHub app against this repository and confirmed these operations:

- Read the default-branch README and Babel/continuity records.
- Created an isolated branch.
- Created and updated a documentation-only Markdown file on that branch.
- Opened a draft pull request against `main`.
- Read the file back and searched GitHub to verify the draft PR.

The proof is [draft PR #162](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/162). It is intentionally temporary and is not a permanent feature or proof of every future scheduled run. The user must decide whether to retain or close it. No merge was performed.

## Scheduled operating model

The current ChatGPT task is **SHIT Buddy — daily Babel continuation**. It is configured for a daily flexible schedule in `America/New_York`. Actual delivery can vary; the schedule is not a guarantee of execution at an exact minute.

Each run must:

1. Read the repository's mandatory instructions, active-session brief, current handoff, loose ends, project log, goal index, Maintainability & Documentation roadmap/README/ACTIONS, and Babel guides.
2. Inspect the current default branch, open PRs, relevant workflow evidence, and source files before relying on recorded status.
3. Select one small, high-priority unfinished documentation task.
4. Make source-grounded, documentation-only changes and update the relevant roadmap/action history and continuity records when needed.
5. Run only safe, relevant checks that are available; never claim a check ran without an actual result.
6. Publish a reviewable draft PR on the dedicated `babel/chatgpt-buddy` branch, reusing its existing PR rather than creating duplicates.
7. Read changes back from GitHub and report files changed, verification, PR state, blockers, and the next action.

The task is designed to be resumable from repository state rather than depending on a long-lived conversation. One bounded batch per run is preferred over broad, risky rewrites.

## Mandatory ChatGPT verification on every SHIT conversation

ChatGPT must check Buddy whenever a conversation involves SHIT, Babel, or Buddy. This is a core repository rule, not an optional reminder.

1. Check the scheduled automation's latest run/result before substantive SHIT work, using the current `America/New_York` date.
2. If no successful, report-bearing run has completed today, report that Buddy is pending (or give the exact failure/blocker). On each later SHIT conversation, make a lightweight status check rather than repeatedly auditing the same unchanged state.
3. Once today's successful run appears, independently review its report, Buddy PR, full diff, changed-file list, read-back evidence, and CI/checks. Compare material claims with current source and tests.
4. Record the review checkpoint in `project/ACTIVE_SESSION_BRIEF.md`: Eastern date, run ID, PR number/head SHA (or no-PR result), outcome, and any user action.
5. On later SHIT conversations the same day, skip the full review if the run ID and PR head SHA are unchanged and the checkpoint records a completed review. Re-review if a new run appears, the PR head changes, or a material check/failure changes.
6. A failed or incomplete run is not a successful daily completion. Checks happen when SHIT conversations occur; this does not create continuous background monitoring.

ChatGPT may make authorized documentation corrections and publish them through a draft PR. It must never write directly to `main`, approve, mark ready, close, merge, or self-merge. The user retains final authority.

## Scope and authority

Allowed:
- Markdown documentation under `docs/` and `project/`.
- `AGENTS.md`.
- Narrow documentation-contract tests in `tests/test_documentation_contract.py` or `tests/test_script_layout.py`, only when needed to enforce a real documentation invariant.

Forbidden:
- Runtime/product code, playlist operations, Spotify/Last.fm/provider calls, generated data, canonical Library/state/audit files, credentials or secret values, dependency manifests, workflow logic, permissions, security controls, and unrelated feature work.
- Direct writes to `main`, PR approval, marking a PR ready, merging, or self-merging.
- Taking over existing PR #161 (the main documentation delivery) or PR #162 (temporary connectivity proof).

The user retains final authority over every proposal. Buddy may prepare draft changes; it cannot authorize or merge them.

## Relationship to the Codex worker

The repository-hosted Codex worker remains documented in [BABEL_AGENT.md](BABEL_AGENT.md), but its latest recorded execution reached the API and failed with a quota-exceeded response. Do not trigger it or assume it is operational while the user has chosen a $0 API budget.

The ChatGPT scheduled worker uses the connected GitHub app, not the Codex workflow or an OpenAI API key. The successful connectivity proof establishes that GitHub operations are possible in the tested task context; each future run must still verify its own access and results.

## Completion gate

Buddy must not declare Babel complete because a scheduled run succeeded or because a documentation PR was created. Completion requires the Maintainability & Documentation roadmap's acceptance criteria to be satisfied on merged `main`, plus a successful fresh-session simulation using repository documentation alone. Draft/unmerged work does not count.

If scheduled execution, GitHub access, permissions, or task limits block work, report the exact limitation and stop without workarounds. Do not ask the user to pay for API credits or weaken security controls.
