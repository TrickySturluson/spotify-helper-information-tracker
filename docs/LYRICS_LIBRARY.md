# Lyrics analysis and local song lookup

SHIT's lyrics subsystem is an opt-in research aid for song discovery and recommendation quality. Run it locally:

```bash
python lyrics_library.py analyze "Song Title" "Artist Name" --album "Album" --duration 210
python lyrics_library.py lookup --title "Song Title"
python lyrics_library.py lookup --phrase "a remembered phrase of five or more words"
python lyrics_library.py recent
```

The default database is `data/lyrics/library.sqlite3`. It is local runtime data and should not be committed. The database contains track identity, provider links/check status, theme evidence, analysis confidence, and one-way five-word phrase fingerprints. It deliberately does **not** retain full copyrighted lyrics. Phrase fingerprints support approximate local phrase-to-song matching without storing a copy of the lyrics; exact short fragments under five words are not indexed.

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

The versioned analyzer extracts explicit song-level themes, with an initial emphasis on horror, slasher/murder, blood/gore, monsters, vampires, zombies/undead, ghosts/supernatural, witchcraft/occult, dark fantasy, Halloween-party imagery, and death/afterlife. It records matched evidence terms, counts, source agreement, word count, a relevance score, and a coarse assessment. When multiple providers return lyrics, their theme evidence is merged rather than overwritten. This is a transparent lexical baseline, not an AI interpretation of metaphor, narrative, irony, or musical sound. A low score means "not enough explicit evidence found", not proof that the song is unrelated.

For Booze or Boos!, the lyric result should be combined with track/artist metadata and listening judgment. Halloween/horror relevance is a gate; energy and sonic fit determine sequencing only after that gate is satisfied.

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

After rebuilding recommendation features, merge any locally analyzed lyric evidence into the generated track feature file:

```bash
python build_music_analytics.py
python enrich_recommendation_lyrics.py
```

The enrichment is local-only and additive. It joins on normalized artist + track title, writes a compact `lyric_analysis` object into `assistant_data/recommendations/track_features.json`, and leaves tracks without a local lyric record explicitly marked `null`. A clean cloud runner without the local SQLite database skips this step rather than fabricating empty evidence. The canonical Last.fm archive and Spotify reference data are not modified.
