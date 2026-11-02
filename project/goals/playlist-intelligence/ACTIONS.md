# Playlist Intelligence & Safety — Actions & Evidence

Newest entries first. Record verified outcomes separately from plans, assumptions and unverified artifacts.

## 2026-11-01 — Goal workspace initialized

- **Action:** established this goal's dedicated documentation and action-history location.
- **Context:** 2026-11-01: Sorting, daily learner, generated-playlist safety and transition goals consolidated. No playlist changes made by this documentation. Next: after migration recovery, inspect sorter state/tests and run preview before any authorized write.
- **Outcome:** documentation initialized; no runtime implementation or data mutation implied unless explicitly stated above.

## 2026-11-01 — Project-wide audit: playlist loose ends consolidated

- **References:** Tricky Daily `4yUVHSMQySfWeEowfIMcx7`; Booze or Boos! `4diIlnF8BlgoJrwUfejf49`; open sequence-preview issue #4 https://github.com/TrickySturluson/spotify-helper-information-tracker/issues/4.
- **Sorter requirements:** smooth adjacent transitions are primary; avoid jarring changes; gradual energy/BPM/loudness movement; mood/theme/genre sections; configurable peak placement (roughly 80–90% default concept); smooth resolution.
- **Learner requirements:** use actual plays and explicit likes distinctly; do not treat unplayed Tricky Daily tracks as negative feedback; liked tracks may be down-ranked, not automatically excluded.
- **Booze or Boos! constraints:** energetic, fun Halloween party list; every track should have a strong Halloween connection (murder/monster/slasher/vampire/creature themes), with campy/dark-playful/chaotic/danceable/metal energy. Avoid sad-victim/apocalypse mood and generic novelty staples previously rejected. A prior user report said 66 tracks while project state may have been stale; recheck live Spotify before edits.
- **Safety:** generated playlists only by default; personal playlists read-only absent explicit authorization; Tricky Daily is an approved exception, not blanket write permission. Preview and audit before writes. No playlist writes during migration recovery.
- **Outstanding:** reconcile issue #4 sequence preview with current sorter and live playlist; validate dedupe/removal blacklist persistence, live counts versus snapshots, and daily description rotation.
- **Failed approach / lesson:** stale local playlist snapshots and unplayed daily placements are not reliable current counts or negative preference evidence.
- **Outcome:** documentation only; no Spotify playlist changes.
- **Next action:** after migration recovery, inspect sorter/tests/state and preview before any explicitly authorized write.

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


## 2026-11-02 — Blind five-playlist audition evaluation and human comparison

- **Purpose:** Run the 25 SHITting Grounds audition tracks independently against all five registered calibration targets, then compare frozen model predictions with the separate human slider labels.
- **Blind procedure:** Read the audition track identities and the five reference playlist snapshots. Human slider values were not read or used until the prediction artifact was committed. The existing human-label file was accessed in an identity-only pass to recover the 25 track names; score fields and model_prediction fields were explicitly excluded from that pass.
- **Prediction artifact:** `assistant_data/spotify/playlist_fit_model_predictions.json` (25 tracks × 5 target scores, independent confidence by target, per-track rationale). Commit: `b21de5bd95d6891ece4503c0f7c996266bc0585f`.
- **Comparison artifact:** `assistant_data/spotify/playlist_fit_model_comparison_20261102.json` (125 paired scores, per-target MAE/bias/correlation, per-track errors and top-target agreement). Commit: `3f5608d010b52646f9f91826f101ea624398f67c`.
- **Execution qualification:** This pass was an independent SHIT-style model assessment using the current reference snapshots and available track/style knowledge. It was not a repository-native five-target classifier execution, and it did not perform fresh audio analysis or track-by-track playback. Confidence reflects the clarity of the available musical/style evidence, not a calibrated probability.
- **Headline result:** 25 tracks / 125 slider comparisons; MAE 14.14 points; Pearson r 0.844; 70/125 scores within 10 points; top-target agreement 19/24 excluding the all-50 Dog response.
- **Per-target:** To 11 MAE 8.04 (r=.941); Somber Party 11.44 (r=.897); . . . 19.44 (r=.786); =^= 10.40 (r=.951); Smooth 21.36 (r=.681).
- **Key findings:** Strongest alignment is To 11 and =^=. Smooth is the largest weakness, especially overestimating synthwave/psychedelic/instrumental fit for MARBLE HALLS, Running Up That Hill, Deep Cover and Fantasy Trash Wave. The . . . target is also over-predicted for Oom Sha La La and Armchair, where the human ratings lean Somber Party. Dog was rated 50 on all five targets and is non-discriminative.
- **Confidence check:** 90+ confidence scores had MAE 9.3, but there were still notable high-confidence misses (e.g. MARBLE HALLS/Smooth, Running Up That Hill/Smooth, Deep Cover/Smooth, Fantasy Trash Wave/Smooth). Confidence is independent of the human labels but is not yet statistically calibrated.
- **Outcome:** Blind predictions frozen before comparison; comparison generated and committed. No Spotify playlist contents were changed.
- **Next action:** Improve boundary discrimination between Smooth and . . . / Somber Party; review track-level evidence for instrumental, psychedelic and dream-pop cases; collect another blind batch before changing weights or calibration. Keep the prediction file immutable as the original blind run and append future runs as new versioned artifacts.
