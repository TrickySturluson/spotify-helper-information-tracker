# Discovery & Recommendations

## Goal

Capture suggested, recommended and discovered songs in the Library so they can be identified, enriched, deduplicated and retrieved without polluting listening history or overstating preference.

## Scope, decisions and constraints

Store source/provider, context, capture time, candidate identity and observable response (added, saved, played later, explicitly liked, rejected, ignored) where available. Keep recommendations/exposure distinct from Last.fm scrobbles, Spotify playback, explicit likes/saves and confirmed preferences. A recommendation is never a play or preference by itself.

PR #60: https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/60

**Status: proposed; PR implementation and tests require review.**

**Resume:** review PR #60 and CI; validate candidate schema and canonical linkage; implement provenance-aware ingestion; test deduplication and evidence separation.

## Documentation and resume

Read [ACTIONS.md](ACTIONS.md) for dated work and evidence. After each meaningful action, update it with files changed, execution, exact verification and outcome. Update [the central handoff](../../NEXT_WORK.md) when priority or blockers change.
