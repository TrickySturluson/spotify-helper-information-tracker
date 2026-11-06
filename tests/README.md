# SHIT Test Suite

The `tests/` directory contains the Python unittest suite protecting historical analytics, canonical music Library contracts, metadata enrichment, discovery, playlist intelligence and safety, Tricky Daily behavior, compatibility, and documentation continuity.

## Run tests

From the repository root, run `python -m unittest discover -s tests -t . -v`.

For focused checks, run `python -m unittest tests.test_documentation_contract -v` or `python -m unittest tests.test_script_layout -v`.

## Test families

- **Documentation and repository layout:** `test_documentation_contract.py` checks required control documents, all goal workspace roadmaps/READMEs/action logs, the assistant entry point, domain navigation, local links from primary entry points, and complete listing of GitHub Actions workflows in docs/WORKFLOWS.md. `test_script_layout.py` checks compatibility delegation and bottom-of-file overview coverage.
- **Library integrity:** migration, schema, identity confidence, health, maintenance, and freshness tests.
- **Metadata and discovery:** provider enrichment, recording identity, acoustic descriptors, lyrics, mood inference, and candidate ingestion.
- **Playlist intelligence:** fit scoring, feedback calibration, previews, sequencing, discovery, and removal feedback.
- **Tricky Daily:** cycle scheduling, feedback scoring, playlist generation, and preflight safeguards.
- **Spotify operations:** playlist management, reference-library synchronization, descriptions, and playback observations.

Test filenames provide the detailed inventory. Use the relevant workstream roadmap and action log to understand why a behavior is protected and what live verification remains necessary.

## Evidence and safety

Passing unit tests demonstrate tested code behavior only. They do not prove provider authentication, a successful live Spotify write, a scheduled workflow's operational health, or correctness of remote state. Record those separately with exact workflow/run/read-back evidence. Tests should use fixtures or mocks for external side effects unless a test explicitly documents a safe read-only integration.

## File overview

This guide explains test ownership, standard commands, major test families, and the distinction between unit-test success and live operational verification.
