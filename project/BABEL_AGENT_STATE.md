# Babel AI continuation state

status: active
worker: OpenAI Codex through openai/codex-action
branch: babel/agent-progress
trigger: GitHub Actions schedule every six hours, manual dispatch, plus push to babel/dispatch-* when .github/babel/dispatch.json changes
publication: dedicated branch and one reviewable pull request; never auto-merge
scope: documentation, continuity records, and narrowly scoped documentation-contract tests only
last_result: first dispatch run #42181953313 reached preflight but Codex failed before prompt execution on Ubuntu 26.04 during drop-sudo D-Bus socket restriction; agent job pinned to ubuntu-24.04 as workaround; end-to-end verification pending
completion_rule: all Maintainability & Documentation roadmap acceptance criteria plus a successful cold-start simulation, with exact test and workflow evidence

## Operating contract

- This is an automation aid for **SHIT Documentation & Continuity (internal codename: Babel)**, not a replacement for source review or human approval.
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

## Recovery

If a run is interrupted or fails, inspect the latest GitHub Actions run and the open `babel/agent-progress` pull request. The next scheduled/manual run starts from the latest dedicated branch when it exists. Record any blocker in this file and the Maintainability & Documentation action history.

## Activation requirement

The GitHub Actions repository secret `OPENAI_API_KEY` must be configured by the repository owner. The key must be created in the OpenAI API platform; ChatGPT subscription access is not itself an API key. Never put the key in the repository or chat.
