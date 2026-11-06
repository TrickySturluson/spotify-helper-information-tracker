# Recent Track Enrichment

SHIT now maintains a rolling **90-day top-200 track cohort** derived from the canonical Last.fm scrobble archive.

## Selection and provenance

- The ranking counts scrobbles with timestamps in the trailing 90 days at run time.
- Tracks are deduplicated by the same stable identity used by the track-profile builder.
- Ties are resolved by all-time scrobbles, then artist/title for deterministic output.
- The generated `assistant_data/music/recent_top_tracks.json` records the window, generation time, candidate count, stable IDs, names, recent play counts, and all-time play counts.
- This is Last.fm scrobble history, not Spotify's short recently-played API window and not measured Spotify playback tracker intervals.

## Enrichment

The existing incremental track-profile pipeline prioritizes the cohort for Last.fm track tags and MusicBrainz recording tags/genres where a verified recording MBID exists. It retains cached profiles, retries according to existing cooldown rules, and never invents a match when identity is ambiguous. The scheduled workflow processes up to 200 track profiles per run. Manual dispatch offers 120, 300, or 600 lookups (default 300); the standalone script defaults to 120 when no environment override is set. The 200-track cohort size and the per-run lookup budget are separate controls.

Audio measurements remain a separate layer. Spotify's Audio Features and Audio Analysis endpoints are unavailable to many development-mode applications under Spotify's November 2024 API changes; SHIT therefore does not treat those fields as guaranteed. The separate AcousticBrainz and optional GetSongBPM enrichers remain best-effort external sources, with provenance and confidence kept explicit.

## Commands

```bash
TRACK_PROFILE_RECENT_WINDOW_DAYS=90 TRACK_PROFILE_RECENT_TOP_N=200 TRACK_PROFILE_LOOKUPS_PER_RUN=200 TRACK_PROFILE_PRIORITY_PLAYLISTS=4diIlnF8BlgoJrwUfejf49 python compat/build_track_profiles.py
```

### Canonical Library writes and playlist-only candidates

The track-profile builder also writes the selected cohort into canonical song/artist/album records through `MusicLibrary.put_catalogue()`; it does not only update the track-profile cache. The cohort can include exact priority-playlist tracks even when they have zero Last.fm scrobbles. Playlist membership is source/context evidence, not a play, like, save, or positive listening preference. Last.fm play counts remain sourced from the Last.fm archive. This is a repository data write, not a Spotify playlist mutation.

## Workflow

- `SHIT — Spotify Reference Library`: scheduled daily at 06:13 UTC and manually dispatchable. A commit to its workflow definition on `main` also triggers an immediate sync, which is useful when workflow dispatch is unavailable.
- `Enrich Music Metadata`: daily at 08:17 UTC and manually dispatchable. Scheduled track-profile budget is 200; manual dispatch allows 120/300/600. Changes to the workflow, enrichment scripts/compatibility launchers, discovery intake files, or selected priority-playlist snapshot paths trigger an immediate run; generated-data commits do not match those paths.
- Both workflows commit only generated data; they do not modify Spotify playlists.

