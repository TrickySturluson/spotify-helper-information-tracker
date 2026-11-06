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

## Deferred post-Babel objective — SHIT-wide integrity, diagnostics and recovery

After Babel is judged as complete and realistically as good as it can be, revisit a dedicated SHIT-wide **Integrity, Diagnostics & Recovery** workstream. This is explicitly deferred; it does not expand the current documentation-only priority or authorize runtime implementation now.

The intended design is a coordinated health system: (1) health monitoring across project data, documentation, tests and workflows; (2) diagnostics that trace symptoms to likely root causes; (3) bounded recovery/repair for deterministic, reversible cases; (4) Buddy as the permanent Documentation & Continuity Guardian, checking documentation drift, roadmaps, handoffs and evidence; and (5) an improvement backlog for recurring failures and systemic weaknesses. Buddy contributes evidence and documentation maintenance but is not the sole health authority and must not approve its own risky repairs.

Safety contract to carry forward: observe and diagnose by default; preserve canonical data and provenance; distinguish authoritative Last.fm scrobbles from optional Spotify playback observations; never invent, silently delete, or silently rewrite uncertain records; only allow explicitly scoped, deterministic, backed-up, reversible repairs with audit trail and post-repair verification; require user approval for consequential or ambiguous changes. Revisit and formalize scope, ownership, autonomy levels, health dimensions, audit records and acceptance criteria only after Babel's completion gate and cold-start simulation pass.

## Current Buddy activation status

- Workflow: `.github/workflows/babel-ai-continuation.yml`.
- Instructions: `.github/babel/CONTINUATION_PROMPT.md`.
- Durable worker state: `project/BABEL_AGENT_STATE.md`.
- Proposal branch: `babel/agent-progress`.
- The user has reported adding the OpenAI API key to GitHub repository Actions secrets under the exact name `OPENAI_API_KEY`. Secret values must never be read, printed, copied, or documented.
- The first dispatch run is now verified: run [#42181953313](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42181953313) completed with failure. Preflight passed; Codex failed before prompt execution; validation and publisher were skipped. Do not claim activation.
- The user has now confirmed **Settings → Actions → General → Workflow permissions → Allow GitHub Actions to create and approve pull requests** is enabled.
- Workflow trigger enhancement: `.github/workflows/babel-ai-continuation.yml` listens for a push to a `babel/dispatch-*` branch when `.github/babel/dispatch.json` changes. On 2026-11-06, ChatGPT successfully created `babel/dispatch-20261106-01` from `main` and committed `.github/babel/dispatch.json` in commit `7c1abce763d293992872699146eb7f13d10f9b87`. This is the first successful ChatGPT-initiated GitHub write intended to dispatch Buddy. The dispatch branch is only a trigger; preflight/agent/validation/publisher continue to use `main` or `babel/agent-progress` as before. Manual dispatch and the six-hour schedule remain available.
- The marker push successfully triggered run [#42181953313](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42181953313) on commit `7c1abce763d293992872699146eb7f13d10f9b87`. Preflight passed. Codex failed before prompt execution because `ubuntu-latest` resolved to Ubuntu 26.04 and the action's `drop-sudo` D-Bus socket restriction failed (`runner is not a member of the sudo group` / `Could not restrict access`). This matches upstream [openai/codex-action issue #188](https://github.com/openai/codex-action/issues/188). Validation and publisher were skipped; no Buddy PR was created. The workflow's Codex agent job is pinned to `ubuntu-24.04` as a workaround, retaining `drop-sudo` and all existing permission boundaries.
- Retry marker `75d3102e80ffe4158214114fa90c5979edda14e6` on `babel/dispatch-20261106-02` triggered [run #42183337573](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42183337573). Preflight passed; the Ubuntu 24.04 Codex job completed `drop-sudo` isolation; Codex then returned `Quota exceeded. Check your plan and billing details.` Validation and publisher were skipped; no patch or PR was created. The runner fix is verified; the remaining blocker is API quota/billing. Do not retry until the user confirms quota is available.
- Continuity rule is now propagated into `AGENTS.md`, `project/DOCUMENTATION_RULES.md`, `docs/BABEL_AGENT.md`, `project/BABEL_AGENT_STATE.md`, the Buddy continuation prompt, the Maintainability & Documentation roadmap/action log, `project/NEXT_WORK.md`, and `project/PROJECT_LOG.md`. Latest supporting commits include `675351e` (worker state) and `7770474` (project log).
- Post-quota verification must confirm the Codex job succeeds, independent validation passes path/deletion checks and full unittest discovery, and the publisher creates or updates the isolated proposal branch/PR. No automatic merge.

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
