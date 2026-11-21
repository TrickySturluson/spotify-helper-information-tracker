# Trio Coordination — Scope & Design

## Purpose

Keep SHIT's three scheduled development workers operational during extended user absences through explicit readiness checks, reliable handoffs, and eventually tightly bounded recovery.

This is a coordination protocol, not a fourth worker. It does not change the product responsibilities of Buddy, Jockey, or Boots.

## Worker ownership

- **Buddy:** Babel documentation and continuity only.
- **Jockey:** the single current highest-priority implementation workstream.
- **Boots:** all other general engineering, excluding Buddy's documentation and Jockey's current priority.
- **ChatGPT technical lead / user:** assigns or changes priority, resolves owner-only gates, and authorizes any expansion of autonomous repair.

## Handoff sequence

Buddy checks Jockey; Jockey checks Boots; Boots checks Buddy. Each checks the live automation configuration, latest run, task prompt, environment/access evidence, relevant repository branch/PR state, CI and dependencies. A schedule being enabled is not sufficient evidence of readiness.

The canonical operating contract is [TRIO_COORDINATION_PROTOCOL.md](../../TRIO_COORDINATION_PROTOCOL.md).

## Safety model

Phase 1 is read-only with respect to another worker's task configuration and owned branch/PR. A worker may repair only issues within its own remit and existing permissions. It may diagnose another worker's blocker and provide an exact repair instruction, but cannot edit the other worker's prompt, schedule, environment, branch, or PR.

Phase 2 may add a small allowlist of reversible cross-repairs only after Phase 1 is verified and the user authorizes the expansion. Secrets, permissions, production configuration/deployment, provider writes, playlist/Library data, and another worker's branch/PR remain outside the repair boundary.

## Resume instructions

1. Read [the coordination roadmap](ROADMAP.md) and [the protocol](../../TRIO_COORDINATION_PROTOCOL.md).
2. Inspect all three current automation records and latest results; do not rely on this document for live status.
3. Inspect current main, open PRs, worker branches and exact-head checks.
4. Keep the handoff order and ownership boundaries intact.
5. Record each readiness result and blocker in the run report and update this goal's ACTIONS/ROADMAP when the protocol or its verification status changes.
