# Library Identity Review Set

This is a small, inspectable set of real canonical records for confidence and duplicate-entity review. It is **not** an assertion that every candidate is already resolved correctly. Entries marked pending must not be auto-merged. Use this set to validate lookup explanations, identity confidence, relationships, and ambiguity handling before sorter integration.

## 1. Verified recording-ID example

- Song: **Messer Chups — Night Stripper**
- Canonical ID: `mbid:81e13352-0257-4867-8e6e-3718be846dc1`
- File: `assistant_data/music/library/songs/mb/mbid-81e13352-0257-4867-8e6e-3718be846dc1/song.json`
- Stored identity quality: `verified_recording`; confidence: high; recording MBID present.
- Expected lookup behavior: exact recording-MBID lookup should resolve this record with high confidence and retain its album/artist relations.

## 2. Verified Spotify-ID example with market-scoped playability

- Song: **Candy Claws — Into the Deep Time (One Sun)**
- Canonical ID: `spotify:0lw2mlzncwftftvdojdysg`
- Spotify track ID: `0lw2mLzNcwftfTvDojdySG`
- ISRC: `USME31203114`
- File: `assistant_data/music/library/songs/sp/spotify-0lw2mlzncwftftvdojdysg/song.json`
- Stored identity quality: `spotify_track`; confidence: high.
- Playability evidence: market `FROM_TOKEN`, status `playable`, checked `2026-11-01T04:37:06.743654+00:00`; snapshot evidence, not a permanent live guarantee.
- Expected lookup behavior: exact Spotify ID resolves this record; playability is shown with market and timestamp, never as an unqualified permanent property.

## 3. Source-track-only low-confidence example

- Song: **S-Connection — Summerlove (feat. Anabelle) - Scorccio Edit**
- Canonical ID: `source:ab9751cab0ea1fee`
- Source track ID: `track:ab9751cab0ea1fee`
- File: `assistant_data/music/library/songs/so/source-ab9751cab0ea1fee/song.json`
- Stored identity quality: `source_track_id`; confidence: low; no recording MBID, ISRC, or Spotify ID.
- Listening context: 47 Last.fm scrobbles.
- Expected lookup behavior: exact source ID resolves the record with low confidence; title/artist lookup must not silently promote it to a verified recording.

## 4. Duplicate artist candidate — Candy Claws

**Pending manual identity review**

- Name-fallback record: `name:df4e3388540b77ea392a`, file `assistant_data/music/library/artists/na/name-df4e3388540b77ea392a/artist.json`. It contains the display name Candy Claws but no MBID or supporting evidence.
- Verified artist record: `mbid:da5eaa3b-397e-4af8-9a12-5c4ec93e8b48`, file `assistant_data/music/library/artists/mb/mbid-da5eaa3b-397e-4af8-9a12-5c4ec93e8b48/artist.json`. It has verified MBID identity and Last.fm artist evidence.
- Both normalize to the same artist name. This is a duplicate candidate, not permission to merge on name alone.
- Next evidence to inspect: map Spotify artist ID `34Xay0uKsALHCrn5LkrYeh` to the verified MBID using a trustworthy source or existing cache; check for other same-name artists/aliases before any merge.

## 5. Duplicate album candidate — Candy Claws, Ceres & Calypso in the Deep Time

**Pending manual identity review**

- Spotify-snapshot fallback album: `album:985073c24c6efb9b926d`, file `assistant_data/music/library/albums/al/album-985073c24c6efb9b926d/album.json`. It has no release ID/evidence and is linked to the name-fallback artist.
- Enriched canonical album: `album:01632cb9b68c6acda89d`, file `assistant_data/music/library/albums/al/album-01632cb9b68c6acda89d/album.json`. It has an identity-verified album record and Spotify album ID `5KkGAZrad4N4rc5FriwgzU`.
- Spotify song record `spotify:0lw2mlzncwftftvdojdysg` carries the same Spotify album ID in `evidence.track_metadata.spotify_album_id`, but currently points to fallback album `album:985073c24c6efb9b926d`.
- Shared exact Spotify album ID is strong evidence that the fallback album belongs to the enriched album record. This needs an explicit duplicate/cross-link audit and relationship migration plan; do not delete or merge records ad hoc.
- This example demonstrates why structural health alone is insufficient: both records can be internally consistent while representing a duplicated entity.

## Acceptance rules for this review set

- Exact recording MBID / Spotify track ID / ISRC matches must be explainable and high confidence only when the identifier is genuinely present and verified.
- Source-track-only identities remain low confidence unless independent evidence justifies promotion.
- Name-only duplicates remain candidates, not automatic merges.
- Album release identity is separate from artist identity and song identity. A shared Spotify album ID is strong release evidence; same title alone is not.
- Every proposed merge must preserve all song references, source IDs, playability observations, listening context, confidence, and provenance; preview and backup before any mutation.
- Record a decision and evidence for each pending case before enabling sorter reliance on the affected relationships.
