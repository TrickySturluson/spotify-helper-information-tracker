# Cloud Development Environment

## Purpose

Provide SHIT with a reproducible, repository-defined cloud development environment so development and testing do not depend on the user's personal computer. GitHub Codespaces is the initial environment; GitHub Actions remains the repeatable CI and validation plane.

## Scope

This workstream owns the repository devcontainer configuration, Codespaces setup and safe-use instructions, reproducible Python 3.11 and Node.js 22 tooling, secret-free validation, and a documented boundary between ChatGPT repository access and interactive terminal access.

It does not own production Spotify authentication, playlist operations, canonical Library data, Cloudflare deployment, or production secrets. Those remain with their existing SHIT workstreams.

## Architecture

- .devcontainer/devcontainer.json defines the Codespaces image, language runtimes, GitHub CLI, editor extensions, and safe post-create dependency installation.
- .github/workflows/codespaces-devcontainer-check.yml validates the configuration and runs isolated broker tests without production credentials.
- docs/operations/codespaces-development.md is the user/developer runbook.
- Feature branches and pull requests are the publication path.

## Important limitation

A Codespace is not automatically accessible to ChatGPT. The currently connected GitHub interface supports repository and Actions operations but not an interactive Codespaces terminal. This workstream does not claim or create direct terminal access. A future terminal bridge requires a separately reviewed, supported integration and must not expose arbitrary shell execution or production credentials.

## Security invariants

1. No Spotify refresh/access token, Spotify client secret, GitHub App private key, Cloudflare API token, or other production secret is provisioned in the devcontainer.
2. No production provider requests, playlist writes, secret writes, or Worker deployments are part of environment creation or CI.
3. Development changes happen on feature branches and are reviewed through pull requests.
4. Tests and diagnostics are explicitly selected; Codespace creation must not launch operational workflows.
5. The Codespace is disposable and never a source of truth for repository state.

## Resume

Read the roadmap, action log, and Codespaces runbook. Verify the current Codespaces availability and GitHub connection capabilities before claiming terminal access.
