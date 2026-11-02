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

- Playlist-control workflow now polls every accessible owned playlist after each successful control command and commits both the baseline and removal history with the existing state publication step.
- Tricky Daily's scheduled workflow now polls all accessible playlists after the daily cycle, then persists the baseline/removal data with cycle state.
- Tricky Daily now saves and audits a post-mutation snapshot in addition to its pre-change recovery snapshot. Both workflows upload the complete `playlist_backups/` directory as run artifacts (30-day retention).
- Polling is interval-based, not event-driven: a manual Spotify removal that is undone before the next poll cannot be inferred from Spotify's current playlist snapshot. Repeated removals that persist until a poll are captured.
