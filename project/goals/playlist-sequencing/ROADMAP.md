# Playlist Sequencing — Roadmap

**Last reviewed:** 2026-11-05  
**Status:** Active development. Preview/confirmation safeguards and evidence-aware transition scoring are documented; real-playlist quality, coverage and live write authorization must be assessed independently.

## Purpose
Arrange tracks into coherent, enjoyable listening journeys. Smooth transitions are the primary objective; sequencing must not invent acoustic certainty when source metadata is missing.

## User requirements and invariants
- Smooth transitions take priority over abrupt genre or energy jumps. Avoid jarring adjacent tracks.
- Support a controllable energy journey: slow-to-fast/loud or reverse, gradual resolution, theme/genre sections, anchors and a configurable peak position. A peak around 80–90% is a tentative default, not a fixed rule.
- Use track-level mood/theme evidence. Artist identity alone is not enough to claim a track's mood or lyrical subject.
- Use BPM, measured or sourced loudness/energy, audio analysis, lyrics-derived themes and available local lyrics lookup where provenance is clear.
- Unknown metadata is unknown, not a neutral midpoint or a mismatch. Separate acoustic confidence from semantic confidence.
- Keep preview generation read-only. A live write requires an explicit, separate confirmation and must reject a playlist that changed after preview.
- Keep the sequencer separate from the five-axis playlist-fit scorer unless a future design explicitly validates and approves integration.
- Playlist-specific presets may define section order and energy arc; the Booze or Boos! preset must remain energetic, playful and strongly Halloween-related per track.

## Implementation map
- Sequencer: scripts/spotify/spotify_playlist_sequencer.py
- Transition scoring guide: docs/TRANSITION_SCORING.md
- Booze preset guide: docs/BOOZE_OR_BOOS_SORT.md
- Music evidence and track profiles: scripts/music/music_evidence.py, scripts/music/build_track_profiles.py, scripts/music/mood_inference.py
- Lyric/theme evidence: scripts/music/lyrics_library.py and docs/LYRICS_LIBRARY.md
- Regression tests: tests/test_spotify_playlist_sequencer.py
- Playlist Intelligence umbrella: project/goals/playlist-intelligence/ROADMAP.md

## Roadmap
1. **Evidence quality.** Improve recording-level BPM, acoustic energy/loudness, mood, genre and lyric-theme coverage with explicit source, timestamp and confidence.
2. **Transition objective.** Keep unknown dimensions out of mismatch penalties; compare only shared evidence; keep acoustic and semantic confidence separate; report uncertain handoffs honestly.
3. **Journey controls.** Validate direction, peak position, arc strength, section boundaries, anchors, smooth resolution and gradual energy changes.
4. **Artist and repetition handling.** Spread repeated artists where alternatives exist without sacrificing musical compatibility or inventing hard constraints.
5. **Preset quality.** Maintain explainable presets such as Booze or Boos! with section assignments, party-energy requirements and per-track theme checks.
6. **Preview and transaction safety.** Refresh the live playlist before preview; stage full proposed order; issue one-time confirmation; reject stale previews; audit and read back any authorized write.
7. **Evaluation.** Compare transition reports with human listening feedback and held-out examples; preserve failure cases and regressions; do not optimize solely for an opaque aggregate score.

## Acceptance criteria
- Missing metadata never creates an automatic transition penalty or fake measured energy.
- Transition diagnostics identify evidence sources, confidence, and unknown dimensions.
- User controls produce the intended arc and section order without abrupt artificial jumps.
- Presets meet their stated playlist brief; Booze tracks require explicit Halloween relevance and party energy, not just generic musical fit.
- Preview does not mutate Spotify. Confirmation rejects stale playlist state and requires explicit authorization.
- Any authorized write is audited and followed by live read-back verification.
- Regression tests cover evidence sparsity, energy confidence, artist repetition, section order, preview staleness and safety.

## Current gaps / verification requirements
- The transition-scoring guide describes current evidence-aware behavior; inspect implementation and tests before changing it.
- The five-axis playlist-fit model is preview-only and is not wired into the sequencer. Do not claim that model supplies production sorting decisions.
- Current acoustic and semantic coverage is incomplete; unknown must remain visible rather than being filled with invented values.
- A good preview or passing test does not authorize a live playlist write.

## Next action
Audit the current sequencer implementation and tests against this roadmap, then compare a fresh read-only preview with the latest live playlist and evidence coverage. Record specific transition failures before changing weights or presets.

## Related records
[README](README.md) · [ACTIONS](ACTIONS.md) · [Playlist Intelligence](../playlist-intelligence/ROADMAP.md) · [Transition scoring](../../../docs/TRANSITION_SCORING.md) · [Booze preset](../../../docs/BOOZE_OR_BOOS_SORT.md)