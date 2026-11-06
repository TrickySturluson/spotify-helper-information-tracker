# Playlist Intelligence & Safety
> **Roadmap:** [ROADMAP.md](ROADMAP.md) is the durable plan and next-action reference. Read it before work; update it and [ACTIONS.md](ACTIONS.md) in the same session as implementation, testing, decisions, or blockers.
> **Current repository priority:** This workstream is paused for feature implementation while SHIT's documentation audit is active. Only documentation corrections and evidence reconciliation are permitted. Preserve this roadmap; resume its feature next actions only when the [central handoff](../../NEXT_WORK.md) and Maintainability & Documentation roadmap explicitly say documentation is complete.


## Goal

Build reliable playlist curation, sorting, discovery and feedback learning with coherent musical transitions and strict write controls.

## Scope, decisions and constraints

Smooth transitions are the primary sorting objective; avoid jarring adjacent tracks. Support controllable progression/peak placement, energy/BPM/loudness, mood/theme/genre sections and gradual resolution. Mood/theme is track-level. Daily learner distinguishes actual plays, likes/saves, removals and unknown playback coverage; unplayed tracks are not negative feedback by default. Liked tracks may be down-prioritized, not automatically excluded.

Only generated playlists are in scope by default. Personal playlists remain read-only unless explicitly authorized. Preserve deny-by-default controls, explicit unlocks, dedupe, removal blacklists and audits. Tricky Daily is an approved exception, not blanket permission. Booze or Boos! must remain energetic, fun, and strongly Halloween-related per track; inspect live contents before changes.

**Status: feature work paused under the repository-wide documentation-only priority.** Existing playlist intelligence, fit-scoring and sequencing implementation remains documented and preserved; no live playlist write is authorized by this workspace. Resume feature work only after the central handoff says documentation is complete.

**Resume:** inspect sorter/tests/state; verify authorization and lock; preview; assess transitions; apply only explicitly authorized changes; verify order/count/duplicates/audit.

## Documentation and resume

Read [ACTIONS.md](ACTIONS.md) for dated work and evidence. After each meaningful action, update it with files changed, execution, exact verification and outcome. Update [the central handoff](../../NEXT_WORK.md) when priority or blockers change.

## Production playlist-fit model

Read [PLAYLIST_FIT_MODEL.md](PLAYLIST_FIT_MODEL.md) before changing fit scoring. It defines five independent dimensions (genre, sound, energy, mood, theme), source/scope provenance, field-specific confidence, candidate exclusion, held-out evaluation, and production acceptance tests.

The 25-track human slider exercise is exploratory sanity-check context only. It is not ground truth, production labels, training data, or a sorting recipe. A read-only five-axis scorer exists at `scripts/spotify/playlist_fit_model.py`, with synthetic regression tests in `tests/test_playlist_fit_model.py`. A separate integration runner at `scripts/spotify/playlist_fit_preview.py` now builds five target profiles from accessible Spotify snapshots and canonical Library records, joins legacy track tags through exact Library alias indexes, permits only exact artist/title/album plus duration-corroborated medium-confidence fallback when stable IDs are separate, excludes the entire supplied candidate batch by URI and canonical record ID, and emits per-target scores/confidence/coverage. It is not wired into the sequencer. See [the preview runner guide](PLAYLIST_FIT_PREVIEW.md). The post-hoc comparison tool `scripts/spotify/compare_playlist_fit_human_reference.py` runs only after a frozen preview; it is separate from scoring and never trains/tunes the model. Latest CI and security checks pass, but the real-data review found only sparse direct Genre evidence, no direct Sound/Energy/Theme, and low-confidence profiles; therefore this remains preview-only. The five strongly themed playlists are calibration targets; All Time and Hell are broad taste references; SHITting Grounds is the audition destination.


### Booze or Boos! integration milestone — 2026-11-02

Historical 2026-11-02 audit: the five-axis fit model was run over a 64-track Booze snapshot with the candidate batch excluded from calibration profiles. That manifest is now stale. The latest repository snapshot captured 2026-11-06T01:47:59.824523Z contains 92 accessible items, so the old 64-track scores must not be used as current evidence. Regenerate the manifest and redo the hard per-track Halloween/party-energy review after the documentation-only pause. Musical affinity never substitutes for explicit Halloween relevance.
