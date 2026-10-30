# Tricky Last.fm Archive

This repository maintains a personal Last.fm scrobble archive and derived analytics for **TrickySturluson**.

## Source of truth

- `data/scrobbles.json` is the canonical, chronological archive. It retains Last.fm identifiers (MBIDs), timestamps, names and URLs.
- `data/metadata.json` stores the latest imported timestamp and archive count.
- `data/stats.json` is the existing compact dashboard summary.
- `assistant_data/` contains query-friendly, generated JSON indexes and time slices. It is always rebuilt from the canonical archive; do not edit generated files by hand.

## Assistant data layout

| Path | Contents |
|---|---|
| `assistant_data/manifest.json` | Schema version, date coverage, file index and integrity totals |
| `assistant_data/overview.json` | Archive totals, coverage, replay leaders and estimated duration |
| `assistant_data/rankings/artists.json` | Complete artist ranking and first/last-seen details |
| `assistant_data/rankings/tracks.json` | Complete artist + track ranking and first/last-seen details |
| `assistant_data/rankings/albums.json` | Complete artist + album ranking and first/last-seen details |
| `assistant_data/indexes/artists.json` | Compact artist lookup index |
| `assistant_data/listening_patterns.json` | Daily, monthly, yearly, weekday and UTC-hour counts |
| `assistant_data/years/YYYY.json` | Full annual summary and rankings |
| `assistant_data/months/YYYY-MM.json` | Full monthly summary, daily counts, new artists and rankings |
| `assistant_data/advanced/` | MBID-aware artist timelines, discovery/rediscovery, rolling rankings, inferred sessions and monthly diversity |
| `assistant_data/playback/` | Measured Spotify playback hours, artist/track totals and daily/monthly listening time (only for intervals captured by the local tracker) |

All generated timestamps and calendar buckets use UTC. Track identity is the artist/track pair; album identity is the artist/album pair, preventing identical titles by different artists from being collapsed. Advanced analytics prefer MusicBrainz IDs (MBIDs) when present and fall back to case-folded names. They include monthly artist timelines, first-time discovery and 90-day rediscovery events, trailing 30/90-day rankings, inferred listening sessions (30-minute gap threshold), and monthly artist-concentration metrics. Rolling windows end at the newest archived scrobble. Session spans are timestamp-based estimates, not actual playback durations.

## Rebuild locally

```bash
python build_stats.py
python build_assistant_data.py
python build_advanced_analytics.py
python build_playback_analytics.py
```

The scheduled GitHub Actions workflow runs the importer and all analytics builders, validates the generated data, then commits updates. It requires the repository secret `LASTFM_API_KEY`.


## Measured Spotify playback time

The Last.fm archive cannot provide exact played duration. For prospective measurement, `spotify_playback_tracker.py` polls Spotify's playback-state API locally and records progress deltas in `playback_data/segments.jsonl`. `build_playback_analytics.py` aggregates those intervals into `assistant_data/playback/`; the scheduled workflow rebuilds and publishes those aggregates whenever the segment log is present in the repository.

### One-time setup

1. Create a personal app in the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
2. Add this exact Redirect URI in the app settings: `http://127.0.0.1:8888/callback`.
3. Copy the app's Client ID. Do not put a client secret in the repository.
4. Install Python 3.10+ (the tracker uses only the standard library).
5. In a terminal opened in this repository, set the Client ID and start the tracker:

   **Windows PowerShell**
   ```powershell
$env:SPOTIFY_CLIENT_ID="your-client-id"
python spotify_playback_tracker.py
```

   **macOS/Linux**
   ```bash
export SPOTIFY_CLIENT_ID="your-client-id"
python3 spotify_playback_tracker.py
```

6. Approve the requested `user-read-playback-state` permission in Spotify. The local callback stores a refresh token in `.spotify_token.json`, which is excluded by `.gitignore`.
7. Leave the tracker running while listening. Stop with Ctrl+C. It appends measured intervals to `playback_data/segments.jsonl`.
8. To publish the totals to this repository, commit and push the generated `playback_data/segments.jsonl` file. The next Actions run will rebuild `assistant_data/playback/`.

The tracker samples every 10 seconds by default; use `python spotify_playback_tracker.py --interval 15` to reduce API polling. It only counts forward playback progress for the same track across consecutive samples, rejects seeks/resets and pauses, and conservatively caps counted progress to elapsed wall time. Track transitions and time when the tracker is closed are not reconstructed. It currently measures tracks, not podcast episodes or ads.

**Important:** this is prospective, local-device sampling, not Spotify's complete listening history. It cannot backfill past listening time, and it may miss short intervals or playback on devices/states the API does not report. Treat it as a measured lower-bound estimate. Keep `.spotify_token.json` private; never commit it. The JSONL playback log contains listening activity and is also personal data.

## Important limitations

- Last.fm's recent-track archive does not supply actual listening duration. The duration estimate uses 3.5 minutes per scrobble and is labelled as an estimate.
- Genre, release dates, biographies, similar artists and other descriptive metadata are not inferred from scrobbles. They require a separate metadata-enrichment stage and may be incomplete or inconsistent.
- The canonical archive is preserved; assistant analytics are derived outputs and can be regenerated at any time.
