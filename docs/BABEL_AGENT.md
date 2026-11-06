# SHIT Documentation & Continuity — AI continuation worker

> **Internal codename: Babel**

## Purpose and status

Babel has an optional repository-hosted AI worker that continues the documentation audit from GitHub rather than relying on a previous ChatGPT conversation. The worker is implemented in .github/workflows/babel-ai-continuation.yml and uses OpenAI's official openai/codex-action.

**Integration status:** repository configuration is committed and the user reports that the `OPENAI_API_KEY` repository Actions secret has been added. The first dispatch was received by GitHub, but run #42181953313 failed in Codex action sandbox setup before the agent prompt ran; **Activation is pending** until an end-to-end run succeeds. Do not describe the worker as operational yet.

## Active-session context bridge

Before reading the other continuation records, Buddy must read `project/ACTIVE_SESSION_BRIEF.md`. It is a curated SHIT project brief maintained by ChatGPT during active work—not a raw transcript and not a real-time message channel. ChatGPT updates it after material decisions, source findings, changes, tests, failures, and blockers, alongside the affected goal roadmap/action log. Buddy must reconcile the brief against the checked-out repository and newer evidence. It sees only committed changes on a subsequent run; updates do not wake an active job. Never include unrelated personal conversation or secret values.

## How continuation works

1. GitHub Actions starts on a six-hour UTC schedule, manual `workflow_dispatch`, or a ChatGPT-controlled push to a fresh `babel/dispatch-*` branch containing only `.github/babel/dispatch.json`. The dispatch branch is only a trigger: preflight explicitly checks out `main` or the latest `babel/agent-progress` branch for the actual work.
2. Preflight checks project/BABEL_AGENT_STATE.md. If it says status: complete, the workflow stops. Otherwise it selects the latest babel/agent-progress branch, falling back to main for the first run.
3. The Codex job reads AGENTS.md, the mandatory documentation rules, Babel guide, handoff, loose-ends register, project log, and the Maintainability & Documentation roadmap/README/ACTIONS. It chooses one high-priority unfinished documentation task and makes a bounded change, then returns a raw unified Git patch as its final output (or NO_CHANGES). The patch is capped at 700 KB to stay within the workflow handoff limit.
4. The agent job has contents: read, runs on `ubuntu-24.04` (the first `ubuntu-latest`/Ubuntu 26.04 attempt exposed an upstream `drop-sudo` compatibility failure), uses the Codex `:workspace` permission profile and `drop-sudo` safety strategy, and receives no Spotify or music-provider credentials. The workspace profile has no general network access; the preflight/publisher jobs handle branch selection and PR operations outside the model's workspace.
5. A separate validation job has contents: read, no OpenAI API key, and no write-capable GitHub token. It applies the candidate patch, enforces the path allowlist, rejects deletions/out-of-scope changes, and runs full unittest discovery. A final publisher job receives contents: write and pull-requests: write; it reapplies the already-validated patch, rechecks paths, and publishes without executing candidate code.
6. If validation passes and there are changes, the publisher commits to babel/agent-progress and creates or updates one review pull request against main. Later scheduled runs resume from that branch and add further commits to the same PR.
7. The workflow never auto-merges. A human must review and merge the final work. When all acceptance criteria and the cold-start simulation genuinely pass, the agent may set status: complete; subsequent scheduled runs then stop.

## Scope and safety boundary

The publisher allows changes only to:
- AGENTS.md;
- Markdown files under docs/ and project/;
- tests/test_documentation_contract.py;
- tests/test_script_layout.py.

The workflow rejects deletions and all other changed paths. In particular, the worker must not modify runtime implementation, GitHub workflow YAML, dependencies, credentials, generated data, canonical Library records, playback data, or Spotify playlists. It must not make provider requests, rotate credentials, or run operational SHIT workflows.

The Codex job has no GitHub write token. Candidate tests run in a separate read-only job with neither the OpenAI API key nor a write-capable GitHub token, so even a malicious test change cannot steal publishing credentials. The publisher is the only job that can push; it only reapplies the validated patch, rechecks changed paths, and publishes without running candidate code. The agent is instructed to keep the state active unless every Maintainability & Documentation acceptance criterion is evidenced, including a successful fresh-session simulation.

## One-time activation

1. Create an API key in the OpenAI API platform: https://platform.openai.com/api-keys
2. Confirm the repository Actions secret `OPENAI_API_KEY` exists. The user reports that it has been added; never read, print, or share its value.
3. In **Settings → Actions → General → Workflow permissions**, enable **Allow GitHub Actions to create and approve pull requests** if it is disabled.
4. After the Ubuntu 24.04 compatibility fix is on `main`, trigger a fresh run with a new `babel/dispatch-*` marker push or use **Actions → Babel AI continuation → Run workflow** on `main`.
5. Confirm the Codex prompt executes, independent path/deletion validation passes, full unittest discovery passes, and the dedicated branch/PR is created or updated.

ChatGPT subscription access is not itself an API key. OpenAI API usage is billed separately under the API platform account. Set appropriate API usage limits/budget alerts in the OpenAI platform before enabling recurring runs.

## First-run failure and compatibility workaround

The first ChatGPT-triggered push run is [#42181953313](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42181953313). Preflight succeeded; the Codex action failed before the prompt ran while trying to restrict `/run/dbus/system_bus_socket` on the GitHub-hosted Ubuntu 26.04 image selected by `ubuntu-latest`. The same failure is tracked upstream in [openai/codex-action issue #188](https://github.com/openai/codex-action/issues/188). The agent job is pinned to `ubuntu-24.04` as the compatibility workaround; `drop-sudo` remains enabled. Do not switch to `unsafe` to bypass this failure. A fresh run must verify Codex execution, independent path validation/full tests, and isolated PR publication.

## Recovery and operations

- **Latest work:** inspect the open pull request with head branch babel/agent-progress.
- **Latest execution:** inspect Actions → Babel AI continuation and the latest run summary/Codex final-message output.
- **Resume:** the next scheduled run checks out the latest dedicated branch. A manual dispatch can also restart it.
- **Interrupted run:** no progress is assumed unless it was committed to the branch. The next run reads the branch and the repository checkpoints again.
- **No changes:** the workflow reports a no-op; it does not create empty commits.
- **Out-of-scope patch or failed tests:** publisher fails without pushing. Inspect the run log and Codex final-message output, then fix the prompt or documentation manually before retrying.
- **Completion:** only the explicit status: complete sentinel stops future scheduled runs. A no-op is not completion.

The branch is intentionally separate from main; the worker's commits are proposals until human review and merge. This workflow does not promise that the same ChatGPT browser conversation will reopen or receive a new message. It is an independent Codex agent operating from repository state.

## Source files

- Workflow: .github/workflows/babel-ai-continuation.yml
- Agent instructions: .github/babel/CONTINUATION_PROMPT.md
- Durable stop/recovery state: project/BABEL_AGENT_STATE.md
- Workflow catalogue: WORKFLOWS.md
- Canonical Babel contract: BABEL.md

## Verification status

The repository baseline is green: Daily curator tests run #42178656402 passed full unittest discovery (**478 tests**) on commit 69e72829c6cc9e72837025f8c777b4d846c9ba7b. This verifies the repository test suite and documentation contracts, not the Codex continuation worker. No successful Babel AI continuation run has yet been observed. The API secret is reported configured. Do not mark activation complete until a post-fix run proves Codex execution, independent validation, full tests, and the resulting isolated branch/PR.
