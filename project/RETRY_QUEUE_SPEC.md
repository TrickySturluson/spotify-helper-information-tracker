# Metadata Retry Queue — Design Contract

The retry queue is a generated operational worklist for unresolved metadata. It is not a second copy of the music catalogue and must never override canonical Library records.

## Intended location

`assistant_data/music/retry_queue.json`

Keep the generator/reporting code under `scripts/music/`. The queue is rebuildable from canonical song records and provider lookup state. It may retain manual pin/hold annotations only if those annotations are stored separately and merged explicitly.

## One item per recording and provider

A recording can have several independent provider tasks. Do not collapse all providers into one global status: a MusicBrainz miss does not imply a Last.fm miss, and a transient Discogs error does not mean the recording does not exist.

Recommended shape:

```json
{
  "schema_version": 1,
  "generated_at": "2026-11-01T00:00:00Z",
  "source": {
    "library_manifest": "assistant_data/music/library/manifest.json",
    "provider_state": [
      "assistant_data/music/musicbrainz_id_lookup_state.json"
    ]
  },
  "summary": {
    "recordings": 0,
    "provider_tasks": 0,
    "eligible_now": 0,
    "cooldown": 0,
    "transient_failures": 0,
    "definitive_not_found": 0
  },
  "items": [
    {
      "recording_id": "recording-id",
      "artist": "Artist",
      "title": "Track",
      "provider": "musicbrainz",
      "needed": ["recording_mbid"],
      "status": "retry_wait",
      "attempt_count": 1,
      "last_attempt_at": "2026-11-01T00:00:00Z",
      "next_retry_at": "2026-11-02T00:00:00Z",
      "reason": "temporary provider failure",
      "priority": {
        "all_time_plays": 0,
        "recent_plays": 0,
        "score": 0
      },
      "evidence": [],
      "confidence": "unknown"
    }
  ]
}
```

This is an illustrative schema, not live queue content. Empty/unknown values must remain explicit; never fabricate dates, counts, IDs, or provider results.

## Status vocabulary

- `eligible`: missing useful data and eligible for a bounded lookup now.
- `retry_wait`: transient failure or policy cooldown; not yet eligible.
- `not_found`: provider gave a definitive negative result for this exact query/identity. Retry only under an explicit expiry or identity-change policy.
- `ambiguous`: multiple plausible matches; requires stronger identifiers or review, not repeated fuzzy searching.
- `complete`: requested field is already supported by trusted evidence.
- `blocked`: provider unavailable, credentials missing, unsupported endpoint, or policy prevents lookup.
- `invalid`: malformed local record or identity; repair locally before provider requests.

## Required safeguards

- Preserve provider-specific status and cooldowns from the existing checkpoint/state files.
- Distinguish not-found from timeout, rate-limit, authentication, server, parse, and network failures.
- Never make provider requests while generating a report/preview.
- The execution worker must apply per-provider batch caps, pacing, concurrency limits, and request budgets.
- Successful results must be merged through the canonical Library writer with provenance and confidence.
- Re-running the planner must not reset attempt counts or make a cooling-down task eligible.
- Use Last.fm play counts for prioritization; use recent plays as a freshness signal. Recommendations may inform a separate candidate-interest score, but never populate play counts.
- Keep one failed provider task from blocking independent providers for the same recording.
- Record a stable task key (recording ID + provider + requested data family) to make queue generation idempotent.
- A final audit must reconcile queue state with the canonical Library and provider checkpoints.

## Implementation sequence

1. Validate real canonical record and checkpoint schemas.
2. Build a read-only planner that emits the queue deterministically.
3. Add unit tests for negative-cache vs transient failures, cooldowns, duplicate prevention, missing credentials, malformed records, and no-write/no-network behavior.
4. Add a bounded executor only after the planner is verified.
5. Publish queue state without racing other generated-data writers.
