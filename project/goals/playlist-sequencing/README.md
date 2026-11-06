# Playlist Sequencing

Playlist Sequencing is SHIT's ordering engine. It optimizes track-to-track flow and a user-defined listening journey; it is distinct from candidate recommendation and the five-axis playlist-fit scorer.

## Core behavior
- Compare adjacent tracks only on dimensions with evidence for both tracks.
- Keep acoustic evidence (tempo, measured audio energy/loudness) separate from semantic evidence (genre, mood, lyric theme, artist context).
- Preserve source, confidence and scope. Track-level mood/theme must not be inferred solely from artist identity.
- Treat unknown as unknown. A placeholder used for display must never be treated as measured energy or used to attract a track toward an artificial midpoint.
- Explain uncertain transitions instead of labelling missing evidence as a bad match.
- Allow playlist presets to control sections, anchors, energy direction, peak placement and resolution while retaining smooth local transitions.

## Implementation and references
| Concern | Location |
|---|---|
| Sequencer and preview/confirmation | scripts/spotify/spotify_playlist_sequencer.py |
| Transition evidence and scoring rules | docs/TRANSITION_SCORING.md |
| Booze or Boos! section preset | docs/BOOZE_OR_BOOS_SORT.md and assistant_data/spotify/booze_or_boos_sections.json |
| Music evidence/profile construction | scripts/music/music_evidence.py and scripts/music/build_track_profiles.py |
| Lyrics and theme evidence | scripts/music/lyrics_library.py and docs/LYRICS_LIBRARY.md |
| Regression coverage | tests/test_spotify_playlist_sequencer.py |

## Safety and operating sequence
1. Read the roadmap and current implementation/test history.
2. Refresh the source playlist from Spotify; do not rely on stale snapshots for a live preview.
3. Inspect available evidence and coverage before optimizing; record unknowns and confidence.
4. Generate a read-only preview and inspect the entire proposed sequence, sections and transition diagnostics.
5. Confirm only through the separate explicit confirmation path. Confirmation must be bound to the exact staged preview and reject changed live playlist state.
6. After any authorized write, read back the live playlist and compare the ordered URIs with the staged order.

## Separation from playlist-fit scoring
The five-axis playlist-fit model measures a candidate's relationship to a playlist identity. It is a separate preview-only tool and is not automatically a transition score or a production sequencing input. Do not connect them without a documented design decision, evidence validation and regression coverage.

## Related work
[Playlist Intelligence & Safety](../playlist-intelligence/README.md) owns shared playlist fit, discovery and feedback. [Booze or Boos!](../../../docs/BOOZE_OR_BOOS_SORT.md) documents one playlist-specific sequencing preset.