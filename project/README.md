# SHIT Project Control Center
> **Mandatory:** Follow [DOCUMENTATION_RULES.md](DOCUMENTATION_RULES.md) for every task. Every goal must maintain `ROADMAP.md`, `README.md`, and `ACTIONS.md`; update documentation in the same session as implementation or verification. Do not rely on chat history.

This folder is the human-readable control desk and durable memory for ongoing work on **Spotify Helper & Information Tracker (SHIT)**. The repository is the source of truth for project plans and decisions; chat history is not.

It is deliberately separate from `assistant_data/music/library/`: project plans and notes are not music records, provider evidence, or listening history.

## Architecture direction: GitHub-hosted and PC-independent

The product goal is a feature-rich conversational ChatGPT–Spotify experience that continues to operate when the user's PC is off. GitHub is the canonical home for this repository's source, operational configuration, durable workflow state, and documentation; GitHub Actions or another managed service runs supported jobs. Local PowerShell sessions, checkouts, and token caches are not part of normal runtime.

Current GitHub issue commands and Actions workflows provide a remote playlist-control path. Do not represent the broader ChatGPT-to-SHIT feature surface as complete until each feature has a verified GitHub-hosted execution path and a verified user-facing integration. Optional features that inherently poll a personal device must be migrated to a cloud-accessible source or clearly marked local-only.

See [GitHub-hosted operation requirements](../docs/SPOTIFY_API_OPERATIONS.md#product-requirement-github-hosted-and-pc-independent-operation) for source-of-truth rules, acceptance criteria, and the current OAuth setup gap. Code and documentation changes should be made on GitHub branches and pull requests; use a local clone only when the user explicitly requests local work.

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
- [GitHub-hosted operation requirements](../docs/SPOTIFY_API_OPERATIONS.md#product-requirement-github-hosted-and-pc-independent-operation) — PC-independent runtime, centralized state, and OAuth/token setup boundaries.

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
