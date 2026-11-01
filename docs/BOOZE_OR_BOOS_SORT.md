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
