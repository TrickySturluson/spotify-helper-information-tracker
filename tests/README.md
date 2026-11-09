# SHIT Test Suite

The `tests/` directory contains the Python unittest suite protecting historical analytics, canonical music Library contracts, metadata enrichment, discovery, playlist intelligence and safety, Tricky Daily behavior, compatibility, and documentation continuity.

## Run tests

From the repository root, run `python -m unittest discover -s tests -t . -v`.

For focused checks, run `python -m unittest tests.test_documentation_contract -v` or `python -m unittest tests.test_script_layout -v`.

## Test families

- **Documentation and repository layout:** `test_documentation_contract.py` checks required control documents, all goal workspace roadmaps/READMEs/action logs, the assistant entry point, domain navigation, indexing of every `docs/` guide, local Markdown links, workflow catalogue coverage, Great Migration issue/manual-dispatch allowlists, metadata-enrichment budget alignment, Reference Library schedule alignment, Tricky Daily force/idempotency policy, sensitive workflow trigger boundaries, documentation-only next actions in paused goal roadmaps, and workflow file overviews.
  - It also checks the committed-tree inventory against the current handoff; separates Spotify playlist-snapshot evidence from listening history; protects MusicLibrary resolver/sequencer and Great Migration audit/index-rebuild write boundaries; verifies track-profile canonical Library writes and legacy-versus-backup-protected migration paths; and checks Great Migration secret-rotation persistence boundaries and truthful workflow labels.
  - `test_script_layout.py` checks compatibility delegation, bottom-of-file overview coverage, non-boilerplate implementation/test-module summaries, and compatibility references to maintained source files.
- **Library integrity:** migration, schema, identity confidence, health, maintenance, and freshness tests.
- **Metadata and discovery:** provider enrichment, recording identity, acoustic descriptors, lyrics, mood inference, and candidate ingestion.
- **Playlist intelligence:** fit scoring, feedback calibration, previews, sequencing, discovery, and removal feedback.
- **Tricky Daily:** cycle scheduling and force/idempotency, durable ordered stage hashing/commit/read-back, same-date pending-stage guard, repository-head concurrency checks, pre-write live snapshot/lock/blacklist rechecks, exact post-write order/count/uniqueness/blacklist validation, ambiguous Spotify write reconciliation, no-write stage-only mode, feedback scoring, playlist generation, read-only preflight/snapshot/catalog/index refresh, and maintained-source import precedence.
- **Spotify operations:** playlist management, reference-library synchronization, descriptions, and playback observations. `test_spotify_auth_health_workflow.py` protects the commit-status auth-check latch, Retry-After handling, failure classification, token redaction, and no-playlist-write boundary.

Test filenames provide the detailed inventory. Use the relevant workstream roadmap and action log to understand why a behavior is protected and what live verification remains necessary.

## Evidence and safety

Passing unit tests demonstrate tested code behavior only. They do not prove provider authentication, a successful live Spotify write, a scheduled workflow's operational health, or correctness of remote state. Record those separately with exact workflow/run/read-back evidence. Tests should use fixtures or mocks for external side effects unless a test explicitly documents a safe read-only integration.

## File overview

This guide explains test ownership, standard commands, major test families, and the distinction between unit-test success and live operational verification.
