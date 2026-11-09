## 2026-11-09 UTC — Central auth broker base deployment and callback diagnosis

- PR #185 merged the base broker and owner-only deployment workflow; PR #190/#191 merged subsequent Cloudflare and safe diagnostic fixes.
- Cloudflare production Worker `shit-auth-broker` version 14 now receives 100% traffic. Version metadata confirms migration v2 and the existing OAuth state/refresh-lease Durable Objects, but not the broker-owned credential-store binding/keyring. GitHub App secret metadata is `secret_text`.
- A redacted observability query found six Spotify callback failures in the prior 24 hours: four on version 13 at `broker.base_url_configuration`, two on version 14 at `broker.route_dispatch`. The exception contents and credential material were not retrieved.
- PR #187/#188 contain the encrypted credential store, OIDC refresh endpoint and nine-workflow migration. Prior checks are green on documented commits; latest callback-stage instrumentation needs fresh CI. Both PRs remain draft/unmergeable pending branch reconciliation.
- The base Worker deployment is not end-to-end authentication success. No Spotify credential persistence or auth-health pass has been verified, and no playlist operation was performed.
- Next: resolve PR branch ancestry, finish callback diagnostics, provision the missing keyring/client-secret bindings under the owner-controlled release gate, deploy the integrated version, then complete fresh owner consent and two read-only health checks.

---

## 2026-11-07 UTC / 2026-11-06 Eastern — Percent-encoded saved-item request verified

- Updated the shared Daily saved-item lookup to percent-encode each Spotify URI and retain the documented 40-URI maximum.
- Feedback observer #42318532288 passed 519 tests and completed read-only observation of 123 feedback rows using the encoded request format. All 60 current Daily tracks have current liked status observed as false; Last.fm remains available and playback tracker remains unknown due missing segment file.
- The current cycle's historical liked-at-add baseline remains unknown because the pre-fix 50-item request failed; it is not backfilled from the later observation.
- The next cycle will capture the baseline using the corrected helper.

---

## 2026-11-07 UTC / 2026-11-06 Eastern — Saved-item lookup batching and feedback refresh

- Spotify's current `GET /me/library/contains` endpoint accepts at most 40 URIs. The first successful live cycle's 50-item liked-baseline and post-add observation requests returned HTTP 400; playlist publication itself succeeded. The current liked-at-add baseline for the 60 tracks is therefore unknown and must not be backfilled from a later observation.
- Added `spotify_daily_feedback.query_liked_status()` with 40-URI batching and exact response-length checks. The Daily cycle and observation function now share it. Added regression tests for 81 URIs (40/40/1) and 60 tracks (40/20). Mainline Daily curator run #42317712007 passed 519 tests.
- Feedback observer run [#42317820148](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42317820148) succeeded: 123 feedback rows checked, all 60 current Daily tracks have a current liked observation (all unliked at observation time), Last.fm coverage available, playback tracker unknown because the segment file is absent.
- The feedback observation workflow now supports a push on its own workflow file for immediate post-cycle read-only refresh, alongside schedule/manual dispatch.
- Next scheduled Daily rotation after cooldown persistence fix remains unverified. Continue with recovery controls and then the approved recommendation-memory implementation.

---

## 2026-11-07 UTC / 2026-11-06 Eastern — First verified Tricky Daily production cycle

- **Live cycle:** workflow [#42316296314](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42316296314) completed successfully. The trigger was explicitly set to `action: cycle` for this user-authorized attempt. Production stage commit `e08baedf6c006322ff31abd4d11bc8169d69a123` and recovery backup `playlist_backups/20261107T000907379512Z_4yUVHSMQySfWeEowfIMcx7.json` were committed before Spotify mutation. State commit `d7ce8ec476b59d284d468bb4989ead8b0d109871` records `last_cycle_date_eastern=2026-11-06`, status completed, 60 after-URIs and stage SHA-256 `1dc211f78d4402bccd26a9d8e76349381468e930db5865e8770557bee6cd3c7e`.
- **Result:** exactly 60 tracks were published and read back in exact staged order; all URIs were unique/valid, zero blacklisted, and the description `Today's detour starts here.` was read back successfully. 26 prior tracks rotated out neutrally. The run also uploaded the recovery snapshot artifact. Daily curator tests #42316296368 and public security scan #42316296334 passed.
- **Stage proof:** stage-only workflow #42316048566 completed the durable stage/backup commit and committed-blob hash/order verification first. It contained 60 unique tracks from 60 distinct artists with zero blacklist overlap. The ignored `playlist_backups/` path required an explicit `git add -f`; that fix is now in `persist_daily_stage()`.
- **Post-cycle verification:** the same-day read-only `--verify-only` mode was initially short-circuited by the completed-date guard. Fixed the guard to exempt read-only verification only, added a regression test, and passed 517 tests in #42316716912. The actual post-cycle verification #42316824364 then confirmed 60 unique tracks, zero blacklist hits, and description `Today's detour starts here.`.
- **Snapshot reconciliation:** GET-only Daily snapshot workflow [#42316906860](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42316906860) passed and published commit `bae0cb6c435c6c12672b97bde88138ddbd9be0fe`. Snapshot at `2026-11-07T00:13:46.604200+00:00`: 60 accessible/unique tracks, 0 new manual removals, 58 total blacklisted, 3 idempotent removal-feedback events reconciled; reference catalog and removal baseline both report 60.
- **Safety reset:** `.github/test-triggers/tricky-daily-live-cycle.json` is now `action: verify-only`, `force: true`. Future edits to the test-trigger file cannot accidentally start another live replacement.
- **Remaining operational work:** the next scheduled Eastern-midnight cycle after PR #168's durable cooldown-persistence fix is not yet observed. Strict cron-to-DST matching and guided resume/rollback/discard remain open. Recommendation memory is approved but not implemented.
- **Listening coverage:** Last.fm available and liked-song observations present; Spotify playback tracker remains unknown because `playback_data/segments.jsonl` is absent. No-play inference must remain conservative.

---

## 2026-11-06 — Daily operational-first roadmap and recommendation memory

- User decision: stabilize Daily's actual refresh and publication process before expanding recommendation intelligence. First prove the protected no-write stage-only path end-to-end; then verify schedule/DST delivery, same-date idempotency, snapshot freshness and recovery behavior. No live playlist replacement or description mutation is authorized by this decision.
- Daily recommendation memory is now an approved product requirement. It will record each recommendation event and later outcomes across cycles, with separate provenance for Spotify playback, Last.fm scrobbles, likes/saves, manual removals, later retention, no observed play, not-yet-observed and unknown coverage. Repeated recommendations link to a shared track history but remain separate events. High-play-then-remove differs from unplayed-then-remove; track rejection does not automatically imply artist rejection. Memory must be idempotent, versioned, recoverable, auditable and subordinate to hard exclusions/whitelist policy. Historical rows with null evidence must not be backfilled as outcomes.
- The current Daily test trigger was re-read and is configured as `action: stage-only`, `force: true`. The persisted Spotify cooldown deadline is `2026-11-06T19:49:46+00:00`; it is past, but must be rechecked for manual-clear/fail-closed state before Spotify access. No stage-only run was dispatched as part of this documentation update.
- Documentation updates: Daily roadmap commit `3c6a6b87f5f1317431c72b087838ed78a88a4438`; Daily backlog commit `ca72ebfe52880d3db9097be8e4e10657210b8f57`; Daily action log commit `6ff577fbe340eee8b31b84384c27f7d637a12184`. No runtime or workflow code changed.

## 2026-11-06 — Tricky Daily immutable staging and failure-safe publication

- **Authorization:** continued Daily code, test, documentation and safe read-only verification work. No live Spotify track replacement or description mutation was authorized or performed.
- **Durable stage:** the cycle now builds a unique JSON record containing the exact ordered 60 URIs, candidate metadata, intended description, pre-write snapshot ID and URI order, recovery backup path, and SHA-256 over the complete record. In GitHub Actions, the stage, backup and pre-write evidence are committed/pushed to main before any Spotify write. The committed blob is re-read and hash-verified. A failed push or repository-head advance aborts before mutation.
- **Race protection:** the live playlist is re-read before staging and again after the stage commit. Identity, owner, name, description, snapshot ID, complete pagination, ordered URI list and lock state are checked; current blacklist/whitelist policy is reloaded and rechecked immediately before mutation.
- **Ambiguous write handling:** cloud replacement now reads live ordered URIs after a write exception. Exact target means the write applied despite a lost response; exact pre-write order means no mutation occurred; partial or unreadable results raise an explicit ambiguous error. The Daily runner persists a same-date idempotency guard for ambiguous outcomes. A surviving production stage also blocks same-date blind retries.
- **Post-write contract:** read-back must be complete, exactly 60 tracks, exact staged order, unique valid Spotify track URIs, valid primary artists, and free of current blacklist hits before completion is recorded.
- **Safe stage-only mode:** added a test-trigger action that exercises candidate generation, durable stage commit/read-back and pre-write checks but exits before any Spotify playlist write or description update. Test stages use a separate subdirectory and do not block production runs.
- **Verification:** full safe CI run #42268351897 passed 500 tests, including generated-data audit and canonical Library health/confidence checks. Tests cover stage hash/commit failure, repository concurrency, pending-stage guard, pre-write race, exact post-write validation, and ambiguous write reconciliation.
- **No-write stage-only attempt:** workflow run #42268583897 authenticated but Spotify returned HTTP 429 QUOTA_EXCEEDED during candidate search with Retry-After 5781 seconds. It failed before stage creation/commit; the workflow log confirms no playlist changes were attempted. No Spotify API calls were made after that response. Respect the entire Retry-After window before another provider call.
- **Remaining:** the actual GitHub Actions stage commit/push has not yet been exercised end-to-end because the stage-only attempt hit the provider quota before staging. Guided resume/rollback/discard from a surviving stage and a final provider-supported race guarantee remain open. No live cycle should run without separate user authorization.
- **Next:** after the provider cooldown has elapsed, retry only the no-write stage-only path and inspect the committed stage/backup. Keep live track and description mutations separately gated.

---
## 2026-11-06 — Tricky Daily runtime correction and verification recovery

- **Authorization:** user authorized Daily runtime/test corrections, safe verification, and a Daily-only snapshot refresh. Live playlist replacement/description mutation remains separately gated and was not performed.
- **Runtime:** force now bypasses only the clock-window gate; the same-Eastern-date idempotency check is independent of force. Spotify description read-back HTML-unescapes provider text. The source overview and midnight workflow overview comments were corrected to match the implementation.
- **Documentation:** updated the Daily cycle guide, roadmap, TODO, workflow catalogue (including the 19th workflow), active-session brief, loose ends, project log, test guide, and workflow/test contract language.
- **Verification evidence:** full-suite runs found stale contract assertions and comments after the runtime change; they were corrected iteratively. The latest confirmed pre-comment-fix full suite #42260512826 failed only because the midnight workflow YAML still carried the old `--force` comment; commit 4cab258d8114571a7fbb49240069a82e74d1335c corrected it. A fresh post-fix full-suite result is still required. Read-only live preflight #42260095302 passed and reported 29 live Daily items.
- **Snapshot boundary:** after fixing import precedence and orphaned reference-index memberships, snapshot-refresh run #42263830309 passed the 24-test focused schedule/import gate, authenticated, performed the full Spotify GET read, reconciled Daily catalog/index state, and published repository changes in commit `d24fb9acbc17a8acaff4e8e893a7681e91c8a5bd`. Current snapshot: 29 accessible/unique tracks at `2026-11-06T17:41:02.779553+00:00`; baseline 29; blacklist 55; whitelist 0. Daily track/artist index memberships now have zero stale or missing entries. The generated-data audit and full 481-test suite passed in run #42263946943; remote verification and read-only preflight also passed. No Spotify playlist mutation occurred.
- **Next:** finish the remaining P0 live-cycle safeguards: durable exact-order staging, pre-write live-snapshot race detection, ambiguous-write read-back reconciliation, and exact post-write order/count/uniqueness/blacklist verification. Keep live playlist mutation disabled until those safeguards are complete and the user separately authorizes a live cycle.

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

