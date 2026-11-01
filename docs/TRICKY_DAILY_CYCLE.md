# Tricky Daily listening trends

Tricky Daily is a rotating discovery queue, not a fixed mood/theme playlist.
Its discovery engine keeps established taste and Last.fm similarity as the
foundation, uses recent listening momentum as a small soft nudge, and retains
room for exploration outside current patterns.

## Trend profile

`scripts/spotify/spotify_listening_trends.py` builds
`assistant_data/spotify/listening_trends.json` from canonical Last.fm scrobbles
and artist genre/tag metadata. It reports 7-day, 30-day, 90-day, preceding
60-day, and all-time artist activity. Genre/tag trends are aggregated from
recent plays and the artist metadata already available in the project.

The trend layer distinguishes a rising interest from an established favorite.
Sparse or missing comparison history is marked low confidence, never treated
as zero or as an artificial spike. The candidate-ranking nudge is capped at
0.03 and only applies to medium/high-confidence artist trends. No genre is
hard-filtered. Daily ignores playlist lyric-theme affinity; other playlists
retain their playlist-specific theme system.

## Feedback boundaries

Daily's own saves, post-add listening and scrobbles remain useful outcome
signals. Scheduled rotation is neutral housekeeping and never a blacklist or
playlist-fit rejection. This trend profile is user-wide context, not a
replacement for Daily's separate exposure feedback or general playlist-fit
calibration.

## Operation

The midnight cycle refreshes the trend report before building recommendations.
To inspect or regenerate it independently:

```bash
python compat/spotify_listening_trends.py
```
