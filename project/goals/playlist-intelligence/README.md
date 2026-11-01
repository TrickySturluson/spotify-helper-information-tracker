# Playlist Intelligence & Safety

## Goal

Build reliable playlist curation, sorting, discovery and feedback learning with coherent musical transitions and strict write controls.

## Scope, decisions and constraints

Smooth transitions are the primary sorting objective; avoid jarring adjacent tracks. Support controllable progression/peak placement, energy/BPM/loudness, mood/theme/genre sections and gradual resolution. Mood/theme is track-level. Daily learner distinguishes actual plays, likes/saves, removals and unknown playback coverage; unplayed tracks are not negative feedback by default. Liked tracks may be down-prioritized, not automatically excluded.

Only generated playlists are in scope by default. Personal playlists remain read-only unless explicitly authorized. Preserve deny-by-default controls, explicit unlocks, dedupe, removal blacklists and audits. Tricky Daily is an approved exception, not blanket permission. Booze or Boos! must remain energetic, fun, and strongly Halloween-related per track; inspect live contents before changes.

**Status: active development; no live playlist write authorized by these docs. No playlist writes during migration recovery.**

**Resume:** inspect sorter/tests/state; verify authorization and lock; preview; assess transitions; apply only explicitly authorized changes; verify order/count/duplicates/audit.

## Documentation and resume

Read [ACTIONS.md](ACTIONS.md) for dated work and evidence. After each meaningful action, update it with files changed, execution, exact verification and outcome. Update [the central handoff](../../NEXT_WORK.md) when priority or blockers change.
