# Codespaces Development Environment

## Purpose

SHIT uses GitHub Codespaces as an optional, reproducible cloud development environment. It is a development and testing convenience—not a production runtime dependency, authentication broker, Spotify authorization mechanism, or playlist-control plane.

The repository's .devcontainer/devcontainer.json defines the supported baseline: Python 3.11, Node.js 22, GitHub CLI, and the repository's pinned auth-broker dependencies. The Codespaces environment is deliberately provisioned without Spotify, GitHub App, or Cloudflare production credentials.

## What this enables

- A consistent Linux development shell without relying on the user's personal computer.
- Python and Node.js development for SHIT's existing code and auth broker.
- Running repository unit tests, broker security tests, syntax checks, and read-only diagnostics.
- Branch-based edits, commits, and pull requests using the Codespace's repository-scoped GitHub identity.
- Reproducible configuration validation in GitHub Actions through the Codespaces devcontainer check workflow.

## What this does not enable

- ChatGPT does not receive a live terminal merely because a Codespace exists.
- The connected GitHub integration can read and write repository content, branches, commits, pull requests, and Actions evidence where permitted; it does not expose an interactive Codespaces terminal or arbitrary command execution.
- Codespaces does not provide a supported secure channel for sending production credentials to ChatGPT.
- A Codespace is not required for scheduled SHIT operations. GitHub Actions and the managed auth broker remain the cloud execution plane.
- A green devcontainer CI job validates configuration and broker tests; it does not prove a Codespace was actually provisioned or that ChatGPT has terminal access.

## Create a Codespace

1. Open the SHIT repository on GitHub.
2. Select Code → Codespaces → Create codespace on the feature branch you intend to work on (normally a reviewed feature branch, not main).
3. Wait for the devcontainer to finish creating. Its post-create step installs the pinned broker dependencies with lifecycle scripts disabled.
4. Open a terminal in the Codespace and run the checks below.

If the devcontainer is not offered, verify that .devcontainer/devcontainer.json exists on the selected branch and that Codespaces is enabled for the repository/account.

## Safe development checks

Run from the repository root:

    python --version
    node --version
    gh auth status
    python -m unittest discover -s tests -t . -v
    npm test --prefix auth-broker

The full Python test suite and broker tests are local development checks. CI independently runs the relevant checks on pull requests. Do not treat a command as successful unless its exit status and output confirm success.

For read-only SHIT diagnostics, use the specific command documented by the owning workstream. Do not run provider-facing or write-capable workflows merely to test the environment.

## Credential and side-effect policy

- Do not add Spotify refresh tokens, Spotify client secrets, GitHub App private keys, Cloudflare API tokens, or equivalent production credentials as Codespaces secrets.
- Do not paste secrets into terminal output, shell history, issues, commits, artifacts, or ChatGPT.
- Use the minimum repository-scoped Codespaces/GitHub permissions needed for branch work. Review any requested permission expansion before granting it.
- Keep Spotify OAuth and refresh-token handling in the managed auth system. Keep Cloudflare deployment in its owner-gated, manually dispatched workflow.
- Codespaces work must use feature branches and pull requests. Never use it to bypass playlist locks, staging, snapshots, confirmation, audit, or read-back.
- Avoid launching workflows with provider calls or repository/playlist writes unless the owning workstream explicitly authorizes that operation.

## Relationship to Authentication Management & Recovery

Codespaces helps develop and test the auth system; it does not perform production reauthorization. The intended separation is:

1. Authentication Manager: monitors Spotify auth, safely refreshes and persists rotated tokens, and presents an owner-consent link only when Spotify requires fresh authorization.
2. Development Environment: Codespaces provides a reproducible place to edit and test code; GitHub Actions provides repeatable CI evidence.
3. SHIT Operations: Daily, playlist manager, Library and migration workflows consume the shared authentication health contract while retaining their own permissions and safety controls.

A future shared refresh-token single-flight mechanism must live in SHIT's cloud execution/auth architecture. It must not depend on a Codespace remaining online.

## Current access limitation and future integration

The current ChatGPT GitHub connection does not expose Codespaces creation, terminal attachment, or arbitrary command execution. Repository changes and CI evidence can still be exchanged through feature branches, pull requests, and GitHub Actions. This is useful but is not equivalent to direct ChatGPT terminal access.

If a supported, permission-scoped terminal integration becomes available, evaluate it separately. Any bridge must authenticate workloads with short-lived, narrowly scoped identity; validate repository, branch, command, and execution limits server-side; avoid passing production secrets; log command metadata without sensitive output; and never provide a route to playlist writes or production deployment. Do not implement a public command-execution endpoint or accept arbitrary shell commands from untrusted pull-request content.

## Resume instructions

A fresh contributor should read:

1. Repository instructions (AGENTS.md).
2. Current handoff (project/NEXT_WORK.md).
3. Cloud Development Environment roadmap (project/goals/cloud-development-environment/ROADMAP.md).
4. Authentication Management & Recovery (project/goals/mobile-cloud-operation/README.md).
5. Workflow catalogue (docs/WORKFLOWS.md).
