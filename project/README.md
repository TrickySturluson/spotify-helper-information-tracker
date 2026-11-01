# SHIT Project Control Center

This folder is the human-readable control desk and durable memory for ongoing work on **Spotify Helper & Information Tracker (SHIT)**. The repository is the source of truth for project plans and decisions; chat history is not.

It is deliberately separate from `assistant_data/music/library/`: project plans and notes are not music records, provider evidence, or listening history.

## Start here when resuming work

1. Read [NEXT_WORK.md](NEXT_WORK.md) first. It is the authoritative current handoff: active blocker, priorities, constraints, open work, and the next concrete action.
2. Read [LOOSE_ENDS.md](LOOSE_ENDS.md) for the cross-project unfinished-work and verification register.
3. Read [PROJECT_LOG.md](PROJECT_LOG.md) for chronological context and verified outcomes.
4. Read [RETRY_QUEUE_SPEC.md](RETRY_QUEUE_SPEC.md) before changing retry planning/execution.
5. Read the relevant [goal workspace index](goals/README.md) and that goal's `README.md` + `ACTIONS.md`.
6. Read the repository [README](../README.md) for architecture, canonical data locations, and commands.

A new assistant session should inspect these files and current GitHub branches, pull requests, and workflow runs before claiming a task is complete or starting a potentially destructive operation.

## Goal workspaces

Each major objective has its own folder under [`goals/`](goals/README.md). Read that goal's `README.md` for scope, decisions and current status, then `ACTIONS.md` for the dated implementation and verification history. This is the preferred way to recall a specific workstream without loading unrelated project history.

## Files

- [NEXT_WORK.md](NEXT_WORK.md) — current priorities, active work, blockers, and concrete next actions. Update this whenever status changes.
- [PROJECT_LOG.md](PROJECT_LOG.md) — chronological record of meaningful work, decisions, tests, failures, and handoffs.
- [LOOSE_ENDS.md](LOOSE_ENDS.md) — cross-project index of unfinished work, known failures, deferred requirements, and next verification steps.
- [RETRY_QUEUE_SPEC.md](RETRY_QUEUE_SPEC.md) — contract for the machine-maintained metadata retry queue.

## Project goals tracked here

- **Canonical music Library:** durable song/recording, artist, and album entities with reliable identity, provenance, confidence, relationships, and retrieval.
- **Migration and enrichment:** safely migrate existing data, verify publication and integrity, then maximize useful metadata through repeated bounded provider-aware passes.
- **Coverage and retries:** identify missing/weak fields, distinguish transient failures from definitive negatives, and retry only when eligible under provider-specific policies.
- **Discovery intake:** capture recommended/suggested songs and discovery context in the Library while keeping candidate interest separate from listening, scrobbles, likes, saves, and confirmed preferences.
- **Listening analytics:** preserve Last.fm scrobbles as historical source of truth; treat Spotify playback tracking as optional prospective evidence with coverage gaps.
- **Playlist intelligence:** improve sorting, discovery, and generated playlist curation while preserving explicit write authorization, locks, blacklists, deduplication, and audit trails.
- **Maintainability:** document every script/module's purpose, inputs/outputs, side effects, safety boundaries, and place in the system.

## Operating rules

1. Update the log when a meaningful task starts, reaches a milestone, is verified, or is blocked. Record dates, affected paths/workflows, evidence, and links to commits/PRs/runs where available.
2. Keep `NEXT_WORK.md` current so a new session can resume without reconstructing the entire conversation.
3. Record verified facts separately from plans, hypotheses, and unverified artifact output.
4. The retry queue is a worklist, not a source of truth. Canonical song/artist/album records and provider-specific lookup state remain authoritative.
5. Never treat a timeout, rate limit, provider outage, or malformed response as a definitive “not found”.
6. Do not retry before provider-specific cooldowns expire. Respect request budgets, cache successful results, and avoid repeating known negative lookups until their retry policy permits it.
7. Keep recommendations and candidate discoveries distinct from confirmed listening history and explicit user preferences.
8. Do not put credentials, tokens, or private account data in project notes.
9. Keep entries concise and append-only where practical. Correct mistakes with a dated clarification rather than silently rewriting history.

## Where data belongs

- Human plans and progress: `project/`
- Canonical music entities and evidence: `assistant_data/music/library/`
- Generated lookup/retry state: `assistant_data/music/` (machine-managed files)
- Historical listening archive: `data/scrobbles.json`
- Playlist snapshots and controls: their existing playlist data paths

The project log should link to detailed workflow output rather than copying large logs into Git. Update the handoff with exact tests/audits, whether changes are published or only in a branch/artifact, fresh counts with timestamps, remaining gaps, and the next concrete action.
