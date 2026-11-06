# SHIT Documentation Index

This index is the navigation map for **Spotify Helper & Information Tracker (SHIT)**. It is written for contributors and assistant sessions that have no access to previous conversations.

## Start here

1. [Repository instructions](../AGENTS.md) — mandatory rules for assistants and contributors.
2. [Documentation rules](../project/DOCUMENTATION_RULES.md) — required reading, maintenance standard, evidence vocabulary, and handoff checklist.
3. [Current handoff](../project/NEXT_WORK.md) — active task, blockers, priorities, and next concrete action.
4. [Loose-ends register](../project/LOOSE_ENDS.md) — cross-project unfinished work and verification gaps.
5. [Project roadmap](../project/ROADMAP.md) — cross-workstream plan and dependencies.
6. [Project log](../project/PROJECT_LOG.md) — chronological milestone and decision history.
7. [Goal index](../project/goals/README.md) — each workstream's ROADMAP, README, and ACTIONS.

## Documentation families

| Location | What belongs there |
|---|---|
| `project/` | Human-maintained plans, roadmaps, handoffs, decisions, action histories, blockers |
| `project/goals/<goal>/` | Independent workstream ROADMAP, README, ACTIONS, technical contracts and runbooks |
| `docs/` | Cross-cutting architecture, operational guides, security/privacy, file indexes and technical references |
| `scripts/` and subdirectories | Maintained implementation; per-file overview should identify purpose and operational contract |
| `.github/` | GitHub Actions workflows, templates and automation configuration; see [GitHub guide](../.github/README.md) |
| `data/` | Canonical Last.fm archive and source-data documentation |
| `assistant_data/` | Generated query indexes, playlist snapshots, music metadata and recommendation outputs; rebuild through documented generators |
| `playback_data/` | Optional locally measured playback observations; coverage gaps must remain explicit |

## Cross-cutting technical references

- [Repository file index](REPOSITORY_FILE_INDEX.md) — tracked file and directory inventory.
- [Public repository privacy](PUBLIC_REPOSITORY_PRIVACY.md) — public data inventory, credential boundaries, and audit scope.
- [Spotify API operations](SPOTIFY_API_OPERATIONS.md) — Spotify authentication, API behavior, and cloud-operation constraints.
- [Automatic playlist descriptions](AUTOMATIC_PLAYLIST_DESCRIPTIONS.md) — generated-description ownership, safeguards, and rollout.
- [Tricky Daily cycle](TRICKY_DAILY_CYCLE.md) — cycle behavior, schedule, recovery, description rotation and preflight.
- [Tricky Daily backlog](TRICKY_DAILY_TODO.md) — prioritized future improvements; unchecked items are not implemented.
- [Playlist reference guide](../assistant_data/spotify/PLAYLIST_REFERENCE_GUIDE.md) — canonical playlist roles and reference update rules.

## Workstream roadmaps

The [goal index](../project/goals/README.md) links all current goal workspaces. Each goal must maintain three files:
- `ROADMAP.md` for plans, status, milestones, acceptance criteria and next action.
- `README.md` for scope, architecture, decisions and constraints.
- `ACTIONS.md` for dated evidence, implementation history, failures and verification.

## Automated documentation checks

- [Documentation contract tests](../tests/test_documentation_contract.py) verify required repository control documents, all goal workspace ROADMAP/README/ACTIONS files, the root assistant instructions, major domain coverage in this index, and local links from the main fresh-session entry points.
- [Script layout tests](../tests/test_script_layout.py) verify implementation/compatibility layout and bottom-of-file overview coverage for maintained Python and workflow files.
- [Test suite guide](../tests/README.md) explains test families, commands, and the limits of unit-test evidence.
- Both checks are part of the standard unittest discovery suite; the main scheduled/manual update workflow runs that suite before publishing refreshed data.

## Maintenance contract

When a file, workflow, schema, data contract, or operational behavior changes, update its file overview or adjacent documentation and the relevant workstream records in the same session. Update this index when documentation is added, moved, renamed, or retired. Never put explanatory prose into machine-readable data files. Never treat an index entry as proof that the referenced implementation is current; inspect the source and latest workflow evidence.

For the full mandatory process, see [DOCUMENTATION_RULES.md](../project/DOCUMENTATION_RULES.md).
