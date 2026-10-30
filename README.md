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

All generated timestamps and calendar buckets use UTC. Track identity is the artist/track pair; album identity is the artist/album pair, preventing identical titles by different artists from being collapsed. Advanced analytics prefer MusicBrainz IDs (MBIDs) when present and fall back to case-folded names. They include monthly artist timelines, first-time discovery and 90-day rediscovery events, trailing 30/90-day rankings, inferred listening sessions (30-minute gap threshold), and monthly artist-concentration metrics. Rolling windows end at the newest archived scrobble. Session spans are timestamp-based estimates, not actual playback durations.

## Rebuild locally

```bash
python build_stats.py
python build_assistant_data.py
python build_advanced_analytics.py
```

The scheduled GitHub Actions workflow runs the importer and all analytics builders, validates the generated data, then commits updates. It requires the repository secret `LASTFM_API_KEY`.

## Important limitations

- Last.fm's recent-track archive does not supply actual listening duration. The duration estimate uses 3.5 minutes per scrobble and is labelled as an estimate.
- Genre, release dates, biographies, similar artists and other descriptive metadata are not inferred from scrobbles. They require a separate metadata-enrichment stage and may be incomplete or inconsistent.
- The canonical archive is preserved; assistant analytics are derived outputs and can be regenerated at any time.
