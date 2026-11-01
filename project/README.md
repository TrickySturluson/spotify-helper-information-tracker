# SHIT Project Control Center

This folder is the human-readable control desk for ongoing work on **Spotify Helper & Information Tracker (SHIT)**.

It is deliberately separate from `assistant_data/music/library/`: project plans and notes are not music records, provider evidence, or listening history.

## Files

- [PROJECT_LOG.md](PROJECT_LOG.md) — chronological record of meaningful work, decisions, tests, failures, and handoffs.
- [NEXT_WORK.md](NEXT_WORK.md) — current priorities, active work, blockers, and the next concrete actions.
- [RETRY_QUEUE_SPEC.md](RETRY_QUEUE_SPEC.md) — contract for the machine-maintained metadata retry queue.

## Operating rules

1. Update the log when a meaningful task starts, reaches a milestone, is verified, or is blocked. Record dates, affected paths/workflows, evidence, and links to commits/PRs/runs where available.
2. Keep `NEXT_WORK.md` current so a new session can resume without reconstructing the entire conversation.
3. The retry queue is a worklist, not a source of truth. Canonical song/artist/album records and provider-specific lookup state remain authoritative.
4. Never treat a timeout, rate limit, provider outage, or malformed response as a definitive “not found”.
5. Do not retry before provider-specific cooldowns expire. Respect request budgets, cache successful results, and avoid repeating known negative lookups until their retry policy permits it.
6. Keep recommendations and candidate discoveries distinct from confirmed listening history and explicit user preferences.
7. Do not put credentials, tokens, or private account data in project notes.
8. Keep entries concise and append-only where practical. Correct mistakes with a dated clarification rather than silently rewriting history.

## Where data belongs

- Human plans and progress: `project/`
- Canonical music entities and evidence: `assistant_data/music/library/`
- Generated lookup/retry state: `assistant_data/music/` (machine-managed files)
- Historical listening archive: `data/scrobbles.json`
- Playlist snapshots and controls: their existing playlist data paths

The project log should link to detailed workflow output rather than copying large logs into Git.
