# SHIT Repository File & Data-Family Index

**Purpose:** explain where maintained code, control documents, workflows, canonical records, generated outputs, and operational state live. This is a navigational catalogue, not a frozen dump of every generated record path. The canonical current inventory is the Git tree (`git ls-files`); generated Library records are intentionally described by their path conventions rather than copied into this document one-by-one.

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

**Snapshot commit:** `3d2c1ded8dfb44b92e6e0c086673c69350200edc` (after the successful metadata-enrichment publication).

The recursive root-tree response was not used because generated Library records make it too large. The inventory was counted from a non-recursive root tree and one recursive Git Trees request for each of its nine top-level directories. The root and every directory-scoped response returned `truncated=false`. Counts below are Git tree blobs (files), not directory/tree objects.

| Location | File/blob entries |
|---|---:|
| Repository root | 9 |
| `.github/` | 23 |
| `assistant_data/` | 27,981 |
| `compat/` | 42 |
| `data/` | 4 |
| `docs/` | 23 |
| `playback_data/` | 2 |
| `project/` | 50 |
| `scripts/` | 61 |
| `tests/` | 46 |
| **Total** | **28,241** |

The `assistant_data/` subtree contained 55,770 tree entries: 27,981 file blobs and 27,789 directory/tree objects. This is why the recursive root request was truncated; the directory-scoped inventory completed without truncation.

The maintained-code subtrees contain 55 Python implementation modules under `scripts/` (60 Python files including five package initializers), 40 compatibility launchers (41 Python files including the package initializer), 44 test modules (45 Python files including the package initializer), and 17 workflow YAML files. The `docs/` subtree contains 21 technical guides plus `README.md` and `BABEL.md`; `project/` contains 13 goal workspaces.

This snapshot satisfies the committed-tree inventory requirement for the stated commit. Refresh it after structural or generated-data changes; do not treat the counts as timeless. In a complete checkout, `git ls-files` remains the simplest repeatable current inventory.

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
| `assistant_data/spotify/` | Playlist references, generated recommendations, feedback, descriptions and playlist-specific state | Use the owning Spotify tools; distinguish snapshots and generated outputs from live Spotify state |
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
