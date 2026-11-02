# Discovery & Recommendations — Actions & Evidence

Newest entries first. Record verified outcomes separately from plans, assumptions and unverified artifacts.

## 2026-11-01 — Goal workspace initialized

- **Action:** established this goal's dedicated documentation and action-history location.
- **Context:** 2026-11-01: User requirement to ingest suggested/recommended tracks recorded in central handoff. PR #60 identified; implementation and tests not yet verified. Next: review PR #60 and preserve strict evidence separation.
- **Outcome:** documentation initialized; no runtime implementation or data mutation implied unless explicitly stated above.

## 2026-11-01 — Project-wide audit: recommendation intake CI/security failures recorded

- **PR:** #60 https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/60 (open, not merged).
- **Observed checks:** compile, generated-data audit and maintained-file documentation steps passed; unit-test step failed; full-history secret scan failed.
- **Not yet known:** test failure root cause and whether the secret-scan finding is real, historical or a false positive. No suppression/merge decision should be made without inspecting redacted evidence.
- **Loose ends:** diagnose tests and secret scan; validate candidate dedupe against Spotify IDs, ISRCs, recording MBIDs and aliases; verify canonical writer integration and that discovery exposure/acceptance/add/save/play/reject/ignore remain distinct from listening and preferences.
- **User requirement:** every song suggested, recommended, surfaced or otherwise introduced by a discovery workflow should be eligible for Library intake even if never played or saved. Preserve source, prompt/seed/context, capture time, identity confidence and observable response.
- **Failed approach / lesson:** recommendation exposure is not a play, save, like or confirmed preference. Never feed candidate count directly into scrobble or preference analytics.
- **Outcome:** proposed implementation only; PR remains open and checks are failing.
- **Next action:** inspect sanitized unit-test output and redacted Gitleaks result; then fix and rerun both checks.

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


## 2026-11-02 — Canonical Library integration

- Wired `.github/workflows/enrich-music-metadata.yml` to run `scripts/music/sync_music_library.py` after enrichment and before summary/analytics generation.
- Workflow push paths now include `scripts/music/sync_music_library.py`, `scripts/music/discovery_ingestion.py`, and `assistant_data/recommendations/discovery_candidates.json`, so a new discovery intake triggers the integration workflow. Daily schedule remains a backstop.
- The sync uses the canonical `MusicLibrary.put_catalogue` writer, preserving `discovery_only` status and discovery evidence separately from Last.fm scrobbles, Spotify playback, saved/liked status and preference feedback. Audit failure stops the workflow.
- Commits: `0703e77` integration; `f5d9b7a` audit metric correction. Baseline tests on `6666be0` passed; integration runtime verification pending.
- Next: inspect first integration run, verify the new candidate records in the canonical Library, then implement a discovery-only enrichment coverage/retry report and post-add sequencing verification.

## 2026-11-02 — Playlist removal blacklist/whitelist audit and fix

- **Finding:** `spotify_discovery.load_playlist_feedback` correctly scoped removal history by playlist ID. A removed track currently present in that same playlist is counted as whitelisted and omitted from negative evidence. For the Tricky Daily scoring path, exact track/URI and artist removals are deliberately soft ranking penalties, not global hard exclusions; artist-level evidence must not block every track by that artist.
- **Gap found:** hand-curated `booze20_preview` and legacy `horror_preview` resolved candidate lists directly against Spotify and checked only current URI duplicates. They bypassed playlist removal history entirely, so an exact previously removed song could be recommended again.
- **Fix published:** commit `92f86c7` adds `is_playlist_candidate_blocked` for exact playlist-local track/URI removals; commit `ea97b6c` wires it into both curated preview paths. Current membership is processed first by the feedback loader, so a re-added track is whitelisted and is not blocked. Artist-only removals remain soft evidence.
- **Regression coverage:** commit `7196fdd` adds tests for exact track and URI blocking, re-addition whitelist behavior, and a still-removed track remaining blocked.
- **Live data check:** `playlist_removed_tracks.json` currently contains three Booze removals (Shakira — “She Wolf”; The Prodigy — “Voodoo People - Pendulum Mix”; Yeah Yeah Yeahs — “Heads Will Roll - A-Trak Remix”). None matches the 15-track Booze addition batch just pushed, so none should have been admitted by this exact-track filter. The prior Booze batch had already been added before this fix; this is a forward-looking guard, not a retroactive claim that the earlier run checked it.
- **Verification:** Daily curator CI runs #41415718003, #41415724736 and #41415730381 were triggered by the three sequential commits and were still in progress at documentation time. Do not call the fix CI-verified until the final run completes successfully.
- **Next:** inspect the final Actions run; then run a read-only preview against current playlist data when available and confirm the removal/whitelist counts. Keep the distinction clear: Tricky Daily uses soft scoring penalties; curated playlist batches hard-skip only exact removed tracks; a current re-addition is the explicit whitelist signal.



## 2026-11-02 — Sticky playlist removals and mutation snapshots

- User reported repeated re-additions after removing The Cramps — “Human Fly” and Misfits — “Halloween” / “Halloween II”. Added their exact Spotify URIs to Booze or Boos! removal history, sourced as user-reported repeated removals.
- Root cause: the feedback loader treated current playlist membership as implicit approval, allowing automation to erase its own negative evidence.
- Changed removal handling so records remain active even if the track is currently present. Only an explicit playlist-local `whitelisted` entry overrides a removal. Other playlists are unaffected; artist-wide evidence remains soft.
- Replaced the implicit-membership whitelist regression with sticky-removal coverage and explicit-whitelist override coverage.
- Snapshot hooks: local manager saves pre/post snapshots for edits and an initial snapshot on creation; cloud playlist edits save post-change snapshots, including partial failures; dedupe saves a post-change snapshot. Snapshot paths are recorded in the audit log.
- Remaining operational work: wire the removal poll into playlist mutation workflows and a recurring Actions schedule, and ensure snapshots persist as workflow artifacts/committed state. These are not claimed live until verified.


## 2026-11-02 — Removal polling and post-cycle snapshots wired into Actions

- Initial implementation polled every accessible playlist after every control command and from the Tricky Daily cycle. This was subsequently replaced by a lower-cost design: control commands poll only their target playlist; the scheduled reference-library workflow owns the daily account-wide poll.
- Tricky Daily now saves and audits a post-mutation snapshot in addition to its pre-change recovery snapshot. Both workflows upload the complete `playlist_backups/` directory as run artifacts (30-day retention).
- Polling is interval-based, not event-driven: a manual Spotify removal that is undone before the next poll cannot be inferred from Spotify's current playlist snapshot. Repeated removals that persist until a poll are captured.

- Follow-up hardening: local manager edits now also attempt a post-failure snapshot when a multi-step operation raises after partial writes. Snapshot failure is separately audited without masking the original operation error.
- Verification status: repository writes are confirmed. No Actions run was returned for these main-branch commits, so compile/unit-test and live Spotify polling results remain pending.


## 2026-11-02 — Snapshot each individual playlist mutation

- Tightened the rule from batch-level snapshots to per-operation snapshots. The shared manager helper captures a fresh playlist state immediately before each write and refreshes/saves the actual Spotify state immediately after it.
- If a multi-request operation fails partway through, the helper attempts to save and audit the partial live state before re-raising the original error.
- Applied to local manager add/remove/replace/reorder operations; cloud add/remove/replace/reorder/details operations; undo/restore page writes; daily description edits; duplicate cleanup in cloud workflows and the removal tracker. Daily bulk replacement inherits per-page snapshots from the shared restore/replacement helper.
- Batch-level before/after snapshots remain as additional recovery checkpoints. Snapshot files retain the full ordered item list and Spotify snapshot ID.


## 2026-11-02 — All-playlist baseline and sustainable removal polling

- Added a pre-refresh baseline seed from the previous complete canonical playlist snapshots. It seeds only missing playlist IDs and refuses to treat inaccessible, incomplete or missing snapshots as empty.
- The reference-library workflow now performs this order: seed from the prior saved state → refresh the full Spotify playlist catalog and tracklists → compare the refreshed snapshots against the seeded baseline → commit snapshots, baseline and playlist-local removal feedback together.
- Added an offline --from-reference-library tracker mode so the daily full scan reuses the reference sync's fresh results instead of making a second account-wide Spotify pass.
- Added --seed-from-reference-library for one-time baseline creation without Spotify requests. The first baseline is intentionally non-retroactive for playlists without a prior complete snapshot.
- Reduced API load: a control command polls only its target playlist; the full account-wide poll belongs to the daily reference-library refresh. Per-write snapshot bracketing now fetches the exact playlist ID before and after each mutation instead of rescanning /me/playlists.
- The reference sync now retries publication with fetch/rebase and bounded retries, preserving concurrent main commits instead of failing on a push race.
- Live refresh evidence from run 41429176153: 58 playlists enumerated; 42 complete item lists; 16 inaccessible/incomplete; Booze or Boos! freshly reported 82 tracks. The comparison found no missing URI among the prior 64-track Booze snapshot, so it did not identify the two user-reported removals. This cannot rule out tracks added and removed between snapshots or tracks absent from the previous baseline.
- The refresh successfully generated the 58-playlist catalog, 42 initial baselines and two new dated history snapshots in the runner, but its first publication attempt raced with concurrent commits. The retry logic was added afterward; rerun the reference sync and verify that the resulting catalog/baseline commit is present before calling persistence complete.
- Regression tests now cover baseline seeding, inaccessible-snapshot exclusion, sticky removal comparison, and exact-ID pre/post snapshot reads.
- Next verification: ensure CI passes on the latest commit; trigger the reference-library workflow again; verify the baseline and all 58 catalog entries are committed, Booze is current, and the workflow ends green. Confirm the playlist-control workflow polls only the selected playlist.


## 2026-11-02 — Recover two Booze removals from the confirmed post-add state

- Compared the persisted `last_completed.after_uris` from the successful Booze 15-track confirmation (87 tracks; snapshot `AAAA/ScPSXp0d8nmx/aBsb0KprHk94Wa`) with the fresh Spotify reference snapshot (82 tracks; snapshot `AAABA/dKtho948buIMKTHoeoPu5L57D5`).
- Five URIs were absent from the current playlist. Three were already sticky removal records: The Cramps — Human Fly; Misfits — Halloween; Misfits — Halloween II. Two were new: Creature Feature — The Greatest Show Unearthed (`spotify:track:5YEkxfNMTHkfoYlh4d1Y7b`) and Creature Feature — The Netherworld (`spotify:track:62EKjHgJEMoBkL2uhCVHKr`).
- Added the two Creature Feature tracks to Booze's playlist-local removal history with exact URIs and both snapshot IDs as evidence. They now feed the same sticky negative filter as the previous removals.
- Root cause of the three known removals being present in the confirmed batch: that batch was previewed/confirmed at 08:31 UTC, before the sticky-removal fix was committed later that morning. The current curated preview code checks playlist-local removals before staging candidates; the new two records are now covered as well.
- Fixed the Booze candidate audit test to resolve its source snapshot by ID from immutable playlist history rather than comparing a dated audit fixture against the mutable live playlist. Preserved the original 64-track snapshot in history, and changed reference-library sync to preserve each previous complete snapshot before replacing the current pointer.
- Verification: baseline/reference sync is committed; CI for the removal-history and history-preservation changes is running. The read-only control inspection was blocked by the stale live-snapshot test before it could reach the command; rerun it after CI is green.


## 2026-11-02 — Removal tracker live verification

- The full reference refresh and baseline publication are committed: 58 catalog entries, 42 complete playlist baselines, 16 inaccessible playlists explicitly retained as unknown, and Booze or Boos! at 82 items with snapshot AAABA/dKtho948buIMKTHoeoPu5L57D5.
- A read-only Booze inspection then completed successfully through the playlist-control workflow. It fetched the exact playlist, ran the targeted removal poll, reported 0 additional removals and 8 total playlist-local removal records, and found no duplicate track URIs. The baseline and removal-history persistence step completed; the temporary control issue was closed afterward.
- Regression coverage verifies the two newly detected Creature Feature removals are loaded as permanent Booze-specific blocks. The test suite passed on commit 0e0661ac3b93972d861b7fe4adef7d12afc41de8; the additional explicit two-track blocking test is running on commit 6276cbacea29fcd341666540abb4bafbd733945e.
- The reference-library sync now retains the previous complete snapshot in per-playlist history before replacing the live pointer. The original 64-track Booze snapshot was restored into immutable history so the existing identity-only audit fixture remains tied to its actual source snapshot.
- Operating cadence: daily full catalog/snapshot/removal comparison via the reference-library workflow; targeted exact-ID poll after a successful playlist-control command; per-write pre/post snapshots for all actual playlist mutations; inaccessible playlists never count as empty; no webhook claim is made because Spotify playlist changes are detected by polling.


## 2026-11-02 — Recommendation feedback enforcement audit and correction

- **Audit finding:** the general discovery recommender loaded playlist-local exact removals but applied only a score penalty; a sufficiently strong similarity score could still surface a manually rejected track. The curated Booze/Horror preview paths already hard-skipped exact removals. This was inconsistent and unsafe.
- **Correction:** general discovery now hard-excludes exact track-key and Spotify-URI removals before scoring/selection. Explicit playlist-local whitelist records remain the only override; artist-level removals remain soft negative evidence and do not ban an entire artist.
- **Positive feedback:** explicit whitelists now provide a bounded exact-track positive score bonus. Artist representation in the playlist remains a small capped affinity prior, not an assertion that every track by that artist is liked. Tricky Daily post-add likes and measured plays continue as separate positive evidence.
- **Fail-closed behavior:** malformed/unreadable removal feedback now stops recommendation generation rather than silently treating the blacklist as empty.
- **Regression tests added:** general recommender cannot select an exact removed track; explicit whitelist increases exact-track score and clears its matching removal; corrupt feedback blocks recommendation generation.
- **Scope:** playlist-local only. No playlist mutation or live addition performed by this audit.


## 2026-11-02 — Standardized playlist staging reports

- Commit `1b96563` introduced an explicit Booze ten-track staging report with READY/BLOCKED status, eligible tracks, blacklist rejections, other exclusions, and no-write disclosure.
- Commit `5f9ba9b` standardized report headings and status language across sequence previews, generic playlist edit previews, Booze five-track previews, and the 15-track Halloween preview.
- Commit `2c0e9ab` removed the unnecessary unlock requirement from read-only staging previews. A locked playlist can now be inspected and staged without changing its lock; the separate confirmation/write path still requires explicit unlock.
- Staging contract: show the target playlist and operation; current count and projected count where applicable; READY only when the complete requested batch passes validation; otherwise BLOCKED with eligible, blacklisted, already-present, duplicate, and unresolved candidates separated; state plainly that Spotify has not changed; show a one-time confirmation only for a complete READY stage.
- Historical discovery-library entries are intake history, not an eligibility queue. Every candidate must pass current exact-URI / normalized artist-title playlist removal checks and current membership checks before being staged.
- No Spotify playlist changes are made by staging. Confirmation remains a separate explicit operation, and must reject stale playlist snapshots or locked targets.
- Follow-up: bring any remaining preview-like command paths into this same report contract, then add regression tests for READY/BLOCKED reports and locked read-only staging.


## 2026-11-02 — Refresh removal history before staging and confirmation

- **Root cause confirmed from the GitHub Actions state diff:** the Booze ten-track operation added *Where Eagles Dare* at 16:42 UTC; the post-command removal poll then observed the item missing and added its exact URI to `playlist_removed_tracks.json`. Later staging could use an out-of-date removal file because removal polling ran only after command execution.
- **Workflow correction:** strict recommendation previews now poll the exact target playlist before candidate resolution. Targeted polling fails the workflow if that playlist cannot be read, so a stale blacklist cannot silently pass.
- **Confirmation correction:** pending recommendation adds retain exact artist/title/URI metadata and are checked against freshly refreshed removal history again before the first Spotify write. Legacy pending previews without metadata fail closed and require a new stage.
- **Consistency correction:** Booze URI, horror-expansion, and Tricky Daily read-only previews are usable while locked; the separate confirmation path still requires unlock. Remaining preview reports now use the shared staging headings and disclose blacklist results.
- **Regression coverage:** the current Booze history must reject the exact *Where Eagles Dare* URI; pending confirmation rejects new removal conflicts; targeted refresh fails when the exact playlist is unavailable.
- **Scope:** staging remains read-only with respect to Spotify. No playlist write was performed by this fix.
