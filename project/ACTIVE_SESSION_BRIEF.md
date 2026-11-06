# Active SHIT Session Brief

> **Purpose:** This is the curated context bridge between active ChatGPT work and the repository-hosted documentation worker (Buddy). It is not a raw chat transcript, does not contain private conversation material, and is not a real-time message channel.

## Operating rule

During every active SHIT work session, ChatGPT must maintain this file as work proceeds. Update it after each material user decision, scope change, implementation change, source finding, test/audit result, failure, uncertainty, or blocker—not merely at session end. Update the affected goal `ROADMAP.md` and `ACTIONS.md` in the same session; also update `NEXT_WORK.md`, `LOOSE_ENDS.md`, and `PROJECT_LOG.md` when cross-project state or major decisions change.

Buddy must read this file at the start of every run, then reconcile it against the checked-out source, tests, workflow definitions, current branch, and recorded evidence. This brief is a navigation and context aid, not authority to override newer verified source or evidence. If it conflicts with source or fresh evidence, report and resolve the discrepancy rather than repeating stale claims.

Updating this file does not wake Buddy, alter an already-running job, or deliver a live message. Buddy sees committed updates on its next scheduled or manually dispatched run.

## Identity and roles

- Repository/product: **Spotify Helper & Information Tracker (SHIT)**.
- Documentation system: **SHIT Documentation & Continuity**, internal codename **Babel**.
- Documentation worker: **Buddy** in repository documentation and everyday references. Its OpenAI agent identifier is **SHIT-Buddy**, reserved to distinguish it from possible future agents.
- ChatGPT is responsible for active project work, keeping this brief and project records current, and reviewing Buddy's proposals.
- Buddy is a documentation partner only. It may audit and improve documentation, continuity records, roadmaps, action logs, and narrowly scoped documentation-contract tests. It must not perform SHIT runtime/product development or Spotify/Last.fm operations.
- User retains final authority over integration. Buddy may publish only to its isolated `babel/agent-progress` branch and its review PR; it must not write directly to `main`, self-merge, auto-merge, or expand its permissions.

## Current priority

**Babel documentation and continuity completion is the sole active SHIT workstream.** Do not resume feature development, enrichment, provider checks, or Spotify playlist operations until the Maintainability & Documentation roadmap acceptance criteria pass and a fresh-session simulation succeeds using repository documentation alone.

Success means a new assistant with no prior chat history can identify the repository's goals, current verified state, constraints, evidence, unresolved risks, and next executable action from repository files alone.

## Current Buddy activation status

- Workflow: `.github/workflows/babel-ai-continuation.yml`.
- Instructions: `.github/babel/CONTINUATION_PROMPT.md`.
- Durable worker state: `project/BABEL_AGENT_STATE.md`.
- Proposal branch: `babel/agent-progress`.
- The user has reported adding the OpenAI API key to GitHub repository Actions secrets under the exact name `OPENAI_API_KEY`. Secret values must never be read, printed, copied, or documented.
- The repository state file still records `last_result: not yet run`. Do not claim activation until a successful workflow run is observed.
- Remaining owner-side activation check: ensure **Settings → Actions → General → Workflow permissions → Allow GitHub Actions to create and approve pull requests** is enabled, then manually dispatch **Actions → Babel AI continuation → Run workflow** on `main`.
- First-run verification must confirm the Codex job succeeded, the independent validation job passed path/deletion checks and full unittest discovery, and the publisher created or updated the isolated proposal branch/PR. No automatic merge.

## Current repository findings and evidence to reconcile

Read `project/NEXT_WORK.md`, `project/LOOSE_ENDS.md`, `project/PROJECT_LOG.md`, and `project/goals/maintainability-documentation/{ROADMAP.md,README.md,ACTIONS.md}` for the full current audit history and evidence. The following are high-priority carry-forward items from the current handoff; re-check them against current source and live GitHub state before relying on them:

1. Finish source-to-document semantic review of maintained implementation modules, compatibility launchers, test modules, workflows, and technical guides. Prioritize high-risk side effects, credentials, provider access, write boundaries, recovery and evidence semantics.
2. Reconcile all goal roadmaps/action logs, workflow permissions/triggers/publication behavior, open PRs/issues, and the loose-ends register.
3. Preserve the known Tricky Daily `--force`/same-Eastern-date idempotency discrepancy as an unresolved runtime issue; do not change runtime behavior during the Babel documentation-only phase.
4. Preserve the distinction between canonical Last.fm scrobbles and optional Spotify playback-tracker observations. A playlist appearance, recommendation, or saved snapshot is not proof of a play, scrobble, like, or listening.
5. Treat stale snapshots, generated reports, open PR branches, and previous CI runs as historical evidence until freshly checked. Do not merge divergent PR #161 wholesale.
6. Complete a cold-start simulation using only repository documentation and record exact results.

Previously observed test evidence: full unittest discovery passed 478 tests in workflow run #42178656402 on commit `69e72829c6cc9e72837025f8c777b4d846c9ba7b`. This is historical evidence for that commit, not proof that the current HEAD or Buddy workflow has passed.

## Required update format

Keep this brief concise and current. Use these headings when updating:

- **Current objective and success criteria**
- **Material decisions and authorization boundaries**
- **Current work / affected files / branch / PR**
- **Findings and verification evidence**
- **Failures, uncertainty, and blockers**
- **Buddy's next documentation/audit task**
- **Next executable action**

For each test or workflow claim, include the exact command or run URL/ID, commit/ref, outcome, and what it does—and does not—prove. Preserve failures and uncertainty. Do not invent timestamps, test outcomes, branch state, or completed work.

## Privacy and security

This is a curated project brief, not a chat dump. Include only SHIT project context needed for continuation. Exclude unrelated personal conversations, personal or sensitive details, private messages, API keys, secret values, tokens, credentials, and unnecessary account information. Refer to credentials by variable/secret name only.
