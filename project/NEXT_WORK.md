# Current policy overlay — 2026-11-06

> This section supersedes older handoff language below that says Babel is the sole active SHIT workstream or that ChatGPT must wait for user review/merge for every documentation update. The authoritative rules are in [AGENTS.md](../AGENTS.md), [DOCUMENTATION_RULES.md](DOCUMENTATION_RULES.md), and [the ChatGPT Buddy policy](../docs/BABEL_CHATGPT_BUDDY.md).

- Babel remains active, but ChatGPT may continue other explicitly authorized SHIT workstreams in parallel. Buddy remains focused on Babel.
- ChatGPT may independently publish verified documentation-only changes directly to `main` when GitHub permits. It must inspect the complete diff, verify claims against current source/tests/workflows/evidence, run relevant safe checks, and read every changed file back.
- Buddy remains proposal-only on `babel/chatgpt-buddy` and its draft PR; it cannot write to `main`, approve, mark ready, close, merge, or self-merge.
- Operational changes—including runtime/product code, provider operations, playlists, canonical/generated data, workflow logic, permissions, secrets, security controls, and dependency manifests—require separate user authorization.
- Routine documentation publication does not require per-change user review. Report material publications, exact evidence, and blockers.
- **Current session focus (2026-11-06):** Tricky Daily safety work has advanced beyond the force/description/snapshot fixes. A further quota-safety coverage gap was found: three existing Retry-After/cooldown tests were nested under `if __name__ == "__main__"` after `unittest.main()`, so normal discovery did not run them. Test-only PR [#169](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/169) moves them into the test class; PR CI #42272223932 and security scan #42272224111 were pending at last check. The latest confirmed GET-only snapshot (run #42268795272) is 29 accessible/unique tracks, baseline 29, blacklist 55, whitelist 0; feedback has 60 track rows and 55 removal events. The whitelist contract is now source/test verified: only an explicit playlist-local exact-track whitelist clears its matching removal; current membership alone does not. Mainline CI run #42270239847 (Daily curator tests) and #42270239536 (security scan) both passed on `b278da8f4f81bd8202fda50d6ed457e4ccfcb62e`. The cycle has immutable SHA-256 staging, committed-blob verification, repository-head and repeated live-snapshot/policy checks, ambiguous-write reconciliation, and exact post-write order/count/uniqueness/blacklist checks. The no-write stage-only attempt #42268583897 stopped before stage creation on Spotify HTTP 429 QUOTA_EXCEEDED; the persisted deadline is `2026-11-06T19:49:46Z` (14:49:46 Eastern). Do not call Spotify before expiry; after expiry retry only stage-only verification. No live cycle or description mutation without separate user authorization. See project/goals/tricky-daily/ACTIONS.md.
- **Buddy daily check:** run `a1354400-ad1c-8320-906e-888d071012ee` completed today. Draft PR #163 head `c8e4a2ad74b8c50868a6806abf9869b9da4b5725` needs changes because it contradicts mainline ChatGPT documentation-publication authority. Its reported Daily curator test run #42239266411 and security scan #42239266381 both completed successfully. Do not merge the draft until the policy conflict is corrected.

# SHIT — Next Work
> **Mandatory continuity instruction:** Read [DOCUMENTATION_RULES.md](DOCUMENTATION_RULES.md) before continuing. Read the relevant goal's `ROADMAP.md`, `README.md`, and `ACTIONS.md`; update them during the same session as work proceeds. The roadmap is the durable plan; this file is the current cross-project handoff.

This is the authoritative session handoff. Read this file first when resuming work, then read [LOOSE_ENDS.md](LOOSE_ENDS.md), [PROJECT_LOG.md](PROJECT_LOG.md), and [README.md](../README.md). Update this file whenever priorities, blockers, or verified status change.

## 2026-11-06 — ChatGPT can now create the Buddy dispatch trigger

- Successfully created `babel/dispatch-20261106-01` from `main` and committed `.github/babel/dispatch.json` (`7c1abce763d293992872699146eb7f13d10f9b87`). This verifies the connected GitHub integration permits the narrow branch-and-marker write needed to emit the workflow's configured push event.
- Workflow execution is not yet verified; inspect the Actions run associated with that commit. Do not claim Buddy ran until Codex, validation and publisher results are confirmed.
- Strategic direction: use ChatGPT as SHIT's conversational front end for planning, querying, controlled repository changes and verification. Keep GitHub as the durable source of truth, use narrow action-specific permissions, require explicit authorization for consequential changes, and retain review gates for autonomous proposals. Do not grant broad repository or Spotify write access merely to make the interface convenient.

**Documentation system identity:** the public-facing name is **SHIT Documentation & Continuity**; the internal codename is **Babel**. See [docs/BABEL.md](../docs/BABEL.md). Babel remains an active workstream, but explicitly authorized SHIT feature work may proceed in parallel; keep its acceptance criteria and cold-start test active.

## Deferred post-Babel objective — SHIT-wide Integrity, Diagnostics & Recovery

**Revisit only after SHIT Documentation & Continuity (Babel) is considered realistically complete**: its roadmap acceptance criteria must pass and the fresh-session cold-start simulation must demonstrate that a new assistant can resume from repository documentation alone. This is a recorded future goal, not permission to start runtime work during the current documentation-only phase.

Proposed direction: establish a coordinated SHIT-wide health system covering data integrity, documentation/continuity, tests, workflows and operational reliability. Include monitoring, root-cause diagnostics, bounded recovery/repair, and a tracked improvement backlog. Make Buddy a permanent Documentation & Continuity Guardian within that system: it checks documentation drift, roadmap/action-log freshness, handoff accuracy and whether recorded claims have evidence. Buddy should contribute to health reporting but must not be the sole judge of system health or independently authorize risky repairs.

Design constraints to preserve: observe/diagnose before mutation; canonical data and provenance are protected; Last.fm scrobbles remain distinct from optional Spotify playback observations; uncertain records are never invented, silently deleted or silently rewritten; repairs must be explicitly scoped, deterministic, backed up, reversible, audited and verified afterward; consequential or ambiguous changes require user approval. At the post-Babel review, create a dedicated goal workspace and roadmap, define health dimensions/severity, ownership, autonomy levels, repair boundaries, reporting cadence and measurable acceptance criteria.

## 2026-11-06 — Buddy first dispatch diagnosed; runner compatibility fix committed, retest pending

- ChatGPT's marker commit `7c1abce763d293992872699146eb7f13d10f9b87` triggered [Babel AI continuation run #42181953313](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42181953313).
- Preflight passed; Codex failed before running the prompt. `ubuntu-latest` resolved to Ubuntu 26.04 and `openai/codex-action` `drop-sudo` failed restricting `/run/dbus/system_bus_socket`, matching upstream [issue #188](https://github.com/openai/codex-action/issues/188). Validation and publisher were skipped; no PR was produced.
- Fix committed: only the Codex agent job is pinned to `ubuntu-24.04`, retaining the sandbox and permission model. Re-dispatch from a fresh branch based on the updated `main`, then verify all jobs and the review PR. Buddy remains unverified until end-to-end success.

## 2026-11-06 — Buddy runner fix verified; API quota blocks retry completion

- The first run [#42181953313](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42181953313) confirmed the push trigger and preflight but failed during Codex `drop-sudo` setup on Ubuntu 26.04. The Codex job was pinned to Ubuntu 24.04 without weakening its sandbox.
- Retry [#42183337573](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42183337573) passed preflight and the `drop-sudo` isolation step on Ubuntu 24.04, then Codex returned `Quota exceeded. Check your plan and billing details.` Validation and publisher were skipped; no Buddy PR exists.
- Daily curator run [#42183307146](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42183307146) passed all 478 tests on `ffc75f5796d422d6f3bcd889465a00f0c613a57e`; public security scan [#42183307047](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42183307047) passed on the same commit.
- **Next:** user must check OpenAI API billing/usage limits and ensure quota is available. Do not retry until confirmed. Then dispatch again and verify Codex, validation, full tests and PR publication. Buddy remains not yet operationally verified.

## Cross-project loose-ends register

Read [LOOSE_ENDS.md](LOOSE_ENDS.md) for the current audit index across migration, provider coverage, enrichment, analytics, discovery, playlists, workflows and documentation. Each entry links to its goal history. Update the register when an item is resolved, deferred or newly discovered.

## 2026-11-06 — Buddy active-session context bridge added

- Created `project/ACTIVE_SESSION_BRIEF.md` on main (commit `55f1403c8feb614b1b6763ce8873499bdcbe4c86`). It is a curated, privacy-safe SHIT context bridge, not a raw chat dump or real-time messaging channel.
- Updated `.github/babel/CONTINUATION_PROMPT.md` so Buddy reads the brief first and reconciles it against checked-out source/evidence (commit `bad03f65cbe92690718278440886a84014fd79a1`).
- The permanent AGENTS/documentation rules, Babel guide, roadmap and action history are being aligned with the requirement that ChatGPT maintain the brief throughout active SHIT work and keep goal ROADMAP/ACTIONS records synchronized.
- Buddy remains unverified until its first successful manual workflow run. User reports the `OPENAI_API_KEY` Actions secret has been added; still confirm the repository Actions setting permits PR creation, dispatch on `main`, and inspect the run/PR.

## 2026-11-06 — Babel AI continuation integrated; activation pending

- Added .github/workflows/babel-ai-continuation.yml, .github/babel/CONTINUATION_PROMPT.md, project/BABEL_AGENT_STATE.md and docs/BABEL_AGENT.md.
- The OpenAI Codex worker is scheduled every six hours and manually dispatchable. It resumes from babel/agent-progress, makes bounded documentation-only changes, and publishes through one review PR. A separate read-only validation job rejects non-documentation paths/deletions and runs full unittest discovery without write credentials; the publisher rechecks paths and publishes without executing candidate code.
- No Spotify/provider credentials or provider operations are available to the agent. It cannot modify runtime features, generated data, or workflow YAML; it never auto-merges.
- **Activation pending:** the user reports `OPENAI_API_KEY` is configured and has now confirmed **Allow GitHub Actions to create and approve pull requests** is enabled. Next, ChatGPT creates a fresh `babel/dispatch-*` branch from `main` and commits `.github/babel/dispatch.json` to trigger the workflow, then verifies the run and proposal PR. Manual dispatch and the six-hour schedule remain available. API usage is billed separately from ChatGPT subscription access.
- See [Babel AI continuation guide](../docs/BABEL_AGENT.md). The worker is integrated but not yet operationally verified. Documentation remains the only SHIT priority.

## 2026-11-06 — Documentation-only priority; latest evidence reconciled

**Audit baseline:** main at `aacb70fa0345369398c9bd049d00e24a9ca09eb6`; subsequent same-session commits contain documentation-only audit and handoff updates.

- **Naming:** the public-facing system name is **SHIT Documentation & Continuity**; internal codename **Babel**. Canonical guide: [docs/BABEL.md](../docs/BABEL.md).
- **Priority:** documentation remains the only active workstream. Do not resume feature implementation, provider checks/enrichment, or Spotify playlist operations until the Maintainability & Documentation acceptance criteria and fresh-session simulation pass.
- **Overview work:** 28 known generic/underspecified implementation overviews were corrected. The maintained inventory contains 55 Python implementation modules, 40 compatibility launchers, 44 test modules and 18 current workflow YAML files. Automated overview presence and known-placeholder checks cover scripts, compatibility launchers, tests and workflows.
- **Goal structure:** 13 goal workspaces each contain ROADMAP.md, README.md and ACTIONS.md. This update adds a separate documentation-only next action to each of the 12 non-documentation roadmaps while preserving its next feature action for later.
- **Complete committed-tree inventory:** verified at `aacb70fa` with a non-recursive root tree plus nine recursive directory trees; every directory result returned `truncated=false`. Total: **28,241 file/blob entries**, including 27,981 under `assistant_data/`. See [repository file index](../docs/REPOSITORY_FILE_INDEX.md).
- **Automated verification:** Daily curator run [#42168520574](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42168520574) passed **460 tests** on `8153028e`; full-history security scan [#42168520598](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42168520598) passed on the same commit.
- **Enrichment side effect reconciled:** comment-only documentation on `scripts/music/enrich_musicbrainz_recording_ids.py` triggered Enrich Music Metadata run [#42166959478](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42166959478). It completed successfully and published generated-data commit `aacb70fa`. It merged 195 discovery candidates into the canonical Library (13,239 songs); 67 MusicBrainz duration matches were added from 182 lookups; 3,373 artist profiles, 229 tagged track profiles and 905 matched album profiles were present. Duration coverage is 8,254/11,130 unique tracks and 139,758/152,005 scrobbles (91.9%). Final integrity audit: 9 checks, 18 warnings, 0 errors. The warnings are no captured playback intervals and 16 Spotify playlists with inaccessible item contents; preserved snapshots may be stale. No Spotify playlist writes occurred.
- **Open documentation PR #161:** remains open/draft with 117 changed files. Its branch is divergent from current main (571 commits ahead, 29 behind); do not merge or rebase blindly. It contains valuable source-audited documentation and regression-test candidates; selectively reconcile them against current main and live source instead.
- **Other open feature proposals:** #158, #159, #160, #120, #121, #65 and #60 remain proposals, not merged mainline behavior.

### Newly verified high-risk documentation findings

- **Tricky Daily force/idempotency:** corrected on 2026-11-06; force bypasses the clock gate only, and a forced duplicate now hits the same-date guard. Remote CI confirmation is pending.
- **Tricky Daily description read-back:** HTML-unescape comparison added after the saved Spotify description showed `Today&#x27;s detour starts here.`; focused regression test added. Remote CI confirmation is pending.
- **Tricky Daily current saved snapshot:** captured `2026-11-06T14:18:18.958752+00:00`, with 37 accessible items / 37 reported. The removal baseline also has 37 rows; the playlist-local blacklist has 47 removed entries and no whitelist entries. This is repository snapshot evidence, not a new live read.
- **Tricky Daily cycle state:** last accepted cycle marker is `2026-11-05T23:11:08.463502+00:00`, status `replacement_accepted_pending_verification`; no Nov 6 completed-cycle evidence was present in the inspected state.
- **Daily post-write verification gap:** automatic post-write checks still do not compare the returned ordered URI list against a durable staged payload or recheck duplicate/blacklist invariants against the returned snapshot. Durable staging, pre-write live-snapshot race detection and ambiguous-write recovery remain open P0 work.
- **Library report freshness:** the latest canonical Library audit reported 13,239 songs, but `assistant_data/music/library/migration_report.json` still records the earlier 13,005-song migration snapshot from 2026-11-01. The Library README now labels that report historical; reconcile the generated report only after the documentation pause.
- **Resolver and credential side effects:** constructing `MusicLibrary()` may rebuild/write `library_index.json` if missing/empty/incomplete; use the dedicated read-only `library health` path for zero-write structural checks. Great Migration `verify` may persist a replacement Spotify refresh token to the Actions secret store through the scoped GitHub App; it is not purely read-only in cloud runs.
- **Great Migration preflight verified:** `preview` and `prepare-preview` follow the full migrator's `--dry-run` branch, which returns before `MusicLibrary` construction, backup creation or canonical Library writes. No provider requests or Spotify playlist writes occur. A source-backed regression test was added; its CI result is pending.

### Next executable actions

1. Finish the source-to-document semantic audit of all 55 implementation modules, 40 compatibility launchers, 44 test modules, 17 workflows and 21 technical guides.
2. Correct high-risk documentation mismatches first: Library resolver index writes, Spotify snapshot evidence semantics, Great Migration secret rotation and backup boundaries, and the Reference Library schedule. Daily force/idempotency and HTML description read-back fixes are now published but await remote CI confirmation.
3. Port and adapt the useful documentation regression tests from PR #161; do not import stale assertions or merge its divergent history.
4. Reconcile all 13 goal roadmaps, workflow permissions/triggers/publication behavior, open PRs/issues and the loose-ends register.
5. Complete a fresh-session simulation using only repository documentation. No feature development, provider runs or playlist operations before acceptance.


## Historical checkpoint — Documentation system naming established (superseded)

**Public-facing name:** SHIT Documentation & Continuity. **Internal codename:** Babel. The parent product/repository remains Spotify Helper & Information Tracker (SHIT). First references must define the descriptive name and codename; subsequent references may use Babel. See [docs/BABEL.md](../docs/BABEL.md).

- Published the naming convention across root README, AGENTS.md, docs index, mandatory documentation rules, this handoff, project roadmap, and Maintainability & Documentation records.
- The canonical Babel guide defines its mission, responsibilities, naming rules, safety constraints, required structure, and evidence-based completion standard.
- **Historical status at that checkpoint:** naming-link checks and CI were still pending. This was superseded by the verified Babel identity/link tests and passing 460-test run #42168520574 on commit `8153028e`.

## 2026-11-05 — Documentation-first priority reaffirmed; live repository audit resumed

**Active priority: documentation only.** Do not begin feature development, playlist operations, enrichment runs, or unrelated project work until the documentation audit reaches the completion standard in the Maintainability & Documentation roadmap.

### Verified repository baseline
- Canonical repository: `TrickySturluson/spotify-helper-information-tracker`, default branch `main`; inspected current main tree SHA `b542ceab2c40f6910a91ea3fcb84c204fc412c2d`.
- Root structure includes `AGENTS.md`, `project/DOCUMENTATION_RULES.md`, the project control centre, `docs/`, `scripts/`, `compat/`, `tests/`, `data/`, `assistant_data/`, `playback_data/`, `.github/`, and the `shit.py` CLI.
- The current goal index contains **13** goal workspaces. Every workspace contains ROADMAP.md, README.md and ACTIONS.md.
- Current `.github/workflows/` inventory contains 17 workflow YAML files; `docs/WORKFLOWS.md` exists and the documentation contract test requires every workflow filename to appear in it.
- Maintained Python implementation is organized under analytics (7 modules), Last.fm (1), music (24), and Spotify (19); compatibility launchers, tests, and workflow YAMLs are also covered by the bottom-of-file overview test.
- Documentation tests are part of unittest discovery. Latest observed Daily curator test run #42144512658 and public repository security scan #42144512423 both completed successfully on the inspected main SHA. This verifies the automated checks ran successfully; it does **not** prove semantic accuracy of every overview or technical guide.
- The recursive Git tree API response was truncated because generated Library records make the tree very large. Do not use that truncated response as a complete tracked-file inventory. Use directory-scoped listings for maintained code and `git ls-files` in a complete checkout for the authoritative full inventory.

### Workflow overview work and operational side effect
- Replaced generic bottom overviews in nine workflows with workflow-specific trigger, credential, write, safety and related-code descriptions. The workflow catalogue remains the source for the full 17-workflow matrix.
- Editing workflow YAML on main triggered path-filtered jobs even though only comments changed. Reference Library run #42146148971 completed successfully and committed `3e989e33282efab6cc1416e35970e7c59af5f056`, changing 249 generated files: 184 Library records, 63 Spotify reference/history files and 2 removal-state files. It refreshed repository snapshots/removal feedback; it did not write to Spotify playlists.
- Runs #42146153098 (Update Last.fm History), #42146121471 (Enrich Music Metadata), and #42146097964 (Acoustic Metadata Enrichment) were still in progress at the latest inspection. Their completion and any commits/failures must be checked before the documentation audit continues. No workflow cancellation action was exposed by the connected GitHub interface.
- Do not repeat this side effect. The workflow catalogue now explains that comment-only YAML edits can trigger configured push workflows; inspect push path filters before any future workflow edit.

### Current open pull requests observed during this audit
- #158 — Discover Weekly exposure and feedback tracking (open, non-draft).
- #159 — Tricky Daily DST schedule gating (open, non-draft).
- #160 — exposure-aware Tricky Daily discovery (open, non-draft).
- #121 — offline sorter evaluation and ingestion watchdog spec (open draft).
- #120 — incremental Library enrichment and sorter development (open draft).
- #65 — read-only Library coverage planner (open draft).
- #60 — provenance-aware recommendation ingestion (open, non-draft).
Treat all seven as proposals, not merged behavior. Reinspect their diffs, current base/head relationship and checks before updating mainline documentation or selecting future work.

### Findings and remaining audit work
- The documentation architecture is substantial and already includes 13 goal workspaces, 22 cross-cutting guides in `docs/`, the central handoff/loose-ends/log/roadmap, directory guides, workflow catalogue, and automated documentation contract tests.
- The documentation contract currently verifies required control files, goal workspace structure, major-domain navigation, selected local links, workflow catalogue coverage, and bottom FILE OVERVIEW presence. It does not semantically compare each overview or guide with the current implementation.
- The maintainability roadmap and action log still correctly identify manual semantic review, operational contract reconciliation, and a fresh-session resume test as unfinished.
- Open Daily pull requests observed during this audit: #158 Discover Weekly exposure/feedback tracking, #159 DST schedule gating, and #160 exposure-aware Daily discovery. Treat them as unmerged proposals; inspect their current state before incorporating their behavior into mainline documentation.
- The loose-ends register's review date and several historic status statements are stale relative to the current repository. Reconcile each workstream against current main, open PRs/issues and fresh workflow evidence before treating its entries as current.

### Next executable actions
1. Complete a directory-by-directory inventory of maintained source, compatibility shims, tests, workflows, data schemas and operational state owners; use a complete local `git ls-files` inventory when available, and explicitly mark generated per-record data as schema/family-documented rather than individually prose-indexed.
2. Audit every maintained Python/workflow FILE OVERVIEW against its actual code, triggers, permissions, credentials, network calls, writes, retry behavior and test commands; presence alone is not enough.
3. Audit each technical guide and each of the 13 goal roadmaps against current source/tests/workflow evidence; resolve stale paths, contradictory claims and missing runbooks.
4. Reconcile open PRs/issues and latest workflow evidence into the relevant goal ACTIONS, ROADMAP, NEXT_WORK and LOOSE_ENDS records.
5. Add meaningful automated checks for gaps discovered by the audit, without brittle boilerplate or treating generated JSON as hand-maintained documentation.
6. Perform a fresh-session simulation: start only from AGENTS.md, DOCUMENTATION_RULES.md, NEXT_WORK.md and the goal index; verify the next action and safety boundaries are unambiguous.
7. Do not declare documentation complete until every acceptance criterion in `project/goals/maintainability-documentation/ROADMAP.md` has evidence.

## 2026-11-05 — Documentation system expansion in progress

- The repository now has root [AGENTS.md](../AGENTS.md), a central [documentation index](../docs/README.md), and a cross-workstream [project roadmap](ROADMAP.md). These complement—not replace—the mandatory [documentation rules](DOCUMENTATION_RULES.md), 13 individual goal roadmaps, the loose-ends register and chronological project log.
- The repository root README links to the new navigation. No code, canonical Library data, provider state, listening history or Spotify playlists were changed by this documentation-only update.
- **Current documentation priority:** audit actual tracked files against the repository file index and per-file overview standard; check all goal folders and links; identify stale/missing operational contracts; add automated coverage/link checks only after measuring the real gaps.
- **Important limitation:** a complete repository tree/per-file coverage audit has not yet been run. Do not claim the documentation system is fully audited.

## 2026-11-05 — Documentation guardrails added; CI verification pending

- Added `tests/test_documentation_contract.py` to check repository control docs, all goal workspace ROADMAP/README/ACTIONS, the AGENTS continuity contract, docs-index domain coverage, and local links from the main navigation documents.
- Existing `tests/test_script_layout.py` already enforces bottom `FILE OVERVIEW` blocks for maintained Python/workflow files. Updated `docs/CODE_DOCUMENTATION.md` and `docs/README.md` to document both checks.
- Standard unittest discovery runs the new test; `.github/workflows/update.yml` already runs the full test suite before data publication. The new check is implemented but not yet CI-verified.
- Next: inspect CI on commit `38ad97e1edfd84fdf07fed6e98c42a05fc091f3a` and the follow-up documentation commits; fix any test failure. Then build a generated-source inventory / stale-index audit without attempting to enumerate every generated song record as hand-maintained prose.

## 2026-11-05 — Source/data index corrected; latest CI verification pending

- Replaced the misleading exhaustive file catalogue with a maintained source/data-family index. The prior catalogue was stale because it described only 239 assistant_data files while the canonical per-record music Library has grown substantially; the recursive Git tree response was truncated, so do not rely on it as a complete inventory.
- Added `tests/README.md` and expanded `tests/test_documentation_contract.py` to require directory guides for the major code, test, data, and workflow domains.
- Daily curator run #42143513931 passed on commit 7d23db6, including the directory-guide checks and full unittest discovery. Run #42143770161 also passed on commit 79af1f9 after adding the Tricky Daily workspace. Daily curator run #42143913729 passed on commit ec05a646 after adding Playlist Sequencing; the dynamic goal-folder check and full unit-test suite passed. All 13 goal workspaces are now covered.
- Next: inspect CI after the latest commits; fix test failures; then audit every maintained Python/workflow overview and verify docs against actual implementation.

## 2026-11-05 — Dedicated Tricky Daily workstream added

- Added project/goals/tricky-daily/ROADMAP.md, README.md and ACTIONS.md to preserve Daily's 60-track contract, exclusions, forced-run parity, feedback semantics, scheduling, recovery and live verification independently of the wider playlist-intelligence roadmap.
- Added the Daily workspace to the goal index, project-wide roadmap and docs index. The dynamic documentation-contract test will automatically require its three core files.
- Next: inspect the latest Daily curator CI run for the new goal, then audit the actual Daily implementation/workflows and current live evidence against the P0 acceptance criteria. Do not infer live correctness from documentation or unit tests alone.

## 2026-11-05 — Playlist Sequencing workstream separated

- Added project/goals/playlist-sequencing/ROADMAP.md, README.md and ACTIONS.md. It preserves smooth-transition priority, user-controlled energy journeys/peak placement, track-level evidence requirements, uncertainty handling, Booze preset references, and preview/confirmation safety.
- Linked it from the goal index, project-wide roadmap and docs index. The five-axis playlist-fit model remains explicitly separate from the sequencer.
- Next: inspect the latest CI run after the new goal folders, then audit sequencer code/tests and live preview evidence against its acceptance criteria.

## Historical project checkpoint — Playlist intelligence five-axis fit model (not the active task)

**Historical state at the time of this checkpoint:** read-only preview pipeline merged to main (PR #126, squash commit `2f84924b8e76510a1648bfc3e4e369935aa2bdf0`). This section is retained as context only. The active priority is the documentation audit at the top of this file; do not resume this feature work until documentation is complete. Model version `five-axis-fit-v0.3`. Read [playlist-intelligence README](goals/playlist-intelligence/README.md), [model contract](goals/playlist-intelligence/PLAYLIST_FIT_MODEL.md), [preview runner guide](goals/playlist-intelligence/PLAYLIST_FIT_PREVIEW.md), and [ACTIONS.md](goals/playlist-intelligence/ACTIONS.md) before continuing.

- Full repository CI: 398 tests passed; focused preview/comparison tests: 29 passed; full-history Gitleaks scan passed. Real-data preview workflow #35 passed: https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41405523394.
- The five strongly themed calibration targets are To 11 (`5meDjtqrqOe5oHpvZGWRMz`), Somber Party (`7L2rSp4SuohBEyNxEtAurx`), . . . (`4HzqY9iy04M1EVSF5kcD64`), =^= (`0O9ojSstxwa5vQy2V7pO2x`), and Smooth (`2ICCklgbF6cg0q5p4xAHKi`). All Time (`6ZsqAs5OnRMVudhfB2QzTx`) and Hell (`3XQz9AyZP6ADcr9i8iBaVx`) are broad taste references, not narrow theme targets. SHITting Grounds (`4aLdllLgRPh5vKOznkC97D`) is the separate audition destination; its current contents are not yet in the reference snapshot.
- The 24-track held-out identity batch excludes the unplayable Dog — Floating Room. The whole batch is excluded from every target profile by Spotify URI and resolved canonical record ID. Human labels are not read by the scorer; a separate post-hoc diagnostic compares frozen predictions.
- Direct profile coverage by target: To 11 0.2, Somber Party 0.0, . . . 0.2, =^= 0.2, Smooth 0.0. Context coverage: 0.2, 0.2, 0.4, 0.4, 0.0. Only Genre has direct evidence (3, 0, 3, 4, 0 tracks). Sound and Energy have no evidence; Mood has only 3/1 contextual observations in . . . and =^=; Theme has no evidence. Every target profile remains low confidence.
- 15 candidates receive scores against the first four targets; 9 remain unknown per target; Smooth has no scores. All 60 scored human-reference pairs are low confidence, support exactly one dimension, and 12/15 per target are context-only. No medium/high prediction exists.
- Human-reference diagnostic: 24/25 tracks matched; the unmatched item is Dog — Floating Room. Across 60 scored pairs: MAE 26.85, median absolute error 16.79, mean bias -17.63, median bias 0.00, Pearson 0.4473, Spearman 0.4862. To 11 and =^= show stronger rank alignment (Spearman 0.8333 / 0.7094), but these are low-confidence genre/context-only signals, not validation or training targets.
- Preview and diagnostic artifacts from run #35: 13122763665 and 13122659752 (expire 2026-11-16). No Spotify API calls or playlist writes.

### Next work — evidence enrichment, not weight tuning

1. Raise **direct recording-level Genre** coverage across the five target playlists. Context genres remain down-weighted and cannot substitute for track tags.
2. Build/validate direct **Sound** descriptors. Do not turn AcousticBrainz average_loudness/dynamic_complexity or BPM into perceived sound or energy.
3. Build/validate direct **Energy** evidence using an actual calibrated energy measure; tempo alone is not energy.
4. Populate **recording-level Mood** separately from artist identity. Only explicit track-scoped mood evidence may count as direct.
5. Add **lyric-derived Theme** evidence with recording identity, provider, retrieval timestamp and provenance; do not infer track theme from artist/album identity.
6. Inspect current provider failures/cooldowns and credential availability before any enrichment requests. Historical blockers include MusicBrainz 503/rate limits, Last.fm HTTP 400 and missing optional Discogs/GetSongBPM credentials. No blind retry batches.
7. Expand the held-out sample only after the five target profiles have materially better direct coverage. Keep the human diagnostic post-hoc and descriptive; never train/tune to the initial extreme slider labels.
8. Keep the scorer disconnected from the sequencer and all Spotify writes until the direct-coverage, confidence, boundary-error and smooth-transition gates pass. Do not promote low/context-only estimates to production.



## Booze or Boos! functional integration checkpoint — 2026-11-02

- PR #127 merged as `ad391369e3cbe073ea92ecaba9ba8e16e78c7941`. It adds the identity-only 64-track Booze cross-reference audit to the five-axis preview workflow, validates candidate/snapshot integrity, and documents that low/context-only fit scores are not valid add/remove decisions. Focused preview tests, full repository tests and Gitleaks passed.
- Artifact from workflow #41407268653: `booze-five-axis-cross-reference-audit` (artifact 13124415230, expires 2026-11-16). 64/64 saved tracks resolve to canonical Library records (28 Spotify ID; 36 exact artist/title/album/duration). All 64 excluded from each calibration profile. Per target 32/64 score, all low-confidence and one-dimensional; 31/32 use artist-scope genre context, only one direct genre observation; 32/64 remain unknown. Direct Sound/Energy/Mood/Theme evidence absent.
- Exact-key cache audit: 64/64 have legacy track-profile rows, only 2/64 have Last.fm tags, 0 lyric-theme features, 0 direct track-mood rows, 0 recognized energy scores, and one sparse audio-profile match. Missing data is not negative evidence.
- Live read-only sequencer preview run #41407486669 (issue comment #6571714105) refreshed from Spotify and found **72 tracks**, while the saved reference snapshot has 64. Preview proposed 48 reorder operations, found 64/72 section assignments (8 unassigned: Caustic — “666 on the Crucifix - Be My Enemy Mix”; The Dickies — “Killer Klowns”; Richard O'Brien — “Shock Treatment”; Alice Cooper — “Feed My Frankenstein”; Insane Clown Posse — “My Axe”; Tim Curry — “Planet Schmanet Janet”; October Country — “My Girlfriend Is a Witch”; Ninja Sex Party — “Zombie Handjob”). Transition report: 0 gentle, 0 moderate, 0 supported potential jumps; 71 transitions limited-evidence. Confidence: 62 low, 10 unknown. **No Spotify changes were made.**
- Do not apply that preview blindly. The sorter currently has insufficient track-level acoustic/semantic evidence for a trustworthy transition judgment, and the fit model is still effectively genre-context-only for Booze.
- Next sequence: (1) refresh and persist the 72-track live reference snapshot, regenerate the Booze candidate manifest from that exact snapshot; (2) build a bounded, provider-aware recording-level enrichment pass for Booze (track genre/tag, lyrics-derived theme, direct mood, audio/energy), checking prior provider errors/cooldowns before requests and respecting per-run caps; (3) classify the 8 unassigned tracks using explicit track/theme evidence, not title alone; (4) select a substantial addition batch using verified Halloween relevance + party-energy criteria and label evidence/confidence; (5) rerun five-axis cross-reference and the live sequence preview; (6) review the full ordered list and transitions, then apply only through the separate confirmation-gated manager command. Never treat artist-only tags as proof of track-level Halloween theme.



## Booze or Boos! functional integration checkpoint — 2026-11-02

- PR #127 merged as `ad391369e3cbe073ea92ecaba9ba8e16e78c7941`. It adds the identity-only 64-track Booze cross-reference audit to the five-axis preview workflow, validates candidate/snapshot integrity, and documents that low/context-only fit scores are not valid add/remove decisions. Focused preview tests, full repository tests and Gitleaks passed.
- Artifact from workflow #41407268653: `booze-five-axis-cross-reference-audit` (artifact 13124415230, expires 2026-11-16). 64/64 saved tracks resolve to canonical Library records (28 Spotify ID; 36 exact artist/title/album/duration). All 64 excluded from each calibration profile. Per target 32/64 score, all low-confidence and one-dimensional; 31/32 use artist-scope genre context, only one direct genre observation; 32/64 remain unknown. Direct Sound/Energy/Mood/Theme evidence absent.
- Exact-key cache audit: 64/64 have legacy track-profile rows, only 2/64 have Last.fm tags, 0 lyric-theme features, 0 direct track-mood rows, 0 recognized energy scores, and one sparse audio-profile match. Missing data is not negative evidence.
- Live read-only sequencer preview run #41407486669 (issue comment #6571714105) refreshed from Spotify and found **72 tracks**, while the saved reference snapshot has 64. Preview proposed 48 reorder operations, found 64/72 section assignments (8 unassigned: Caustic — “666 on the Crucifix - Be My Enemy Mix”; The Dickies — “Killer Klowns”; Richard O'Brien — “Shock Treatment”; Alice Cooper — “Feed My Frankenstein”; Insane Clown Posse — “My Axe”; Tim Curry — “Planet Schmanet Janet”; October Country — “My Girlfriend Is a Witch”; Ninja Sex Party — “Zombie Handjob”). Transition report: 0 gentle, 0 moderate, 0 supported potential jumps; 71 transitions limited-evidence. Confidence: 62 low, 10 unknown. **No Spotify changes were made.**
- Do not apply that preview blindly. The sorter currently has insufficient track-level acoustic/semantic evidence for a trustworthy transition judgment, and the fit model is still effectively genre-context-only for Booze.
- Next sequence: (1) refresh and persist the 72-track live reference snapshot, regenerate the Booze candidate manifest from that exact snapshot; (2) build a bounded, provider-aware recording-level enrichment pass for Booze (track genre/tag, lyrics-derived theme, direct mood, audio/energy), checking prior provider errors/cooldowns before requests and respecting per-run caps; (3) classify the 8 unassigned tracks using explicit track/theme evidence, not title alone; (4) select a substantial addition batch using verified Halloween relevance + party-energy criteria and label evidence/confidence; (5) rerun five-axis cross-reference and the live sequence preview; (6) review the full ordered list and transitions, then apply only through the separate confirmation-gated manager command. Never treat artist-only tags as proof of track-level Halloween theme.

## Historical checkpoint — Library reliability, enrichment and confidence (not the active resume point)

**Historical state recorded below:** full canonical Library was published on main and structural health/identity confidence checks had passed at the time of this checkpoint. This section is retained for history; the active resume point is the documentation-only audit at the top of this file. Latest verified index: 13,005 songs, 6,386 artists, 7,861 albums. Legacy source coverage: 11,130/11,130 legacy track IDs resolve via source-track or recording-MBID aliases; 5,358/5,358 legacy artist names are represented.

- Run #18 successfully published enrichment commit `c55012f`; run #21 later repeated work from stale checkpoints and failed publication. Its generated output was not pushed. Workflow fix `21cc2ed` now checks out latest `main` before migration.
- Run #22 independent health check: https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41367899566 — 13,005/6,386/7,861; zero errors/warnings.
- Main-branch full CI including confidence audit: https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41368125489 — 314 tests passed.
- Issue #83 post-playability verification: audit/health clean; identity confidence drift 0; initial metadata confidence drift 1,582; duration coverage 10,028; track tags 179; audio features 36; playability evidence on 1,856 songs; legacy source coverage complete.
- Issue #85 maintainer preview: full catalogue clean, proposed index matches current, all aliases reconstructable, no repair needed, zero writes.
- PR #87 merged (`6c9fe06`): health checker now validates market-scoped playability evidence history, status/value semantics, timestamps, IDs/relinking, and latest-by-market index.
- PR #88 merged (`67ab44f`): confidence audit separates missing stored confidence from genuine mismatches, per field; read-only.
- Issue #90 freshness baseline: 13,005 songs / 6,386 artists / 7,861 albums; 8,799 fresh, 0 stale/due tasks, 0 missing playability observations, 42,158 missing field/provider timestamps, 1,184 cooldown skips, 0 invalid timestamps/errors; selected 0/25; provider requests=0, writes=0. The 42,158 count is not a stale count; missing/undated fields are deliberately not scheduled.
- PR #86 merged: native `python shit.py library freshness` CLI and weekly Sunday read-only health/confidence/freshness report workflow (30-day artifacts). No provider-backed generic freshness executor is enabled.
- PR #78 merged and offline playability backfill run #82 published: 3,305 observations across 1,856 song records, 3,250 playable and 55 unplayable in `from_token` context from saved snapshots; zero API requests and playlist writes. Snapshot-time results, not live availability guarantees.
- Issue #92 was created after PR #87/#88 merges for a fresh audit/health/confidence verification against latest main; result pending at this checkpoint.
- Latest published enrichment coverage still needs fresh measurement. Historical run #18 report: approx. 91.1% duration coverage; 115 audio profiles; zero lyric features; 1,778 track profiles; 3,998 artist profiles; 400 album profiles. MusicBrainz had rate limits/503s, Last.fm tag lookups returned HTTP 400, and optional Discogs/GetSongBPM credentials were absent.
- No Spotify playlist writes, force-pushes, blind conflict resolution, or confidence rewrites.

## Current Library reliability work

- **Health checker:** merged PR #73; full-catalogue scan clean. PR #87 adds semantic playability checks; issue #92 verified them against the full catalogue with zero errors/warnings.
- **Data maintainer:** PR #80 merged. `python shit.py library maintain` previews deterministic index rebuilds; apply requires `--apply --repair-index`, alias-preservation proof, backup, atomic replacement, and post-repair health validation/rollback. Full-catalogue previews #85 and #93 found no repair needed; #93 confirmed 0 health errors/warnings, all aliases reconstructable, and zero writes. Weekly workflow now includes the same read-only maintenance preview and preserves its report; no automatic repair. Current repair scope is index-only.
- **Metadata freshness:** PR #81 planner and PR #86 CLI/weekly review merged; PR #100 merged as `61cc5c0`. The planner now separates no-data, data-bearing unknown-age, and missing duration provenance, and rotates a 25-item unknown-age baseline weekly. Full CI/security passed (344 tests); issue #101 validated full-catalogue output: 6,613 baseline candidates, 25 selected (all Last.fm duration), 0 due/stale, 33,689 no-data, 1,856 missing provenance, 1,362 cooldown skips. This is read-only; provider_requests=0, writes=0. No generic provider executor yet. Weekly workflow also runs maintenance preview.
- **Spotify playability:** PR #72/#78 merged. Each song stores append-only market-scoped observations under `evidence.spotify_playability`; snapshot backfill covered 1,856 records. A separate Get Track refresh planner defaults to 25, maximum 50, 90-day TTL, dry-run by default, and requires explicit `--execute --yes`; it is not yet exposed through the scheduled weekly workflow. Do not infer playability from playlist addability.
- **Confidence:** read-only audit merged; PR #88 classifies missing vs mismatched confidence. Issue #92 confirms identity drift 0, missing duration confidence 1,582, genuine mismatches 0. The real-data review set now includes exact MBID, Spotify-ID/playability, low-confidence source-ID examples, and a Candy Claws duplicate artist/album candidate. Issue #102 tracks a read-only duplicate-entity audit. Do not bulk-rewrite confidence or merge records.
- **Migration:** full entity catalogue is published. Read-only prepare preflight #94 confirmed 11,130/11,130 legacy track IDs and 5,358/5,358 artist names represented; 13,005/6,386/7,861 canonical records; current profile caches and bounded provider caps; zero provider requests/writes. It did not prove new enrichment is due. Continue only from durable checkpoints, one serialized writer at a time; do not repeat provider batches merely because a runner-side operation failed publication.

## Immediate priorities

1. **Complete issue #92 verification** against latest main: confirm the new playability semantic health checks pass over all 3,305 observations and inspect missing-vs-mismatch confidence breakdown.
2. **Improve freshness evidence classification:** distinguish absent metadata, present-but-undated values, fresh no-result/negative cache, provider transient failure, cooldown, and genuinely stale observations. Propagate trustworthy source timestamps from existing caches/checkpoints; never infer from file mtimes.
3. **Recover duration observation provenance before any refresh.** Issue #103 and `scripts/music/backfill_duration_observations.py` recover exact `metadata_checked_at` timestamps from legacy shards into canonical song `duration_observations` only when ID, duration, source and matched status agree. Issue #105 preview passed: 8,121 exact matches, zero alias/duration/source/duplicate conflicts; 2,958 unrecognized-provider rows and 51 invalid timestamps skipped. Issue #106 is queued for backup-protected apply. After publication, re-run health/audit/freshness to measure the remaining true unknown-age set.
4. **Design a bounded partial refresh executor** only after provenance recovery. It should consume durable checkpoints/retry state, advance the deterministic rotating sample, respect provider budgets/cooldowns, preserve old evidence on failure, and default to preview. Keep Spotify playability refresh separately market-aware and capped.
4. **Re-measure provider coverage** from current published data; continue only eligible enrichment. Diagnose Last.fm HTTP 400 and MusicBrainz 503/rate-limit behavior before retries; do not repeat no-result requests without cache expiry or changed query evidence.
5. **Finish confidence verification:** use PR #88's missing/mismatch split; inspect missing duration provenance; run the curated [identity review set](goals/library-confidence-verification/IDENTITY_REVIEW_SET.md); implement issue #102's read-only duplicate artist/album/song audit. The Candy Claws fallback artist/album pair is a concrete candidate: do not merge until external-ID evidence and reference preservation are verified.
6. **Return to sorter evaluation only after gates 1–5:** test retrieval, field-specific confidence gating, unknown handling, and smooth transitions against real generated playlists before any playlist write.

## Priority order

1. **Recover, publish, and verify the Great Migration**
   - Establish the exact last successful stage and durable checkpoint.
   - Confirm entity counts, relationships, aliases, manifest/index consistency, and audit output.
   - Confirm what actually reached `main`; distinguish local/artifact success from published success.
   - Record provider availability and metadata gaps separately.
   - Once publication is verified, continue bounded enrichment passes rather than treating migration as the end state.

2. **Enrichment and verification**
   - Use the coverage planner to build a deterministic, read-only view of missing fields and eligible provider work.
   - Resolve trustworthy recording identifiers first; then improve durations, album/artist context, acoustic/audio features, and track-level tags/mood where supported.
   - Preserve field-level provenance, confidence, timestamps, and evidence. Unknown stays unknown; artist-level mood must not be copied onto every recording.
   - Reconcile exports into the canonical Library and run integrity audits after each meaningful pass.
   - Cache successful results; respect provider-specific request budgets, batch caps, pacing, cooldowns, and negative-cache expiry. Never fetch blindly or repeat a known failure without a reason.

3. **Provider-aware retry queue**
   - Implement `assistant_data/music/retry_queue.json` from canonical Library records plus real provider checkpoints/state, following [RETRY_QUEUE_SPEC.md](RETRY_QUEUE_SPEC.md).
   - One task per recording + provider + requested data family.
   - Distinguish eligible, retry-wait, definitive not-found, ambiguous, complete, blocked, and invalid.
   - Record attempt count, last attempt, next eligible time, reason, requested fields, priority, confidence, and evidence references.
   - A failure at one provider must not block independent providers. Planner/report mode must not perform network calls or mutate records.
   - Validate real schemas before implementation; test cooldown preservation, negative-cache semantics, malformed records, deduplication, and no-write/no-network guarantees.

4. **Discovery and recommendation intake**
   - Bring suggested/recommended songs and other discovered candidates into the Library so they can be identified, enriched, deduplicated, and retrieved later.
   - Store source/provider, source playlist/person/context, prompt or recommendation context when available, capture time, and observable user response (added, saved, played later, rejected, ignored, etc.).
   - Keep candidate/recommendation evidence separate from Last.fm scrobbles, Spotify playback, explicit likes/saves, and confirmed preferences. A recommendation is never a play or a preference by itself.
   - Review and verify PR #60: https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/60

5. **Identity and metadata confidence verification — sorter gate**
   - Read [the confidence verification goal](goals/library-confidence-verification/README.md) and report identity-confidence distribution by match method.
   - Recompute field-level confidence from independent source-family evidence; detect missing provenance, conflicts, stale observations, and stored-vs-recomputed drift.
   - Validate the 11,130 legacy track IDs and 5,358 artist-name matches as permanent regression coverage, not just a one-off comparison.
   - Build a curated gold set for verified IDs, same-title collisions, remasters/live versions, ambiguous names, and false-match traps; manually inspect representative high/medium/low/unknown records.
   - Verify lookup_song/get_song retrieval and sorter input confidence gates; no silent auto-upgrades of confidence.

6. **Library coverage planner**
   - Review PR #65 CI and code against actual canonical record/checkpoint schemas.
   - Verify read-only behavior, deterministic output, correct priority ordering, and separation of transient failures from definitive negatives.
   - Do not mark complete based only on PR description; inspect CI and run tests.

7. **Playlist intelligence and safety**
   - Continue sorter work only against generated playlists unless explicitly authorized otherwise; preserve locked-by-default behavior and explicit unlock requirements.
   - Smooth transitions are the primary sorting objective; avoid jarring adjacent tracks. Support controllable progression/peak placement, energy/BPM/loudness, mood/theme/genre sections, and gradual resolution.
   - Use track-level mood/theme evidence rather than assuming an artist has one mood. Lyrics-derived themes may use compact tags/features and provenance; do not store full copyrighted lyrics.
   - Daily learner should use actual plays and explicit likes as distinct signals; unplayed generated daily tracks must not be over-weighted. Liked tracks should be down-prioritized where requested, not automatically excluded.
   - Preserve removal blacklists, deduplication, audit/state files, playlist exceptions (including Tricky Daily), and preview/test-before-write workflows.
   - No playlist writes during migration recovery.

8. **Maintainability and documentation**
   - Every project script/module should explain its purpose, inputs/outputs, side effects, safety boundaries, and how it fits into SHIT.
   - Keep a top-level project overview and a concise per-file overview in scripts.
   - Keep this handoff and the chronological log updated as work proceeds.

## Open pull requests / status to re-check

- **#67 — Per-goal documentation workspaces:** merged as `4ad701c2c4f36b9f6f73926e83db1f84cbfbcc2c`; tests and secret-history scan passed.
- **#65 — Read-only Library coverage planner:** open draft; unit tests failed while compile/data-doc checks and secret scan passed. Diagnose before relying on it. https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/65
- **#60 — Provenance-aware recommendation ingestion:** open; unit tests and secret-history scan failed. Diagnose both before relying on it. https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/60

## Standing data and safety rules

- Last.fm scrobbles are the historical listening source of truth.
- Spotify playback-tracker data is optional prospective evidence with coverage gaps; never silently treat it as complete historical listening.
- Recommendations/discoveries are candidate-interest signals, not plays, scrobbles, likes, saves, or confirmed preferences.
- Preserve song, artist, and album identities separately; recording-level evidence must remain recording-level.
- Preserve provenance and confidence for every enrichment. Do not fabricate metadata or silently promote weak matches.
- Respect provider rate limits, caps, cooldowns, caches, and retry state. Avoid blind/redundant requests.
- Prefer preview, bounded batches, backups, checkpoints, deterministic outputs, and final audits.
- Do not write to Spotify playlists without the relevant explicit authorization/unlock.
- Never commit credentials, tokens, private account data, or full copyrighted lyrics.

## Goal-based documentation workflow

Every major project objective has a dedicated folder under [`goals/`](goals/README.md). When starting work, open only the relevant goal's `README.md` and `ACTIONS.md` alongside this handoff. After meaningful work, append a dated action entry recording purpose, files/workflows changed, execution, exact tests/audits, outcome, blockers, and next action. Update the goal README when its scope/design/current status changes. Update this central handoff only when cross-project priority, blockers, or resume order changes. Do not make the central log a duplicate of detailed goal histories.

## Session completion checklist

Before handing off, update this file and the project log with:
- What changed and where (paths, PRs, commits, workflow runs).
- What was actually executed, including exact tests/audits and their results.
- What is published versus only present in an artifact/branch/local workspace.
- Current counts/coverage only when freshly measured, with source and timestamp.
- Remaining gaps, blockers, retry/cooldown state, and the single next concrete action.
- Any user decision or constraint that future work must preserve.


## 2026-11-02 — Latest verified checkpoint: both duration provenance passes

- The timezone-aware ISO-8601 timestamp parser is published on `main`. Issue #113 preview passed: 8,172 legacy rows had valid timestamps and exact canonical ID/duration/source/matched-status alignment; 8,121 observations already existed and 51 MusicBrainz observations remained to add. Zero alias, file, duration, source, status, timestamp, or duplicate conflicts; 2,958 unknown-provider rows skipped; no provider requests or preview writes.
- Issue #114 apply reported success: 51 song files changed, backup created, post-write health passed, zero provider requests and zero Spotify playlist writes. Independent verification of published `songs/so/source-3e2d305ebc76ea39/song.json` confirms a MusicBrainz duration observation (139,000 ms, exact source and timestamp) is on main.
- Fresh read-only post-publication checks are queued: #115 audit, #116 health, #117 freshness review, #118 combined audit/health/confidence. Inspect issue comments and Actions status before treating them as complete.
- Next gate: use the fresh freshness report to quantify remaining unknown-age duration candidates; then complete the read-only duplicate-entity audit and implement/verify the provider-aware retry queue per [`RETRY_QUEUE_SPEC.md`](RETRY_QUEUE_SPEC.md). Provider calls stay disabled until the report demonstrates eligibility and retry budgets/cooldowns are clear. Sorter remains gated on these checks.

## Automatic playlist descriptions
- Implemented the deterministic profile-based description generator and regression tests in `scripts/spotify/spotify_playlist_descriptions.py` and `tests/test_spotify_playlist_descriptions.py`.
- Next: wire preview/confirmation into the playlist cloud controller, then schedule a bounded refresh for eligible managed playlists only. Preserve non-empty manual descriptions; require explicit `details` permission and unlock for writes; skip unchanged signatures; respect Spotify cooldown.
- Do not auto-edit personal playlists merely because their description is blank.


## 2026-11-02 — Recommendation intake + playlist follow-through default

- Default for every song SHIT recommends or proposes for a playlist: persist compact identity/discovery evidence in `assistant_data/recommendations/discovery_candidates.json` (not listening evidence), resolve/dedupe its Spotify identity, and make it eligible for canonical Library enrichment. Do not treat a recommendation as a play, like, acceptance, or negative signal if ignored.
- Default after any playlist addition: refresh the actual live playlist, verify duplicates/blacklist and identity, run the sequencer preview against the post-add contents, and review the sequence. Sorting is a required follow-through step, but automatic playlist reordering remains confirmation-gated; do not blindly write when transition evidence is low.
- Booze batch preview now records resolved tracks through `append_candidates` before staging, with an audit event. Fixed a missing `time` import that caused `booze20_preview` to fail before resolution. Needs a fresh workflow run and tests to verify end-to-end.
- First 15-track recommendation set is being assembled as a review batch; do not assume any item is absent until compared with a fresh live playlist snapshot.


## 2026-11-02 — Discovery-to-Library integration wired

- Commit `0703e77` adds a canonical Library sync step to `.github/workflows/enrich-music-metadata.yml` after the metadata enrichment stages and before summary/analytics rebuilds. It runs `scripts/music/sync_music_library.py`, which merges `discovery_candidates.json` into `MusicLibrary.put_catalogue` as `discovery_only` records and preserves the distinction from listening evidence.
- The workflow now triggers when discovery intake, its ingestion helper, the canonical sync script, or the workflow itself changes. This makes new discovery intake automatically schedule the normal enrichment workflow; the scheduled daily run also refreshes the canonical merge.
- Commit `f5d9b7a` corrects the audit output to report the Library's `songs` metric. The sync step fails closed if the canonical Library audit is not `ok`.
- Prior code/data tests on commit `6666be0` passed: compile, generated-data audit, full Library health/confidence checks, freshness-plan and unit tests. The integration workflow itself is now awaiting its first run; do not claim end-to-end verified until that run completes.
- Next: validate the workflow run and inspect its summary/artifact to confirm discovery-only records landed; then add a small regression test for discovery sync and confirm the post-add live sequence preview path. Do not change Spotify playlists during ingestion.

## 2026-11-02 — Recommendation blacklist/whitelist audit

- Found and fixed a real bypass: Tricky Daily's scoring path loaded playlist-scoped removal history, but hand-curated Booze/horror recommendation previews did not consult it and could re-suggest an exact removed track.
- Commits: `92f86c7` adds exact playlist-local block helper; `ea97b6c` applies it to curated Booze and horror previews; `7196fdd` adds regression tests for exact track/URI block and current-membership whitelist.
- Semantics: Daily recommendation removals remain soft ranking penalties (artist-level removals are not a blanket artist ban); curated manual batches hard-skip an exact previously removed track. A track currently present in that same playlist overrides its old removal and is whitelisted.
- Current Booze removal history has 3 records (Shakira “She Wolf”; The Prodigy “Voodoo People - Pendulum Mix”; Yeah Yeah Yeahs “Heads Will Roll - A-Trak Remix”). None overlaps the 15 additions in the last batch. The earlier batch predated this guard, so do not imply it was filtered at add time.
- CI triggered on commits above; verify final run #41415730381 before marking complete. Next: run current read-only feedback report / preview and inspect live removal + whitelist counts.

