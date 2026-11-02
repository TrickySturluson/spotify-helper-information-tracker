# Offline Sorter Evaluation Plan

## Goal

Evaluate the existing `scripts/spotify/spotify_playlist_sequencer.py` against real generated-playlist snapshots and Library evidence without writing to Spotify.

## Evaluation stages

1. **Baseline inventory:** load the same playlist snapshot and Library profiles used by preview; report playlist size, identity match rate, profile coverage by field (energy, tempo, loudness, track mood, genre, lyric/theme), and confidence distribution. Missing values remain unknown.
2. **Transition diagnostics:** run the existing `transition_report` for every adjacent pair in the proposed order. Count supported/provisional/uncertain handoffs and potential jumps separately. Report actual numeric energy/BPM/loudness gaps only where both sides have comparable evidence.
3. **Objective comparison:** compare original order and sequenced order using the same evidence-aware objective. Also compare 70%, 85%, and 95% peak positions when the CLI supports `--compare`. Do not claim improvement solely from a lower score; disclose evidence coverage and uncertain transitions.
4. **Robustness:** repeat with sparse/missing profile fields and verify that unknowns do not become mismatches, placeholder energy does not attract the journey curve, and low-confidence artist/album context cannot dominate track-level evidence.
5. **Musical review:** inspect the largest measured adjacent jumps and the most uncertain runs. For Booze or Boos!, validate energetic party pacing and strong Halloween relevance independently of smoothness. For Tricky Daily, optimize comfortable flow and variety without interpreting unplayed exposure as rejection.
6. **Performance:** record runtime, candidate count, and optimizer settings; avoid repeated full-catalogue loads and provider requests. Library-first per-playlist retrieval should be reused.
7. **Output:** deterministic JSON/Markdown report with input snapshot identifiers, Library/index version, settings, coverage, confidence, transition counts, worst supported jumps, baseline comparison, and limitations.

## Acceptance criteria

- Entire evaluation is offline/read-only: zero provider requests, Library writes, Spotify writes, or playlist changes.
- Same inputs and settings produce the same order and report (apart from explicitly excluded generated-at metadata).
- Unknown evidence is never scored as a measured mismatch or a fabricated numeric gap.
- Every recommendation is accompanied by field coverage and confidence.
- Tests cover sparse data, conflicting track mood, missing acoustic evidence, BPM half/double-time compatibility, repeated-artist constraints, and peak-position variants.
- Live playlist previews are only read-only snapshots; no apply or manager mutation is invoked.

## First evaluation targets

- Synthetic regression suite in `tests/test_spotify_playlist_sequencer.py`.
- Booze or Boos! snapshot only after checking whether the checked-in snapshot is current; prior user-reported live count was 66 and repository state may be stale.
- Tricky Daily as a separate flow/variety profile; preserve liked-track down-ranking as a soft preference and do not penalize unplayed tracks.
