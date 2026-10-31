# Spotify Helper & Information Tracker (SHIT)

**Spotify Helper & Information Tracker (SHIT)** is the home for Spotify playlist intelligence, playlist curation and safety tooling, personal listening analytics, and the canonical Last.fm scrobble archive for **TrickySturluson**.

The project combines Spotify's live playlist and playback interfaces with Last.fm's long-term scrobble history. Spotify playlist operations are handled separately from the historical analytics archive, with read-only inspection and preview-first safeguards for changes.

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
| `assistant_data/music/` | Cached track metadata, durations, confidence/provenance, artist-sharded dictionaries, artist genre/mood/theme profiles, and independently sourced track-level tag profiles |
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

The daily workflow fills the Last.fm duration cache gradually (120 unique-track lookups per run by default); subsequent runs query only missing/unmatched entries. The **Enrich Music Metadata** workflow now runs automatically once a week (Monday 08:17 UTC) in small batches, in addition to remaining manually dispatchable with larger lookup limits. Scheduled runs use conservative limits (300 MusicBrainz duration lookups, 100 artist profiles, and 120 track profiles); manual runs retain their selectable larger limits. A concurrency group prevents overlapping enrichment runs from racing to commit generated data. It uses MusicBrainz as a secondary source for unresolved durations, builds artist genre/mood/theme profiles from Last.fm community tags, and independently enriches individual tracks with Last.fm and MusicBrainz tags. MusicBrainz requests are limited to roughly one per second. Artist profiles preserve the original community tags and separately expose conservative genre/mood/theme subsets; tags are community-sourced and should be treated as descriptive signals, not definitive classifications. To backfill the entire catalogue on demand, use **Actions → Backfill Music Durations → Run workflow**. It processes up to 12,000 unique tracks in one run, commits the resulting cache, and can be run again if Last.fm rate limits interrupt it. Successfully resolved tracks are cached, so reruns resume rather than repeat completed lookups. Unmatched records are retained and retried after 30 days. The backfill uses Last.fm's `track.getInfo` endpoint and waits between requests to reduce rate-limit pressure.

### Artist profiles for recommendations\n\n`assistant_data/music/artist_profiles.json` stores each artist's play count, source, check status, raw community tags and derived `genres`, `moods`, and `themes` lists. The raw tags are preserved because genre boundaries are fuzzy and community tagging can be inconsistent. The manual **Enrich Music Metadata** action fills profiles incrementally, prioritizing artists with the most scrobbles. These are artist-level signals and are never treated as track-level ground truth. The same workflow now builds `assistant_data/music/track_profiles.json` with Last.fm `track.getTopTags` and, when a recording MBID is already present, MusicBrainz recording tags and genres. Track tags retain source attribution and lookup status. MusicBrainz enrichment deliberately does not guess recording identity through fuzzy search; recordings without a trusted MBID remain Last.fm-only or unresolved. `build_music_analytics.py` exposes track-sourced `genres`, `moods`, and raw `track_tags` separately from `artist_genres`, `artist_moods`, and `artist_themes`. Track moods are mapped conservatively from track-sourced tags only; artist-level mood labels are not copied onto every track.\n\n## Measured Spotify playback time

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

## Playlist sorting and sequencing engine

spotify_playlist_sequencer.py is a preview-only playlist arrangement engine. **Smooth Flow** is the default: it optimizes the complete chain of song-to-song handoffs, then uses the requested energy journey as a soft structural guide. It does not divide the playlist into rigid energy bands. Genre and theme affinity are optional soft preferences; cross-genre transitions remain welcome when they flow naturally.

### Shape the listening journey

- **rising** (default): gradual build toward a configurable peak, then a cooldown.
- **falling**: start intense and ease toward a quieter finish.
- **wave**: create a broad rise-and-release arc.
- **steady**: favor a relatively consistent energy level.

The peak-position control defaults to **85%** of playlist length. It is a soft target, not a forced maximum: the actual peak depends on the available tracks and transition quality. The peak-shape setting (gradual, sharp, sustained) controls the character of the crest and cooldown.

Examples:

    python spotify_playlist_sequencer.py YOUR_PLAYLIST_ID
    python spotify_playlist_sequencer.py YOUR_PLAYLIST_ID --journey rising --peak-position 85 --peak-shape gradual
    python spotify_playlist_sequencer.py YOUR_PLAYLIST_ID --journey falling
    python spotify_playlist_sequencer.py YOUR_PLAYLIST_ID --journey wave
    python spotify_playlist_sequencer.py YOUR_PLAYLIST_ID --journey steady
    python spotify_playlist_sequencer.py YOUR_PLAYLIST_ID --genre-strength 0.4 --theme-strength 0.6

### Anchors, sections and alternatives

- --opener-uri URI and --closer-uri URI reserve the first and last positions.
- Repeat --pin-uri URI to keep tracks at their current positions.
- --sections sections.json accepts an ordered JSON object mapping section names to URI lists. Section affinity is soft; transitions across section boundaries are still optimized.
- --compare creates alternative 70%, 85%, and 95% peak previews (skipping the selected peak), each as a separate manager-compatible plan.
- --genre-strength and --theme-strength accept soft preference values from 0 to 1.

Example sections file:

    {
      "Opening": ["spotify:track:TRACK_A", "spotify:track:TRACK_B"],
      "Climax": ["spotify:track:TRACK_C"],
      "Cooldown": ["spotify:track:TRACK_D"]
    }

### Other sorting modes

- energy: sort by inferred energy, ascending or descending.
- atmosphere: cluster by inferred mood/vibe.
- style: cluster by genre.
- narrative: arrange broad emotional phases.
- discovery: surface lower-play-count artists before more familiar artists when play-count data exists.
- hybrid: backwards-compatible alias for Smooth Flow.

### Transition explanations and evidence limits

The preview reports each adjacent handoff as gentle, moderate, or a potential jump, with shared track moods, genres, themes, energy differences, artist repetition, and an evidence-confidence label. These are metadata heuristics, not acoustic measurements. Missing track evidence remains explicitly unknown; artist-level tags are not presented as track-level facts.

The current playlist manager does not fetch Spotify audio features. Spotify restricted Audio Features and Audio Analysis endpoints for new Web API use cases and development-mode apps without a pending extension request; existing extended-mode apps that relied on them were grandfathered. The sequencer can consume such features if a supported source supplies them, but current live-playlist scoring primarily uses cached Last.fm/MusicBrainz community metadata. It does not know musical key, waveform, timbre, or reliable BPM unless supplied by a supported source. See Spotify's API changes: https://developer.spotify.com/blog/2024-11-27-changes-to-the-web-api.

The command writes playlist-sequence-plan.json by default. It never modifies Spotify directly. Review the plan, then pass it to the existing locked-by-default manager:

    python spotify_playlist_manager.py apply playlist-sequence-plan.json

The manager produces its normal preview, checks playlist lock/ownership and snapshot state, saves a pre-change backup, and requires typing APPLY before making changes. The sequencer refuses to create a partial plan if playlist items are unavailable or lack track URIs.



## Project feature map

| Area | Important features and subfeatures |
|---|---|
| Last.fm archive | Incremental scrobble imports, chronological canonical history, MBID retention, duplicate-safe updates |
| Historical analytics | Artist/album/track rankings, daily/monthly/yearly trends, weekday and UTC-hour patterns, discovery/rediscovery, rolling rankings, inferred sessions, diversity and concentration |
| Music metadata | Track durations, MusicBrainz fallback, artist community tags, genre/mood/theme profiles, independent track tags, provenance, identity checks, retry cooldowns and coverage reports |
| Listening-time analytics | Scrobble-based estimates, known-duration equivalents, theoretical minimum qualifying time, prospective measured Spotify playback, daily/monthly playback aggregates |
| Recommendations | Artist/track feature datasets, familiarity and recency, duration trends, source-aware metadata, versioned scoring |
| Playlist intelligence | Playlist identity profiles, genre/mood/theme summaries, metadata coverage, duplicate/missing-item checks, artist concentration, removal/whitelist feedback, read-only health reports |
| Daily curation | Tricky Daily candidate ranking, favorites/rediscovery/deep cuts, recency filters, artist caps, exact Spotify matching, preview and confirmation |
| Discovery curation | Similar-artist consensus, Spotify catalogue search, familiarity penalties, Liked Songs awareness, confidence tiers and reasons |
| Playlist sequencing | Smooth Flow global transition optimization, configurable energy journey and peak position/shape, section affinity, pinned/opening/closing tracks, A/B peak previews, transition explanations and confidence |
| Playlist management | Inspect/create, lock/unlock, add/remove/replace/reorder, ownership and snapshot checks, backups, undo and audit history |
| Cloud control | Owner-verified GitHub issue commands, preview-first confirmations, persistent lock state, recovery artifacts and health commands |
| Project integrity | Unit tests, full-module compilation, generated-data manifest checks, cross-dataset consistency audit and scheduled workflows |

Main entry points include update_lastfm.py, build_stats.py, build_assistant_data.py, build_advanced_analytics.py, build_music_metadata.py, build_track_profiles.py, build_music_analytics.py, spotify_playback_tracker.py, playlist_intelligence.py, spotify_daily_playlist.py, spotify_discovery.py, spotify_playlist_sequencer.py, spotify_playlist_manager.py, spotify_playlist_cloud.py, and audit_project.py.

## Important limitations

- Last.fm's recent-track archive does not supply actual listening duration. Duration-based estimates exclude scrobbles whose track duration is unknown; the metadata backfill action can improve coverage. Last.fm scrobble thresholds provide a theoretical minimum only, not exact played time.
- Genre, release dates, biographies, similar artists and other descriptive metadata are not inferred from scrobbles. They require a separate metadata-enrichment stage and may be incomplete or inconsistent. Track-level community tags are crowd-sourced descriptors, not objective audio analysis; the source is retained and artist-level tags are kept separate.
- The canonical archive is preserved; assistant analytics are derived outputs and can be regenerated at any time.


## Spotify playlist manager

\`spotify_playlist_manager.py\` is a separate local tool for inspecting and managing your Spotify playlists. It does not feed Spotify playlist content into \`assistant_data/\` or the Last.fm analytics pipeline.

### Setup

1. Use the same Spotify Developer app and Client ID as the playback tracker.
2. Ensure the app's Redirect URI includes \`http://127.0.0.1:8888/callback\`.
3. Stop \`spotify_playback_tracker.py\` before first playlist-manager authorization if it is using port 8888.
4. Set \`SPOTIFY_CLIENT_ID\` as shown in the playback tracker setup.
5. Run \`python spotify_playlist_manager.py list\` and approve the additional playlist permissions in Spotify.

The manager now also requests \`user-library-read\` so the discovery curator can check Liked Songs. If you authorized the manager before this permission was added, reauthorize it once:
- Stop any other local tool using port 8888.
- Delete the existing \`.spotify_playlist_token.json\` so the manager starts a fresh authorization.
- Run \`python spotify_playlist_manager.py list\` again and approve the expanded permissions.
- Run \`python spotify_playlist_manager.py export-refresh-token\` and replace the repository's GitHub Actions secret \`SPOTIFY_REFRESH_TOKEN\` with the newly printed token. Do not commit or share the token.

The manager uses its own \`.spotify_playlist_token.json\`; it does not overwrite the playback tracker's token. It uses Authorization Code with PKCE and requires no client secret.

### Commands

\`\`\`bash
python spotify_playlist_manager.py list
python spotify_playlist_manager.py export-refresh-token
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


**Spotify content boundary:** complete playlist tracklists and snapshots stay outside `assistant_data/` and are never included in control issue comments. For user-requested management, the control panel surfaces only minimal operational metadata (playlist name, ID, item count, lock state) and the explicit track URIs in a proposed plan. Full pre-change snapshots are stored as GitHub Actions artifacts for recovery, not in issue comments or assistant-facing analytics.

The manager is intentionally local and uses the Spotify Web API. Spotify's current playlist endpoints use \`/items\` (not the older \`/tracks\` routes). Spotify's development-mode requirements and API access limits may apply to the connected Developer app.


### GitHub Actions control panel

After this branch is merged into `main`, add these repository Actions settings:

- Variable: `SPOTIFY_CLIENT_ID` (the Spotify app Client ID)
- Secret: `SPOTIFY_REFRESH_TOKEN` (the playlist-manager refresh token; never commit or paste it into an issue)

Spotify refresh tokens expire six months after authorization; refreshing an access token does not extend that deadline. If the cloud workflow reports an expired or invalid refresh token, reauthorize the playlist manager locally and replace this GitHub Actions secret with the newly issued refresh token. Spotify may also return a replacement refresh token during a refresh; the workflow warns if that happens because a temporary runner cannot update repository secrets. If warned, reauthorize locally and replace the secret before the next command.

Create one open issue titled exactly **SHIT — Playlist Control**. Its body is a JSON command. Editing the body runs the control workflow; results are posted as issue comments.

Status:
```json
{"command":"status"}
```

Lock/unlock one owned playlist or lock all owned playlists:
```json
{"command":"lock","playlist_id":"PLAYLIST_ID"}
{"command":"unlock","playlist_id":"PLAYLIST_ID"}
{"command":"lock_all"}
```

To change a playlist, unlock it first, then submit a preview command. The preview lists the exact requested Spotify track URIs and does not modify the playlist:
```json
{
  "command": "preview",
  "playlist_id": "PLAYLIST_ID",
  "operations": [
    {"action": "add", "uris": ["spotify:track:TRACK_ID"]}
  ]
}
```

The preview returns a one-time confirmation code. Submit only that code to execute the exact pending plan:
```json
{"command":"confirm","confirmation":"CODE_FROM_PREVIEW"}
```

Confirmation is rejected if the playlist was locked or its snapshot changed after preview. Only the repository owner can issue commands, and only playlists owned by the connected Spotify account can be edited. New and unknown playlists remain locked by default. A lock or lock-all command cancels a pending preview. Pre-change snapshots are uploaded as GitHub Actions artifacts (30-day retention); the lock state and audit log are stored in the repository under `.github/`.

The control issue reports playlist names, IDs, item counts and lock states. Preview comments include only the URIs explicitly supplied in the proposed plan; complete playlist tracklists are not sent to the control issue. Recovery snapshots remain separate Actions artifacts and are not included in assistant-facing analytics.


Undo the most recent completed change with:
```json
{"command":"undo"}
```

Undo is a preview-first restore from the exact pre-change snapshot. It requires the playlist to be unlocked and its ordered item URIs to match the post-change state recorded by the manager (legacy records fall back to the Spotify snapshot ID). Confirm with the one-time code returned by the preview. The restore replaces the playlist contents in their original order, preserves duplicate track/episode URIs, and saves the current contents as a new recovery artifact first (so undoing an undo can restore the prior state). Recovery artifacts are retained for 30 days; undo is unavailable after the artifact expires or is deleted.

### Playlist intelligence and health reports

Mood inference uses a broader, explicitly curated affect vocabulary (including dreamlike, eerie, nocturnal, introspective, chaotic, groovy, theatrical, cinematic, cathartic, and wistful). Sound/style signals are kept separate from moods: playlist profiles expose genre tags, recurring sound families, and artist-level themes independently. These are conservative artist-level Last.fm community-tag signals, not track-level audio analysis; genre labels are never treated as moods simply because their names sound evocative.


`playlist_intelligence.py` builds a read-only identity profile from a playlist's current membership and the cached Last.fm artist metadata. It summarizes represented artists and their genre, mood, and theme tags, reports metadata coverage, and keeps removal/whitelist counts scoped to that playlist. Profiles are calculated from the live snapshot when requested; they do not overwrite the canonical listening archive or playlist contents.

Recommendation weights and confidence thresholds live in the versioned `assistant_data/recommendations/playlist_scoring.json` file. The discovery curator reads this configuration rather than scattering scoring constants through the code. Each recommendation now includes a confidence tier (strong fit, promising, or wildcard) and concise reasons describing its supporting similarity seeds, playlist-local positive/negative feedback, familiarity, and Liked Songs status. Confidence is a diagnostic heuristic, not a guarantee of quality.

Use the cloud control issue for a read-only playlist health report:

```json
{"command":"health","playlist_id":"YOUR_PLAYLIST_ID"}
```

The report checks exact duplicate track URIs, surplus copies, missing URIs, non-track items, primary-artist concentration, metadata coverage, and playlist-specific removal/whitelist feedback. It never modifies Spotify. The Tricky Daily preview includes confidence counts, a playlist identity summary, and a short explanation for each recommendation.

The existing playlist manager audit log already records previews, confirmations, completed edits, cleanup, and undo events. Removal history supplies negative feedback; current membership supplies positive/whitelist evidence. A/B scoring experiments and automated weight calibration are intentionally not enabled yet: the current weights are versioned and observable first, so we can establish a reliable baseline before letting user decisions tune them automatically.

### Tricky Daily curator

The cloud control panel supports a preview-first daily recommendation command for the playlist named exactly Tricky Daily:

```json
{"command":"daily_preview","playlist_id":"YOUR_TRICKY_DAILY_PLAYLIST_ID"}
```

The curator ranks tracks already present in assistant_data/recommendations/track_features.json. It favors tracks not scrobbled recently, gives familiarity a modest anchor role, and caps artist concentration to encourage variety. It resolves Spotify URIs only when both track title and primary artist match exactly; ambiguous or unavailable matches are skipped. Tracks already in the playlist are excluded. At least 20 exact matches (or the requested target size if lower) are required before a preview is created.

The preview lists the proposed tracks and returns a one-time confirmation code. It does not modify Spotify. Confirming uses the existing backup-first replace operation and normal lock, ownership, state-revalidation, and undo protections. Tricky Daily must be explicitly unlocked before previewing or confirming. The initial curator uses previously scrobbled tracks only; external discovery is intentionally a later enhancement. The score is a transparent heuristic, not a claim that every scrobble represents a positive preference.


## Spotify reference library and playlist safety

The canonical Spotify reference library lives under `assistant_data/spotify/`:

- `playlists.json` catalogs every playlist returned by the authorized Spotify account, including owner, visibility, collaboration state, snapshot ID and item count.
- `playlists/{playlist_id}.json` stores each playlist's ordered item records, including Spotify IDs/URIs, artists, album, duration, availability hints and added-at metadata.
- `history/{playlist_id}/` stores dated snapshots when playlist contents or Spotify's snapshot ID change.
- `reference_index.json` maps track URIs and artist names back to playlists.
- `managed_playlists.json` is the deny-by-default mutation registry. Only playlists created by SHIT and explicit user-approved exceptions may be edited. Account ownership, an unlocked state, or an `APPLY` confirmation is not permission. Tricky Daily (`4yUVHSMQySfWeEowfIMcx7`) is an explicit approved exception; unknown and personal playlists remain read-only.

Refresh the reference library locally with:

```bash
python spotify_reference_library.py sync
```

This is a read-only Spotify operation. It does not modify playlists. A scheduled GitHub Actions workflow refreshes the catalog every Sunday and can also be run manually from **Actions → SHIT — Spotify Reference Library**. The import is limited to playlists the authorized Spotify API account exposes; it cannot guarantee visibility into every public playlist on Spotify. Playlists whose item contents are restricted by Spotify are still cataloged, with the visibility limitation recorded.

Browse and search the saved dataset locally:

```bash
python spotify_reference_library.py list
python spotify_reference_library.py lookup "artist or track name"
```

### Tricky Daily retention feedback

A scheduled read-only observation workflow refreshes Liked Songs status and Last.fm post-add counts daily, even when Tricky Daily itself is not edited. It can be run manually from **Actions → SHIT Daily Feedback Observation**. The GitHub runner does not have the local playback segment file, so measured Spotify playback remains unknown there unless a separate local observation is performed; missing tracker data is never interpreted as zero listening.


`spotify_daily_feedback.py` records when tracks enter and leave Tricky Daily, checks whether newly added tracks are in Liked Songs, and records measured post-add playback intervals from `playback_data/segments.jsonl`. The feedback record distinguishes:
- Whether a track was already in Liked Songs at preview time, and whether it was saved afterward.
- Distinct measured Spotify listening sessions and playback milliseconds after the first Daily addition.
- Post-add Last.fm scrobbles from the canonical timestamped archive, kept separate from measured Spotify playback.
- Playlist removals and repeat additions.
- Unknown coverage from a confirmed zero-play observation.

A day without listening is neutral. Missing tracker data is unknown, not zero. Spotify save checks or playback tracking can fail independently without interrupting an already-confirmed playlist edit. Last.fm scrobbles remain a separate secondary signal and are not mislabeled as measured Spotify playback.

The reference library and feedback files are personal listening data. Keep the repository private and never commit OAuth tokens or local playback credentials.
