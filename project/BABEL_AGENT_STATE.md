# Babel AI continuation state

status: active
worker: OpenAI Codex through openai/codex-action
branch: babel/agent-progress
trigger: GitHub Actions schedule every six hours, manual dispatch, plus push to babel/dispatch-* when .github/babel/dispatch.json changes
publication: dedicated branch and one reviewable pull request; never auto-merge
scope: documentation, continuity records, and narrowly scoped documentation-contract tests only
last_result: run #42181953313 exposed Ubuntu 26.04 drop-sudo failure; after pinning agent to ubuntu-24.04, retry #42183337573 passed preflight and drop-sudo but Codex returned API quota exceeded; validation/publisher skipped; awaiting user billing/quota fix
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

## Retry evidence — 2026-11-06

- Retry marker commit: `75d3102e80ffe4158214114fa90c5979edda14e6` on `babel/dispatch-20261106-02`, based on the updated `main`.
- Workflow run: [#42183337573](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42183337573), event `push`, completed with failure.
- `preflight`: success. The agent job checked out the latest source on `ubuntu-24.04`; its `drop-sudo` isolation successfully restricted `/run/snapd-snap.socket`. Codex then returned `Quota exceeded. Check your plan and billing details.`
- `validate` and `publish`: skipped. No candidate patch, `babel/agent-progress` branch, or Buddy PR was produced.
- **Conclusion:** the Ubuntu runner compatibility workaround is verified. The current blocker is OpenAI API quota/billing availability. Do not trigger repeated retries until the repository owner confirms quota is available. Never weaken the sandbox to `unsafe`.

## Recovery

If a run is interrupted or fails, inspect the latest GitHub Actions run and the open `babel/agent-progress` pull request. The next scheduled/manual run starts from the latest dedicated branch when it exists. Record any blocker in this file and the Maintainability & Documentation action history.

## Activation requirement

The GitHub Actions repository secret `OPENAI_API_KEY` must be configured by the repository owner. The key must be created in the OpenAI API platform; ChatGPT subscription access is not itself an API key and does not supply API credits. The API project/organization must also have available quota/credits and a usable billing limit. Never put the key in the repository or chat.
