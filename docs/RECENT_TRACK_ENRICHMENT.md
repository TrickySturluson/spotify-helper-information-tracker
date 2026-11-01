# Recent Track Enrichment

SHIT now maintains a rolling **90-day top-200 track cohort** derived from the canonical Last.fm scrobble archive.

## Selection and provenance

- The ranking counts scrobbles with timestamps in the trailing 90 days at run time.
- Tracks are deduplicated by the same stable identity used by the track-profile builder.
- Ties are resolved by all-time scrobbles, then artist/title for deterministic output.
- The generated `assistant_data/music/recent_top_tracks.json` records the window, generation time, candidate count, stable IDs, names, recent play counts, and all-time play counts.
- This is Last.fm scrobble history, not Spotify's short recently-played API window and not measured Spotify playback tracker intervals.

## Enrichment

The existing incremental track-profile pipeline prioritizes the cohort for Last.fm track tags and MusicBrainz recording tags/genres where a verified recording MBID exists. It retains cached profiles, retries according to existing cooldown rules, and never invents a match when identity is ambiguous. The workflow budgets up to 200 track-profile lookups per run.

Audio measurements remain a separate layer. Spotify's Audio Features and Audio Analysis endpoints are unavailable to many development-mode applications under Spotify's November 2024 API changes; SHIT therefore does not treat those fields as guaranteed. The separate AcousticBrainz and optional GetSongBPM enrichers remain best-effort external sources, with provenance and confidence kept explicit.

## Commands

```bash
TRACK_PROFILE_RECENT_WINDOW_DAYS=90 TRACK_PROFILE_RECENT_TOP_N=200 TRACK_PROFILE_LOOKUPS_PER_RUN=200 TRACK_PROFILE_PRIORITY_PLAYLISTS=4diIlnF8BlgoJrwUfejf49 python compat/build_track_profiles.py
```

## Workflow

- `SHIT — Spotify Reference Library`: scheduled every six hours and manually dispatchable. A commit changing its workflow definition also triggers an immediate sync, which is useful when workflow dispatch is unavailable.
- `Enrich Music Metadata`: daily schedule and manual dispatch; commits to its workflow or track-profile implementation trigger an immediate enrichment run.
- Both workflows commit only generated data; they do not modify Spotify playlists.

