# Maintainability & Documentation — Actions & Evidence

Newest entries first. Record verified outcomes separately from plans, assumptions and unverified artifacts.

## 2026-11-06 — Test-module overview audit uncovered another boilerplate class

- A repository code search found 11 test modules using generic `Purpose: Regression test module` / generic scope / generic related-file overviews, including playlist manager/cloud, Daily feedback/discovery, sequencing, reference-library, MusicBrainz ID, track-profile, playlist-intelligence and lyrics tests.
- Replaced those generic overviews with test-specific coverage summaries and direct implementation/guide links. Also made `tests/test_script_layout.py` describe its actual layout/documentation guard responsibilities.
- Extended `test_script_layout.py` to reject generic test-module overview boilerplate, so this second documentation-quality gap is now enforced rather than only manually noted.
- Updated `docs/CODE_DOCUMENTATION.md` and `docs/README.md` to document the stronger test-overview contract.
- **Verification:** changes are on draft PR #161; no local checkout/runtime was available to execute unittest here. Prior passing CI runs apply to earlier PR heads only. Exact current-head CI and full-history security scan remain required.
- **Next:** review the PR's current head and obtain exact-head CI/security results; continue semantic sampling of remaining test modules, guide claims, and goal handoffs.

## 2026-11-06 — Latest documentation audit continuation

- Reopened draft PR [#161](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/161) and inspected its current metadata: branch `docs/semantic-documentation-audit`, head `5ec318d6dd46de6741e73feb0f2dde1e6cc089e4`, base `main` at `a5fe4de6398e2a3d6651fa7e439d2cb898f4fe0a`; 83 changed files, 790 additions and 237 deletions. PR remains draft and unmerged.
- Manually sampled the PR-branch overviews for `scripts/spotify/spotify_playlist_manager.py`, `spotify_playlist_cloud.py`, `spotify_reference_library.py`, and `scripts/music/migrate_full_music_library.py`. The manager now identifies its local token/config/backup/audit/cooldown files and confirmation/backup/read-back safety model; the cloud handler documents owner verification, deny-by-default controls, blacklist, preview/confirmation and delegation; the reference library distinguishes read-only snapshots from bounded playability refresh and backup-protected song-record writes; the migration overview identifies offline inputs and non-invention of missing mood evidence.
- Confirmed CI run #42150802119 passed on earlier PR head `1bbfed67ae63c77628f6d8b775b7d12c50060d11`, including compilation, generated-data audit, full read-only Library health/confidence checks, freshness planning, documentation checks and unit tests. Full-history security scan #42150801849 also passed on that earlier head.
- The PR has since advanced to `5ec318d6dd46de6741e73feb0f2dde1e6cc089e4`. The connected commit-status/workflow-run lookups returned no checks for this exact head, so the earlier passing results must not be represented as verification of the current head. Current-head CI and security verification remain outstanding.
- No application code, provider jobs, canonical data, playback history or Spotify playlists were changed in this continuation. No workflow YAML was edited.
- **Next:** obtain current-head CI and security results; inspect remaining test-module overviews and technical guide claims against source; complete semantic reconciliation before merging PR #161.

## 2026-11-06 — Documentation quality checks passed after compatibility fixes

- First PR validation run #42149665344 failed the new compatibility-overview check for three wrappers: `compat/migrate_full_music_library.py`, `compat/migrate_music_library.py` and `compat/music_library.py`. Their bottom overviews were updated to name the exact maintained `scripts/music/` implementation.
- Latest draft PR head `5b8bfab94064e74100c6b3ac183817b6a3f4d4bd` passed Daily curator tests run #42149783445.
- Successful checks included Python compilation, generated-data audit, full canonical Library health check, full Library confidence audit, bounded freshness planning, maintained-file documentation checks, and full unittest discovery.
- This confirms the new implementation-overview quality test, compatibility references, complete technical-guide index, repository-wide Markdown local-link check, workflow-overview checks and existing unit tests passed on that PR head.
- Public repository security scan #42149783463 subsequently succeeded on the earlier head. The latest PR head `31e8f3811ac7791dfc11ed560506ae138ea2213a` passed Daily curator tests run #42150601947; complete-history security scan #42150601862 is still in progress. Recheck it before merge.

## 2026-11-06 — Documentation quality expansion and all-workstream pause recorded

- **Source overview audit:** rewrote 32 maintained implementation overviews across `scripts/analytics/`, `scripts/lastfm/`, `scripts/music/` and `scripts/spotify/` to replace generic fallback boilerplate with source-specific purpose, inputs, outputs, evidence semantics, side effects, safety boundaries and run instructions.
- **Guide navigation:** expanded `docs/README.md` to link all 21 technical guides; removed a duplicated maintenance paragraph in `project/goals/README.md`.
- **Automated quality gates:** draft PR #161 adds repository-wide local Markdown-link checks, complete docs-guide index coverage, specific workflow overview checks, non-boilerplate implementation overview checks and compatibility-to-source references. Checks must pass on the latest PR head before merge.
- **Workflow documentation:** nine workflow YAML overviews were made specific. `docs/WORKFLOWS.md` now warns that comment-only edits to workflow YAMLs can trigger path-filtered automation. The resulting unintended runs and failures are recorded above.
- **Priority propagation:** added an explicit documentation-only pause/override to all 12 non-documentation goal roadmaps and the goal index, so a new session cannot mistake a queued feature next-step for current authorization.
- **PR:** [#161](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/161), draft, branch `docs/semantic-documentation-audit`; current head is being checked by CI. Do not merge until all tests pass and any newly discovered documentation defects are fixed.
- **Status:** substantial file-level quality improvements are staged in a draft PR; the repository-wide documentation audit remains incomplete. The complete tracked-file inventory, semantic guide review, all goal README/ACTIONS reconciliation, and fresh-session simulation remain outstanding.

## 2026-11-06 — Update Last.fm History publication also failed on shared-state conflicts

- Run #42146153098 completed its provider/data steps successfully: Last.fm history import, artist genre/mood/theme enrichment, recent-top-200 track tag enrichment, duration prioritization, recording-ID resolution, AcousticBrainz fetch and derived statistics all completed.
- The final publication step failed while rebasing commit `137fab61` ("Update Last.fm history and assistant analytics"). Git reported **120 unique conflicted paths**: 59 canonical music Library files and 61 Spotify playlist snapshots/reference files. The conflict set reflects the concurrent Reference Library commit `3e989e3` changing the same shared generated state.
- The Last.fm import and analytics generated in the workflow workspace were therefore **not published**. Do not update mainline archive counts or claim those enrichment results as canonical.
- This confirms a second shared-writer race in the same incident: Reference Library publication overlapped with the broad Update pipeline. No Spotify playlist writes occurred.
- **Deferred remediation:** shared writer serialization across all workflows touching `assistant_data/music/library/` and `assistant_data/spotify/`; stale-base conflict handling that does not blindly overwrite concurrent state; explicit publication conflict reporting and recovery. Do not fix during the documentation-only phase.

## 2026-11-06 — Accidental workflow execution during workflow-overview documentation

- **Context:** comment-only edits to workflow YAMLs on `main` matched their push-path filters and started data workflows. This was unintended during the documentation-only phase; the prevention rule is now recorded in `docs/WORKFLOWS.md`.
- **Reference Library:** run #42146148971 succeeded and published commit `3e989e33282efab6cc1416e35970e7c59af5f056`. It changed 249 files (184 Library records, 63 Spotify reference/history files, 2 removal-state files), with 4,445 additions and 644 deletions. It refreshed repository snapshots/removal feedback; it did not mutate any Spotify playlist.
- **Enrich Music Metadata:** run #42146121471 completed enrichment steps but failed at publication while rebasing commit `cbae47de` ("Enrich music durations and artist profiles"). Git reported multiple add/add conflicts in canonical song JSON files that had just been added by the Reference Library commit. The enrichment changes were not published. This is direct evidence of a shared generated-Library publication race; no manual conflict resolution or retry was attempted.
- **Acoustic Metadata Enrichment:** run #42146097964 completed 100 AcousticBrainz batches of 25 IDs each: 2,500 candidates checked, 207 profiles found, 2,293 misses, 322 total stored profiles and 3,678 negative-cache entries. Optional GetSongBPM was skipped because GETSONGBPM_API_KEY was absent. Publication then failed because `git add` included `assistant_data/music/getsongbpm_lookup_state.json`, which did not exist (exit 128). No AcousticBrainz changes were published. This is a concrete workflow robustness defect when an optional provider state file is absent.
- **Update Last.fm History:** run #42146153098 was still active at the latest check, in the track-profile enrichment phase after successful Last.fm import, artist-profile enrichment, recent-top track tag enrichment, duration prioritization, recording-ID resolution and AcousticBrainz fetch. Inspect its terminal result and any commit before resuming.
- **Safety boundary:** none of these runs wrote to Spotify playlists. Reference snapshots and removal state were committed; the two failed enrichment publication steps did not publish their workspace outputs.
- **Follow-up (after documentation phase):** serialize all workflows that write shared Library paths or add stale-base conflict detection/rebase verification; make optional provider state paths conditional before staging; add tests for absent optional output files. Do not implement these fixes during the current documentation-only phase.
- **Outcome:** unintended automation side effects fully identified for two terminal runs; one run still requires final inspection. Record these failures as findings, not successful enrichment publication.

## 2026-11-05 — Workflow overview audit found boilerplate; push-trigger side effects recorded

- **Finding:** all 17 workflow files are listed in `docs/WORKFLOWS.md`, but nine workflow YAMLs had generic bottom overviews that did not describe their actual triggers, credentials, writes or safety boundaries. This passed the existing FILE OVERVIEW presence test but failed the intended documentation-quality standard.
- **Changes:** replaced the generic overview blocks in `acoustic-metadata-enrichment.yml`, `backfill-music-durations.yml`, `daily-curator-tests.yml`, `enrich-music-metadata.yml`, `playlist-manager-check.yml`, `spotify-daily-feedback-observation.yml`, `spotify-playlist-manager.yml`, `spotify-reference-library.yml`, and `update.yml` with workflow-specific contracts. Added a warning to `docs/WORKFLOWS.md` that comment-only edits to workflow YAMLs can trigger path-filtered workflows.
- **Verification:** Daily curator tests and public-repository security scans passed on the workflow-overview commits through `217bb36049a1791f467c2ed9fbcda34c36daf602`; examples include run #42146153109 and #42146153169.
- **Operational side effect:** editing workflow YAML files on `main` triggered configured push workflows. Reference-library run #42146148971 completed successfully and produced commit `3e989e33282efab6cc1416e35970e7c59af5f056`: 249 files changed (184 canonical Library records, 63 Spotify reference/history files, and 2 removal-state files), 4,445 additions and 644 deletions. It refreshed snapshots and removal feedback; it did **not** write to Spotify playlists.
- **Other triggered jobs:** Update Last.fm History run #42146153098, Enrich Music Metadata run #42146121471, and Acoustic Metadata Enrichment run #42146097964 were still in progress at the latest check. Their completed steps included Last.fm import/artist enrichment, MusicBrainz duration/recording-ID lookups, and strict MusicBrainz ID resolution respectively; track-tag/AcousticBrainz enrichment was still running. These runs were not part of the requested documentation-only scope. The available GitHub connection did not expose a workflow-cancellation action, so they could not be stopped from this session.
- **Lesson / prevention:** inspect all workflow push-path filters before committing workflow documentation. A comment-only change is still a triggering file change. Future overview edits should be staged and reviewed with their trigger consequences understood; do not repeat this side effect.
- **Separate code-documentation audit:** inspection of maintained source overviews found further generic fallback text in analytics, Last.fm, music and Spotify modules. Marker presence is not proof of a useful overview; continue semantic review and repair those files.
- **Outcome:** nine workflow overviews improved and tested; workflow audit remains incomplete; provider refresh side effects are being monitored and must be reconciled in the handoff.
- **Next:** monitor the three remaining runs to terminal state and inspect any resulting commits; then improve the source-module overview quality and strengthen tests so generic fallback boilerplate is rejected.

## 2026-11-05 — Live repository inventory and documentation audit resumed

- **Purpose:** continue the user-directed documentation-only phase and verify the current repository rather than relying on prior chat summaries.
- **Repository:** canonical `TrickySturluson/spotify-helper-information-tracker`, default branch `main`, inspected tree SHA `b542ceab2c40f6910a91ea3fcb84c204fc412c2d`.
- **Inventory evidence:** 13 goal directories were listed individually; all 13 contain ROADMAP.md, README.md and ACTIONS.md. The current workflow directory contains 17 YAML files. Maintained implementation directories list 7 analytics modules, 1 Last.fm module, 28 music modules and 19 Spotify modules. The repository also contains compatibility launchers, tests, canonical data, generated analytics/Library records, playback observations, playlist state and the CLI.
- **Automated verification:** latest observed Daily curator run #42144512658 and public repository security scan #42144512423 both succeeded on the inspected main SHA. Existing tests check goal workspace structure, selected local links, workflow catalogue coverage and bottom FILE OVERVIEW marker presence across maintained Python/workflow files.
- **Important limitation:** the recursive Git tree API response was truncated by the very large generated per-record Library tree. It is not a complete inventory. Directory-scoped listings are adequate for the maintained code/workflow/goal counts above, but a full checkout plus `git ls-files` is still needed for exhaustive tracked-path reconciliation.
- **Accuracy finding:** passing marker/link tests do not prove that every FILE OVERVIEW, workflow summary, technical guide, or roadmap remains semantically accurate. Manual source-to-document review remains required.
- **Open work observed:** Daily PRs #158 (Discover Weekly exposure/feedback), #159 (DST schedule gating), and #160 (exposure-aware discovery) were open at audit time. They must remain clearly distinguished from merged mainline behavior until reviewed and merged.
- **Changes:** updated `project/NEXT_WORK.md` to make documentation the sole active priority and record the verified baseline/next actions; updated this roadmap and action history. No application code, data, provider state, or Spotify playlists were changed.
- **Outcome:** audit resumed; documentation remains in progress and is not declared complete.
- **Next:** obtain a complete tracked-file inventory; audit all maintained file overviews and operational guides against source; reconcile all goal workspaces, open PRs/issues and current workflow evidence; add targeted checks for actual gaps; complete the fresh-session simulation.

## 2026-11-05 — Playlist Sequencing split into an independently resumable workstream

- **Reason:** the ordering engine has distinct user requirements (smooth transitions first, configurable energy journey/peak, sections, track-level evidence) and safety requirements (preview, explicit confirmation, stale-preview rejection, live read-back). It should not be buried inside the broader recommendation/fit-model workspace.
- **Changes:** added project/goals/playlist-sequencing/ROADMAP.md, README.md and ACTIONS.md; linked the workspace from the goal index, project-wide roadmap and docs index.
- **Boundary preserved:** the five-axis playlist-fit model remains a separate preview-only system and is not wired into the sequencer.
- **Verification:** documentation paths and stated behavior were cross-checked against the transition-scoring guide, Booze preset guide and existing playlist-intelligence roadmap. A fresh CI run is required to verify the dynamic goal-directory check.
- **Outcome:** dedicated workstream documentation created; runtime behavior unchanged.
- **Next action:** inspect CI and audit sequencer implementation/tests against this roadmap.

## 2026-11-05 — Tricky Daily split into an independently resumable workstream

- **Reason:** Daily is an active, safety-sensitive system with its own 60-track product contract, forced-run parity, feedback model, schedule, recovery and live-verification requirements. Keeping it only as a subsection of Playlist Intelligence made its own roadmap less discoverable.
- **Changes:** added project/goals/tricky-daily/ROADMAP.md, README.md and ACTIONS.md; linked the new workspace from the goal index, project-wide roadmap and docs index. The existing Daily TODO and cycle guide remain detailed technical references.
- **Guardrail:** the documentation contract test discovers every goal directory dynamically and requires ROADMAP/README/ACTIONS, so the new goal is automatically included in CI coverage.
- **Verification:** GitHub file creation succeeded. A new CI run is required to verify the dynamic goal check after this workspace was added. No code, playlist, Library data or provider state was changed.
- **Outcome:** dedicated workstream documentation created; CI verification pending.
- **Next action:** inspect the latest CI run, then audit Daily implementation and workflow evidence against the new P0 roadmap without assuming unchecked backlog items are complete.

## 2026-11-05 — Repository index corrected and test-suite guide added

- **CI verification:** Daily curator tests run #42143513931 passed on commit 7d23db6a12ec80eb0830a84738dab3c856ef8dff after the directory-guide additions and index correction. The run completed successfully, including the documentation-layout step and full unittest discovery. A later run #42143770161 also passed on commit 79af1f93756878d27a40a02c3a2abc4b627643ce after the dedicated Tricky Daily workspace was added. The new Playlist Sequencing workspace is newer and awaits its own run.

- **Finding:** the previous `docs/REPOSITORY_FILE_INDEX.md` described itself as a complete tracked-file catalogue and listed only 239 assistant_data files, while the current canonical music Library contains a much larger per-record tree. The recursive Git tree API also reported `truncated: true`, so it was not safe to claim a complete recursive inventory from that response.
- **Changes:** replaced the stale exhaustive snapshot with a source and data-family index. It documents code/workflow/test ownership, canonical Last.fm data, canonical structured Library records, generated analytics, optional playback observations, Spotify state/feedback, and commands to inspect the exact current Git inventory. Added `tests/README.md` and linked it from the documentation index.
- **Verification:** repository directories and goal workspaces were inspected through GitHub contents listings. The previous docs contract test passed on commit `38ad97e`; the new directory-guide requirement and corrected index have not yet had a fresh CI run.
- **Outcome:** index scope corrected; further CI verification pending.
- **Next action:** inspect the new test run after the latest commits, fix any failures, then audit source/workflow file overviews against the actual tree and stale operational descriptions.

## 2026-11-05 — Automated documentation contract checks added

- **Purpose:** catch missing documentation foundations and broken navigation before future changes can quietly erode continuity.
- **Changes:** added `tests/test_documentation_contract.py`. It checks repository control documents, every goal folder's ROADMAP/README/ACTIONS, root assistant instructions, coverage of major repository domains in the docs index, and local links from the main fresh-session entry points. Updated `docs/README.md` and `docs/CODE_DOCUMENTATION.md` to explain the checks.
- **Execution:** test is included in standard unittest discovery; the existing `.github/workflows/update.yml` runs full unittest discovery before publishing refreshed data. No workflow YAML change was required.
- **Verification:** file creation succeeded. The new test has not yet been executed in GitHub Actions; do not mark the guardrail verified until a successful run is inspected.
- **Outcome:** implemented; CI verification pending.
- **Next action:** inspect the latest workflow run after this commit. If tests fail, diagnose and fix only the actual broken paths/contract assumptions, then add coverage for source inventory and stale file-index detection.

## 2026-11-05 — Repository navigation and mandatory agent instructions added

- **Purpose:** make the documentation system discoverable and enforceable from the repository root, not dependent on a chat summary.
- **Changes:** added root AGENTS.md; added docs/README.md as the cross-cutting documentation index; added project/ROADMAP.md as the cross-workstream roadmap; linked all three from the repository README and documented the expansion in project/NEXT_WORK.md.
- **Existing foundation verified:** project/DOCUMENTATION_RULES.md, project/NEXT_WORK.md, project/LOOSE_ENDS.md, project/PROJECT_LOG.md, the goal index and 11 goal workspaces already exist on main. Each goal is intended to have ROADMAP/README/ACTIONS.
- **Verification:** fetched and inspected the existing root README, documentation rules, project handoff/log/index, loose-ends register, maintainability workspace, playlist-intelligence workspace, Tricky Daily backlog/cycle guide and privacy/description guides. New files were created successfully on the repository default branch. No code, Library data, provider state, listening history or Spotify playlists were changed.
- **Limitation:** this is not yet a full tracked-file inventory audit. The complete file-index accuracy, per-file overview coverage, link integrity, goal-file completeness and current GitHub run/PR status remain to be verified.
- **Outcome:** navigation/control structure expanded; documentation coverage audit still in progress.
- **Next action:** obtain the complete tracked-file tree, compare all scripts/modules/workflows/tests/schemas/data contracts with documentation, fix the highest-risk gaps, then add automated checks and perform a fresh-session resume test.

## 2026-11-05 — Mandatory project roadmaps and same-session documentation rule

- **User direction:** every project/workstream must have a durable roadmap so future assistant sessions can continue without previous chat knowledge; documentation must explicitly require ongoing maintenance.
- **Changes:** added `project/DOCUMENTATION_RULES.md`; created `ROADMAP.md` for all 11 goal workspaces; linked each goal README to its roadmap; updated the goal index, repository README, project control-centre README, NEXT_WORK handoff, and PROJECT_LOG.
- **Required structure:** each goal has a roadmap for plan/status/acceptance/next action, a README for scope/design/invariants, and ACTIONS for dated implementation and verification evidence.
- **Verification:** all 11 indexed goal workspaces received a roadmap. Changes are documentation-only; no code, Library records, provider state, listening history, or Spotify playlists were changed.
- **Outcome:** complete for the currently indexed goal workspaces.
- **Next action:** audit roadmap accuracy against latest main, PRs, issues and workflow runs; audit per-file documentation coverage and keep this standard for all new workstreams.


## 2026-11-01 — Goal workspace initialized

- **Action:** established this goal's dedicated documentation and action-history location.
- **Context:** 2026-11-01: Added the goal-based workspace design on branch `codex/goal-workspaces`. This folder's README and ACTIONS are part of that proposed structure. Next: finish all goal folders, update central index/handoff, verify links, and merge.
- **Outcome:** documentation initialized; no runtime implementation or data mutation implied unless explicitly stated above.

## 2026-11-01 — Per-goal workspaces merged; repository-wide documentation audit opened

- **PR:** #67 https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/67
- **Merge:** squash merge succeeded as `4ad701c2c4f36b9f6f73926e83db1f84cbfbcc2c`.
- **Verification:** PR checks `tests` and `Scan complete Git history for secrets` both completed successfully. The merge was documentation-only; no Library records, provider checkpoints, listening history or Spotify playlists were changed.
- **Audit scope:** reviewed repository directory/workflow inventory, open issues/PRs, and prior SHIT conversation decisions. Added `project/LOOSE_ENDS.md` as a cross-project index; detailed findings are logged in each goal history.
- **Loose ends:** audit every maintained Python script and workflow for concise in-file purpose, inputs/outputs, side effects, data paths, safety boundaries and run/test guidance. Existing `scripts/README.md` is a directory overview, not proof every file has its own overview. Add automated documentation coverage checks.
- **Failed experiments / lessons policy:** action histories must record failed tests, failed workflow steps, rejected/abandoned approaches, performance/rate-limit problems, root-cause findings and why a decision changed—not only successful work. Never expose credentials or raw secret values in logs.
- **Outcome:** goal workspace foundation merged; broader documentation audit remains in progress.
- **Next action:** use the loose-ends register to work through each goal and verify per-file documentation coverage.

## Entry template

### YYYY-MM-DD — Action
- **Purpose:**
- **Changes / files:**
- **Execution:** command, workflow run, PR, commit
- **Verification:** exact tests/audits, including failing steps and diagnostic evidence
- **Outcome:** complete / partial / blocked / deferred
- **Failed or abandoned approaches:** what was tried/rejected and why; never omit meaningful failures
- **Performance / provider limits:** latency, request volume, cooldowns, quotas, caching, or inefficiencies observed
- **Lessons learned / decision changes:**
- **Next action:**
- **References:**

## 2026-11-05 — All 13 goal workspaces pass documentation contract CI

- **Verification:** Daily curator run #42143913729 completed successfully on commit ec05a646db68e9931c5562f34124e1c8998c6997 after the Playlist Sequencing workspace was added. The workflow completed generated-data audit, read-only full Library health/confidence checks, bounded freshness planning, maintained-file documentation checks, and full unittest discovery. Earlier run #42143770161 passed after Tricky Daily was added.
- **Result:** dynamic goal discovery now verifies all 13 goal folders have ROADMAP.md, README.md and ACTIONS.md. The new documentation contract and directory-guide checks are included in the full unittest suite.
- **Limit:** these checks verify navigation and required structures; they do not yet prove every Markdown statement matches live implementation or every workflow overview accurately describes permissions and side effects.
- **Next:** audit every maintained Python/workflow overview against source and add a read-only report for stale links, missing technical contracts and generated-data ownership.
\n## 2026-11-05 — Workflow catalogue and working Markdown-link audit verified\n\n- **Changes:** added docs/WORKFLOWS.md with the 17 workflow names, triggers, permission boundaries, credential variable names, primary actions and side effects. Added a dynamic test requiring every .github/workflows/*.yml file to appear in the catalogue.\n- **Audit correction:** inspection found the Markdown-link test regex was over-escaped and therefore did not reliably capture ordinary links. Corrected it in commit 9a62487581afcb3116fa21a1a42ea39c9a5b9c18 so primary control-document links are actually parsed and checked. Earlier passing runs verified other contract checks but must not be cited as proof of link validation.\n- **Verification:** Daily curator run #42144349548 passed on commit 9a62487581afcb3116fa21a1a42ea39c9a5b9c18. Compile, generated-data audit, full Library health/confidence, bounded freshness planning, maintained-file documentation check and full unittest discovery all completed successfully. This run includes the corrected link regex and workflow catalogue coverage.\n- **Outcome:** workflow inventory and primary-link contract checks implemented and CI-verified. Full semantic accuracy of every workflow summary and every implementation overview remains a manual audit task.\n- **Next:** audit per-file overview accuracy and cross-reference technical documentation against current source; record gaps by risk rather than treating presence of an overview as proof of correctness.\n