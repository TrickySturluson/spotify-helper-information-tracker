# Canonical Library Enrichment — Actions & Evidence

Newest entries first. Record verified outcomes separately from plans, assumptions and unverified artifacts.
## 2026-11-06 — Incremental Library enrichment PR status rechecked

- PR #120 `codex/incremental-library-sorter-work` remains open/draft, 5 commits ahead and 419 behind current main, mergeable=false. Old-head tests #41380622956 and security scan #41380622844 passed.
- Those results are from a stale/diverged base and do not establish current-main compatibility. Rebase and rerun CI after the documentation-only pause; no enrichment or provider work was performed.



## 2026-11-06 — Incremental enrichment strategy PR remains proposal-only

- [PR #120](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/120) remains open draft. Its observed tests and full-history security scan passed, but the PR records a strategy change and does not implement a bounded provider executor, retry queue or completed on-demand enrichment path.
- Provider-backed enrichment remains paused under the repository-wide documentation-only priority.

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

## 2026-11-01 — Goal workspace initialized

- **Action:** established this goal's dedicated documentation and action-history location.
- **Context:** 2026-11-01: Consolidated enrichment goals and safeguards in central handoff. No fresh coverage totals or provider-availability measurements asserted. Next: after migration verification, generate a read-only coverage report and select bounded batches.
- **Outcome:** documentation initialized; no runtime implementation or data mutation implied unless explicitly stated above.

## 2026-11-01 — Project-wide audit: enrichment backlog clarified

- **Purpose:** capture metadata/provider limitations found in prior conversations and open work.
- **Verified context:** no fresh post-publication coverage report has been confirmed. Prior conversational counts (artist 1,587; track 9,778; album 6,384; unresolved duration 2,919) are stale snapshots, not current coverage.
- **Known provider gaps:** lyrics remain unpopulated; MusicBrainz previously returned 503/rate-limit failures; Discogs and GetSongBPM require optional credentials; AcousticBrainz timeout resilience was a recent fix target. Recheck actual provider state after migration; do not infer current availability.
- **Outstanding fields:** recording IDs/MBIDs and aliases; duration; acoustic/audio features; track-level tags/mood/theme; album tracklists/descriptions/release context; artist profiles/genres; artwork references where useful.
- **Design lesson:** preserve recording/artist/album separation, field-level provenance/confidence/timestamps/evidence, and unknown values. Do not infer track mood from artist identity. Lyrics enrichment must use compact permitted features/tags, not full copyrighted lyrics.
- **Failed approach / lesson:** blind refetching unavailable providers wastes quota and can turn transient failures into misleading missing-data conclusions. Cache success, honor cooldowns and distinguish transient, ambiguous, credential-blocked and definitive negative states.
- **Outcome:** audit documentation only; no provider requests or Library mutations.
- **Next action:** after migration publication, run a read-only field coverage report and plan bounded passes.

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
