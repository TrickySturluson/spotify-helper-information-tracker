# Great Migration — Actions & Evidence

Newest entries first. Record verified outcomes separately from plans, assumptions and unverified artifacts.

## 2026-11-01 — Fixed-workflow migration rerun requested

- **Action:** opened owner-authored issue #68, `[SHIT LIBRARY] prepare`, after confirming the publication fix is on `main`.
- **Request:** reuse saved Spotify snapshots, skip Spotify refresh, publish only `assistant_data/music/`, and preserve generated music data/checkpoints plus backup/log in the artifact.
- **Reference:** https://github.com/TrickySturluson/spotify-helper-information-tracker/issues/68
- **Outcome:** request submitted; workflow completion and publication not yet observed. Do not report migration complete until post-publish audit/status passes.
- **Next:** inspect issue result and Actions run; if successful, independently run audit/status against `main`; if publication fails, recover generated output from the new artifact rather than repeating provider work blindly.

## 2026-11-01 — Recover run #17 evidence and repair publication scope

- **Purpose:** determine whether the Great Migration itself completed and remove the publication failure that prevented its data from reaching `main`.
- **Evidence:** run #17 https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41357689889; artifact #13104699873; job #125005910236.
- **Verified execution:** compile/regression step passed; `prepare` command exited successfully; incremental syncs and final audit passed with 13,005 songs, 6,382 artists, 7,861 albums and zero audit errors. Final status reported 1,856 Spotify-ID aliases, 11,338 recording-MBID aliases, 1,816 ISRC aliases and 13,003 source-track-ID aliases.
- **Verified enrichment snapshot:** 1,580 track profiles; 3,898 artist profiles; 300 album profiles; 93 acoustic profiles. Duration coverage was 138,473 / 152,005 scrobbles (91.1%). Discogs and GetSongBPM were skipped because optional credentials were absent. AcousticBrainz queried 500 batch slots and stored 36 additional profiles; 907 negative-cache entries were recorded. Track/album profile backlog remained large.
- **Publication failure:** Git rebase failed with conflicts in dozens of `assistant_data/spotify/playlists/*.json` files and `assistant_data/spotify/reference_index.json`. The run had refreshed read-only Spotify snapshots, then staged all of `assistant_data/`. This was the conflict source; it did not mean the migration or final audit failed.
- **Artifact inspection:** downloaded and inspected artifact #13104699873 (23,946,780 bytes). It contains the pre-migration backup and `shit-library-run.log`; it does **not** contain the generated Library output. Therefore the successful runner state was not recoverable from that artifact.
- **Workflow fix:** commit `bdf75f74d7fd156e9d5e54ae8a66c814e5667dc8` removes the Spotify refresh-token setup from prepare, invokes `prepare --skip-spotify-refresh`, stages only `assistant_data/music/`, and uploads the complete music data directory plus log so generated output/checkpoints survive even if publication fails. This intentionally leaves all Spotify playlist snapshots and live playlists untouched.
- **Safety:** no Spotify playlist writes were performed. No force-push or blind conflict resolution was used.
- **Outcome:** run #17's migration/enrichment/audit are verified on its ephemeral runner; publication remains unverified. Workflow fix and goal status are committed to `main`.
- **Next action:** start a fresh `[SHIT LIBRARY] prepare` run on the fixed workflow; verify successful publication; then run a separate audit/status against `main` and continue enrichment from the newly durable checkpoints.
- **Lessons:** successful pre-publish audit is not proof of published data; failure artifacts must include generated output/checkpoints as well as rollback backup; migration publication must not include unrelated Spotify reference snapshots.

## 2026-11-01 — Goal workspace initialized

- **Action:** established this goal's dedicated documentation and action-history location.
- **Context:** Run #17 recovery is the immediate action. The only verified fact in the handoff is that publication/rebase failed; whether earlier migration stages or final audit completed is unknown. Next: inspect artifact and backup, reconcile safely, then verify published state.
- **Outcome:** documentation initialized; no runtime implementation or data mutation implied unless explicitly stated above.

## 2026-11-01 — Project-wide audit: migration recovery remains the critical path

- **Purpose:** reconcile previous migration requests and current repository state.
- **Evidence:** run #17 https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41357689889; open repeated prepare issues #61, #62, #63, #64 and earlier #57/#59.
- **Verified:** publication/rebase failed due generated Library/index conflicts; an artifact and backup were reported. The exact last successful stage, artifact contents, backup contents, audit result and published state remain unverified.
- **Loose ends:** inspect logs/artifact/backup; compare with main; preserve valid newer records; inspect all workflows writing shared generated paths; serialize writers/stale-base checks; fresh integrity audit before publish.
- **Failed approach / lesson:** do not blindly rerun a write-heavy migration or force-resolve generated data conflicts. The run failure at publication does not prove earlier stages failed or passed.
- **Outcome:** blocked; no migration recovery or Library write performed during this documentation audit.
- **Next action:** inspect run #17 artifact and backup, then reconcile safely.

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
