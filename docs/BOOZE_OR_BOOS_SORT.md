# Booze or Boos! — sequence preset

This preset follows the intended party arc:

1. Campy surf, monster-party novelty, lyrical crowd-pleasers and Messer Chups.
2. Dark club, synth and rave-leaning Halloween tracks.
3. Horror punk and psychobilly as the energy climbs.
4. A short industrial/heavy-rock closer, ending with Rob Zombie.

The four sections are kept in their declared order and smoothed internally. A single global rising-energy curve is used across the acts, with the high-energy target sustained through the end. Artist repetition is penalized so Messer Chups and other favorites are spread out rather than played in one long block. Genre-family energy estimates are conservative; they are not measured Spotify audio features. The preview reports confidence so uncertain estimates are visible.

The live sequence_preview command refreshes the playlist directly from Spotify, reads artist and track profiles plus the compact lyric-theme export, and creates a one-time confirmation preview. It does not change Spotify. Confirmation is a separate command and is rejected if the playlist changed after preview.

## Run from the SHIT control issue

Set the open issue titled SHIT — Playlist Control to this JSON body:

```json
{"command":"sequence_preview","playlist_id":"4diIlnF8BlgoJrwUfejf49"}
```

The GitHub Actions workflow posts the live proposed order and a one-time confirmation code. Review the full sequence before submitting a separate confirm command. The playlist must remain unlocked and unchanged between preview and confirmation.

Section assignments in assistant_data/spotify/booze_or_boos_sections.json are keyed by Spotify track URI. If the playlist gains new tracks, the preview reports them as unassigned so they can be categorized before applying the sort.


## Five-axis cross-reference audit

The playlist-fit preview workflow now runs an additional read-only audit over the saved Booze or Boos! snapshot. The identity-only candidate manifest is `assistant_data/spotify/playlist_fit_booze_candidates_20261102.json`. It scores current Booze tracks against the five independent calibration-target profiles, excluding the entire Booze candidate batch from those profiles to avoid candidate leakage. This indicates broader musical affinity and evidence gaps; it does **not** certify that a track is Halloween-related. Use explicit recording-level theme/lyric evidence and the party brief for that judgment. The current saved snapshot has 64 tracks; regenerate the manifest if the source snapshot changes. No playlist writes are performed by this workflow.


## Current metadata coverage finding (2026-11-02)

The 64-track saved snapshot resolves to canonical Library records, but the five-axis cross-reference is not yet a safe automatic sorting signal: only 32/64 tracks score against each target, all low-confidence and one-axis; 31/32 rely on artist-scope genre context, only one track has direct Genre evidence, and 32/64 remain unknown. Sound/Energy/Mood/Theme direct evidence is absent in the reference profiles. The local cache check found 64 track-profile rows but only 2 Last.fm-tagged tracks and no lyric-theme, direct track-mood or recognized energy rows for Booze. Treat missing data as unknown, not as a negative or neutral musical trait. The immediate work is recording-level evidence enrichment and a separate Halloween-theme audit; don't rank additions from the current cross-reference scores.


## Live preview evidence loading — 2026-11-02

The GitHub control-issue `sequence_preview` path now loads per-recording audio and album evidence from the canonical Library, then fills missing records from the legacy audio/album caches. Previously this cloud-only path omitted both inputs even though the local sequencer supported them, which understated available acoustic evidence. The staging report now prints acoustic-confidence counts and the source/tempo coverage actually used. Semantic genre/theme similarity remains provisional and cannot be presented as measured acoustic smoothness; when recording-level evidence is absent, the sorter must say so rather than invent energy or tempo.

The ten currently staged additions have URI-based section assignments prepared: Kid Congo in the campy opener, Alien Sex Fiend in dark club/rave, and the remaining horror-punk/psychobilly tracks in the heavy finale. These assignments become active when the tracks are actually added; they do not change the Spotify playlist by themselves.
