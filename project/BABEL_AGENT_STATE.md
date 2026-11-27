# Babel AI continuation state — repository-hosted Codex/API experiment

# This file is consumed by .github/workflows/babel-ai-continuation.yml.
# status: active means Babel acceptance remains open; status: complete is the state-file stop sentinel.
status: active
worker: historical OpenAI Codex experiment through openai/codex-action; not the current SHIT Buddy
current_buddy: scheduled ChatGPT task using the connected GitHub app; see docs/BABEL_CHATGPT_BUDDY.md
branch: babel/agent-progress (legacy Codex branch; separate from babel/chatgpt-buddy-v2)
trigger: workflow YAML declares a six-hour schedule, manual dispatch, and push to babel/dispatch-* when .github/babel/dispatch.json changes; repository-level enabled/disabled state not confirmed
publication: legacy dedicated branch and one reviewable pull request; never auto-merge
scope: documentation, continuity records, and narrowly scoped documentation-contract tests only
last_result: scheduled runs #44808721608 (2026-11-20) and #44878119328 (2026-11-21) passed preflight, then Codex agent failed with API quota exceeded; validation/publisher skipped; no candidate patch or PR; no manual dispatch by ChatGPT Buddy
completion_rule: all Maintainability & Documentation roadmap acceptance criteria plus a successful cold-start simulation, with exact test and workflow evidence

## Operating contract

- This is an automation aid for **SHIT Documentation & Continuity (internal codename: Babel)**, not a replacement for source review or human approval.
- This state file belongs only to the repository-hosted Codex/API experiment. It does not describe or control the current scheduled ChatGPT Buddy.
- The workflow YAML still declares scheduled, manual, and push triggers. GitHub recorded scheduled runs #44808721608 and #44878119328; both passed preflight and failed in the Codex agent with quota exceeded. These runs prove the schedule triggered at those times, but the available read-only API did not expose the current workflow enabled/disabled setting. Preflight also skips the agent when `OPENAI_API_KEY` is absent; this audit did not inspect the secret value.
- `status: active` is not a pause switch. The state-file stop condition is the exact `status: complete` value; preflight also skips the agent if `OPENAI_API_KEY` is absent. Never misuse the completion sentinel to suppress Codex execution because it would falsely mark Babel complete.
- If no Codex API execution is wanted, the repository owner must disable the workflow in GitHub Actions or separately authorize a workflow change. Buddy must not change workflow settings/logic or dispatch it.
- Repository documentation is the durable memory. Every run must read the current handoff and relevant goal records before acting.
- Every run must read `project/ACTIVE_SESSION_BRIEF.md` first, then reconcile its claims against the checked-out repository and current evidence. The brief is a curated, privacy-safe context bridge, not a raw chat transcript or live message channel.
- The worker may make bounded documentation/test changes only. It must not perform SHIT feature work, provider requests, playlist operations, credential rotation, or generated-data writes.
- A separate read-only validation job applies the patch, enforces the allowlist, and runs full unittest discovery without the API key or a write-capable GitHub token. The publisher alone has write permissions; it rechecks paths and publishes without executing candidate code.
- The workflow does not merge its pull request. Review and merge remain a human-controlled boundary.
- If this file says `status: complete`, scheduled continuation stops. Never set that state merely because a run has no useful changes or because one batch is finished.

## Latest execution evidence — 2026-11-06

- Dispatch commit: `7c1abce763d293992872699146eb7f13d10f9b87` on `babel/dispatch-20261106-01`.
- Workflow run: [#42181953313](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42181953313), event `push`, completed with failure.
- `preflight`: success. `agent`: failure. `validate` and `publish`: skipped. No agent patch, continuation branch, or PR was produced by this run.
- Root cause: `ubuntu-latest` resolved to Ubuntu 26.04; Codex action `drop-sudo` failed restricting `/run/dbus/system_bus_socket` and reported the runner was not in the sudo group. This matches [upstream issue #188](https://github.com/openai/codex-action/issues/188).
- Remediation: pin only the Codex agent job to `ubuntu-24.04`; retain `drop-sudo`, `:workspace`, read-only GitHub permissions, independent validation, and isolated publisher. Retry and verify every job before calling Buddy operational.

## Retry evidence — 2026-11-06

- Retry marker commit: `75d3102e80ffe4158214114fa90c5979edda14e6` on `babel/dispatch-20261106-02`, based on the updated `main`.
- Workflow run: [#42183337573](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42183337573), event `push`, completed with failure.
- `preflight`: success. The agent job checked out the latest source on `ubuntu-24.04`; its `drop-sudo` isolation successfully restricted `/run/snapd-snap.socket`. Codex then returned `Quota exceeded. Check your plan and billing details.`
- `validate` and `publish`: skipped. No candidate patch, `babel/agent-progress` branch, or Buddy PR was produced.
- **Conclusion:** the Ubuntu runner compatibility workaround is verified, but the two latest scheduled runs still failed with API quota exceeded before validation/publication. No manual retry is authorized; do not ask the user to fund API usage or weaken the sandbox to `unsafe`. If scheduled Codex attempts are unwanted, the repository owner must disable the workflow in GitHub Actions; Buddy must not change workflow settings or logic.

## Recovery

This workflow is a separate historical experiment, not the current ChatGPT Buddy. Do not manually dispatch, retry, or assume it is disabled. If the user explicitly reauthorizes the Codex experiment, first confirm the repository-level workflow state, inspect the latest workflow run, and inspect any existing `babel/agent-progress` branch or PR before proceeding. The workflow YAML still declares a six-hour schedule, manual dispatch, and a push trigger; whether GitHub currently permits those triggers is not confirmed by this state file. Record any verified blocker or recovery result here and in the Maintainability & Documentation action history.

## Historical activation prerequisites — no current action

The historical workflow references the repository Actions secret `OPENAI_API_KEY`. Never read, print, copy, or expose its value. ChatGPT subscription access does not provide OpenAI API credits. Do not ask the user to create a key, add credits, or re-enable the experiment. Any future activation requires explicit user reauthorization and owner-controlled GitHub Actions configuration.
