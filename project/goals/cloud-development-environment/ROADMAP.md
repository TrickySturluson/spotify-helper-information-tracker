# Cloud Development Environment — Roadmap

**Status:** Initial repository configuration and runbook prepared on a feature branch; Codespace provisioning and user-side launch are not yet verified. ChatGPT terminal access is not available through the current GitHub connection.
**Priority:** Supporting infrastructure for SHIT-wide authentication development and ongoing maintenance.

## Goal

Make SHIT development reproducible in GitHub Codespaces without depending on the user's personal computer, while preserving a strict boundary between development and production operations.

## Requirements

1. Provide a repository-defined devcontainer with supported Python and Node.js versions.
2. Keep setup reproducible and avoid executing arbitrary package lifecycle scripts during initial dependency installation.
3. Provide GitHub CLI and editor support for repository development.
4. Validate the devcontainer configuration and relevant isolated tests in GitHub Actions.
5. Keep production Spotify, GitHub App, and Cloudflare credentials out of Codespaces.
6. Preserve feature-branch/PR development and existing playlist/auth safeguards.
7. Clearly distinguish repository/CI access from an actual interactive terminal connection.
8. Never require a Codespace for scheduled authentication, Daily, playlist, or Library workflows.
9. Evaluate a future terminal integration only if a supported, permission-scoped interface exists; do not build an arbitrary remote-shell endpoint.

## Milestones

### M0 — Define safe development environment
- [x] Create .devcontainer/devcontainer.json with Python 3.11, Node.js 22, GitHub CLI, and VS Code extensions.
- [x] Install pinned auth-broker dependencies with lifecycle scripts disabled.
- [x] Document setup, safe checks, credential restrictions, and current ChatGPT access limitation.
- [ ] Confirm Codespaces is enabled and create a Codespace on a feature branch.
- [ ] Run Python and broker test suites inside the Codespace and record exact results.

### M1 — CI verification
- [x] Add a read-only workflow to validate devcontainer JSON and assert production secret names are not injected.
- [x] Run the isolated auth-broker test suite in CI without production credentials.
- [ ] Obtain a green run for the new workflow and full repository PR checks.
- [ ] Verify devcontainer configuration with the official Dev Containers CLI or an actual Codespaces provision.

### M2 — Practical ChatGPT development loop
- [x] Document the existing GitHub repository/PR/Actions evidence loop and its limits.
- [ ] Verify the current GitHub integration can read new CI evidence and update feature branches/PRs reliably.
- [ ] If a supported terminal connection becomes available, assess its identity, scope, command allowlist, logs, timeouts, and secret isolation.
- [ ] Do not create a public or unauthenticated arbitrary command-execution bridge.

### M3 — Auth and operations integration
- [ ] Complete Authentication Management & Recovery workstream's shared refresh-token coordination design.
- [ ] Keep production auth recovery independent of Codespaces uptime.
- [ ] Confirm development tooling cannot unlock or mutate playlists.

## Acceptance criteria

- A contributor can create the Codespace from the repository and run the documented checks.
- The environment installs pinned dependencies and has no production credentials by default.
- CI validates configuration and broker tests without provider credentials or write permissions.
- Documentation clearly states that Codespaces availability does not imply ChatGPT terminal access.
- Auth recovery and scheduled SHIT operations continue independently of Codespaces.
