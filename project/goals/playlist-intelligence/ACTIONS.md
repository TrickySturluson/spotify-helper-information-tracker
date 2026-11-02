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


## 2026-11-02 — Evidence-based blind vibe verification (25-track audition)

- **Purpose:** Independently verify the musical vibe of the 25 SHITting Grounds audition tracks using track/album resources, artist/label pages, track-specific reviews, official lyrics/descriptions and community tags, without reading human slider values.
- **Important methodological correction:** The audition tracks are present in the five reference playlist snapshots. The prior prediction pass was blind to human slider values, but not blind to playlist membership. Membership must not be used as evidence of fit. This verification explicitly excludes all 25 audition tracks when describing the five reference playlist profiles. Future benchmark runs should use held-out tracks or leave-one-out reference profiles and should clearly state the type of blindness.
- **Reference profiles after exclusion:** To 11 retains a clear aggressive rap-metal/nu-metal/hard-rock identity. . . . remains a large hazy indie/bedroom-pop/dream-pop collection. =^= retains gritty swaggering alternative/garage/blues rock. Somber Party and Smooth have only three and six non-audition reference tracks respectively, so their profile confidence is lower.
- **Evidence method:** Prioritize track-specific sources over artist-level genre. Separate sound, energy, mood, lyrics/theme and production. Do not infer track mood from artist identity or title. Where track-level evidence is absent, mark unverified rather than manufacturing certainty.
- **Artifact:** `assistant_data/spotify/playlist_fit_vibe_verification_20261102.json` (25 per-track verdicts, source URLs, fit interpretation, recommended adjustment and reference-profile caveats). Commit: `bb1ca506c1400fbd13c4ef090940c62484c82e69`.
- **Findings:** To 11 predictions strongly supported. Oom Sha La La and Wharf (ii) are good Somber Party examples. Running Up That Hill (Chromatics) is better treated as vocal-led dreamy synth-pop / indie atmosphere than as a primary Smooth match. Armchair and A Little Wicked are boundary cases. Hakdo and MARBLE HALLS lack sufficient recording-specific evidence to support the original high-confidence estimates. Smooth's reference identity is distinctive: lo-fi electronic/synthwave/ambient/soundtrack/dub-psych rather than generic relaxed music. Deep Cover and Fantasy Trash Wave are plausible Smooth fits but their organic dub-psych and abrasive warped-breakbeat textures should temper confidence.
- **Limitations:** No direct playback, audio waveform analysis, or Spotify audio-feature retrieval was available in this pass. The report uses cited external textual evidence and existing library metadata; it is not a claim of having listened to the recordings.
- **Human labels:** Not accessed during this verification pass. Original predictions and human rating records were not modified. No Spotify playlist contents were changed.
- **Next action:** Obtain track-level audio evidence for Hakdo, MARBLE HALLS and other boundary cases; then run a genuinely held-out blind batch with test tracks removed from reference profiles before making any calibration changes.


## 2026-11-02 — Production playlist-fit model contract and human-score separation

- **Purpose:** Turn the five-axis model recommendations into a durable production contract and correct the status of the first human-rating experiment.
- **Decision:** The 25 SHITting Grounds human slider ratings are exploratory sanity-check observations only. They are not ground truth, production labels, training data, a sorting recipe, or a calibration target. The original rating and comparison artifacts remain preserved and must not be imported into production scoring/profile construction.
- **New specification:** `project/goals/playlist-intelligence/PLAYLIST_FIT_MODEL.md`. Defines independent Genre / Sound / Energy / Mood / Theme dimensions; default starting blend (explicitly untrained); profile distributions and candidate exclusion; field/scope/source provenance; independent confidence and missing-data treatment; decision boundaries; 15 production acceptance tests; implementation sequence.
- **Reference guide correction:** `assistant_data/spotify/PLAYLIST_REFERENCE_GUIDE.md` now states that human scores are exploratory observations and that candidates/held-out batches must be excluded from reference profiles.
- **Goal handoff:** `project/goals/playlist-intelligence/README.md` links the contract and explicitly distinguishes current sequencer infrastructure from the not-yet-implemented five-axis fit classifier.
- **Repository inspection:** Existing `scripts/spotify/spotify_playlist_sequencer.py` already separates acoustic energy, semantic score, mood scope, genre/theme groups and transition confidence. It does not yet implement per-target five-axis playlist-fit scoring. Existing `playlist_feedback_calibration.py` is a separate, conservative feedback ledger and must not ingest the exploratory slider dataset.
- **Outcome:** Documentation and methodology guardrails committed. No classifier code or weights changed; no human ratings modified; no Spotify playlist reads/writes performed in this step.
- **Next action:** Implement the profile builder and five-axis scorer as a separate read-only module; add synthetic regression tests for dimension isolation, missingness, duplicate sources, identity ambiguity, contradictions, candidate/holdout leakage, thin profiles, instrumental tracks, determinism and human-score non-import. Then run held-out evidence evaluation before enabling preview recommendations.
- **Commits:** model contract `f6f996cedc5bd212505715c441d66576a512697c`; reference guide `c3786ad2c0507fdd1d43247fe8d85769c748686f`; goal README `b2315b4cc05a3b719b88c18b59b74a00e84deaa0`.


## 2026-11-02 — Five-axis scorer prototype and regression suite

- **Purpose:** Move the production contract from documentation into an executable, read-only scoring prototype.
- **Implementation:** `scripts/spotify/playlist_fit_model.py` adds deterministic per-target scoring across Genre, Sound, Energy, Mood and Theme. It keeps missing dimensions unknown, separates fit from confidence, weights evidence scope, counts independent source families, requires recording-level evidence for energy, and supports candidate/held-out exclusion from reference profiles. It does not import human ratings, call Spotify, or write playlists.
- **Tests:** `tests/test_playlist_fit_model.py` covers candidate exclusion, held-out batch exclusion, strong multi-source evidence, missingness, artist-only context, duplicate/single-source evidence, unresolved identity, independent target scores and no-evidence behavior.
- **Documentation:** Updated the model contract and goal README to distinguish this scorer prototype from production integration. The scorer is not yet wired to canonical Library evidence or the sequencer.
- **Verification:** Code and tests were committed to main. The repository's normal GitHub Actions workflow compiles all Python modules and runs full unittest discovery; this entry does not claim that workflow passed. Await the actual run result before treating tests as verified.
- **Outcome:** Prototype and regression cases committed; production status remains preview-only / not enabled.
- **Next action:** Check Actions for compile/test results. Fix any failures. Then add a tested adapter from canonical Library records to the five-axis evidence schema, profile coverage/snapshot provenance, per-target output and an end-to-end read-only preview. Run a genuinely held-out candidate batch with the whole batch excluded from profiles and independent evidence review frozen before comparison.
- **Commits:** scorer `86c5c715ffb8182261d501a56fb4a1357fe12d9a`; tests `b780903d95cf74657e5b1b9cf450f645895dd7c7`; status updates `d147efa5da40998b280cfb7d08c8426457c040b0`, `5e64e5853314e651c2080fdf660e34b5211794ed`.


## 2026-11-02 — Model robustness pass; human score style treated as ordinal reference

- **User direction:** Take ownership of improving accuracy. Treat the user's initial human ratings as somewhat extreme-leaning personal judgments, not neutral numeric measurements.
- **Human-score handling:** Original values remain untouched and excluded from production scoring. For exploratory interpretation only, document broad ordinal bands (0–20 emphatic mismatch; 21–40 leaning mismatch; 41–59 mixed/uncertain; 60–79 leaning fit; 80–100 emphatic/standout fit). Prefer ordering, band agreement and major reversals over raw point error. No fixed shrinkage coefficient or model fitting is justified by 25 observations.
- **Scoring improvement:** Energy profile now stores p10/p90 and observed min/max and scores candidates against the target playlist's distribution rather than distance from its mean. Reference aggregation counts each recording once per descriptor and once in the energy distribution, so duplicate provider tags/observations cannot overweight a recording.
- **Canonical adapter:** Added `track_from_library_record(record)` to `scripts/spotify/playlist_fit_model.py`. It maps recording-scoped genre tags, recording-level moods, compact lyric themes, explicit measured audio energy and recording-level sound descriptors. It intentionally excludes artist/album mood contexts and refuses to infer energy from tempo, genre or mood. Current canonical sample records are sparse; unsupported dimensions remain unknown.
- **Regression tests:** Added tests for canonical record scope, tempo-only missing energy, energy distribution scoring and duplicate-source tag weighting. Added the required bottom FILE OVERVIEW to the new test file after the first layout check exposed that omission.
- **CI diagnosis:** Earlier workflow failed at maintained-file documentation because the new test module lacked its required bottom FILE OVERVIEW. This was corrected. The subsequent workflow run is in progress; compilation, generated-data audit and full Library health check have passed in the latest observed run. Do not mark the full suite passed until Actions reports completion.
- **Files:** `scripts/spotify/playlist_fit_model.py`, `tests/test_playlist_fit_model.py`, `project/goals/playlist-intelligence/PLAYLIST_FIT_MODEL.md`, `project/goals/playlist-intelligence/README.md`.
- **Commits:** energy distribution `f47c452df4d5781671db70aaf341eb85bc3af512`; canonical adapter `64edaec5c2f116db9b13e0e0bcb3681f6c2dece1`; adapter tests `52d73e21deb4fbdb774b0edf69ced57c7e1ee982`; score-style guidance `fc303fa2563fbea52dbd0a720faa59aa792581a0`; duplicate-evidence fix `af7633472086efd6f4583c8c9311f7ef6c6ed59f`; duplicate regression `3e303dcfa1b50b31558207bf037de600223dab9c`.
- **Next:** verify current CI; inspect exact real-world Library evidence field coverage; implement a read-only reference profile builder and held-out preview runner from canonical song records and the five playlist snapshots; do not integrate to sorter until those are verified.


## 2026-11-02 — Full CI pass; Library coverage audit and exact-ID cache integration

- **CI verification:** GitHub Actions run `41399936573` completed successfully. Python compilation, generated-data audit, full canonical Library health check, confidence audit, bounded freshness planner, maintained-file documentation check and full unit suite passed. Full suite: **382 tests, OK**. Run: https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41399936573
- **Regression failures found and fixed:** The first run exposed inconsistent normalization between held-out Spotify URIs and canonical song identities (25 vs 24 and 24 vs 22 profile-count failures). Held-out IDs now pass through the same normalizer as candidate/reference identities. Another earlier test run exposed confidence rules allowing artist-only context to count as medium and a 4/5-dimension profile to count as high; direct-evidence counts now gate confidence and high requires all five dimensions. These fixes are in the current scorer.
- **Full Library audit (read-only):** 13,005 songs, 6,386 artists and 7,861 albums scanned by freshness planning; 11,130/11,130 legacy track-index IDs and 5,358/5,358 artist IDs represented. Field coverage: duration 10,028; track tags 179; audio features 36; Spotify playability 1,856. Track-profile cache has 1,778 rows; audio-profile cache 115; lyric-feature export currently empty. This shows the identity/archive migration is strong, but descriptive track-level evidence remains the bottleneck for five-axis fit.
- **New data-path correction:** Canonical song records do not yet contain all cached recording tags. `track_from_library_record` now accepts an optional track-profile cache row only when its stable recording/source ID exactly matches the canonical song identity; no artist/title-only cache joins. Provider-family names normalize MusicBrainz recording tags and genres to one MusicBrainz family so they cannot falsely count as two independent sources.
- **Next critical build:** Extend the preview adapter to exact-ID merge track-profile and audio-profile caches, preserving their own provenance and field scope; add a read-only five-target profile builder/held-out preview runner; measure per-target reference coverage before scoring. Keep sound/energy/mood/theme unknown when the available cache does not genuinely support them. No Spotify writes.
- **Commits:** identity/holdout normalization `36fc6b0036d227a6fceedaff19b6650d5f3931f7`; exact-ID track-profile adapter `21aed2492477e47360807c6849bfc60b76a3ca83`; identity guard test `0c49b6b631f39acf535dbf5ca812ff42fadfc784`.
