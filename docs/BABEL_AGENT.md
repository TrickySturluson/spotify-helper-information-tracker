# Repository-hosted Codex/API experiment (historical)

> **Internal codename: Babel**

## Purpose and status

This guide documents a **separate, historical repository-hosted Codex/API experiment**. It is not the active SHIT documentation continuation worker. The current worker is the scheduled ChatGPT task using the connected GitHub app; see [BABEL_CHATGPT_BUDDY.md](BABEL_CHATGPT_BUDDY.md).

**Execution status:** the runner compatibility workaround was verified, but the last verified Codex attempt was blocked by API quota before validation or publication (runs [#42181953313](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42181953313) and [#42183337573](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42183337573)). The workflow YAML still declares a six-hour schedule, manual dispatch, and a push trigger. The repository-level enabled/disabled state could not be confirmed through the available read-only GitHub access; do not describe the workflow as disabled or guaranteed dormant. It is not the active SHIT documentation continuation worker. Do not manually dispatch, retry, re-enable, or request API funding without explicit user reauthorization. If no scheduled Codex execution is wanted, the repository owner must disable the workflow in GitHub Actions or separately authorize a workflow change. Buddy will not change workflow settings or logic.

## Historical Codex experiment architecture

The sections below describe the repository-hosted Codex workflow as built and tested in November 2026. They are retained for audit and recovery context only; they do not describe Buddy's current execution path. The scheduled ChatGPT Buddy uses the connected GitHub app and its own persistent draft-PR branch.

The historical Codex continuation prompt also required its agent to read `project/ACTIVE_SESSION_BRIEF.md`. The active scheduled ChatGPT Buddy has the same continuity requirement: it must reconcile the curated SHIT brief against current repository source and newer evidence. The brief is maintained by ChatGPT during active work, is not a raw transcript or real-time message channel, and must exclude unrelated personal conversation and secret values.

## How continuation works

1. GitHub Actions starts on a six-hour UTC schedule, manual `workflow_dispatch`, or a ChatGPT-controlled push to a fresh `babel/dispatch-*` branch containing only `.github/babel/dispatch.json`. The dispatch branch is only a trigger: preflight explicitly checks out `main` or the latest `babel/agent-progress` branch for the actual work.
2. Preflight checks project/BABEL_AGENT_STATE.md. If it says status: complete, the workflow stops. Otherwise it selects the latest babel/agent-progress branch, falling back to main for the first run.
3. The Codex job reads AGENTS.md, the mandatory documentation rules, Babel guide, handoff, loose-ends register, project log, and the Maintainability & Documentation roadmap/README/ACTIONS. It chooses one high-priority unfinished documentation task and makes a bounded change, then returns a raw unified Git patch as its final output (or NO_CHANGES). The patch is capped at 700 KB to stay within the workflow handoff limit.
4. The agent job has contents: read, runs on `ubuntu-24.04` (the first `ubuntu-latest`/Ubuntu 26.04 attempt exposed an upstream `drop-sudo` compatibility failure), uses the Codex `:workspace` permission profile and `drop-sudo` safety strategy, and receives no Spotify or music-provider credentials. The workspace profile has no general network access; the preflight/publisher jobs handle branch selection and PR operations outside the model's workspace.
5. A separate validation job has contents: read, no OpenAI API key, and no write-capable GitHub token. It applies the candidate patch, enforces the path allowlist, rejects deletions/out-of-scope changes, and runs full unittest discovery. A final publisher job receives contents: write and pull-requests: write; it reapplies the already-validated patch, rechecks paths, and publishes without executing candidate code.
6. If validation passes and there are changes, the publisher commits to babel/agent-progress and creates or updates one review pull request against main. Later scheduled runs resume from that branch and add further commits to the same PR.
7. The workflow never auto-merges. A human must review and merge the final work. When all acceptance criteria and the cold-start simulation genuinely pass, the agent may set status: complete; subsequent scheduled runs then stop.

## Execution-control caveat

The workflow source still defines automatic and manual triggers. The `status: active` value in [project/BABEL_AGENT_STATE.md](../project/BABEL_AGENT_STATE.md) means Babel's acceptance criteria remain open; it is not a disable switch. The preflight skips the agent when the state file is exactly `status: complete` or when `OPENAI_API_KEY` is absent. This audit did not inspect the secret value or verify its presence. The completion sentinel must not be used to suppress API execution because Babel is not complete. Repository-level workflow enablement was not verified in this audit. If the owner wants to prevent any scheduled Codex/API attempt, the owner must disable the workflow in GitHub Actions or separately authorize a workflow change. Buddy must not change workflow logic/settings or dispatch the experiment.

## Scope and safety boundary

The publisher allows changes only to:
- AGENTS.md;
- Markdown files under docs/ and project/;
- tests/test_documentation_contract.py;
- tests/test_script_layout.py.

The workflow rejects deletions and all other changed paths. In particular, the worker must not modify runtime implementation, GitHub workflow YAML, dependencies, credentials, generated data, canonical Library records, playback data, or Spotify playlists. It must not make provider requests, rotate credentials, or run operational SHIT workflows.

The Codex job has no GitHub write token. Candidate tests run in a separate read-only job with neither the OpenAI API key nor a write-capable GitHub token, so even a malicious test change cannot steal publishing credentials. The publisher is the only job that can push; it only reapplies the validated patch, rechecks changed paths, and publishes without running candidate code. The agent is instructed to keep the state active unless every Maintainability & Documentation acceptance criterion is evidenced, including a successful fresh-session simulation.

## Historical activation procedure — do not use without explicit reauthorization

1. Create an API key in the OpenAI API platform: https://platform.openai.com/api-keys
2. Confirm the repository Actions secret `OPENAI_API_KEY` exists. The user reports that it has been added; never read, print, or share its value.
3. In **Settings → Actions → General → Workflow permissions**, enable **Allow GitHub Actions to create and approve pull requests** if it is disabled.
4. After the Ubuntu 24.04 compatibility fix is on `main`, trigger a fresh run with a new `babel/dispatch-*` marker push or use **Actions → Babel AI continuation → Run workflow** on `main`.
5. Confirm the API project has available quota, then verify the Codex prompt executes, independent path/deletion validation passes, full unittest discovery passes, and the dedicated branch/PR is created or updated.

ChatGPT subscription access is not itself an API key. OpenAI API usage is billed separately under the API platform account. Set appropriate API usage limits/budget alerts in the OpenAI platform before enabling recurring runs.

## First-run failure, runner fix, and API quota blocker

The first ChatGPT-triggered push run is [#42181953313](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42181953313). Preflight succeeded; the Codex action failed before the prompt ran while trying to restrict `/run/dbus/system_bus_socket` on the GitHub-hosted Ubuntu 26.04 image selected by `ubuntu-latest`. The same failure is tracked upstream in [openai/codex-action issue #188](https://github.com/openai/codex-action/issues/188). The agent job is now pinned to `ubuntu-24.04`; `drop-sudo` remains enabled.

The second run, [#42183337573](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42183337573), passed preflight and successfully completed the `drop-sudo` socket-restriction step on Ubuntu 24.04. Codex then returned **`Quota exceeded. Check your plan and billing details.`** Validation and publishing were skipped; no patch, continuation branch, or PR was produced. This proves the runner workaround, but not the agent task or publishing pipeline.

**Current action:** no Codex execution is authorized. Do not manually dispatch or retry. The workflow file still declares a six-hour schedule, manual dispatch, and push trigger; repository-level enabled/disabled state is unverified. The owner must confirm that the workflow is disabled in GitHub Actions if scheduled API execution is not wanted, or explicitly reauthorize a separate workflow change. Do not use `status: complete` as a pause mechanism. The active ChatGPT Buddy path is independent and uses the connected GitHub app.

## Recovery and operations

- **Latest work:** the historical Codex branch is `babel/agent-progress`; it is separate from the current ChatGPT Buddy branch `babel/chatgpt-buddy-v2` and draft PR #201.
- **Latest execution:** the last verified Codex attempts are #42181953313 and #42183337573. No later Codex execution was independently verified in this audit.
- **Resume:** only after explicit user reauthorization and owner confirmation of the repository-level workflow state. Do not manually dispatch while authorization is absent. The YAML's scheduled trigger remains present in source.
- **Interrupted run:** no progress is assumed unless it was committed to the legacy branch. Reconcile current main and the legacy branch before any reauthorized continuation.
- **No changes:** the workflow reports a no-op; it does not create empty commits.
- **Out-of-scope patch or failed tests:** the publisher fails without pushing. Do not retry without reauthorization.
- **Completion:** the exact `status: complete` sentinel stops continuation at preflight; the agent is also skipped when `OPENAI_API_KEY` is absent. This audit did not inspect the secret value or verify its presence. A no-op is not completion, and the sentinel must not be used as a pause switch.

This historical workflow used a separate proposal branch and did not reopen the active ChatGPT browser conversation. It is an independent Codex agent operating from repository state, not the current Buddy task.

## Source files

- Workflow: .github/workflows/babel-ai-continuation.yml
- Agent instructions: .github/babel/CONTINUATION_PROMPT.md
- Durable stop/recovery state: project/BABEL_AGENT_STATE.md
- Workflow catalogue: WORKFLOWS.md
- Canonical Babel contract: BABEL.md

## Verification status

Daily curator run [#42183307146](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42183307146) passed full unittest discovery (**478 tests**) on commit `ffc75f5796d422d6f3bcd889465a00f0c613a57e`; public security scan [#42183307047](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42183307047) also passed on that commit. These are historical repository checks, not proof of a successful Codex run. The first Codex attempt failed on Ubuntu 26.04; the second reached Codex on Ubuntu 24.04 but was blocked by API quota. No successful Codex task, independent validation, or isolated Codex PR publication is verified. Repository-level workflow enablement is unconfirmed; do not assume this historical workflow is disabled.
