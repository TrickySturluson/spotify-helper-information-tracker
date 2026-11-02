# Playlist Intelligence & Safety — Actions & Evidence

Newest entries first. Record verified outcomes separately from plans, assumptions and unverified artifacts.

## 2026-11-02 — Parallelize sorter development with incremental data enrichment

- Decision: do not make complete metadata coverage a prerequisite for all sorter development. Use the current canonical Library and existing profile exports to build offline evaluation and confidence-aware fallbacks while read-only health/freshness monitoring continues.
- Required behavior: missing BPM/energy/mood/theme must be explicit; do not fabricate or silently inherit artist-level mood. Prefer high-confidence measured evidence; expose lower-confidence estimates and unknown coverage in previews.
- Safety: development/evaluation is read-only. No playlist writes are authorized by this change. Before any live application, verify current playlist state, deduplication/removal blacklist, ownership/lock state, preview freshness, and explicit authorization.
- Next: inspect the actual scripts/spotify/spotify_playlist_sequencer.py implementation and its tests; define a deterministic transition-quality evaluation using real available data, report coverage and confidence, then improve the algorithm before any live playlist changes.

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
