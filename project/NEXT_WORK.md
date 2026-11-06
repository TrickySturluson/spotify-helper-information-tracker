# SHIT — Next Work
> **Mandatory continuity instruction:** Read [DOCUMENTATION_RULES.md](DOCUMENTATION_RULES.md) before continuing. Read the relevant goal's `ROADMAP.md`, `README.md`, and `ACTIONS.md`; update them during the same session as work proceeds. The roadmap is the durable plan; this file is the current cross-project handoff.

This is the authoritative session handoff. Read this file first when resuming work, then read [LOOSE_ENDS.md](LOOSE_ENDS.md), [PROJECT_LOG.md](PROJECT_LOG.md), and [README.md](../README.md). Update this file whenever priorities, blockers, or verified status change.

## Cross-project loose-ends register

Read [LOOSE_ENDS.md](LOOSE_ENDS.md) for the current audit index across migration, provider coverage, enrichment, analytics, discovery, playlists, workflows and documentation. Each entry links to its goal history. Update the register when an item is resolved, deferred or newly discovered.

## 2026-11-06 — Documentation-first priority reaffirmed; live repository audit resumed

**Latest continuation:** Draft PR [#161](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/161) is on `docs/semantic-documentation-audit` at head `5ec318d6dd46de6741e73feb0f2dde1e6cc089e4`, based on main `a5fe4de6398e2a3d6651fa7e439d2cb898f4fe0a`. Earlier tests #42150802119 and security scan #42150801849 passed on prior head `1bbfed67ae63c77628d6f8b775b7d12c50060d11`; they do not verify the current head. The connected GitHub status/run lookup returned no checks for `5ec318d`, so current-head CI/security are outstanding. Do not merge until exact-head checks pass. Manual samples of playlist manager, cloud handler, reference library and offline migration overviews on the PR branch now show substantially more specific operational contracts.


**Active priority: documentation only.** Do not begin feature development, playlist operations, enrichment runs, or unrelated project work until the documentation audit reaches the completion standard in the Maintainability & Documentation roadmap.

### Verified repository baseline
- Canonical repository: `TrickySturluson/spotify-helper-information-tracker`, default branch `main`; current inspected main head is `a5fe4de6398e2a3d6651fa7e439d2cb898f4fe0a` (includes the documentation-control updates and the completed Reference Library snapshot commit). The earlier baseline SHA `b542ceab2c40f6910a91ea3fcb84c204fc412c2d` is historical.
- Root structure includes `AGENTS.md`, `project/DOCUMENTATION_RULES.md`, the project control centre, `docs/`, `scripts/`, `compat/`, `tests/`, `data/`, `assistant_data/`, `playback_data/`, `.github/`, and the `shit.py` CLI.
- The current goal index contains **13** goal workspaces. Every workspace contains ROADMAP.md, README.md and ACTIONS.md.
- Current `.github/workflows/` inventory contains 17 workflow YAML files; `docs/WORKFLOWS.md` exists and the documentation contract test requires every workflow filename to appear in it.
- Maintained Python implementation is organized under analytics (7 modules), Last.fm (1), music (28), and Spotify (19); compatibility launchers, tests, and workflow YAMLs are also covered by the bottom-of-file overview test.
- Documentation tests are part of unittest discovery. Latest observed Daily curator test run #42144512658 and public repository security scan #42144512423 both completed successfully on the inspected main SHA. This verifies the automated checks ran successfully; it does **not** prove semantic accuracy of every overview or technical guide.
- The recursive Git tree API response was truncated because generated Library records make the tree very large. Do not use that truncated response as a complete tracked-file inventory. Use directory-scoped listings for maintained code and `git ls-files` in a complete checkout for the authoritative full inventory.

### Workflow overview work and operational side effect
- Replaced generic bottom overviews in nine workflows with workflow-specific trigger, credential, write, safety and related-code descriptions. The workflow catalogue remains the source for the full 17-workflow matrix.
- Editing workflow YAML on main triggered path-filtered jobs even though only comments changed. Reference Library run #42146148971 completed successfully and committed `3e989e33282efab6cc1416e35970e7c59af5f056`, changing 249 generated files: 184 Library records, 63 Spotify reference/history files and 2 removal-state files. It refreshed repository snapshots/removal feedback; it did not write to Spotify playlists. The Daily removal blacklist gained two manual removals from the 2026-11-05 pre-cycle snapshot: Joseph Dubay — `Loser Boy` and Mal Blum — `Fine!` (playlist ID `4yUVHSMQySfWeEowfIMcx7`).
- Enrich Music Metadata #42146121471 and Acoustic Metadata Enrichment #42146097964 both reached terminal failure at publication; exact conflict/pathspec evidence is recorded below. Update Last.fm History #42146153098 also reached terminal failure with 120 unique shared-state conflicts; its workspace outputs were not published. No workflow cancellation action was exposed by the connected GitHub interface.
- Do not repeat this side effect. The workflow catalogue now explains that comment-only YAML edits can trigger configured push workflows; inspect push path filters before any future workflow edit.

### Documentation PR verification
- Draft PR #161 initially failed its new compatibility-reference test on three wrappers; those overviews were corrected.
- Daily curator tests run #42149783445 passed on head `5b8bfab94064e74100c6b3ac183817b6a3f4d4bd`, including compile, data audit, full Library health/confidence checks, bounded freshness plan, maintained-file documentation checks and full unittest discovery.
- This verifies all-Markdown local links, all 21 technical-guide index entries, non-boilerplate implementation overviews, compatibility references and specific workflow overviews on that head.
- Public repository security scan #42149783463 remained in progress at the last check. Confirm terminal success and ensure PR #161 has not advanced to a different untested head.

### Final workflow side-effect results (2026-11-06)
- Reference Library #42146148971 succeeded and committed `3e989e33282efab6cc1416e35970e7c59af5f056` (249 files: 184 Library records, 63 Spotify reference/history files, 2 removal-state files; 4,445 additions / 644 deletions). Repository snapshots/removal feedback changed; no Spotify playlist was written.
- Enrich Music Metadata #42146121471 failed publication during rebase with add/add conflicts in canonical song JSON files introduced by the Reference Library commit. Its workspace enrichment was not published.
- Acoustic Metadata Enrichment #42146097964 completed 100 batches (2,500 IDs; 207 found; 2,293 misses; 322 total profiles; 3,678 negative-cache entries), skipped optional GetSongBPM because its key was not configured, then failed at `git add` because `assistant_data/music/getsongbpm_lookup_state.json` did not exist. No acoustic profile changes were published.
- Update Last.fm History #42146153098 completed provider/data steps but failed publication while rebasing commit `137fab61`; 120 unique conflicts affected 59 music Library paths and 61 Spotify playlist snapshot/reference paths. Its Last.fm import, analytics and enrichment workspace outputs were not published.
- These accidental workflow runs are documented as an incident. Do not rerun or repair enrichment workflows during the documentation-only phase. Once docs are complete, the operational backlog must include shared-writer serialization/stale-base conflict handling and conditional staging of optional provider files.

### Current open pull requests observed during this audit
- #161 — documentation quality expansion (draft PR; branch `docs/semantic-documentation-audit`). It contains 32 source overview rewrites, the complete docs index and expanded quality/link tests. Wait for CI and keep it unmerged until the audit is complete.
- #158 — Discover Weekly exposure and feedback tracking (open, non-draft).
- #159 — Tricky Daily DST schedule gating (open, non-draft).
- #160 — exposure-aware Tricky Daily discovery (open, non-draft).
- #121 — offline sorter evaluation and ingestion watchdog spec (open draft).
- #120 — incremental Library enrichment and sorter development (open draft).
- #65 — read-only Library coverage planner (open draft).
- #60 — provenance-aware recommendation ingestion (open, non-draft).
Treat all eight open PRs as proposals, not merged behavior. Reinspect their diffs, current base/head relationship and checks before updating mainline documentation or selecting future work.

### Findings and remaining audit work
- The documentation architecture is substantial and already includes 13 goal workspaces, 22 cross-cutting guides in `docs/`, the central handoff/loose-ends/log/roadmap, directory guides, workflow catalogue, and automated documentation contract tests.
- Mainline's existing documentation contract verifies required control files, goal workspace structure, major-domain navigation, selected local links, workflow catalogue coverage, and bottom FILE OVERVIEW presence. It does not yet semantically compare every overview or guide with the implementation. Draft PR #161 extends this with all-Markdown link checks, complete guide indexing, workflow-overview quality checks, implementation boilerplate rejection, and compatibility-to-source checks; these new checks passed on PR head `31e8f3811ac7791dfc11ed560506ae138ea2213a` in run #42150601947; the PR remains unmerged and the current security scan #42150601862 is in progress.
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

