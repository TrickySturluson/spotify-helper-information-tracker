## 2026-11-06 — Tricky Daily runtime correction and verification recovery

- **Authorization:** user authorized Daily runtime/test corrections, safe verification, and a Daily-only snapshot refresh. Live playlist replacement/description mutation remains separately gated and was not performed.
- **Runtime:** force now bypasses only the clock-window gate; the same-Eastern-date idempotency check is independent of force. Spotify description read-back HTML-unescapes provider text. The source overview and midnight workflow overview comments were corrected to match the implementation.
- **Documentation:** updated the Daily cycle guide, roadmap, TODO, workflow catalogue (including the 19th workflow), active-session brief, loose ends, project log, test guide, and workflow/test contract language.
- **Verification evidence:** full-suite runs found stale contract assertions and comments after the runtime change; they were corrected iteratively. The latest confirmed pre-comment-fix full suite #42260512826 failed only because the midnight workflow YAML still carried the old `--force` comment; commit 4cab258d8114571a7fbb49240069a82e74d1335c corrected it. A fresh post-fix full-suite result is still required. Read-only live preflight #42260095302 passed and reported 29 live Daily items.
- **Snapshot boundary:** snapshot-refresh run #42257653420 failed in its focused schedule test. Run #42261171958 passed focused tests and credential validation but failed at import time because `compat/spotify_listening_trends.py` shadowed the maintained implementation; it stopped before Spotify client construction or GET refresh. The last saved snapshot remains 37 items and is not a live read. The read-only preflight fetched 29 live items. The 47-entry Daily blacklist remains preserved.
- **Next:** obtain green full/focused CI, then run the GET-only Daily snapshot refresh and inspect reconciliation. Keep live playlist mutation disabled until all remaining P0 staging, race-detection, ambiguous-write, and post-write verification safeguards are complete and separately authorized.

## 2026-11-06 — Resumed parallel SHIT work while Babel continues

- **Decision:** resume explicitly authorized SHIT workstreams in parallel with SHIT Documentation & Continuity (Babel). Buddy remains documentation-only; ChatGPT owns active feature work and must keep each workstream's roadmap and action log current.
- **First workstream selected:** Tricky Daily. A read-only audit of current main source confirmed that `--force` bypasses the same-Eastern-date completion guard as well as the clock gate. The current test asserts the bypass, contradicting the required force-bypasses-clock-only contract. The saved 58-item snapshot remains historical evidence, not a live Spotify read.
- **Authorization boundary:** no runtime/test correction, provider request, generated-data write, or Spotify playlist operation has been performed. The Daily runtime/test correction awaits specific user authorization; live playlist writes remain separately gated.
- **Babel checkpoint:** today's Buddy run `a1354400-ad1c-8320-906e-888d071012ee` updated draft PR #163 (head `c8e4a2ad74b8c50868a6806abf9869b9da4b5725`). Independent review found a policy contradiction: the draft prohibits ChatGPT direct documentation publication to `main`, while current mainline rules authorize independently verified documentation-only publication. PR #163 remains draft and must not be merged until corrected. Its reported Daily curator tests #42239266411 and security scan #42239266381 both completed successfully; no PR reviews or inline threads were present.
- **Continuity updates:** active-session brief, Daily roadmap/action log, and current handoff were updated on main. No feature behavior changed.
- **Next action:** obtain authorization for the smallest Daily force/idempotency code and regression-test correction; continue Babel semantic audits in parallel.

## 2026-11-06 — Active-session brief established as a core continuity rule

- **Decision:** maintain `project/ACTIVE_SESSION_BRIEF.md` throughout active SHIT work as the curated context bridge from ChatGPT to Buddy. It records material decisions, current work, evidence, failures, blockers, and the next action; relevant goal roadmaps and action logs remain synchronized in the same session.
- **Privacy and timing:** the brief is not a raw chat dump and must exclude unrelated personal context and secret values. It is not real-time messaging; Buddy sees committed changes on a later run and cannot interrupt an active conversation.
- **Implementation:** created the brief and updated Buddy's startup prompt, root instructions, mandatory documentation rules, Babel agent guide, worker state, documentation roadmap/action log, and cross-project handoff. See `project/goals/maintainability-documentation/ACTIONS.md` for commit-level evidence.
- **Status:** documentation rule implemented on `main`; Buddy's first successful workflow run and cold-start simulation remain pending.

## 2026-11-06 — Babel AI continuation infrastructure added

- Integrated a scheduled OpenAI Codex worker through GitHub Actions so documentation continuation can resume from repository state rather than a prior ChatGPT conversation.
- The worker uses a six-hour schedule plus manual dispatch, resumes from a dedicated branch, and publishes only allowlisted documentation/test changes through a review PR after full unittest discovery. It does not auto-merge or receive Spotify/provider credentials.
- Activation remains pending on repository secret OPENAI_API_KEY and the GitHub Actions setting that permits workflow-created pull requests. First-run success is not yet verified.
- Operating guide: docs/BABEL_AGENT.md. Durable status: project/BABEL_AGENT_STATE.md.

## 2026-11-06 — Daily idempotency, Library side effects and workflow budgets documented

- Source audit confirmed a P0 Tricky Daily mismatch: `--force` bypasses both the clock gate and same-Eastern-date completion guard, although the intended contract is clock-gate bypass only. The current test codifies the broader behavior; runtime/test correction remains deferred during the documentation-only pause.
- The latest saved Daily snapshot is 58 accessible unique URIs at `2026-11-06T01:48:00.233040+00:00`, below the 60-track target; it is not a live read-back. The automatic post-write verification also does not prove exact ordered staged-payload equality.
- Corrected documentation for MusicLibrary resolver index-rebuild writes, read-only health boundaries, Great Migration token rotation and legacy migration backup limitations, Reference Library canonical evidence writes, playlist-only candidate semantics, Reference Library 06:13 UTC schedule and metadata enrichment budgets.
- Identified a stale generated `migration_report.json`: it still records 13,005 songs while the latest canonical Library audit reported 13,239. The README now labels it historical; no generated data was edited.
- Expanded documentation regression coverage with source-to-guide contracts, schedule/budget alignment, local Markdown links, all 12 paused roadmaps, inventory counts, and sensitive workflow boundaries. CI verification pending.

## 2026-11-06 — Documentation continuity, inventory and enrichment reconciliation

- **Babel:** reaffirmed SHIT Documentation & Continuity as the public name and Babel as its internal codename. The canonical guide and first-contact link are in `docs/BABEL.md`.
- **Goal roadmaps:** added an explicit documentation-only next action to all 12 non-documentation roadmaps while preserving each next feature action; corresponding ACTIONS logs record the pause.
- **Inventory:** verified 28,241 committed file/blob entries at main commit `3d2c1ded` using a non-recursive root Git Tree and nine recursive directory trees; every subtree returned `truncated=false`. `assistant_data/` contains 27,981 files. See `docs/REPOSITORY_FILE_INDEX.md`.
- **Overview guardrails:** 28 known generic/underspecified implementation overviews were corrected. The maintained inventory includes 55 implementation modules, 40 compatibility launchers, 44 test modules, 17 workflow YAMLs and 21 technical guides.
- **CI/security:** Daily curator run #42168520574 passed 460 tests on `8153028e`; full-history security scan #42168520598 passed on the same commit.
- **Workflow side effect reconciled:** Enrich Music Metadata run #42166959478 completed successfully and published generated-data commit `3d2c1ded`. It merged 195 discovery candidates into the canonical Library (13,239 songs), added 67 MusicBrainz duration matches from 182 lookups, and rebuilt metadata summaries/analytics. Duration coverage: 8,254/11,130 tracks and 139,758/152,005 scrobbles (91.9%). Artist profiles: 3,373 matched; track profiles with sourced tags: 229; matched album profiles: 905. Final audit: 9 checks, 18 warnings, 0 errors. Warnings: no captured playback intervals and 16 Spotify playlist snapshots with inaccessible item contents. No Spotify playlist writes occurred.
- **PR #161:** remains open/draft with 117 changed files. Its branch diverges from current main (571 ahead, 29 behind); it is an audit/reference source, not a safe merge candidate. Selectively port high-value tests and documentation after checking them against current source.
- **Status:** documentation remains the only active workstream. Semantic audit and fresh-session acceptance remain open.

## 2026-11-01 — Goal workspaces merged and project-wide loose ends audited

- **Goal:** make each project objective independently recallable and ensure unfinished requirements from repository history and prior SHIT conversations are not lost.
- **Work:** merged PR #67 (squash) as `4ad701c2c4f36b9f6f73926e83db1f84cbfbcc2c`; added seven goal workspaces with README/ACTIONS histories. Added `project/LOOSE_ENDS.md` as the cross-project audit index and updated each goal action log with verified findings, failed checks, constraints and next steps.
- **Verification:** PR #67 `tests` passed; `Scan complete Git history for secrets` passed. Documentation-only; no canonical Library records, provider checkpoints, listening history or Spotify playlists modified.
- **Newly recorded:** run #17 publication recovery; PR #65 unit-test failure; PR #60 unit-test and secret-scan failures; duration analytics checklist; provider gaps; recommendation/deep-cut requirements; Booze or Boos! sequence preview and live-count discrepancy; per-file documentation coverage; shared generated-data publication concurrency.
- **Important distinction:** PR #60 and #65 are still open and their failures are not diagnosed. The retry queue remains a specification. Great Migration run #17 remains unpublished/unverified until artifact inspection, fresh audit and publication checks.
- **Next action:** inspect Great Migration run #17 artifact and backup; keep playlist writes paused until migration recovery is complete.
- **References:** PR #67 https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/67; PR #60 https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/60; PR #65 https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/65; run #17 https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41357689889

# SHIT Project Log

## 2026-11-06 — Future SHIT-wide health system deferred until Babel completion

- **User direction:** once Babel is considered realistically as complete as it can be, revisit making Buddy a permanent part of SHIT's overall health.
- **Future concept:** a coordinated Integrity, Diagnostics & Recovery workstream with monitoring across data/docs/tests/workflows, root-cause diagnostics, tightly bounded recovery/repair, Buddy-led documentation/continuity guardianship, and a systemic improvement backlog.
- **Role boundary:** Buddy contributes documentation and continuity evidence but is not the sole health authority and does not self-authorize risky repairs.
- **Gate:** explicitly deferred until Babel's roadmap acceptance criteria and fresh-session cold-start simulation pass. No runtime implementation is authorized by this entry.
- **Safety:** preserve canonical data and provenance; distinguish Last.fm scrobbles from optional Spotify playback observations; never invent or silently discard uncertain records; require scoped deterministic repairs, backups, reversibility, audit trails, post-repair verification and user approval for consequential/ambiguous changes.
- **Next at revisit:** create a dedicated goal workspace and specify health dimensions, ownership, severity, autonomy levels, repair boundaries and acceptance criteria.

# SHIT Project Log

## 2026-11-06 — 28 source overviews corrected and broad anti-placeholder coverage

- **Additional analytics documentation:** specified the exact input/output contracts for advanced analytics, assistant analytics, listening-time summary, and music analytics builders.
- **Total:** 28 maintained implementation overviews now describe concrete inputs, outputs, provider behavior, identity semantics, safety boundaries, and invocation rather than generic fallback prose.
- **Automated protection:** placeholder detection now covers maintained Python implementations, compatibility launchers, test modules, and workflow YAML files.
- **Verification:** Daily curator run #42168360237 passed 460 tests on `8fb80589968a7868fd50bba5e13af7f787ed5c15`; security scan #42168221944 passed on the previous source-overview commit. Latest security scan #42168360298 was still in progress.
- **Operational exception:** Enrich Music Metadata run #42166959478 remains in progress after being triggered by the source-comment path filter; duration, artist-profile, and recording-ID stages succeeded, with track-tag enrichment active. Reconcile generated-data publication when it finishes.

## 2026-11-06 — Documentation identity, overview guardrails, and CI verification

- **Naming:** SHIT Documentation & Continuity is the public-facing name; Babel is its internal codename. The canonical guide is `docs/BABEL.md`.
- **Documentation:** 24 generic implementation overviews replaced with concrete module-specific contracts; anti-placeholder test now scans every Python file under `scripts/`. Documentation index and fresh-session tests explicitly enforce Babel identity and links.
- **Verification:** Daily curator run #42167849568 passed **460 tests** on `da3be75844e3ce28eacd46ce8d87960493402503`; public repository security scan #42167849588 passed on the same commit.
- **Operational exception:** Enrich Music Metadata run #42166959478 is still active at the MusicBrainz duration stage after a source-comment edit matched its push filter. It may publish generated metadata; no playlist-write step is part of this workflow. Reconcile the run and any resulting bot commit before declaring the repository state stable.
- **Status:** Babel naming and automated documentation guardrails are implemented and verified. Full semantic audit and fresh-session acceptance remain open.

## 2026-11-06 — Twenty-four maintained module overviews corrected

- **Goal:** replace generic per-file boilerplate with accurate module-specific operating contracts to improve fresh-session continuity.
- **Work:** updated 24 maintained modules spanning Spotify playlist management/cloud control/reference snapshots/feedback/discovery, Last.fm import, music metadata and provider enrichment, lyrics/audio analysis, historical analytics, playback tracking, and playlist intelligence.
- **Automation:** added a regression assertion that rejects known generic fallback phrases in maintained `scripts/` overviews; CI verification of this new assertion is pending.
- **Verification:** Daily curator tests run #42167054690 passed on commit `0c055578` with 458 tests, before the new anti-placeholder assertion was added. Naming/link checks passed on `9f2c788a`; the security scan passed there too.
- **Operational exception:** a comment-only update to a source path matched Enrich Music Metadata's push filter and triggered run #42166959478. It was in its MusicBrainz duration stage at last inspection; reconcile any provider calls and generated-data commit. No playlist writes are part of that workflow.
- **Status:** documentation quality improved; full semantic audit and fresh-session acceptance remain incomplete.

## 2026-11-06 — Documentation system named SHIT Documentation & Continuity (codename Babel)

- **Decision:** the documentation/continuity system's public-facing name is **SHIT Documentation & Continuity**; its internal codename is **Babel**. The parent product and repository remain Spotify Helper & Information Tracker (SHIT).
- **Rationale:** first-time contributors and AI sessions should understand the system's purpose immediately. The codename is useful only after it has been defined.
- **Canonical contract:** [docs/BABEL.md](../docs/BABEL.md). The convention is surfaced in the root README, AGENTS.md, docs index, mandatory documentation rules, current handoff, project roadmap, and Maintainability & Documentation workspace.
- **Status:** naming documentation published to main. Link and CI verification after these commits remains pending; the broader semantic documentation audit is still in progress.
- **Next:** validate the naming entry points and continue the source-to-document semantic audit. Documentation remains the sole active priority.

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


## 2026-11-06 — ChatGPT-initiated Buddy trigger

ChatGPT successfully created branch `babel/dispatch-20261106-01` from `main` and committed `.github/babel/dispatch.json` (`7c1abce763d293992872699146eb7f13d10f9b87`). This is the first verified ChatGPT-initiated GitHub trigger write for Buddy. The workflow's actual run and job outcomes have not yet been verified; see the Maintainability & Documentation action log and `project/ACTIVE_SESSION_BRIEF.md`.
