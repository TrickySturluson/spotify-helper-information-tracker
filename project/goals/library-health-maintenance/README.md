# Library Health Checker & Data Maintainer
> **Roadmap:** [ROADMAP.md](ROADMAP.md) is the durable plan and next-action reference. Read it before work; update it and [ACTIONS.md](ACTIONS.md) in the same session as implementation, testing, decisions, or blockers.
> **Current repository priority:** This workstream is paused for feature implementation while SHIT's documentation audit is active. Only documentation corrections and evidence reconciliation are permitted. Preserve this roadmap; resume its feature next actions only when the [central handoff](../../NEXT_WORK.md) and Maintainability & Documentation roadmap explicitly say documentation is complete.


## Goal

Keep the canonical per-recording Library structurally sound, internally consistent, retrievable, and recoverable as it grows. Health checks must detect problems without silently changing data; maintenance must repair only safe, deterministic issues and preserve evidence.

## Components

1. **Read-only health checker**
   - Validate JSON parsing, schema/version expectations, required identity fields, stable IDs, shard paths, file/index agreement, alias targets, duplicate aliases, and artist/album/song relationships.
   - Detect orphaned files, missing referenced files, dangling relationship paths, malformed evidence/provenance, impossible values, inconsistent timestamps, and stale derived indexes.
   - Compare canonical records with source manifests/counts without assuming all source rows must resolve to a unique recording.
   - Report severity, affected entity IDs/paths, concise reason, safe remediation, and whether the issue blocks sorter use.
   - Produce machine-readable JSON plus concise human-readable output; exit nonzero for configured blocking errors.

2. **Data maintainer**
   - Separate diagnosis from mutation. Default mode is report/preview only.
   - Safe automated repairs may rebuild derived indexes from canonical records, normalize deterministic serialization, repair missing non-authoritative cache files, and re-establish directory/manifest metadata.
   - Never guess identities, merge ambiguous songs, overwrite stronger evidence with weaker evidence, invent missing metadata, erase provenance, or resolve contradictory provider values by arbitrary precedence.
   - Every write requires a timestamped backup, atomic replacement, idempotent behavior, and before/after audit. Keep a repair journal with changed paths, reason, old/new hashes, and tool version.
   - Quarantine malformed or conflicting records for human review; never delete them automatically.
   - No Spotify playlist writes and no provider calls in the local repair phase.

## Health dimensions

- **Integrity:** files parse and match schema.
- **Referential integrity:** all index and relationship pointers resolve.
- **Identity safety:** aliases are unique or explicitly candidate lists; ambiguous matches remain ambiguous.
- **Evidence quality:** field values retain source, observation time, confidence, and provider status.
- **Coverage:** known missing fields are counted without treating unknown as invalid.
- **Freshness:** assessed separately by field/provider policy (see [Metadata Freshness](../metadata-freshness/README.md)).
- **Playback availability:** assessed separately and market-scoped (see [Spotify Playability](../spotify-playability/README.md)).

## Proposed commands

- `python shit.py library health` — read-only comprehensive report.
- `python shit.py library maintain` — preview safe repairs by default.
- `python shit.py library maintain --apply` — apply only allow-listed deterministic repairs after backup.
- `python shit.py library maintain --apply --repair-index` — explicit derived-index repair.

The `maintain` command is implemented in PR #80. Its first repair scope is deliberately limited to rebuilding `library_index.json`; it requires `--apply --repair-index`, proves existing aliases are reconstructable, creates a timestamped backup, performs atomic replacement, and runs a post-repair health check with rollback on failure. It does not repair song/artist/album records.

## Acceptance criteria

- A read-only health run never writes files or makes network requests.
- A maintenance preview never writes files or makes network requests.
- Applying safe repairs is idempotent and backup-protected.
- Deliberately malformed, orphaned, duplicate, ambiguous, and dangling-reference fixtures are detected with actionable diagnostics.
- The health report clearly distinguishes blocking errors, warnings, unknown fields, stale fields, and provider-unavailable states.
- No repair can silently change song identity or Spotify playlist state.

## Current status

**Read-only health checker merged in PR #73.** `scripts/music/library_health.py` scans JSON records, stable IDs/shards, index targets, aliases, and entity relationships without constructing `MusicLibrary` (whose constructor can rebuild/write an index). The CLI exposes `python shit.py library health [--json]`. CI ran it against the full published catalogue: 13,005 songs, 6,386 artists, 7,861 albums, zero errors and zero warnings. The safe derived-index maintainer was merged in [PR #80](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/80). Its tests cover read-only preview, explicit apply, backup creation, missing-index recovery, and refusal when aliases would be lost. A full-catalogue preview on issue #85 passed: 13,005 songs, 6,386 artists, 7,861 albums; zero health errors/warnings; all existing aliases reconstructable; no repair needed; zero writes. PR #87 also extends the health scan to validate present Spotify playability observations: status/raw boolean consistency, checked timestamps, market/latest-map agreement, requested IDs, and relinked identity continuity. Missing playability is allowed; malformed present evidence is reported. Broader record repair, evidence normalization, and repair-journal support remain out of scope until separately designed and tested.



**Weekly monitoring:** `.github/workflows/library-freshness-review.yml` now runs a read-only maintenance preview alongside health, confidence, and freshness checks every Sunday at 09:17 UTC. The preview is validated as `mode=preview`, `changed=false`, zero provider requests, and zero playlist writes, then preserved in the 30-day report artifact. It never auto-applies repairs. A full-catalogue preview on issue #85 found no repair necessary; issue #92 confirmed the merged playability semantic checks pass across the current song records.

## Resume

Read [ACTIONS.md](ACTIONS.md), inspect the merged index-only repair implementation, and validate it against a disposable copy of the full catalogue before any real repair. Keep future record/evidence repairs separately scoped.
