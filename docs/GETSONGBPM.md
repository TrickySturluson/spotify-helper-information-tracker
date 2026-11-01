# GetSongBPM fallback

SHIT can use GetSongBPM as an optional BPM/key source after the bulk
AcousticBrainz pass. It is deliberately secondary: it provides catalog tempo
and key metadata, not a measured loudness curve or beat-by-beat analysis.

## Enable it

1. Register the project at [GetSongBPM API](https://getsongbpm.com/api).
2. Add a backlink to GetSongBPM in the project's public-facing documentation
   or website as required by its API terms.
3. Add the API key to GitHub repository Actions secrets as
   `GETSONGBPM_API_KEY`.
4. Run **Acoustic Metadata Enrichment** manually or wait for its daily schedule.

The workflow skips this stage when the secret is absent. It queries at most
300 tracks per run by default, caches misses for 30 days, and accepts a result
only when exactly one search result has an exact normalized artist and title
match. Ambiguous and version-mismatched results are rejected. Existing primary
tempo values are never overwritten.

The API documents a 3,000-request/hour limit and requires an API key. SHIT
uses a slower default request interval and stores provider attribution,
GetSongBPM song URI, tempo, key, time signature, danceability, and acousticness
where returned. Values remain explicitly source-tagged. GetSongBPM's
danceability/acousticness fields are database metadata, not measurements made
by SHIT.

## Limits

GetSongBPM does not provide integrated LUFS, loudness range, beat positions,
or within-track loudness envelopes. Those remain separate measurements:
AcousticBrainz for historical average/dynamic descriptors, and optional local
Essentia analysis for actual segment-level audio measurements.
