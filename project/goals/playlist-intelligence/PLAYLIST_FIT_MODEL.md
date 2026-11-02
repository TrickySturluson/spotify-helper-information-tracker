# Playlist-fit model — production contract

**Status:** production contract plus read-only scorer prototype. The scorer and synthetic regression tests now exist, but target-profile integration, broader source adapters, full regression execution and held-out evaluation are still required before production enablement.

## 1. Purpose and decision boundary

The classifier answers: **how well does this recording belong in this particular playlist?**

It does not answer whether the user likes the song globally, whether it is popular, whether the artist usually makes this kind of music, or whether it should be played next in a smooth sequence. Those are separate signals and policies.

The five registered reference playlists are independent targets. A track may fit several, none, or sit between them. Scores are independent per-target fit estimates; do not force the five scores to sum to 100. The highest score is a ranking aid, not an automatic add instruction.

## 2. The five evidence dimensions

Every track-to-playlist comparison must evaluate these dimensions separately before producing an aggregate fit score.

| Dimension | Question | Preferred evidence | What must not be substituted |
|---|---|---|---|
| **Genre** | Does the track's musical lineage/style belong in this playlist? | Track-level MusicBrainz genres/tags, Discogs styles with release scope, verified track metadata | Artist genre as if every song shares it |
| **Sound** | Does the recording's texture, instrumentation, production, arrangement and sonic character resemble the playlist? | Track-specific descriptions/reviews, verified recording metadata, local audio descriptors, validated audio models | Genre labels alone; album identity; title/artist assumptions |
| **Energy** | Does its intensity, drive, tempo, loudness/dynamics and movement suit the playlist? | Spotify track audio features when actually available; Essentia local measurements; AcousticBrainz with provenance; catalog BPM as weak rhythm context | Mood words, genre, lyrics or a BPM value alone as measured intensity |
| **Mood** | What emotional/affective character does this particular recording convey? | Recording-level tags from independent source families, validated audio valence/arousal, track-specific reviews | Artist-level mood; album-level mood presented as track truth; lyrical subject alone |
| **Theme** | What is the song about, and does that subject/narrative belong here? | Track-specific lyric analysis, official descriptions, track-specific editorial sources | Artist biography, song title alone, inferred themes without text/source evidence |

Genre, sound, energy, mood and theme are related but not interchangeable. Keep their raw evidence, scores, provenance, scope and confidence independently inspectable.

### 2.1 Default blend

Initial global starting weights (to be versioned in config and reviewed against the playlist's role):

- Genre: 0.15
- Sound: 0.25
- Energy: 0.20
- Mood: 0.25
- Theme: 0.15

These are initial engineering priors, not fitted coefficients or human-score-derived weights. Playlist-specific role profiles may change them only through explicit, versioned configuration. For a playlist whose identity is primarily lyrical/theme-based, theme can be weighted more heavily; for an instrumental electronic playlist, sound and energy should dominate and lyric absence must not count against it.

For each dimension, calculate an independent 0–100 compatibility score against the target playlist profile. Aggregate only dimensions with usable evidence:
`fit = sum(weight_i * dimension_score_i) / sum(weight_i for observed dimensions)`

Do **not** encode missing dimensions as zero. Alongside the normalized fit, report which dimensions were observed, their effective weights and total evidence coverage. Missingness must reduce confidence and may force a provisional result even when the normalized fit is high.

The aggregate is a fit score, not a probability. Do not label 85 as an 85% chance of belonging.

## 3. Playlist profiles are distributions, not stereotypes

Build each target profile from its current, complete, retrieved playlist snapshot and its track-level Library evidence. Keep:
- distribution of genre/style families, not only top tags;
- sound/production/instrumentation descriptors;
- energy/tempo/loudness/dynamic ranges and their source coverage;
- mood/valence/arousal distributions, including meaningful combinations and contrasts;
- lyrical/narrative theme clusters;
- track count, unique-artist count, profile coverage, snapshot ID and capture time.

Use track-level observations where possible. Artist-level evidence may describe broad context, but must be separately scoped and down-weighted. Album/release evidence is contextual and cannot masquerade as recording-level evidence.

A profile must be marked weak or provisional when the snapshot is incomplete, very small, stale, or has poor field coverage. In particular, the current non-audition sample for Somber Party and Smooth is small; do not let those thin samples produce falsely precise boundaries.

Reference construction must exclude the candidate being evaluated. For benchmark runs, exclude the entire held-out batch from profile construction. For live scoring, exclude the candidate URI from its target playlist profile (leave-one-out) so membership cannot create circular proof that it fits.

## 4. Confidence is independent of fit

Return at least:
- `fit_score`: 0–100 compatibility estimate;
- `confidence_tier`: high / medium / low / unknown;
- `confidence_reasons`: readable reasons;
- `dimension_scores`: five independent score/evidence objects;
- `evidence_coverage`: observed dimensions and source families;
- `identity_confidence`: confidence that the metadata belongs to the correct recording;
- `conflicts`: source disagreements or contradictory signals;
- `profile_confidence`: strength/completeness of the target playlist profile;
- `model_version` and `profile_snapshot_id`.

Confidence must not be copied from the fit score. A high fit with one weak source is low-confidence; a moderate fit supported by multiple independent recording-level sources may be medium/high confidence.

Confidence gates:
- **High:** strong recording identity; at least 4 of 5 dimensions supported; at least 2 independent source families across the decisive dimensions; no unresolved material contradiction; target profile sufficiently sampled.
- **Medium:** at least 3 dimensions supported, or 2 strong independent dimensions with clear direct evidence; identity is at least medium; no critical ambiguity.
- **Low:** only 1–2 dimensions, artist/album fallback dominates, target profile is weak, or material disagreement remains.
- **Unknown:** identity unresolved or no usable evidence. Do not invent a score from title/artist alone.

These are conservative operational tiers, not probabilities. Revisit thresholds only with held-out evidence. Confidence should be field-specific too: acoustic, semantic, mood, lyric/theme, identity and profile confidence must remain separately available.

## 5. Evidence and provenance rules

Every observation should preserve:
- field/dimension and normalized value;
- exact scope: recording, release, artist, lyric text, or audio file;
- provider/source family and source reference;
- observed/checked timestamp and freshness state;
- identity match method and confidence;
- raw provider value separately from normalized interpretation;
- model/version where derived.

Independence is counted by source family, not number of tags, pages, or repeated values. Multiple Last.fm tags are not multiple independent providers. A source can be authoritative for one field and weak for another.

Conflicts are retained, not averaged away silently. A track tagged both dreamy and aggressive can legitimately have both moods; do not force a single artist-level stereotype. If source disagreement changes the likely target, lower confidence and expose the conflict.

Lyrics describe narrative/theme, not acoustic mood. Track title alone is never lyric evidence. Artist tags are context only. Album tags are context only. Catalog BPM is weak tempo context, not loudness or energy measurement. Missing provider data is unknown, never negative evidence.

## 6. Human scoring and evaluation data

The 25-track SHITting Grounds human sliders were an **initial exploratory test**. They are useful reference observations for whether a model result seems reasonable in a real-world playlist scenario, and for spotting obvious boundary disagreements. They are **not**:
- production labels or ground truth;
- a sorting policy or target to imitate;
- training data for the first production model;
- evidence about sound, mood, energy or theme;
- permission to tune weights until the model reproduces those slider values.

Keep the human-rating file immutable as a separate exploratory reference dataset. Do not feed it into profile construction, scoring, confidence, sorting, or automatic calibration. Any future human review must be a separately designed evaluation set with explicit task instructions and provenance; it must not silently convert this first exploratory set into labels.

The initial comparison can be reported as a descriptive sanity check only, with its limitations attached. It is not a production acceptance metric. Future validation should combine:
1. held-out candidate batches whose members are excluded from reference profiles;
2. independent track-specific evidence reviews that do not read the model score or human sliders;
3. real playlist outcomes with clear provenance (explicit accept/reject, not ignored exposure);
4. transition-quality checks as a separate sequencing evaluation.


## 6.1 Interpreting the initial human slider style

The user has clarified that their initial SHITting Grounds scores tend somewhat toward the extremes. Preserve the raw ratings exactly, but do not interpret their numeric distance as a neutral, evenly calibrated measurement.

For descriptive comparison only, read the values primarily as ordinal/severity bands:
- 0–20: emphatic mismatch
- 21–40: leaning mismatch
- 41–59: uncertain / mixed / middle
- 60–79: leaning fit
- 80–100: emphatic or standout fit

Use rank/order agreement, broad band agreement and notable reversals before raw point error. Do not apply a fixed shrinkage coefficient without additional observations. Do not transform the stored values, use them as production labels, or tune production weights against them. The scores are a small, user-style-specific reference sample, not a universal scale. Future comparisons should preserve both the raw value and this explicitly derived ordinal interpretation.

## 7. Production decision policy

Fit scoring is one input to a later decision layer:
- **Strong candidate:** fit and confidence both clear configured thresholds; no safety/blacklist/identity issue.
- **Review candidate:** promising fit but low/medium confidence, profile uncertainty, or dimension disagreement.
- **Do not recommend:** weak fit supported by adequate evidence, or a hard policy exclusion.
- **Insufficient evidence:** unknown/low evidence. Keep it out of automatic writes, but do not call it a bad song or a negative taste signal.

Do not use fit scoring as the sequence optimizer. Sequencing remains a separate problem: adjacent transitions, energy contour, tempo relationship, mood/theme continuity, repetition/diversity, peak position and resolution. A track can be an excellent playlist fit but a poor next transition, and vice versa.

All Spotify writes remain behind the existing lock/allowlist, preview, audit and explicit-authorization controls. No model score bypasses these controls.

## 8. Production acceptance tests

A production implementation is not ready until the following regression tests pass:

1. **Dimension isolation:** artist genre cannot raise track mood or acoustic confidence; lyrics cannot raise acoustic energy; tempo cannot stand in for loudness; title-only themes remain unknown.
2. **Missingness:** removing one provider lowers coverage/confidence but does not turn the missing dimension into a zero score or reverse unrelated dimension scores.
3. **Source independence:** duplicated tags from one provider do not count as multiple confirmations.
4. **Identity:** ambiguous artist/title matches cannot attach evidence to the wrong recording; unresolved identity yields unknown.
5. **Scope:** album and artist evidence remain contextual and cannot be serialized as track-level facts.
6. **Contradictions:** conflicting moods/styles remain visible and lower confidence where material.
7. **Candidate exclusion:** a candidate's presence in a target playlist cannot improve its own fit; held-out batches are excluded from profile generation.
8. **Thin profiles:** small/incomplete Somber Party or Smooth profiles produce lower profile confidence and conservative decisions.
9. **Instrumental tracks:** absence of lyrics is neutral; sound/energy can still yield strong fit.
10. **Vocal/theme tracks:** lyrical theme may support theme fit but cannot override a strong sound/energy mismatch by itself.
11. **Cross-playlist independence:** scores do not sum to 100; multiple strong matches and no-match outcomes are both valid.
12. **Determinism:** same versioned inputs produce the same score and explanation.
13. **Explainability:** every dimension score points to evidence and scope; every confidence reduction has a reason.
14. **No feedback leakage:** the exploratory human ratings file is not imported by the production scoring path.
15. **No write side effects:** scoring/evaluation is read-only and cannot edit Spotify playlists.

## 9. Implementation sequence

1. Freeze this contract and correct the reference guide's description of human scores.
2. Build a versioned target-profile builder with candidate/holdout exclusion and coverage reporting.
3. Implement five-axis per-target scoring with field-specific evidence and confidence.
4. Add synthetic unit tests for isolation, missingness, source duplication, contradictions and leakage.
5. Run a fresh held-out blind batch; separately run track-specific evidence checks without viewing scores.
6. Compare only after both outputs are frozen. Treat the human exploratory dataset as context, not a training objective.
7. Connect the fit result to the existing sequencer/recommender as a read-only ranking signal; preserve the existing transition optimizer and playlist write safeguards.
8. Enable production recommendations in preview-only mode. Only consider writes after repeated held-out success and explicit authorization.

## 10. Current implementation boundary

The existing sequencer already has a separate acoustic energy estimate, semantic score, mood evidence scope, genre/theme groups, transition confidence, and provider provenance. It is useful infrastructure, but it is **not yet this five-axis playlist-fit classifier**: it currently scores perceived energy and transition compatibility, not per-target fit across five dimensions. Keep that distinction explicit until the profile builder, fit scorer and acceptance tests above exist and pass.
