# Human listening calibration — SHITting Grounds

**Project:** Spotify Helper & Information Tracker (SHIT)

## Purpose

Use the user's listening judgments to calibrate SHIT's inferred track-to-playlist fit. This is a human-in-the-loop evaluation, not an automatic playlist sorter. The user listens to candidates in [SHITting Grounds](https://open.spotify.com/playlist/4aLdllLgRPh5vKOznkC97D) and rates how well each belongs in each of the five pinned reference playlists.

The five references are independent targets. Do not collapse them into a single taste score, and do not treat playlist names as ground truth when the tracklists disagree.

## Reference targets and initial hypotheses

These are provisional hypotheses based on the complete checked-in snapshots captured 2026-11-01. Human ratings override these hypotheses.

| Playlist | ID | Snapshot size | Initial sound/fit hypothesis | Confidence |
|---|---|---:|---|---|
| [To 11](https://open.spotify.com/playlist/5meDjtqrqOe5oHpvZGWRMz) | `5meDjtqrqOe5oHpvZGWRMz` | 16 | Aggressive, high-impact alternative rock / nu-metal / rap-rock; punchy, confrontational, loud, energetic | Medium-high |
| [Somber Party](https://open.spotify.com/playlist/7L2rSp4SuohBEyNxEtAurx) | `7L2rSp4SuohBEyNxEtAurx` | 8 | Melancholic or emotionally off-kilter music with enough groove/character to coexist in a party context; likely intentionally eclectic | Low (small sample) |
| [. . .](https://open.spotify.com/playlist/4HzqY9iy04M1EVSF5kcD64) | `4HzqY9iy04M1EVSF5kcD64` | 191 | Indie / bedroom-pop / dream-pop / jangly and hazy alternative; relaxed, wistful, soft-edged, melodic | Medium |
| [=^=](https://open.spotify.com/playlist/0O9ojSstxwa5vQy2V7pO2x) | `0O9ojSstxwa5vQy2V7pO2x` | 60 | Gritty swaggering alt-rock / blues-rock / garage-rock; dark, confident, stomping, cinematic, often devilish or rebellious | Medium-high |
| [Smooth](https://open.spotify.com/playlist/2ICCklgbF6cg0q5p4xAHKi) | `2ICCklgbF6cg0q5p4xAHKi` | 11 | Hazy downtempo / lo-fi / synthwave / instrumental electronic; relaxed, atmospheric, groove-led, low-friction | Medium-low (small sample) |

## Human rating scale

For every auditioned track, collect a separate 0–100 fit rating for each reference:

- **0–19 — No fit:** actively wrong for this playlist.
- **20–39 — Weak:** a few shared traits, but does not belong.
- **40–59 — Borderline:** plausible adjacent fit; would need the right context or sequence.
- **60–79 — Good:** naturally belongs, even if not a defining example.
- **80–94 — Strong:** clear fit and representative of the playlist.
- **95–100 — Defining:** near-perfect exemplar of what the playlist is about.

Also collect:
- **Primary placement:** the one playlist the user would choose if forced to pick one; allow `none`.
- **Optional note:** why the prediction was right/wrong (lyrics, mood, energy, production, groove, context, or something the model missed).
- **Confidence in the user's own rating:** optional; do not force a false precision.

A track may score highly for more than one playlist. Do not force mutually exclusive labels. The primary placement is a convenience label, not a replacement for the five independent fit ratings.

## Prediction vs human judgment

Store model predictions and human labels separately. For every track record, retain:

- Spotify track URI and stable track identity (artist + title; album when needed to disambiguate)
- calibration-set version and exact reference playlist IDs
- per-reference predicted fit (0–100), evidence/confidence, and short explanation
- per-reference human fit (0–100), primary placement, optional note, and rating timestamp
- source snapshot ID / capture time and metadata provenance used for the prediction

Never overwrite inferred metadata with human preference ratings. Never treat a low fit rating as a negative listening preference; it only says the track is a poor fit for that particular playlist.

## Audition batch design

Once SHITting Grounds and the candidate pool have fresh snapshots:

1. Exclude tracks already in the five calibration references.
2. Score eligible candidates independently against all five targets.
3. Build a balanced first batch: clear high-confidence examples, close-call tracks, and low-confidence/metadata-poor cases. Avoid filling the batch only with obvious matches.
4. Prefer a manageable batch (roughly 20–30 tracks) with coverage across all five targets.
5. Write the candidate set to SHITting Grounds only through the existing preview/confirmation workflow and only after the target playlist is explicitly authorized for that action. Preserve existing items; do not replace the playlist.
6. Present the predicted primary placement, five fit scores, confidence and rationale for each candidate.
7. After listening, ingest the user's ratings as calibration labels and report where the model over- or under-predicts.

## Current retrieval and write status

- The five calibration snapshots are complete in the 2026-11-01 reference snapshot: To 11 16/16, Somber Party 8/8, . . . 191/191, =^= 60/60, Smooth 11/11.
- SHITting Grounds is registered as `sorter_audition_destination`, but the checked-in catalog does not yet contain its playlist snapshot. Its live contents must be checked before additions so existing tracks are preserved and duplicates are avoided.
- The current conversation has no connected Spotify read/write action available. Do not claim that tracks have been added. Use the repository's authenticated Spotify workflow or a fresh local reference sync when available.
- All Time and Hell remain useful broad taste/history references, but are not narrow calibration targets.

## Safety

- Reference playlists are read-only.
- SHITting Grounds is the intended audition destination, not a blanket write authorization for other playlists.
- Preview exact additions and preserve current contents. Never replace or reorder a reference playlist.
- Keep the existing owner verification, managed-playlist authorization, lock state, backup, and one-time confirmation protections.
