# Library Health Checker & Data Maintainer

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

Names/flags are proposals until implemented and tested. Existing `status` and `audit` commands remain supported.

## Acceptance criteria

- A read-only health run never writes files or makes network requests.
- A maintenance preview never writes files or makes network requests.
- Applying safe repairs is idempotent and backup-protected.
- Deliberately malformed, orphaned, duplicate, ambiguous, and dangling-reference fixtures are detected with actionable diagnostics.
- The health report clearly distinguishes blocking errors, warnings, unknown fields, stale fields, and provider-unavailable states.
- No repair can silently change song identity or Spotify playlist state.

## Current status

**Read-only health checker implemented on draft branch; CI pending.** `scripts/music/library_health.py` scans JSON records, stable IDs/shards, index targets, aliases, and entity relationships without constructing `MusicLibrary` (whose constructor can rebuild/write an index). The CLI exposes `python shit.py library health [--json]`. A separate safe maintainer/repair workflow is still only specified and must not be conflated with this read-only checker.

## Resume

Read [ACTIONS.md](ACTIONS.md), inspect `scripts/music/music_library.py` and `scripts/music/library_cli.py`, then design the report schema and fixture-based tests before wiring commands into the CLI.
