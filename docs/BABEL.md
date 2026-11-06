# SHIT Documentation & Continuity
> **Internal codename: Babel**

## What this is

**SHIT Documentation & Continuity** is the repository's documentation, knowledge-preservation, and project-continuity system. Its internal codename is **Babel**.

The descriptive name is the default public-facing name because a first-time reader should immediately understand the system's purpose. “Babel” is a concise internal name used after this definition has been read.

This document is the canonical explanation of the name and the system's responsibilities. Do not rename the repository or the parent SHIT product to Babel.

## Mission

Make Spotify Helper & Information Tracker (SHIT) understandable, maintainable, auditable, and independently continuable by a developer or AI assistant who has no access to previous conversations.

The repository—not chat history—is the durable source of truth. Babel makes that source of truth navigable, explicit, evidence-based, and safe to continue.

## Naming rules

- **Parent product/repository:** Spotify Helper & Information Tracker (SHIT).
- **Public-facing documentation-system name:** SHIT Documentation & Continuity.
- **Internal codename:** Babel.
- **First reference in a fresh document or session:** “SHIT Documentation & Continuity (internal codename: Babel).”
- **Later references:** “Babel” is acceptable after the relationship has been established.
- **Navigation and first-contact headings:** prefer the descriptive name. Do not use “Babel” alone as a heading or link label when a reader may not yet know what it means.
- **Scope boundary:** Babel is the documentation/continuity system, not a separate music feature, runtime service, playlist, data provider, or replacement name for SHIT.

## Responsibilities

Babel maintains and connects:

1. **Repository orientation:** entry points, architecture, directory and file inventories, ownership, and navigation.
2. **Independent workstream roadmaps:** each major project has its own ROADMAP, README, and ACTIONS record.
3. **Current handoff:** one authoritative next-work record that names the active priority, blockers, and next executable action.
4. **Decision history:** preserve requirements, constraints, rationale, reversals, and rejected approaches.
5. **Operational contracts:** document inputs, outputs, dependencies, permissions, credentials by name only, network calls, writes, side effects, limits, retries, recovery, and verification.
6. **Evidence and status:** distinguish planned, implemented, merged, deployed, and verified; attach exact test, workflow, commit, PR, or read-back evidence.
7. **Cross-project dependencies:** show how workstreams and shared data/contracts depend on one another.
8. **Fresh-session continuity:** enable a new assistant to resume safely without asking the user to reconstruct prior decisions.
9. **Continuous maintenance:** update affected documentation in the same session as meaningful implementation, testing, failure, decision, or status changes.

## Required operating structure

The following repository documents are the primary continuity path:

1. [Repository instructions](../AGENTS.md) — mandatory rules for every assistant and contributor.
2. [Documentation rules](../project/DOCUMENTATION_RULES.md) — required reading and same-session maintenance contract.
3. [Current handoff](../project/NEXT_WORK.md) — active priority, blockers, and next executable action.
4. [Loose-ends register](../project/LOOSE_ENDS.md) — unresolved cross-workstream work and verification gaps.
5. [Project roadmap](../project/ROADMAP.md) — cross-workstream priorities and dependencies.
6. [Project log](../project/PROJECT_LOG.md) — chronological milestone and decision history.
7. [Goal index](../project/goals/README.md) — independent workstream workspaces.
8. [Documentation index](README.md) — technical guides, inventories, and runbooks.

Every major workstream must maintain:
- `ROADMAP.md`: purpose, requirements, constraints, verified status, milestones, open tasks, acceptance criteria, blockers, and next action.
- `README.md`: scope, architecture, invariants, dependencies, links, and resume instructions.
- `ACTIONS.md`: dated history of changes, decisions, commands, tests, outcomes, failures, and evidence.

## Operating constraints

- **Documentation-first means no unsupported claims.** A file existing or a test passing does not prove its prose is accurate.
- **No silent uncertainty.** Mark stale, partial, unverified, inferred, blocked, or unknown information explicitly.
- **No invented implementation.** Keep planned proposals separate from code on main, open PRs, deployed behavior, and live verification.
- **No lost history.** Preserve failures and consequential decisions when they prevent repeated mistakes.
- **No unsafe side effects.** Documentation work must not casually trigger provider requests, generated-data writers, or Spotify playlist operations. Inspect workflow path filters before editing workflow files; comment-only workflow edits may still trigger jobs.
- **No secret disclosure.** Document credential names and setup requirements, never credential values, tokens, or private keys.
- **No prose in machine data.** Keep explanations in Markdown or supported code overviews, not canonical/generated JSON or other machine-readable records.
- **No feature work during the documentation gate.** The user's current instruction is to finish the documentation and fresh-session audit before resuming unrelated feature development or playlist operations.

## Definition of success

Babel is ready for independent continuation only when the Maintainability & Documentation roadmap's acceptance criteria have been met with evidence, including:

- Every indexed goal has a current ROADMAP, README, and ACTIONS file.
- Maintained source, tests, workflows, schemas, data contracts, and operational state owners are inventoried accurately.
- Per-file overviews and technical guides are semantically checked against current implementation, not merely present.
- Important operational contracts explain side effects, permissions, safety boundaries, failures, retries, recovery, and verification.
- Cross-project roadmaps, handoff, loose ends, and open PR/workflow evidence are reconciled.
- Automated checks cover meaningful documentation invariants without brittle boilerplate.
- A fresh-session simulation can follow the documented entry path, identify the active priority and exact next action, and preserve all safety constraints without relying on chat history.

Until then, report the documentation system as **in progress** and state the remaining audit gaps. Do not declare Babel complete based on the naming change or structural coverage alone.
