# Babel AI continuation state

status: active
worker: OpenAI Codex through openai/codex-action
branch: babel/agent-progress
trigger: GitHub Actions schedule every six hours, manual dispatch, plus push to babel/dispatch-* when .github/babel/dispatch.json changes
publication: dedicated branch and one reviewable pull request; never auto-merge
scope: documentation, continuity records, and narrowly scoped documentation-contract tests only
last_result: dispatch marker pushed successfully; workflow execution not yet verified
completion_rule: all Maintainability & Documentation roadmap acceptance criteria plus a successful cold-start simulation, with exact test and workflow evidence

## Operating contract

- This is an automation aid for **SHIT Documentation & Continuity (internal codename: Babel)**, not a replacement for source review or human approval.
- Repository documentation is the durable memory. Every run must read the current handoff and relevant goal records before acting.
- Every run must read `project/ACTIVE_SESSION_BRIEF.md` first, then reconcile its claims against the checked-out repository and current evidence. The brief is a curated, privacy-safe context bridge, not a raw chat transcript or live message channel.
- The worker may make bounded documentation/test changes only. It must not perform SHIT feature work, provider requests, playlist operations, credential rotation, or generated-data writes.
- A separate read-only validation job applies the patch, enforces the allowlist, and runs full unittest discovery without the API key or a write-capable GitHub token. The publisher alone has write permissions; it rechecks paths and publishes without executing candidate code.
- The workflow does not merge its pull request. Review and merge remain a human-controlled boundary.
- If this file says `status: complete`, scheduled continuation stops. Never set that state merely because a run has no useful changes or because one batch is finished.

## Recovery

If a run is interrupted or fails, inspect the latest GitHub Actions run and the open `babel/agent-progress` pull request. The next scheduled/manual run starts from the latest dedicated branch when it exists. Record any blocker in this file and the Maintainability & Documentation action history.

## Activation requirement

The GitHub Actions repository secret `OPENAI_API_KEY` must be configured by the repository owner. The key must be created in the OpenAI API platform; ChatGPT subscription access is not itself an API key. Never put the key in the repository or chat.
