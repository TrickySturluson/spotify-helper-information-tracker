# Booze or Boos! — sequence preset

This preset implements the user's intended party arc:

1. Campy surf, monster-party novelty and Messer Chups.
2. Horror punk and psychobilly as the energy climbs.
3. Dark club, synth and rave-leaning Halloween tracks.
4. Heavy horror-rock and industrial-metal finale.

The section assignments are soft ordering preferences, not hard blocks. The sequencer still optimizes neighboring transitions, artist repetition, mood/genre/theme affinity and a rising energy curve. The rising curve now holds at high energy through the final section instead of falling away after its peak.

The live sequence_preview command refreshes the playlist directly from Spotify, reads artist and track profiles plus the compact lyric-theme export, and creates a one-time confirmation preview. It does not change Spotify. The preview reports energy confidence and warns about unassigned tracks and uncertain transitions. Confirmation is a separate command and is rejected if the playlist changed after preview.

## Run from the SHIT control issue

Set the open issue titled SHIT — Playlist Control to this JSON body:

```json
{"command":"sequence_preview","playlist_id":"4diIlnF8BlgoJrwUfejf49"}
```

The GitHub Actions workflow posts the live proposed order and a one-time confirmation code. Review the full sequence before submitting a separate confirm command. The playlist must remain unlocked and unchanged between preview and confirmation.

Section assignments in assistant_data/spotify/booze_or_boos_sections.json are keyed by Spotify track URI. If the playlist gains new tracks, the preview reports them as unassigned so they can be categorized before applying the sort.
