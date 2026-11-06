## 2026-11-06 — Booze snapshot and hard-fit requirements revalidated

- The latest repository snapshot for Booze or Boos! (`4diIlnF8BlgoJrwUfejf49`) was captured at `2026-11-06T01:47:59.824523+00:00`: 92 items reported/fetched, 92 unique track URIs (zero duplicate URIs), accessible, no item error.
- The earlier 64-track five-axis candidate manifest `playlist_fit_booze_candidates_20261102.json` is stale and must not be used as current coverage or sorting evidence.
- Updated `docs/BOOZE_OR_BOOS_SORT.md` with the hard per-track Halloween/horror relevance gate, energetic/campy/party requirement, user-approved sound anchors, previously rejected novelty staples, duplicate/removal protections, and the current 92-item snapshot.
- No Booze playlist mutation or sorter preview was run. The playlist-specific feature work remains paused until documentation acceptance criteria pass; regenerate the manifest and perform the hard-fit review only after that pause is lifted.

# Playlist Intelligence & Safety — Actions & Evidence

## 2026-11-06 — Open proposal inventory and documentation pause

- PR #121 (offline sorter evaluation/ingestion watchdog) and PR #120 (incremental Library enrichment/sorter development) remain open drafts; neither is merged behavior. Compare their diffs with current main before selecting future work.
- Related Daily proposals #158–#160 also remain open and are separately tracked in the central handoff.
- Existing fit, calibration and intelligence code is preserved. Feature work and live playlist operations in this goal remain paused until documentation acceptance criteria pass.

Newest entries first. Record verified outcomes separately from plans, assumptions and unverified artifacts.

## 2026-11-01 — Goal workspace initialized

- **Action:** established this goal's dedicated documentation and action-history location.
- **Context:** 2026-11-01: Sorting, daily learner, generated-playlist safety and transition goals consolidated. No playlist changes made by this documentation. Next: after migration recovery, inspect sorter state/tests and run preview before any authorized write.
- **Outcome:** documentation initialized; no runtime implementation or data mutation implied unless explicitly stated above.

## 2026-11-01 — Project-wide audit: playlist loose ends consolidated

- **References:** Tricky Daily `4yUVHSMQySfWeEowfIMcx7`; Booze or Boos! `4diIlnF8BlgoJrwUfejf49`; open sequence-preview issue #4 https://github.com/TrickySturluson/spotify-helper-information-tracker/issues/4.
- **Sorter requirements:** smooth adjacent transitions are primary; avoid jarring changes; gradual energy/BPM/loudness movement; mood/theme/genre sections; configurable peak placement (roughly 80–90% default concept); smooth resolution.
- **Learner requirements:** use actual plays and explicit likes distinctly; do not treat unplayed Tricky Daily tracks as negative feedback; liked tracks may be down-ranked, not automatically excluded.
- **Booze or Boos! constraints:** energetic, fun Halloween party list; every track should have a strong Halloween connection (murder/monster/slasher/vampire/creature themes), with campy/dark-playful/chaotic/danceable/metal energy. Avoid sad-victim/apocalypse mood and generic novelty staples previously rejected. A historical user report on 2026-11-01 said 66 tracks; the latest repository snapshot on 2026-11-06 supersedes that with 92 accessible items. Still refresh live Spotify before any future edit.
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


## 2026-11-02 — Cached metadata adapter validation

- **Additional source integration:** `track_from_library_record` now accepts a track-profile cache row only after an exact stable recording/source-ID match. It preserves cache tags when canonical metadata contains empty placeholder arrays, and normalizes MusicBrainz recording tags and genres to the same provider family.
- **Regression coverage:** exact-ID acceptance, wrong-recording rejection, provider-family normalization and preservation of cached tags when canonical arrays are empty.
- **Verification:** GitHub Actions run `41400200745` passed: compile, generated-data audit, full Library health, confidence audit, freshness plan, file-layout check, and **383 unit tests**. Run: https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41400200745
- **Current state:** read-only scorer and exact-ID track-profile adapter are green. The separate legacy cache has 1,778 track rows while canonical song records report only 179 with track tags; integrating that cache safely is important to avoid throwing away existing useful evidence. The lyric export is empty and direct recording mood coverage was not reported in the current audit, so those dimensions must remain unknown until enriched.
- **Next:** add exact-ID audio-profile cache ingestion only for fields that genuinely support the relevant dimension; then build and test a read-only target-profile/held-out preview using the saved five playlist snapshots. Keep human scores out of scoring and keep Spotify writes disabled.
- **Commits:** cache merge fix `00a3d8c19c16ee2438fd70a276a6c3737b4f0775`; cache regression test `f3f89bd631688e4000749ca159fc90f1004f5ee5`.


## 2026-11-02 — Read-only five-target profile and preview integration

- **Purpose:** Connect the five-axis scorer to canonical SHIT records and saved reference snapshots without using human labels or changing Spotify.
- **Implementation:** Added `scripts/spotify/playlist_fit_preview.py`. It validates the five registered target snapshots, checks snapshot identity and reported/fetched counts, resolves playlist items to canonical song records by exact Spotify ID, joins legacy track-profile cache rows only by exact stable source/recording/Spotify ID, builds per-target profiles, and scores an identity-only candidate batch.
- **Leakage control:** The complete candidate batch is excluded from every target profile. Human score fields are never loaded; candidate parsing extracts only track identity/title/artist. No artist/title joins, Spotify API calls or playlist writes.
- **Conservative evidence handling:** The runner does not turn AcousticBrainz loudness/complexity or BPM into energy/sound descriptors. Unsupported dimensions remain unknown. It emits profile sizes, per-dimension coverage, snapshot provenance, per-target scores, confidence reasons and explicit no-write flags.
- **Tests added:** `tests/test_playlist_fit_preview.py` covers strict Spotify ID parsing, identity-only candidate extraction/deduplication, exact cache joins, whole-batch exclusion and read-only output flags.
- **Documentation:** Added `PLAYLIST_FIT_PREVIEW.md` and updated the goal README.
- **Verification:** Implementation and tests are committed to the isolated branch. CI has not yet been observed for this branch; do not treat tests as passed until Actions reports success. The real-data preview has not yet been run.
- **Outcome:** Integration prototype implemented; still preview-only and not connected to the sequencer.
- **Held-out batch:** Added `assistant_data/spotify/playlist_fit_heldout_candidates_20261102.json` with 24 playable candidate identities resolved to unique Spotify IDs from the saved target snapshots. The unplayable Dog — Floating Room track is excluded. No score or confidence fields are present. The full 24-track batch is excluded from every target profile.
- **Execution workflow:** Added `.github/workflows/playlist-fit-preview.yml` to run focused tests and the real-data preview without Spotify credentials, then retain the JSON artifact for 14 days. It runs on relevant PR changes or manual dispatch.
- **CI:** Main repository PR workflow run `41401453395` passed all stages and **389 unit tests**. The dedicated real-data preview workflow was added after that run and is now awaiting its own result. The public-repository secret-history scan `41401453357` was still running at the last check.
- **Next:** Verify the dedicated preview workflow and inspect its artifact: candidate-to-Library match rate, per-target profile counts/coverage, confidence tiers and unknown dimensions. Then perform an independent evidence review of the largest boundary errors before any human-score comparison. Keep human scores out of the scoring path and Spotify writes disabled.


### Preview workflow diagnostic — 2026-11-02

- **First real-data workflow:** run 41401744033 — focused regression tests passed (20/20), but the preview CLI failed immediately with ModuleNotFoundError: No module named 'scripts'.
- **Root cause:** direct execution places scripts/spotify/ rather than the repository root on sys.path; importing the scorer as scripts.spotify.playlist_fit_model therefore worked in tests but not in the CLI entry point.
- **Fix:** the runner now inserts its repository root into sys.path before importing the scorer. No data/schema or scoring behavior changed.
- **Next verification:** rerun the dedicated preview workflow against the 24-track identity-only held-out batch; inspect the generated artifact and then record exact coverage/results. Do not treat the initial failed run as a scoring failure.


### Reference evidence coverage diagnostic and identity-bridge refinement — 2026-11-02

- **First full-data result:** workflow run 41401858727 successfully produced a 24-candidate / 5-target artifact, but all five target profiles had zero dimension coverage and every fit score was null. This was a correct insufficient-evidence outcome, not a scoring failure.
- **Identity-layer diagnosis:** Spotify-only canonical song records and Last.fm source-track records are sometimes separate records even when the same recording is represented. Direct Spotify ID resolution therefore found the playlist record but did not reach the separate source-track profile row. The Library's alias index correctly maps the cache row to its source record, but no shared stable ID exists between the two records in those cases.
- **Safe bridge:** the preview now tries exact Spotify ID first, then only a Library exact artist + title + album lookup with an additional duration check within 2,000 ms. The fallback is explicitly marked medium identity confidence. It never uses fuzzy text matching or artist/title alone. It does not mutate canonical records.
- **Leakage guard:** candidate resolution occurs before profile construction; the entire held-out batch is excluded by Spotify URI and by resolved canonical record ID. Reference profiles deduplicate resolved canonical records so relinked/duplicate Spotify IDs cannot overweight a recording.
- **Candidate metadata:** the 24-track held-out identity file now includes exact album, duration and ISRC from saved Spotify snapshots; no human scores, fit scores or confidence values are present.
- **Fail-closed status:** when all five profiles have zero usable evidence, output status is blocked_insufficient_reference_evidence and all fit scores remain null.
- **Regression tests:** added coverage for exact album/duration fallback, medium identity confidence without mutating the Library record, duration mismatch rejection, canonical-record holdout exclusion, and blocked zero-evidence output.
- **Verification pending:** focused and full CI plus a fresh real-data artifact must pass after this adapter change. No Spotify API calls or playlist writes.


### Exact identity bridge test correction — 2026-11-02

- Workflow run 41403433459 failed one new regression fixture because the fake Last.fm source record omitted its duration; the implementation correctly refused the fallback and retained the exact Spotify record. The fixture now supplies the required matching 100,000 ms duration. No production logic was weakened.
- The bridge is now implemented as a read-only index over canonical song records rather than calling the Library's mutating fallback repair paths. It selects exactly one non-Spotify source record with normalized exact artist/title/album and duration within 2,000 ms; zero or multiple matches are rejected.
- Latest verification is pending for the corrected fixture and the full real-data preview.


### Explicit context adapter and confidence boundary — 2026-11-02

- The preview now reads canonical artist/album relation records by their stored relative paths and adds only explicit genre fields plus explicit mood fields as context. Artist genre remains artist-scoped; release genre remains release-scoped; explicit moods retain the same scope. No artist tag is promoted to track mood, and no context is used for sound, energy or lyrics-derived theme.
- Existing scorer scope weights remain unchanged: artist 0.15, release 0.35, direct recording/audio/lyrics 1.0.
- Profile output now separates direct and contextual track counts per dimension. Primary coverage and profile confidence use direct evidence only; contextual coverage is reported separately. Context-only output cannot promote a profile to medium/high confidence.
- Model version bumped to five-axis-fit-v0.3 for the new direct/context confidence semantics.
- Added tests proving contextual-only data does not raise direct profile confidence and explicit artist/release context stays in its proper dimensions.
- Latest preview/full CI/security runs are in progress; inspect the resulting artifact before interpreting scores.


### Frozen preview and separate human-reference diagnostic — 2026-11-02

- Latest full real-data preview workflow run 41404493636 succeeded and uploaded artifact 13122518748. It used model version five-axis-fit-v0.3, 24 candidate tracks, five target snapshots, no human ratings in scoring, zero Spotify API calls and zero playlist writes.
- Direct profile coverage remains sparse: To 11 0.2, Somber Party 0.0, . . . 0.2, =^= 0.2, Smooth 0.0. Context coverage is 0.2, 0.2, 0.4, 0.4, 0.0 respectively. Only Genre has direct coverage (3, 0, 3, 4, 0 tracks); Sound and Energy have no evidence; Mood has three/one context-only observations in . . . and =^=; Theme has no evidence. Profile confidence remains low across all targets.
- Exact identity resolution for the 24 held-out tracks: 16 exact artist/title/album+duration corroborated source-record fallbacks, 8 exact Spotify-ID records. No fuzzy matching.
- Fifteen tracks receive low-confidence genre-only scores against To 11, Somber Party, . . . and =^=; nine remain unknown. Smooth has no comparable profile evidence. No candidate receives medium/high confidence. These are provisional evidence-limited scores, not production decisions.
- Added scripts/spotify/compare_playlist_fit_human_reference.py and tests/test_playlist_fit_human_reference_comparison.py. The comparison is a separate post-hoc step after preview generation, with unknown scores left missing and human labels excluded from model training/scoring. It reports error, bias, correlation, coverage and confidence strata. The preview workflow now uploads a second diagnostic artifact.
- Full repository CI/security and latest focused preview tests are pending for the final v0.3 + comparison workflow changes. Keep preview-only and no Spotify writes.


## Final verification and post-hoc reference results — 2026-11-02

- **Merged:** PR #126 was squash-merged to main as commit 2f84924b8e76510a1648bfc3e4e369935aa2bdf0. The scorer remains a read-only preview and is not wired into the sequencer.
- **Verification:** latest full CI run 41405523463 passed 398 unit tests plus full-catalogue health, confidence, freshness and documentation checks; focused preview/comparison workflow run 41405523394 passed 29 tests; complete-history Gitleaks scan 41405523513 passed.
- **Artifacts:** preview artifact 13122763665 and human-reference diagnostic artifact 13122659752, from workflow run 41405523394, are retained until 2026-11-16.
- **Human-reference comparison:** 25 human-rated tracks; 24 matched to the 24-track identity batch; unmatched item was Dog — Floating Room (unplayable, deliberately excluded). There were 120 possible target-rating pairs: 60 scored and 60 unknown. All 60 scored pairs were low confidence; 0 medium/high. Twelve of the 15 scored tracks per target were context-only; only three had direct genre support. Each scored track supported exactly one dimension.
- **Overall diagnostic:** n=60, MAE=26.85, median absolute error=16.79, mean bias (model-human)=-17.63, median bias=0.00, Pearson r=0.4473, Spearman r=0.4862. To 11: n=15, MAE=28.97, Spearman=0.8333; Somber Party: n=15, MAE=22.12, Spearman=0.3069; . . .: n=15, MAE=19.56, Spearman=0.1240; =^=: n=15, MAE=36.75, Spearman=0.7094; Smooth: n=0 (no evidence). Human ratings remain exploratory reference labels, not ground truth or training data; endpoint-heavy ratings make rank/median statistics more informative than raw mean bias alone.
- **Interpretation:** some directional rank alignment appears for To 11 and =^=, but it is currently genre/context-driven and low-confidence. These results do not validate the scorer or justify weight tuning. The 5-axis model still lacks direct Sound, Energy, Mood and Theme evidence, and target profiles remain low confidence.
- **Reference-role preservation:** the five strongly themed playlists remain sorter calibration targets. All Time and Hell remain broad_taste_reference profiles, not narrow theme labels. SHITting Grounds remains the separate audition destination and is not a substitute for the five target snapshots.
- **Next:** increase direct recording-level evidence across all five dimensions, especially validated sound and energy, recording-level mood, lyric-derived theme tags and track-level genre. Keep context scoped and down-weighted. Re-run the held-out preview, then the separate human diagnostic; never let human labels enter scoring/training. No Spotify writes until evidence and confidence gates are met.


## 2026-11-02 — Booze five-axis cross-reference preview added

- Added identity-only candidate manifest `assistant_data/spotify/playlist_fit_booze_candidates_20261102.json` generated from saved Booze or Boos! snapshot `AAAA8bx0/IayXwvWXBdkeCowLo32i5oU` (64 tracks; captured 2026-11-02T03:58:22Z).
- Updated the read-only fit workflow for a historical 2026-11-02 preview using the 64-track Booze snapshot against the five calibration-target profiles, excluding the complete candidate batch from those profiles. Output is a cross-reference audit, not a Halloween-theme verdict and not an automatic add/remove/sort decision.
- Added a regression test requiring exact ordered URI agreement with the saved playlist snapshot, uniqueness, and identity-only fields. The workflow includes this test.
- The existing sequencer remains responsible for smooth adjacent transitions, section order, artist spacing and the 85% gradual peak. No Spotify API calls or playlist writes were added. This branch is a reviewable PR; it must pass CI and real-data artifact inspection before merge.
- Next: inspect the new audit artifact and evidence coverage, then use the live sequence preview against a fresh snapshot. Separately audit each Booze track's explicit Halloween theme evidence; five-axis similarity to other playlists is useful musical context but is not itself proof of Halloween relevance. Do not apply a sort until the expanded candidate set and complete proposed order are reviewed.


### Booze audit artifact findings — workflow #41407268653

- The read-only cross-reference artifact completed successfully for all 64 saved tracks; all 64 resolved to a canonical Library record (28 exact Spotify-ID joins, 36 exact artist/title/album/duration joins). No candidate leakage into calibration profiles: all 64 candidates were excluded from each target profile.
- **The model is not yet useful as an automatic sorter input for Booze.** Per target, only 32/64 tracks received a non-null fit score; all 32 are low confidence, support exactly one dimension, and 31/32 rely on artist-scope genre context. Only one track has direct Genre evidence. The other 32 tracks are unknown for each target. Sound, Energy, Mood and Theme have zero direct coverage in the target profiles; Smooth has no direct profile evidence at all.
- Playlist-local cache coverage check: 64/64 have a legacy track-profile row, but only 2/64 have Last.fm tags; 0/64 have lyric-theme features, 0/64 have direct track mood, 0/64 have recognized energy scores, and 0/64 have a usable audio profile by the sequencer's exact artist/title key except 1 sparse row. This is an identity/metadata coverage problem, not evidence that the music lacks those qualities.
- Therefore the cross-reference report is diagnostic only. Do not use its single-axis/context-only scores to select additions or claim Halloween fit. After documentation completion, the next phase must prioritize trustworthy recording-level tags/lyrics/theme and usable acoustic evidence, then run a fresh live Booze sequence preview with the existing smooth-flow sorter. Do not apply until additions and full order are reviewed.


## 2026-11-02 — Booze live preview baseline and next functional blockers

- Live read-only sequencer preview run #41407486669 / comment #6571714105 found 72 tracks, 48 reorder operations, 64/72 section assignments and 8 unassigned tracks. Transition summary: 0 gentle, 0 moderate, 0 supported potential jumps; 71 transitions have limited evidence. Confidence: 62 low, 10 unknown. No Spotify changes were made.
- Current live list differs from the saved snapshot (72 vs 64); refresh and persist the reference snapshot before further fit evaluation.
- Cross-reference fit artifact is useful as a data-gap report, not as a sorter input: only one direct genre observation, no direct Sound/Energy/Mood/Theme evidence, and only 2/64 Last.fm-tagged Booze tracks. Do not confirm the current sequence.
- Next: provider-aware bounded recording-level enrichment with cooldowns and per-run caps; classify the 8 unassigned tracks using evidence; prepare a substantial addition batch with explicit Halloween relevance; rerun five-axis audit and sequence preview; inspect complete order; then confirmation-gated sort.


## 2026-11-02 — New-song default operation

- Recommendation/playlist candidates are now expected to enter discovery-library intake at preview time with source and playlist context; canonical Library enrichment follows through the existing intake/migration process. Listening evidence stays separate.
- Every confirmed addition must trigger a fresh live snapshot, duplicate/blacklist check, and sequence preview. Sequencer writes remain separately confirmed while direct track-level Sound/Energy/Mood/Theme evidence is insufficient.
- Fixed missing `time` import in `scripts/spotify/spotify_playlist_cloud.py`; added idempotent candidate intake/audit to `booze20_preview`. Re-run workflow and focused tests before treating this path as verified.


## 2026-11-02 — live Booze sorter and Spotify auth recovery

- Diagnosed the cloud `sequence_preview` implementation: unlike the local sequencer, it omitted canonical Library audio profiles and album profiles from `sequence_tracks`. That caused the live report to understate available recording-level evidence.
- Updated `scripts/spotify/spotify_playlist_cloud.py` to load per-recording Library profiles first and fill missing artist, track, audio, and album records from legacy caches. The preview now reports acoustic-confidence counts, audio-source coverage, and tempo-source coverage.
- Removed a redundant duplicate conditional in transition classification. Limited metadata remains explicitly provisional; no guessed acoustic measurements are introduced.
- Added URI-based section assignments for the pending ten-track Booze batch so new additions won't be left unassigned after they are actually added.
- Updated `docs/BOOZE_OR_BOOS_SORT.md` with the cloud evidence-loading behavior and limits.
- Fixed the playlist workflow so it mints the GitHub App secret-writer token for Spotify control operations. The token mint succeeded, but the live unlock then failed with Spotify `invalid_grant`: the repository's `SPOTIFY_REFRESH_TOKEN` secret is stale/revoked or was invalidated by refresh-token rotation.
- The playlist remains locked; no Spotify playlist edit or reorder occurred. The ten-track preview remains staged with confirmation code `UBiP2nOo2rxVppmt` and a 92-item expected snapshot. Do not retry this old credential. Required recovery: locally reauthorize the playlist manager, export the new refresh token, and replace the GitHub Actions secret before any further Spotify command.
- Verification: compile and generated-data/library audit steps passed in the latest CI run; unit tests were still running at the time of this entry. A fresh live preview remains blocked until OAuth is restored.
