## 2026-11-06 — Documentation audit uncovered workflow publication defects

- **Context:** while documenting workflow YAMLs, comment-only commits to four push-path-triggered workflows started their configured automation. This was unintended; the workflow guide now explicitly warns that YAML comments still match path filters.
- **Verified repository effect:** Reference Library run #42146148971 refreshed snapshots/removal state and committed 249 files (184 Library records, 63 Spotify snapshot/history files, 2 removal-state files). It made no Spotify playlist writes.
- **Failures:** Enrich Music Metadata run #42146121471 could not rebase its generated song records over the simultaneous Reference Library additions (add/add conflicts), so its enrichment output was not published. Acoustic Metadata Enrichment run #42146097964 completed 100 batches (2,500 IDs; 207 found; 2,293 misses; 322 total profiles; 3,678 negative-cache entries) but could not commit because an optional GetSongBPM state file was absent and was unconditionally included in `git add`.
- **Update Last.fm History:** run #42146153098 completed its provider/data steps but failed publication during rebase of commit `137fab61`, with 120 unique conflicts (59 music Library paths and 61 Spotify snapshot/reference paths). Its generated Last.fm/analytics/enrichment workspace output was not published.
- **Lesson:** documentation-only workflow edits must be staged with their push-trigger consequences understood. No workflow repair or additional enrichment was undertaken; remediation is deferred until the documentation-only priority is complete.
- **References:** [Reference Library run #42146148971](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42146148971), [Enrich Music Metadata run #42146121471](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42146121471), [Acoustic Metadata run #42146097964](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42146097964), [Update Last.fm run #42146153098](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42146153098).

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


## 2026-11-05 — Mandatory roadmap and documentation-maintenance standard

- **User direction:** every project/workstream must have a durable roadmap specifically so a future assistant can reference plans without previous chat knowledge. Documentation must always be maintained and must explicitly instruct future assistants to keep it current.
- **Work completed:** added `project/DOCUMENTATION_RULES.md`; created `ROADMAP.md` for all 11 existing goal workspaces; updated repository/project entry points and the goal index to make the standard mandatory.
- **Required structure:** each goal maintains `ROADMAP.md` (plan/status/next action/acceptance criteria), `README.md` (scope/design/invariants), and `ACTIONS.md` (dated implementation and verification evidence). Central `NEXT_WORK.md`, `LOOSE_ENDS.md`, and `PROJECT_LOG.md` remain the repository-level continuity records.
- **Operating rule:** read the relevant roadmap before work and update documentation in the same session as implementation, testing, failures, decisions, or blockers. Never leave project knowledge only in chat; never claim planned work is implemented or a merged change is operationally verified without evidence.
- **Verification:** documentation-only changes. Roadmap files were created for all 11 indexed goal folders; index and entry-point updates link to the rules and roadmaps. No code, Library data, provider state, listening history, or Spotify playlists were changed.
- **Next action:** audit all goal folders for missing/stale `ACTIONS.md`/README files and reconcile each roadmap against latest main, open PRs, issues, and workflow runs. Then apply this standard to any new independent project/workstream.


## 2026-11-05 — Documentation control centre and active playlist workspaces expanded

- Added root AGENTS.md, docs/README.md, project/ROADMAP.md, automated documentation-contract tests, and a corrected source/data-family index after finding the prior exhaustive snapshot had become stale as the canonical music Library expanded.
- Added dedicated ROADMAP/README/ACTIONS workspaces for Tricky Daily and Playlist Sequencing so their independent user requirements, safety constraints, evidence and next actions survive chat boundaries.
- CI evidence: Daily curator tests #42143513931 passed on 7d23db6 (including documentation contract and directory guides); #42143770161 passed on 79af1f9 after the Daily workspace was added. Playlist Sequencing was added afterward and passed in Daily curator run #42143913729. A later run #42144349548 passed after adding the workflow catalogue and correcting the primary Markdown-link parser.
- No playlist writes, Library data changes, provider state changes, or listening-history changes were performed as part of this documentation work.
- Next: verify the latest CI run after the Playlist Sequencing workspace; then audit file-level overviews and reconcile all workstream roadmaps with current code/workflow evidence.
