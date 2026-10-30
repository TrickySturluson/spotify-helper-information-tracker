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
| `assistant_data/music/` | Cached track metadata, durations, confidence/provenance, artist-sharded dictionaries and artist genre/mood/theme profiles |
| `assistant_data/recommendations/` | Recommendation-ready artist/track features plus monthly and yearly duration trends |

All generated timestamps and calendar buckets use UTC. Track identity is the artist/track pair; album identity is the artist/album pair, preventing identical titles by different artists from being collapsed. Advanced analytics prefer MusicBrainz IDs (MBIDs) when present and fall back to case-folded names. They include monthly artist timelines, first-time discovery and 90-day rediscovery events, trailing 30/90-day rankings, inferred listening sessions (30-minute gap threshold), and monthly artist-concentration metrics. Rolling windows end at the newest archived scrobble. Session spans are timestamp-based estimates, not actual playback durations.

## Rebuild locally

```bash
python build_stats.py
python build_assistant_data.py
python build_advanced_analytics.py
python build_music_analytics.py
LASTFM_API_KEY=your-key python build_music_metadata.py
python build_playback_analytics.py
```

The scheduled GitHub Actions workflow imports new scrobbles, incrementally enriches missing track metadata, runs the analytics builders, validates generated data, and commits updates. It requires the repository secret `LASTFM_API_KEY`. Daily metadata enrichment is capped at 120 lookups per run; the separate manual backfill workflow can process up to 12,000 tracks in one run.


## Cached music metadata and duration estimates

`build_music_metadata.py` builds `assistant_data/music/` from the canonical scrobble archive. It uses Last.fm `track.getInfo` to retrieve track duration in milliseconds, preferring a track MBID when present and otherwise querying artist + title without autocorrection. It verifies returned artist/title labels before accepting a duration. Exact MBID matches are marked high confidence; exact artist/title matches without an ID are medium confidence. Missing or ambiguous results remain unknown and are retried after 30 days.

The catalogue is split into 32 fixed artist-hash shards to avoid thousands of tiny files. `indexes/artists.json` maps artist IDs to shard files; `indexes/tracks.json` maps track IDs to their artist/shard. Each artist entry contains its albums and track records. `overview.json` reports metadata coverage, known-duration full-track-equivalent hours, and a known-duration minimum qualifying-time estimate. Last.fm's documented scrobble rule requires at least half the track or four minutes, whichever comes first (for tracks longer than 30 seconds); the scrobble may be submitted as soon as that threshold is met. The minimum is a theoretical lower bound for the matched subset, not proof of actual playback. Full-track-equivalent assumes every scrobble played the whole track. Unknown-duration scrobbles are excluded from both duration totals. The original scrobble archive is never modified.

The daily workflow fills the Last.fm duration cache gradually (120 unique-track lookups per run by default); subsequent runs query only missing/unmatched entries. The manual **Enrich Music Metadata** workflow uses MusicBrainz as a secondary source for unresolved durations and builds artist genre/mood/theme profiles from Last.fm community tags. MusicBrainz requests are limited to roughly one per second. Artist profiles preserve the original community tags and separately expose conservative genre/mood/theme subsets; tags are community-sourced and should be treated as descriptive signals, not definitive classifications. To backfill the entire catalogue on demand, use **Actions → Backfill Music Durations → Run workflow**. It processes up to 12,000 unique tracks in one run, commits the resulting cache, and can be run again if Last.fm rate limits interrupt it. Successfully resolved tracks are cached, so reruns resume rather than repeat completed lookups. Unmatched records are retained and retried after 30 days. The backfill uses Last.fm's `track.getInfo` endpoint and waits between requests to reduce rate-limit pressure.

### Artist profiles for recommendations\n\n`assistant_data/music/artist_profiles.json` stores each artist's play count, source, check status, raw community tags and derived `genres`, `moods`, and `themes` lists. The raw tags are preserved because genre boundaries are fuzzy and community tagging can be inconsistent. The manual **Enrich Music Metadata** action fills profiles incrementally, prioritizing artists with the most scrobbles. These are artist-level signals; track-level mood/theme labels can be added later where there is reliable evidence.\n\n## Measured Spotify playback time

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

- Last.fm's recent-track archive does not supply actual listening duration. Duration-based estimates exclude scrobbles whose track duration is unknown; the metadata backfill action can improve coverage. Last.fm scrobble thresholds provide a theoretical minimum only, not exact played time.
- Genre, release dates, biographies, similar artists and other descriptive metadata are not inferred from scrobbles. They require a separate metadata-enrichment stage and may be incomplete or inconsistent.
- The canonical archive is preserved; assistant analytics are derived outputs and can be regenerated at any time.


## Spotify playlist manager

\`spotify_playlist_manager.py\` is a separate local tool for inspecting and managing your Spotify playlists. It does not feed Spotify playlist content into \`assistant_data/\` or the Last.fm analytics pipeline.

### Setup

1. Use the same Spotify Developer app and Client ID as the playback tracker.
2. Ensure the app's Redirect URI includes \`http://127.0.0.1:8888/callback\`.
3. Stop \`spotify_playback_tracker.py\` before first playlist-manager authorization if it is using port 8888.
4. Set \`SPOTIFY_CLIENT_ID\` as shown in the playback tracker setup.
5. Run \`python spotify_playlist_manager.py list\` and approve the additional playlist permissions in Spotify.

The manager uses its own \`.spotify_playlist_token.json\`; it does not overwrite the playback tracker's token. It uses Authorization Code with PKCE and requires no client secret.

### Commands

\`\`\`bash
python spotify_playlist_manager.py list
python spotify_playlist_manager.py inspect YOUR_PLAYLIST_ID
python spotify_playlist_manager.py unlock YOUR_PLAYLIST_ID
python spotify_playlist_manager.py lock YOUR_PLAYLIST_ID
python spotify_playlist_manager.py create "New playlist name" --description "Description"
python spotify_playlist_manager.py apply change-plan.json
\`\`\`

All playlists are **LOCKED by default**, including newly created playlists. Only explicitly unlocked playlists can be modified. A change plan is previewed before any write, then requires typing \`APPLY\`; plans containing a replacement require typing \`REPLACE\`. The manager checks the lock again immediately before each operation and stops if it has become locked. It also checks playlist ownership and detects changes made after the preview.

### Change-plan format

Track URIs must be Spotify track URIs (for example, \`spotify:track:...\`). Supported operations are \`add\`, \`remove\`, \`replace\`, and \`reorder\`.

\`\`\`json
{
  "playlist_id": "YOUR_PLAYLIST_ID",
  "operations": [
    {
      "action": "add",
      "uris": ["spotify:track:TRACK_ID"]
    },
    {
      "action": "remove",
      "uris": ["spotify:track:ANOTHER_TRACK_ID"]
    }
  ]
}
\`\`\`

For a reorder operation, provide zero-based \`range_start\`, \`insert_before\`, and \`range_length\`. A replace operation replaces the full contents and requires the separate \`REPLACE\` confirmation.

Before applying a plan, the manager saves a complete pre-change playlist snapshot under \`playlist_backups/\`. It records lock changes, cancelled plans, and completed changes in \`playlist_manager_audit.jsonl\`. These files and the local OAuth token are private runtime data and should not be committed. Snapshots are recovery references; they are not automatically restored by the tool.

The manager is intentionally local and uses the Spotify Web API. Spotify's current playlist endpoints use \`/items\` (not the older \`/tracks\` routes). Spotify's development-mode requirements and API access limits may apply to the connected Developer app.
