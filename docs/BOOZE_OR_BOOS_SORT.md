# Booze or Boos! — sequence preset

## Playlist brief and hard inclusion gate

Booze or Boos! is a Halloween party playlist, not a generic dark/alternative playlist. **Every track must have a clear, explainable Halloween or horror connection at track level.** Acceptable anchors include monsters, vampires, zombies, witches, ghosts, murder/slasher themes, haunted houses, supernatural/occult imagery, or a specific Halloween/horror film, game or television connection. A dark sound, spooky artist brand, vague "night" reference or generic genre match is not enough. Record the evidence (title/theme/lyric analysis/media source) and hold or reject a track when the connection cannot be defended.

The party-energy gate is separate from Halloween relevance. Tracks should feel confident, playful, campy, chaotic, energetic and party-ready—ideally danceable or a strong singalong/banger. Do not turn the playlist into a somber horror soundtrack, sad-victim narrative or apocalypse mood. A song can be genuinely horror-related and still fail if it drains the party.

The preferred palette includes campy surf/monster-party sounds, psychobilly and horror punk, dark club/synth/rave, industrial and heavy rock/metal. Useful taste anchors include Messer Chups, "Who Do You Voodoo" (Dead Island), "Hex Girl" (Scooby-Doo), Night Club's dark-dance energy, the upbeat feel of "Locals", "Zombie Catches" as a banger, and Rob Zombie/heavy tracks. These are examples, not mandatory quotas or a license to accept weak Halloween fits.

Previously rejected overused novelty staples should not be reintroduced without a new explicit user request: Ghostbusters, Monster Mash, Thriller, This Is Halloween, Somebody's Watching Me, Addams Family, Purple People Eater, and Nightmare on My Street. Avoid duplicates. Treat `playlist_removed_tracks.json` as an absolute removal-protection source; do not re-add a manually removed track because it scores well musically.

Only the generated Booze or Boos! playlist is in scope. Keep the manager's deny-by-default lock, backup, full preview, explicit confirmation and post-write read-back requirements. This guide's sequence preset never authorizes a live write by itself.

## Latest saved snapshot status — 2026-11-06

The latest repository snapshot for playlist `4diIlnF8BlgoJrwUfejf49` was captured at `2026-11-06T01:47:59.824523+00:00`: 92 items were reported and fetched, all 92 track URIs were unique (zero duplicate URIs), the items snapshot was accessible, and no item error was recorded. This is a repository snapshot, not a playlist mutation by the reference workflow.

The older five-axis candidate manifest `assistant_data/spotify/playlist_fit_booze_candidates_20261102.json` and its 64-track audit below describe the earlier 2026-11-02 snapshot only. They are stale for the current 92-item snapshot and must not be used as current coverage or sorting evidence. Regenerate the candidate manifest and rerun the per-track Halloween-relevance/party-energy audit after the documentation-only project pause is lifted.

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

The 2026-11-02 playlist-fit preview audit used the identity-only candidate manifest `assistant_data/spotify/playlist_fit_booze_candidates_20261102.json` to score a 64-track Booze snapshot against five independent calibration-target profiles, excluding the entire candidate batch to avoid leakage. This indicated broad musical affinities and evidence gaps; it did **not** certify Halloween relevance. The 64-track manifest is historical and stale for the 92-item 2026-11-06 snapshot described above. Regenerate it before drawing current conclusions. No playlist writes are performed by this workflow.


## Historical metadata coverage finding (2026-11-02; superseded by the 2026-11-06 snapshot)

In that historical 2026-11-02 audit, 32/64 tracks scored against each target, all low-confidence and one-axis; 31/32 relied on artist-scope genre context, only one track had direct Genre evidence, and 32/64 remained unknown. Direct Sound/Energy/Mood/Theme evidence was absent in the reference profiles. The local cache then had 64 track-profile rows but only 2 Last.fm-tagged tracks and no lyric-theme, direct track-mood or recognized energy rows for Booze. These are historical coverage figures for the old 64-track snapshot, not the current 92-item playlist. Missing data remains unknown, never negative or neutral. Rebuild the recording-level evidence and hard Halloween-theme audit before ranking additions.


## Historical live-preview evidence loading — 2026-11-02

The GitHub control-issue `sequence_preview` path now loads per-recording audio and album evidence from the canonical Library, then fills missing records from the legacy audio/album caches. Previously this cloud-only path omitted both inputs even though the local sequencer supported them, which understated available acoustic evidence. The staging report now prints acoustic-confidence counts and the source/tempo coverage actually used. Semantic genre/theme similarity remains provisional and cannot be presented as measured acoustic smoothness; when recording-level evidence is absent, the sorter must say so rather than invent energy or tempo.

The 2026-11-02 staging plan prepared URI-based section assignments for ten proposed additions: Kid Congo in the campy opener, Alien Sex Fiend in dark club/rave, and the remaining horror-punk/psychobilly tracks in the heavy finale. This is a historical proposal, not evidence that those ten tracks are still staged or present in the current 92-item snapshot. Reconcile assignments against the latest live snapshot before any future preview; section assignments alone do not change Spotify.
