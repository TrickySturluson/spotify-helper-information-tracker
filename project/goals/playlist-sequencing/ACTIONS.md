# Playlist Sequencing — Actions & Evidence

Newest entries first. Distinguish design intent, implementation, preview output, authorized writes and independent live read-back.

## 2026-11-05 — Dedicated sequencing workstream documentation created

- **Purpose:** make the ordering engine independently resumable because its transition-evidence rules and user-defined listening-journey controls are distinct from recommendation/fit scoring.
- **Requirements captured:** smooth transitions are primary; configurable slow/fast/loud progression and reverse; tentative 80–90% peak; gradual resolution; mood/theme/genre sections; track-level evidence; honest handling of missing metadata; preview-first writes; stale-preview rejection and live read-back.
- **Changes:** added ROADMAP.md, README.md and ACTIONS.md; documented the sequencer, transition scoring guide, Booze preset, music evidence and tests as the implementation map.
- **Important separation:** the five-axis playlist-fit model is a separate preview-only system and is not wired into the sequencer. Do not merge those concerns without explicit design and validation.
- **Verification:** paths and current behavior descriptions were cross-checked against docs/TRANSITION_SCORING.md, docs/BOOZE_OR_BOOS_SORT.md and the playlist-intelligence roadmap. The new goal has not yet passed a post-creation documentation-contract CI run.
- **Outcome:** dedicated documentation initialized; runtime behavior unchanged.
- **Next action:** add this goal to the goal index and project-wide roadmap; then audit the sequencer's current code/tests and latest preview evidence against the acceptance criteria.

## Entry template

### YYYY-MM-DD — Action
- **Purpose:**
- **Changes / files:**
- **Execution:** command, workflow run, PR, commit
- **Verification:** exact tests/audits and results, including failures
- **Outcome:** complete / partial / blocked / deferred
- **Failed or abandoned approaches:**
- **Next action:**
- **References:**