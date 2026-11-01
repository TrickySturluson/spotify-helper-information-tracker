# Transition scoring and evaluation

## Why scores could look artificially poor

The previous transition cost treated absent mood, genre, and theme metadata as a mismatch. For example, two tracks with no mood tags received the same mood penalty as two tracks with known, conflicting moods. It also compared placeholder energy scores for tracks with no usable energy evidence. This made sparse metadata look like negative musical compatibility.

## Current behavior

The sequencer now uses evidence-aware transition scoring:

- A metadata dimension contributes only when both tracks have evidence for that dimension.
- Unknown energy is not compared as though a measured score of 50 were real.
- When no comparable evidence exists, the report labels the handoff **uncertain**, not a potential jump or a failed match.
- Available dimensions are normalized over their actual weights, so missing fields do not create automatic penalties.
- BPM compatibility is included when both tracks have valid tempo values.
- Half-time and double-time relationships are treated as rhythmically compatible (for example, 80 and 160 BPM).
- Repeating the same primary artist remains a sequencing cost, but its capped penalty cannot dominate the musical evidence.
- Genre and theme preferences remain soft bonuses, not hard grouping requirements.

## Reading evaluation output

`gentle`, `moderate`, and `potential jump` are evidence-backed transition assessments. `uncertain` means there is not enough shared metadata to judge the transition. It is not a negative score.

Track energy confidence remains separate from transition confidence. The sequence preview prints track confidence counts, loaded acoustic-profile count, and transition counts so users can distinguish missing coverage from poor compatibility. With --compare, it also writes alternative plans at 70%, 85%, and 95% peak positions (skipping the selected target) and prints each alternative's transition counts. These are preview files only; apply remains a separate, confirmation-gated manager operation.

## Data provenance

Tempo and acoustic descriptors retain their provider/source fields. AcousticBrainz average loudness is not LUFS. GetSongBPM tempo is catalog metadata, not a local audio measurement. Essentia LUFS and segment-level dynamics are available only for legally obtained local audio analyzed by the project. Missing values must remain missing; do not fill them with zero.

## Regression tests

Run from the repository root:

```bash
python -m unittest tests.test_spotify_playlist_sequencer -v
```

The tests cover unknown metadata, half/double-time BPM relationships, the effect of shared metadata on transition cost, and formatting of alternative-preview summaries.

## FILE OVERVIEW

- **Purpose:** Explains how SHIT evaluates song-to-song transitions and how to interpret evidence-limited results.
- **Scope:** Missing-data handling, BPM relationships, transition labels, and source provenance.
- **Related implementation:** `scripts/spotify/spotify_playlist_sequencer.py`.
- **Regression coverage:** `tests/test_spotify_playlist_sequencer.py`.
- **Related guides:** `docs/AUTOMATED_AUDIO_METADATA.md` and `docs/GETSONGBPM.md`.