# Spotify playlist reference guide

**Project:** Spotify Helper & Information Tracker (SHIT)

This guide explains how SHIT identifies and retrieves playlist references. It is deliberately separate from playlist write permissions.

## Canonical data

- `playlists.json` is the generated playlist catalog: names, IDs, owner, snapshot ID, item counts, accessibility, capture timestamps and per-playlist record paths.
- `playlists/<playlist_id>.json` is the per-playlist snapshot: Spotify metadata, ordered items, track/artist/album identifiers, duration and playability fields where available.
- `reference_index.json` maps track URIs to playlists and supports reverse lookup.
- `playlist_roles.json` is the curated semantic registry: canonical Spotify links, project role, human notes and the path to each snapshot.
- `managed_playlists.json` is the only source of playlist mutation permissions. Role registration does not authorize edits.

## Registered reference sets

### Sorter calibration targets

These five user-selected playlists are the strong, specific theme references for sorter evaluation. Their tracklists, not their titles alone, are the evidence for what belongs.

| Playlist | Spotify | Snapshot |
|---|---|---|
| To 11 | [Open playlist](https://open.spotify.com/playlist/5meDjtqrqOe5oHpvZGWRMz) | `playlists/5meDjtqrqOe5oHpvZGWRMz.json` |
| Somber Party | [Open playlist](https://open.spotify.com/playlist/7L2rSp4SuohBEyNxEtAurx) | `playlists/7L2rSp4SuohBEyNxEtAurx.json` |
| . . . | [Open playlist](https://open.spotify.com/playlist/4HzqY9iy04M1EVSF5kcD64) | `playlists/4HzqY9iy04M1EVSF5kcD64.json` |
| =^= | [Open playlist](https://open.spotify.com/playlist/0O9ojSstxwa5vQy2V7pO2x) | `playlists/0O9ojSstxwa5vQy2V7pO2x.json` |
| Smooth | [Open playlist](https://open.spotify.com/playlist/2ICCklgbF6cg0q5p4xAHKi) | `playlists/2ICCklgbF6cg0q5p4xAHKi.json` |

Use these as separate classification targets. Do not collapse them into one general taste profile. Build profiles from current track-level evidence and exclude each candidate (or the entire held-out evaluation batch) from its target profile to prevent membership leakage. The 25-track SHITting Grounds human sliders are exploratory sanity-check observations only: they are not production labels, ground truth, sorting instructions, or training/calibration targets. Keep them in a separate immutable reference file and never feed them into production profile construction or scoring. See [the production playlist-fit model contract](../../project/goals/playlist-intelligence/PLAYLIST_FIT_MODEL.md).

### Sorter audition destination

[SHITting Grounds](https://open.spotify.com/playlist/4aLdllLgRPh5vKOznkC97D) is the user's audition playlist for candidate tracks. The latest reference catalog now includes it with a 25-item, accessible snapshot captured at `2026-11-06T01:47:59.822814+00:00` in `assistant_data/spotify/playlists/4aLdllLgRPh5vKOznkC97D.json`. **The curated role registry is stale:** its `playlist_roles.json` entry still has `snapshot_record: null`, `snapshot_accessible: null`, and `sync_status: not_yet_in_reference_snapshot`. Reconcile that registry entry after the documentation-only pause; do not treat the old registry status as evidence that the snapshot is missing. Its registration and snapshot do not imply that any tracks have been added.

### Broad taste references — not calibration targets

- [All Time](https://open.spotify.com/playlist/6ZsqAs5OnRMVudhfB2QzTx): diverse, multi-genre, curated “cream of the crop” sequence. It fits across styles and must not be treated as a narrow theme.
- [Hell](https://open.spotify.com/playlist/3XQz9AyZP6ADcr9i8iBaVx): broad collection of music the user has listened to and enjoyed since its last update. It is useful as a broad taste/history reference, not a specific theme.

### Existing managed playlists

- [Booze or Boos!](https://open.spotify.com/playlist/4diIlnF8BlgoJrwUfejf49): Halloween party playlist.
- [Tricky Daily](https://open.spotify.com/playlist/4yUVHSMQySfWeEowfIMcx7): daily shuffle playlist.

## Retrieval rules

1. Resolve a playlist by exact Spotify playlist ID first; names are not unique.
2. Read `playlist_roles.json` for its purpose and canonical link.
3. Read `playlists.json` for the latest catalog status and record path.
4. Read the per-playlist record for ordered tracks and metadata. Check `items_accessible`, reported count, fetched count and snapshot ID before relying on completeness.
5. Use `reference_index.json` for track-to-playlist reverse lookup; validate against the current playlist snapshot when freshness matters.
6. An inaccessible or absent playlist is unknown/unretrieved, never an empty playlist.
7. Keep user-provided slider ratings separate from inferred metadata and from scrobble/playback counts.

## Updating

The Spotify Reference Library sync should refresh the catalog and per-playlist snapshots. When a new playlist becomes a stable project reference, add its ID, exact name, Spotify URL, role, concise notes and snapshot path to `playlist_roles.json`. Do not hand-edit generated catalog/snapshot/index files; rebuild them through the existing sync workflow.

Playlist roles are descriptive metadata only. All write authorization remains deny-by-default and is controlled by `managed_playlists.json`.
