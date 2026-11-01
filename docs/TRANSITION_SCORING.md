# Transition scoring and evaluation

## Why scores could look artificially poor

The previous transition cost treated absent mood, genre, and theme metadata as a mismatch. For example, two tracks with no mood tags received the same mood penalty as two tracks with known, conflicting moods. It also compared placeholder energy scores for tracks with no usable energy evidence. This made sparse metadata look like negative musical compatibility.

## Current behavior

The sequencer now uses evidence-aware transition scoring:

- A metadata dimension contributes only when both tracks have evidence for that dimension.
- Unknown energy is not compared as though a measured score of 50 were real.
- Only explicit `acoustic_confidence=medium|high` can support an energy comparison. A legacy generic `confidence=medium` without an acoustic basis is not trusted.
- Acoustic and semantic confidence are separate. Multiple genre, mood, lyric, or artist tags cannot promote acoustic confidence.
- Track-level mood confidence is reported separately from broad semantic coverage: one descriptive tag is low confidence; multiple distinct tags or independent track-tag sources can support medium confidence; high confidence requires at least two independent track-tag source families, at least two distinct mood descriptors, and no opposing affect-direction conflict. Raw community tag counts do not create corroboration or independently raise confidence.
- Last.fm track tags and MusicBrainz recording tags may corroborate track mood. Genre fields, Discogs release styles, lyric themes, and artist-level tags do not count as track-level mood confirmations.
- Opposing energetic/gentle mood evidence is retained and surfaced as a conflict. It lowers mood confidence and contributes a neutral mood-energy value rather than arbitrarily selecting one direction.
- Artist-level mood is an explicitly low-confidence fallback when track-level mood tags are absent. It remains useful as context but is not presented as a track-specific assessment.
- Mood affinity is confidence-weighted during sequencing: high-confidence moods receive the strongest continuity weight, medium moods a reduced weight, low moods a small hint, and unknown moods no weight.
- Low-confidence mood matches do not count as independent evidence when a transition is labeled supported. Preview diagnostics report track mood confidence counts and source-family coverage separately from overall semantic coverage.
- The displayed perceived-energy score may blend acoustic and descriptive cues, but transition energy gaps and the journey curve use the separate acoustic-only score. Semantic-only tracks have no acoustic score and are not pulled toward a fictitious journey-curve target.
- Low-confidence estimates retain a reduced journey-curve weight, while unknown placeholders remain display-only.
- Transition confidence is marked supported only when at least two comparable dimensions exist and both tracks have medium/high energy evidence.
- The optimizer uses four evenly distributed starting tracks and two local-refinement passes within a 12-position neighborhood to keep real-playlist previews responsive.
- The placeholder score of 50 is display-only: the sequence journey objective skips unknown-energy tracks, so it cannot attract them toward a fictitious midpoint.
- Transition reports expose `energy_gap: null` when either track lacks energy evidence, rather than publishing a misleading numeric gap.
- When no comparable evidence exists, the report labels the handoff **uncertain**, not a potential jump or a failed match.
- Available dimensions are normalized over their actual weights, so missing fields do not create automatic penalties.
- BPM compatibility is included when both tracks have valid tempo values; each estimate retains its source (Essentia, Spotify-provided features, AcousticBrainz, or GetSongBPM catalog).
- The source summary reports tempo-provider coverage and cross-provider agreement/disagreement, with half/double-time equivalence handled before judging agreement.
- Multiple providers for the same artist/title are merged into one profile without discarding provider-specific records; a later provider cannot erase a populated value with a null.
- Discogs styles/genres may enrich the descriptive genre context only after exact artist and tracklist validation against one unique release/master. They never count as acoustic evidence.
- Half-time and double-time relationships are treated as rhythmically compatible (for example, 80 and 160 BPM).
- Repeating the same primary artist receives a strong sequencing-only diversity penalty; the greedy builder avoids a third consecutive track by the same artist when alternatives exist, and the sequence objective penalizes any remaining run of three or more. The transition report keeps musical compatibility separate from that preference.
- Genre and theme preferences remain soft bonuses, not hard grouping requirements.

## Reading evaluation output

`gentle`, `moderate`, and `potential jump` are evidence-backed transition assessments. `provisional` means some metadata suggests a handoff quality, but the underlying evidence is too weak to call it a confirmed jump or smooth transition. `uncertain` means there is not enough shared metadata to judge the transition. It is not a negative score.

Track energy confidence remains separate from transition confidence. The sequence preview prints track confidence counts, loaded acoustic-profile count, and transition counts so users can distinguish missing coverage from poor compatibility. With --compare, it also writes alternative plans at 70%, 85%, and 95% peak positions (skipping the selected target) and prints each alternative's transition counts. These are preview files only; apply remains a separate, confirmation-gated manager operation.

## Data provenance

Tempo and acoustic descriptors retain provider/source fields. AcousticBrainz average loudness is not LUFS; multiple AcousticBrainz submissions are median-aggregated with spread and count retained. GetSongBPM tempo is catalog metadata, not a local audio measurement. Spotify loudness in dB is not LUFS. Essentia LUFS and segment-level dynamics are available only for legally obtained local audio analyzed by the project. Discogs genres/styles are release-level context, not track-level acoustic evidence. Missing values must remain missing; do not fill them with zero.

## Regression tests

Run from the repository root:

```bash
python -m unittest tests.test_spotify_playlist_sequencer -v
```

The tests cover unknown metadata, acoustic-versus-semantic confidence separation, provider merging and tempo agreement, half/double-time BPM relationships, the effect of shared metadata on transition cost, and formatting of alternative-preview summaries.

## FILE OVERVIEW

- **Purpose:** Explains how SHIT evaluates song-to-song transitions and how to interpret evidence-limited results.
- **Scope:** Missing-data handling, BPM relationships, transition labels, and source provenance.
- **Related implementation:** `scripts/spotify/spotify_playlist_sequencer.py`.
- **Regression coverage:** `tests/test_spotify_playlist_sequencer.py`.
- **Related guides:** `docs/AUTOMATED_AUDIO_METADATA.md` and `docs/GETSONGBPM.md`.