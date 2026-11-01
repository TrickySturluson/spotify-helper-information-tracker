# Album metadata and lookup confidence

## Album metadata

The album enrichment stage uses one Last.fm `album.getInfo` request per unique
artist/album candidate. It retains a verified ordered tracklist, track positions,
durations and recording MBIDs when supplied, album artwork and provider links,
community tags, and a short attributed wiki summary. Full wiki content is not
copied. The exact returned artist and album must match the requested identity.

The Library stores album information under the album record's `evidence` field.
A release tracklist describes a release, not every version of a recording.
A song is not assigned to a release solely because its title appears in a
tracklist; release MBID and track position relationships must be verified. When
an existing verified song record is cross-linked, the tracklist entry stores
`linked_song_id` and `linked_recording_mbid` separately from the provider's
`mbid` field. That preserves provenance when the provider tracklist did not
supply a recording MBID. Discogs tracklist validation remains a separate release
evidence source.

## Lookup hierarchy

1. Exact Spotify track ID.
2. Verified MusicBrainz recording MBID.
3. Exact ISRC.
4. Stable source-profile ID (useful for retrieval, not proof of a canonical recording).
5. Verified release MBID + disc number + track number.
6. Exact artist/title only when unique; exact album can disambiguate a collision.
7. Fuzzy candidates are review-only and are never silently accepted.

The lookup audit reports status, matched identifier, candidate IDs, reason, and
categorical identity confidence. An unresolved duplicate artist/title query
returns all candidates instead of selecting the first.

## Confidence model

Identity confidence and metadata confidence are separate dimensions.

- **High identity confidence:** a stable exact track identifier, ISRC, or
  verified release-position relationship.
- **Medium identity confidence:** exact artist/title with a unique candidate,
  or exact artist/title/album disambiguation.
- **Low identity confidence:** source-profile ID without canonical recording
  corroboration, or fallback release/name context.
- **Unknown:** no match or an unresolved ambiguity.

Metadata confidence is evaluated separately for each field. Evidence is
grouped by source family, not raw result count. Repeated values from one family
do not count as independent corroboration. Independent sources that agree may
raise confidence; disagreement is retained and lowers confidence. A source is
marked authoritative only when it is authoritative for that particular field.

These labels are explainable categories, not probabilities. Acoustic confidence
remains independent: album descriptions, tags, genres, release styles, and
artist biographies cannot raise acoustic confidence.

## Maintenance and audit

Use `MusicLibrary.lookup_song()` to inspect why a song resolved. The legacy
`get_song()` API remains available and includes its lookup explanation under
`lookup_audit`. Use `MusicLibrary.audit()` to check index aliases and record
relationships. Never replace ambiguous candidates with an arbitrary match.


## Album affinity and sound similarity

The playlist sequencer reports **album affinity** separately from **sound similarity**. Album affinity is based on an exact artist/title match in a verified album tracklist; it is not an acoustic measurement. A linked recording cross-reference raises membership identity confidence, while a tracklist-only match remains contextual. An exact verified tracklist match can therefore have 100 album affinity without claiming 100% recording-identity certainty.

Sound similarity compares track-level descriptive genre/style labels with album-level descriptive tags. It is directional coverage of the track's known labels, not an energy score or an acoustic fingerprint. Missing labels remain unknown rather than being treated as disagreement. Album-wide tags provide context but are never relabelled as track-specific mood evidence.

Genre-family scoring checks specific atmospheric styles (including shoegaze and dream pop) before broad umbrella genres such as rock and indie rock, so broad tags cannot mask a more informative style label.
