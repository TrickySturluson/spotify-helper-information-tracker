# SHIT Documentation Index

**SHIT Documentation & Continuity** is the public-facing name of this documentation system. Its internal codename is **Babel**. Read [BABEL.md](BABEL.md) for the naming convention, purpose, scope, and operating contract.

This index is the navigation map for **Spotify Helper & Information Tracker (SHIT)**. It is written for contributors and assistant sessions that have no access to previous conversations.

## Start here

1. [Documentation-system identity and purpose](BABEL.md) — public name, internal codename, scope, and continuity contract.
2. [AI continuation worker](BABEL_AGENT.md) — scheduled Codex worker, branch/PR publishing, security boundaries, activation and recovery.
3. [Repository instructions](../AGENTS.md) — mandatory rules for assistants and contributors.
4. [Documentation rules](../project/DOCUMENTATION_RULES.md) — required reading, maintenance standard, evidence vocabulary, and handoff checklist.
5. [Current handoff](../project/NEXT_WORK.md) — active task, blockers, priorities, and next concrete action.
6. [Loose-ends register](../project/LOOSE_ENDS.md) — cross-project unfinished work and verification gaps.
7. [Project roadmap](../project/ROADMAP.md) — cross-workstream plan and dependencies.
8. [Project log](../project/PROJECT_LOG.md) — chronological milestone and decision history.
9. [Goal index](../project/goals/README.md) — each workstream's ROADMAP, README, and ACTIONS.

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

## Technical and operational guide catalogue

Every maintained guide in `docs/` is listed below. Use the workstream roadmap and action log alongside these technical references; a guide explains a contract, while the roadmap records its current implementation status.

### Repository, privacy and operations

- [Repository file index](REPOSITORY_FILE_INDEX.md) — maintained code, workflows, data families, source-of-truth boundaries and verified inventory method.
- [Code documentation standard](CODE_DOCUMENTATION.md) — file overviews, module docstrings, inline documentation and automated enforcement.
- [Public repository privacy](PUBLIC_REPOSITORY_PRIVACY.md) — published personal data, secret boundaries and repository exposure risks.
- [Spotify API operations](SPOTIFY_API_OPERATIONS.md) — authentication, permissions, API behavior, token handling and cloud-operation constraints.
- [GitHub Actions workflow catalogue](WORKFLOWS.md) — all 18 workflows, triggers, permissions, credentials, writes and operational boundaries.
- [Great Migration guide](GREAT_MIGRATION.md) — canonical Library migration, validation, backup, publication and recovery.

### Canonical Library, identity and metadata

- [Per-recording music Library](PER_RECORDING_MUSIC_LIBRARY.md) — artist/album/song entities, identity resolution, aliases, provenance, evidence and canonical storage.
- [Album metadata and lookup confidence](ALBUM_METADATA_AND_LOOKUP_CONFIDENCE.md) — exact album identity, release context, provider evidence and confidence boundaries.
- [Automated audio metadata](AUTOMATED_AUDIO_METADATA.md) — provider enrichment, duration/tag/profile jobs, limits, caches and retry behavior.
- [Recent-track enrichment](RECENT_TRACK_ENRICHMENT.md) — rolling recent-top-track selection and bounded priority enrichment.
- [Track mood evidence](TRACK_MOOD_EVIDENCE.md) — track-level mood/theme evidence, source distinctions and confidence rules.
- [GetSongBPM integration](GETSONGBPM.md) — optional tempo/key fallback, exact-match requirements and credential handling.
- [Audio analysis](AUDIO_ANALYSIS.md) — local audio feature extraction, supported inputs, outputs and operational constraints.
- [Audio mood models](AUDIO_MOOD_MODELS.md) — optional DEAM/Essentia inference, model provenance, license and confidence limitations.
- [Lyrics library](LYRICS_LIBRARY.md) — transient lyric lookup, local metadata storage, phrase fingerprints and copyright boundaries.

### Playlist intelligence, feedback and sequencing

- [Automatic playlist descriptions](AUTOMATIC_PLAYLIST_DESCRIPTIONS.md) — description ownership, preservation of manual text, safeguards and rollout.
- [Playlist feedback calibration](PLAYLIST_FEEDBACK_CALIBRATION.md) — immutable fit predictions, explicit feedback, calibration diagnostics and separation from Daily learning.
- [Transition scoring](TRANSITION_SCORING.md) — evidence-aware adjacent-track scoring, missing-data handling and journey construction.
- [Booze or Boos! sorting](BOOZE_OR_BOOS_SORT.md) — Halloween playlist goals, fit requirements, evidence gates and safe sequencing.
- [Tricky Daily cycle](TRICKY_DAILY_CYCLE.md) — cycle behavior, Eastern-time schedule, recovery, description rotation and live preflight.
- [Tricky Daily backlog](TRICKY_DAILY_TODO.md) — prioritized future improvements; unchecked items are not implemented.

### Spotify reference data

- [Playlist reference guide](../assistant_data/spotify/PLAYLIST_REFERENCE_GUIDE.md) — canonical playlist roles, snapshot semantics and reference update rules.

## Workstream roadmaps

Tricky Daily now has its own dedicated [roadmap, scope guide and action history](../project/goals/tricky-daily/ROADMAP.md), alongside the broader Playlist Intelligence & Safety workstream. The ordering engine also has an independent [Playlist Sequencing roadmap](../project/goals/playlist-sequencing/ROADMAP.md), separating transition quality and journey controls from recommendation fit. This keeps both active systems independently resumable.

The [goal index](../project/goals/README.md) links all current goal workspaces. Each goal must maintain three files:
- `ROADMAP.md` for plans, status, milestones, acceptance criteria and next action.
- `README.md` for scope, architecture, decisions and constraints.
- `ACTIONS.md` for dated evidence, implementation history, failures and verification.

## Automated documentation checks

- [Documentation contract tests](../tests/test_documentation_contract.py) verify required repository control documents, all goal workspace ROADMAP/README/ACTIONS files, the root assistant instructions, major domain coverage, Babel identity and local links from the main fresh-session entry points.
- [Script layout tests](../tests/test_script_layout.py) verify implementation/compatibility layout, bottom-of-file overview coverage, and known generic-placeholder rejection across maintained Python and workflow files.
- [Test suite guide](../tests/README.md) explains test families, commands, and the limits of unit-test evidence.
- Both checks are part of the standard unittest discovery suite; the main scheduled/manual update workflow runs that suite before publishing refreshed data.

## Maintenance contract

When a file, workflow, schema, data contract, or operational behavior changes, update its file overview or adjacent documentation and the relevant workstream records in the same session. Update this index when documentation is added, moved, renamed, or retired. Never put explanatory prose into machine-readable data files. Never treat an index entry as proof that the referenced implementation is current; inspect the source and latest workflow evidence.

For the full mandatory process, see [DOCUMENTATION_RULES.md](../project/DOCUMENTATION_RULES.md).
