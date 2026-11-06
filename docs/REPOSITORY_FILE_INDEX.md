# SHIT Repository File & Data-Family Index

**Purpose:** explain where maintained code, control documents, workflows, canonical records, generated outputs, and operational state live. This is a navigational catalogue, not a frozen dump of every generated record path. A complete committed-tree inventory was verified on the documentation audit branch using directory-scoped GitHub Git Trees API requests; the measured snapshot and method are recorded below. In a local checkout, `git ls-files` remains the simplest way to regenerate the current path list.

## Repository entry points

- `AGENTS.md` — mandatory instructions for assistant/contributor sessions.
- `README.md` — project overview and setup/navigation entry point.
- `shit.py` — command-line interface for Library and project operations.
- `sitecustomize.py` — compatibility import-path bootstrap.
- `.gitignore`, `.gitleaks.toml`, `requirements-audio-analysis.txt` — repository hygiene, secret scanning policy, and optional local audio-analysis dependencies.
- `playlist_removed_tracks.json`, `playlist_removal_baseline.json` — playlist-removal feedback/baseline state; use their owning playlist tooling and documentation, not casual manual edits.

## Maintained source and test code

| Path | Ownership and contents | Documentation contract |
|---|---|---|
| `scripts/analytics/` | Last.fm archive analytics, aggregate builders, playback analytics, project audit | `scripts/README.md`; each maintained Python file has a bottom `FILE OVERVIEW` |
| `scripts/lastfm/` | Canonical Last.fm scrobble importer | Same per-file overview rule |
| `scripts/music/` | Music Library, migration, enrichment, provenance, audio/mood, lyrics, health and freshness | Same per-file overview rule plus relevant `docs/` guide and goal roadmap |
| `scripts/spotify/` | Playlist manager, Daily, discovery, sequencing, feedback, playback and reference-library operations | Same per-file overview rule plus relevant operational guide and goal roadmap |
| `compat/` | Legacy CLI/import shims delegating to `scripts/` | `compat/README.md`; each maintained launcher has a bottom overview naming its canonical implementation |
| `tests/` | Python unittest regression suite | `tests/README.md`; each test module has a bottom overview |
| `sitecustomize.py` and `shit.py` | Root-level import bootstrap and CLI entry point | Bottom file overview and linked operational documentation |

## Complete committed-tree inventory snapshot — 2026-11-06

**Audited commit:** `7cc839f3f00eeb026cd898099654eea8f9a79497` (documentation branch `docs/semantic-documentation-audit`).

The inventory was assembled from the root Contents listing and directory-scoped Git Trees API requests for every top-level directory. The large `assistant_data/music/` tree was queried separately from its sibling families. Every queried subtree returned `truncated=false`; all root entries and all immediate `assistant_data/` entries were included. This avoids the 100,000-entry truncation encountered by a single recursive root-tree request.

| Repository area | Committed files | Notes |
|---|---:|---|
| Root-level files | 9 | README, AGENTS, CLI/bootstrap, config, removal state and optional requirements |
| `.github/` | 23 | Includes all 17 workflow YAMLs, test triggers and persisted manager/cooldown state |
| `compat/` | 42 | 40 Python compatibility launchers, README and package marker |
| `data/` | 4 | Canonical Last.fm archive, metadata/statistics and README |
| `docs/` | 22 | 21 technical guides plus documentation index |
| `playback_data/` | 2 | README and empty-directory marker; local tracker observations are optional |
| `project/` | 50 | Control-centre files, 13 goal workspaces and supporting specifications |
| `scripts/` | 61 | 55 maintained implementation modules, five package markers and README |
| `tests/` | 46 | 44 test modules, package marker and README |
| `assistant_data/` | 27,902 | Generated analytics, canonical Library, profiles, snapshots and state |
| **Total** | **28,161** | Complete committed file/blob entries at the audited commit |

### Generated-data family detail

| `assistant_data/` family | Files |
|---|---:|
| Root-level files | 5 |
| `advanced/` | 8 |
| `indexes/` | 1 |
| `months/` | 43 |
| `music/` | 27,680 |
| `playback/` | 6 |
| `rankings/` | 3 |
| `recommendations/` | 8 |
| `spotify/` | 144 |
| `years/` | 4 |
| **Total** | **27,902** |

The `assistant_data/music/` subtree contains 27,680 files and 27,641 directories; 27,676 of those files are JSON records and four are Markdown guides. These generated/canonical records are documented by schema, provenance, family and owning writer—not by thousands of individual prose entries. The `assistant_data/spotify/` subtree contains 144 files, including 143 JSON files and one Markdown guide.

### Maintained-code coverage

- `scripts/analytics/`: 7 implementation modules.
- `scripts/lastfm/`: 1 implementation module.
- `scripts/music/`: 28 implementation modules.
- `scripts/spotify/`: 19 implementation modules.
- `compat/`: 40 compatibility launchers.
- `tests/`: 44 test modules.
- `.github/workflows/`: 17 workflows.
- `docs/`: 21 technical guides plus the index.
- `project/goals/`: 13 workspaces; each contains ROADMAP.md, README.md and ACTIONS.md.

**Scope and freshness:** this is a complete committed-tree inventory for the stated commit, not a claim that future commits cannot add/remove files. Refresh the snapshot after significant structural changes. The tree count includes generated JSON records, configuration/state files and documentation blobs; it does not count directories as files.
 
## Automation and repository state

| Path | Contents | Ownership / safety |
|---|---|---|
| `.github/workflows/` | Scheduled, manual, push and PR automation | Each YAML workflow has a bottom `FILE OVERVIEW`; workflows should call maintained scripts rather than duplicate business logic |
| `.github/README.md` | Workflow and state directory guide | Read before changing automation or persisted state |
| `.github/spotify_playlist_manager_state.json` | Playlist-manager locks and persisted operation state | Update through owning manager/workflow only |
| `.github/spotify_playlist_manager_audit.jsonl` | Append-oriented operation audit history | Append through owning tooling; preserve history |
| `.github/spotify_api_cooldown.json` | Spotify Retry-After cooldown state | Managed by Spotify API tooling; do not clear to bypass cooldowns |
| `.github/test-triggers/` | Explicit test/live-cycle trigger payloads | Follow workflow preflight and authorization requirements |

## Canonical and derived data

| Path | Data role | Source of truth / regeneration |
|---|---|---|
| `data/scrobbles.json` | Chronological Last.fm scrobble archive | Canonical historical listening record; do not replace with Spotify tracker observations |
| `data/metadata.json`, `data/stats.json` | Archive metadata and summary | Maintained by Last.fm ingestion and analytics builders |
| `data/README.md` | Archive semantics, provenance and maintenance | Read before changing the canonical archive format |
| `assistant_data/` | Generated historical analytics, indexes, monthly/advanced aggregates and manifests | Rebuild with documented analytics builders; not the canonical raw archive |
| `assistant_data/music/library/` | Canonical structured music Library with artist, album and song records, indexes and migration report | Use Library CLI/migration/sync tools and documented schemas; do not hand-edit records or bypass provenance/identity safeguards |
| `assistant_data/music/` outside `library/` | Generated metadata profiles, indexes, manifests, coverage summaries and enrichment caches | Rebuild/update through the documented music metadata pipeline |
| `assistant_data/spotify/` | Playlist references, generated recommendations, feedback, descriptions and playlist-specific state; reference snapshots also feed canonical Library playlist-source and playability evidence | Use the owning Spotify tools; distinguish snapshots and generated outputs from live Spotify state |
| `assistant_data/playback/` | Derived analytics from measured Spotify playback | Optional prospective observations; not interchangeable with Last.fm scrobbles; coverage gaps must remain explicit |
| `playback_data/` | Optional local playback-tracker observations | Local measurement source; may be absent in cloud runs and must not be treated as complete history |
| `playlist_removed_tracks.json` and `assistant_data/spotify/daily_feedback.json` | User feedback signals | Preserve provenance and use owning feedback/reconciliation tools |

## Documentation and control centre

- `project/DOCUMENTATION_RULES.md` — mandatory maintenance process and evidence/status vocabulary.
- `project/NEXT_WORK.md` — current cross-project handoff and next executable action.
- `project/LOOSE_ENDS.md` — unresolved tasks, blockers and verification gaps.
- `project/PROJECT_LOG.md` — major milestone and decision history.
- `project/ROADMAP.md` — cross-workstream priorities and dependencies.
- `project/goals/<goal>/ROADMAP.md`, `README.md`, `ACTIONS.md` — required independent plan, design/scope, and evidence history for every major goal.
- `docs/README.md` — navigation index for technical and operational guides.
- `docs/CODE_DOCUMENTATION.md` — per-file documentation standard and automated enforcement.

## Find the exact current tracked inventory

Run from the repository root:

- `git ls-files` — every tracked path, including generated Library records.
- `git ls-files '*.py'` — all tracked Python modules, scripts, launchers and tests.
- `git ls-files '.github/workflows/*'` — all tracked GitHub Actions workflows.
- `find assistant_data/music/library -name '*.json' -type f` — inspect individual structured Library records.
- `python -m unittest tests.test_script_layout tests.test_documentation_contract -v` — verify file-overview coverage and the repository documentation contract.

## Maintenance rules

1. Update this guide when top-level architecture, data ownership, or directory responsibilities change.
2. Do not enumerate every generated song/artist JSON record here; document its schema, identity rules, provenance, and owning writer in the Library guides and manifests.
3. Keep Last.fm scrobbles, measured Spotify playback, sourced provider metadata, inferred features, user feedback, and live playlist state distinct.
4. Never hand-edit generated records or machine state when an owning writer exists.
5. Treat the Git tree as the current path inventory; a documentation entry does not prove the file still exists or behaves as described.
