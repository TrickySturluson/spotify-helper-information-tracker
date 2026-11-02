## 2026-11-01 — Goal workspaces merged and project-wide loose ends audited

- **Goal:** make each project objective independently recallable and ensure unfinished requirements from repository history and prior SHIT conversations are not lost.
- **Work:** merged PR #67 (squash) as `4ad701c2c4f36b9f6f73926e83db1f84cbfbcc2c`; added seven goal workspaces with README/ACTIONS histories. Added `project/LOOSE_ENDS.md` as the cross-project audit index and updated each goal action log with verified findings, failed checks, constraints and next steps.
- **Verification:** PR #67 `tests` passed; `Scan complete Git history for secrets` passed. Documentation-only; no canonical Library records, provider checkpoints, listening history or Spotify playlists modified.
- **Newly recorded:** run #17 publication recovery; PR #65 unit-test failure; PR #60 unit-test and secret-scan failures; duration analytics checklist; provider gaps; recommendation/deep-cut requirements; Booze or Boos! sequence preview and live-count discrepancy; per-file documentation coverage; shared generated-data publication concurrency.
- **Important distinction:** PR #60 and #65 are still open and their failures are not diagnosed. The retry queue remains a specification. Great Migration run #17 remains unpublished/unverified until artifact inspection, fresh audit and publication checks.
- **Next action:** inspect Great Migration run #17 artifact and backup; keep playlist writes paused until migration recovery is complete.
- **References:** PR #67 https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/67; PR #60 https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/60; PR #65 https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/65; run #17 https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41357689889

# SHIT Project Log

## 2026-11-01 — Per-goal workspaces established

- **Goal:** make individual project objectives independently recallable without loading unrelated history.
- **Work:** added `project/goals/` index and seven goal workspaces: Great Migration, Library Enrichment, Metadata Coverage & Retries, Discovery & Recommendations, Listening Analytics, Playlist Intelligence, and Maintainability & Documentation. Each contains a `README.md` for scope/design/status/resume instructions and an `ACTIONS.md` for dated work, verification, and next actions.
- **Central workflow:** updated project control-centre guidance and session handoff to direct new sessions to the relevant goal folder and require action-log updates after meaningful work.
- **Verification:** files created on branch `codex/goal-workspaces`; links and completeness must be checked before merge. Documentation-only change; no Library records, provider state, listening history, or playlists modified.
- **Outcome:** pending PR/merge and link verification.
- **Next action:** verify all 15 goal files and links, then merge documentation change.


Chronological handoff record for substantial project work. New entries go at the top, newest first. Record verified outcomes, not intentions as completed work.

## 2026-11-01 — Continuity system and consolidated project goals

- **Goal:** make the repository, rather than cross-chat memory, the durable source of truth for project decisions, active work, test evidence, blockers, and next actions.
- **Work completed in this branch:** created the `project/` control-centre structure with a project index, chronological log, current handoff, and retry-queue design contract. Expanded `NEXT_WORK.md` to capture migration recovery, bounded enrichment, provider retry semantics, recommendation/discovery ingestion, playlist intelligence/safety, and documentation requirements.
- **Files:** `project/README.md`, `project/PROJECT_LOG.md`, `project/NEXT_WORK.md`, `project/RETRY_QUEUE_SPEC.md`.
- **Migration status:** Great Migration run #17 failed during Git rebase/publication. Publication and final verification remain unconfirmed. Do not treat counts from a generated artifact as published Library state. Inspect the artifact, backup, and run logs before retrying or reconciling generated files.
- **Run reference:** https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41357689889
- **Related open work:** PR #65 proposes a read-only coverage planner; PR #60 proposes recommendation intake with evidence separation. Both require CI/code verification before being treated as complete.
- **Verification:** documentation changes only. No canonical Library records, provider checkpoints, listening history, or Spotify playlists were modified by this documentation work. Retry queue is a specification only; no queue was generated or executed.
- **Outcome:** partial — continuity documentation is prepared on the PR branch; not yet merged into `main`.
- **Next action:** inspect Great Migration run #17 artifacts and audit result; then continue with the next-work priorities.

## 2026-11-01 — Project control centre proposed

- **Goal:** establish one durable place to track work completed, work in progress, next steps, blockers, and metadata that needs another provider lookup.
- **Changes proposed:** add `project/NEXT_WORK.md`, this log, and a retry-queue specification; keep the machine-maintained retry queue beside music metadata state, not inside the canonical Library records.
- **Safety:** project notes are separate from music data; retry entries must preserve the distinction between definitive negative results and transient/provider failures.
- **Verification:** documentation structure only at this stage. The retry queue still needs an implementation that builds it from canonical records and provider checkpoints.
- **Related work:** read-only Library coverage planner is proposed in PR #65: https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/65
- **Migration note:** Great Migration run #17 failed in the Git publish/rebase stage. Its output artifact and backup must be inspected before attempting recovery or another write-heavy migration. Run: https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41357689889

## Entry template

### YYYY-MM-DD — Short task name
- **Goal:**
- **Work completed:**
- **Files/workflows affected:**
- **Verification:**
- **Outcome:** complete / partial / blocked
- **Next action:**
- **References:** PRs, commits, workflow runs, issues


## 2026-11-02 — GitHub-hosted, PC-independent product requirement

- **User direction:** SHIT is intended to be a feature-rich conversational ChatGPT–Spotify experience that remains available with the user's PC powered off. GitHub is to remain the central project and operations home; local-PC development is not to be used unless explicitly requested.
- **Documentation:** added the target architecture, central source-of-truth rules, PC-independence acceptance criteria, and current OAuth/token synchronization gap to the Spotify operations guide and project control center.
- **Verified current boundary:** the playlist-control workflow runs on GitHub Actions. The manager's OAuth callback still uses `127.0.0.1:8888`, and optional playback tracking depends on a local process; these are setup/local-only limits and must not be represented as always-on cloud features.
- **Decision:** use GitHub branches, pull requests, and Actions as the canonical path for code and remote operations. Treat the local token file as a cache only, never as the Actions credential source of truth. Do not build on the user's PC unless explicitly requested.
