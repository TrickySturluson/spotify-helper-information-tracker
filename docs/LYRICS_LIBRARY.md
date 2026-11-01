# Lyrics analysis and local song lookup

SHIT's lyrics subsystem is an opt-in research aid for song discovery and recommendation quality. Run it locally:

```bash
python compat/lyrics_library.py analyze "Song Title" "Artist Name" --album "Album" --duration 210
python compat/lyrics_library.py lookup --title "Song Title"
python compat/lyrics_library.py lookup --phrase "a remembered phrase of five or more words"
python compat/lyrics_library.py recent
python compat/lyrics_library.py export
```

The default database is `data/lyrics/library.sqlite3`. It is local runtime data and should not be committed. Each successful `analyze` command also refreshes `assistant_data/recommendations/lyric_features.json`, a compact export of derived theme metadata that can be committed for use by cloud workflows. The export deliberately excludes full lyric text and phrase fingerprints. The database contains track identity, provider links/check status, theme evidence, analysis confidence, and one-way five-word phrase fingerprints. It deliberately does **not** retain full copyrighted lyrics. Phrase fingerprints support approximate local phrase-to-song matching without storing a copy of the lyrics; exact short fragments under five words are not indexed.

## Providers and fallback behavior

The lookup checks these sources independently, so one unavailable provider does not prevent the others from being tried:

1. **LRCLIB** — open API, exact title/artist match, with optional album and duration to reduce mismatches. The client identifies itself and waits between requests; it respects rate-limit responses.
2. **Musixmatch** — official API, enabled when `MUSIXMATCH_API_KEY` is set. Use an API key issued for an account whose plan and terms permit the intended use. The API may return only a licensed excerpt/snippet.
3. **Lyrics.ovh** — open lyrics endpoint, used as a third text-lyrics fallback. Coverage and availability vary.
4. **Genius** — official API, enabled when `GENIUS_ACCESS_TOKEN` is set. Used for song/artist identity and a canonical song-page URL only. Genius's public developer API does not provide full lyrics; SHIT does not scrape Genius pages or bypass its restrictions.

Set optional credentials in the local environment, never in source code or committed config:

```bash
export MUSIXMATCH_API_KEY="..."
export GENIUS_ACCESS_TOKEN="..."
```

LRCLIB and Lyrics.ovh are queried even when no API credentials are configured. Missing credentials and provider failures are reported separately from a genuine no-match. Provider availability and API terms can change; each provider remains independently optional.

## What is analyzed

The versioned v3 analyzer extracts reusable song-level themes across multiple areas:

- **Horror:** slasher/murder, blood/gore, monsters, vampires, zombies/undead, ghosts, occult, Halloween, death and dark fantasy.
- **Relationships:** romance, love, heartbreak and loss.
- **Social energy:** nightlife, clubbing, parties, celebration and friendship.
- **Personal/emotional:** rebellion, freedom, nostalgia, identity, alienation and belonging.
- **World and setting:** science fiction/space, travel/escape, war/conflict, nature/weather and religion/spirituality.
- **Other recurring subjects:** substance use and related nightlife imagery.

Each theme retains evidence terms, counts and source agreement. Horror relevance is calculated only from horror-specific themes; ordinary party, romance or nightlife language cannot inflate the horror score. Multiple providers are merged into one analysis. This is a transparent lexical baseline, not an AI interpretation of metaphor, narrative, irony or musical sound. A low score means "not enough explicit evidence found", not proof that a song is unrelated. Schema and method versions are stored so later analyzers can be compared and migrated safely.

For Booze or Boos!, horror relevance remains a gate; lyrical themes, track/artist metadata and listening judgment are combined, while energy and sound similarity determine sequencing after the gate is satisfied. For other playlists, the broader theme vocabulary can be used without applying the horror gate.

## Local lookup and privacy

The database supports searching by title, artist, remembered phrase, and recent additions. The phrase index is built from transient lyric responses; it stores SHA-256 hashes of five-word sequences rather than the lyric text itself. The database is personal local data. Do not commit it, publish it, or include provider API keys. A future SHIT workflow can call this module to enrich track features with source-backed lyric themes and use the same local index to resolve "what's that song with the line..." queries.

## Current limitations

- Lyrics coverage varies, especially for obscure and instrumental tracks.
- Musixmatch and Genius require credentials; LRCLIB is the only provider that works without setup.
- Genius is metadata/link-only in this implementation.
- Theme extraction is keyword-based and intentionally conservative; nuanced interpretation, narrative understanding, and audio-energy analysis remain separate.
- Source agreement is recorded, but providers may return excerpts or variant lyric text; agreement is supporting evidence, not a guarantee of correctness.
- A phrase lookup needs at least five words and works only for songs previously analyzed into this local database.


## Recommendation feature integration

`python compat/build_music_analytics.py` rebuilds recommendation features and automatically merges matching analyses from the committed `lyric_features.json` export and, when present, the local SQLite database into each track's `lyric_analysis` field. Local records take precedence. It also reports the number of enriched tracks in the recommendation manifest. The standalone `compat/enrich_recommendation_lyrics.py` remains available for rebuilding the join after the feature file has already been generated.

The SQLite database is intentionally local and git-ignored. The compact `assistant_data/recommendations/lyric_features.json` export contains only track identity and derived theme metadata; it contains no full lyric text or phrase fingerprints. Commit that export when you want the same analyzed themes available to GitHub Actions and other SHIT environments. Both `compat/build_music_analytics.py` and playlist discovery read the export, and local SQLite records take precedence on the machine where they exist. The canonical Last.fm archive and Spotify reference data are not modified.

Playlist discovery also consults the lyric index. When a candidate and the current playlist both have lyric analyses, shared themes provide a small capped ranking bonus (up to 0.06) and an explicit explanation in the recommendation. Last.fm artist similarity remains the dominant signal; unindexed candidates receive no lyric bonus, and missing lyric coverage is never treated as negative evidence. Playlist profiles expose their analyzed lyric themes and coverage so the fit can be inspected.
