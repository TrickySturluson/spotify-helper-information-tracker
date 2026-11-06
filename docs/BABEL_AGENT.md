# SHIT Documentation & Continuity — AI continuation worker

> **Internal codename: Babel**

## Purpose and status

Babel has an optional repository-hosted AI worker that continues the documentation audit from GitHub rather than relying on a previous ChatGPT conversation. The worker is implemented in .github/workflows/babel-ai-continuation.yml and uses OpenAI's official openai/codex-action.

**Integration status:** repository configuration is committed. **Activation is pending** until the repository owner adds the OPENAI_API_KEY GitHub Actions secret and starts the first manual run. Do not describe the worker as operational before a successful run is observed.

## How continuation works

1. GitHub Actions starts on a six-hour UTC schedule or manual workflow_dispatch.
2. Preflight checks project/BABEL_AGENT_STATE.md. If it says status: complete, the workflow stops. Otherwise it selects the latest babel/agent-progress branch, falling back to main for the first run.
3. The Codex job reads AGENTS.md, the mandatory documentation rules, Babel guide, handoff, loose-ends register, project log, and the Maintainability & Documentation roadmap/README/ACTIONS. It chooses one high-priority unfinished documentation task and makes a bounded change, then returns a raw unified Git patch as its final output (or NO_CHANGES). The patch is capped at 700 KB to stay within the workflow handoff limit.
4. The agent job has contents: read, uses the Codex :workspace permission profile and drop-sudo safety strategy, and receives no Spotify or music-provider credentials. The workspace profile has no general network access; the preflight/publisher jobs handle branch selection and PR operations outside the model's workspace.
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
2. In the GitHub repository, open **Settings → Secrets and variables → Actions → New repository secret**.
3. Name the secret exactly OPENAI_API_KEY and paste the API key into GitHub's secret field. Do not put the key in a file, issue, commit, or ChatGPT message.
4. Open **Actions → Babel AI continuation → Run workflow** and start it on main.
5. In **Settings → Actions → General → Workflow permissions**, enable **Allow GitHub Actions to create and approve pull requests** if it is disabled.
6. Inspect the first run. Confirm the Codex job succeeds, the publisher's path validation and full unittest suite pass, and the dedicated branch/PR is created or updated.

ChatGPT subscription access is not itself an API key. OpenAI API usage is billed separately under the API platform account. Set appropriate API usage limits/budget alerts in the OpenAI platform before enabling recurring runs.

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

The repository baseline is green: Daily curator tests run #42178656402 passed full unittest discovery (**478 tests**) on commit 69e72829c6cc9e72837025f8c777b4d846c9ba7b. This verifies the repository test suite and documentation contracts, not the Codex continuation worker. No successful Babel AI continuation run has yet been observed. The API secret must be configured by the repository owner; do not mark activation complete until the first worker run and its resulting branch/PR are verified.
