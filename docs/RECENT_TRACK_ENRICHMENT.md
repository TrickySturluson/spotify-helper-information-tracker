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

## Latest verified enrichment run — 2026-11-06

Enrich Music Metadata run [#42166959478](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42166959478) completed successfully and published generated-data commit `3d2c1ded`.

- MusicBrainz duration fallback: 67 matches from 182 lookups; 2,695 tracks remained unresolved at that stage.
- Artist profiles: 3,373 matched; 100 lookups in the run; 56 new profiles with tags; 787 pending.
- Recording-ID resolution: 0 new exact matches from 3 lookups; 5,461 tracks still lacked a recording MBID.
- Track profiles: 229 records with sourced tags; 200 Last.fm lookups (6 tagged), 114 MusicBrainz lookups (6 tagged), 8,428 pending.
- Album profiles: 905 matched; 100 lookups in the run; 65 tagged; 5,700 due/pending across 6,603 catalogue albums.
- Canonical Library sync merged 195 discovery candidates and passed its audit at 13,239 songs.
- Final duration coverage: 8,254/11,130 unique tracks and 139,758/152,005 scrobbles (91.9%).
- Final project integrity audit: 9 checks, 18 warnings, 0 errors. Warnings were no captured playback intervals and 16 Spotify playlists whose item contents were inaccessible; retained snapshots may be stale. The workflow did not modify Spotify playlists.

These are timestamped run results, not timeless coverage guarantees. Re-read the current generated manifests and reports before using them as a later baseline.

## Commands

```bash
TRACK_PROFILE_RECENT_WINDOW_DAYS=90 TRACK_PROFILE_RECENT_TOP_N=200 TRACK_PROFILE_LOOKUPS_PER_RUN=200 TRACK_PROFILE_PRIORITY_PLAYLISTS=4diIlnF8BlgoJrwUfejf49 python compat/build_track_profiles.py
```

## Workflow

- `SHIT — Spotify Reference Library`: scheduled daily at **06:13 UTC** and manually dispatchable. A commit changing its workflow definition also triggers an immediate sync, which is useful when workflow dispatch is unavailable.
- `Enrich Music Metadata`: daily schedule and manual dispatch; commits to its workflow or track-profile implementation trigger an immediate enrichment run.
- Both workflows commit only generated data; they do not modify Spotify playlists.

