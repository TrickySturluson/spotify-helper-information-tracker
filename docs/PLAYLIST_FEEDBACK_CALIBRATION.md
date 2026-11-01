# Playlist feedback calibration

## Scope

This subsystem calibrates playlist-fit predictions using playlist-specific
feedback. It is intentionally separate from Tricky Daily, whose discovery-first
ranking, familiarity penalties, and pre-liked-track behavior remain specialized.

## Two feedback layers

1. **Playlist refinement:** explicit whitelist/blacklist decisions, playlist
   additions, and manual removals describe whether a track belongs in one
   particular playlist.
2. **Calibration refinement:** immutable fit predictions are joined to those
   outcomes. The report compares predicted fit bands with weighted observed
   acceptance and exposes systematic over- or under-scoring.

The calibration layer does not yet rewrite production weights. It produces
reviewable diagnostics first; a later change must demonstrate improvement on
held-out outcomes before any calibrated transform is enabled.

## Prediction records

Call `record_prediction()` when a playlist-fit score is generated. Each record
preserves playlist and track identity, original score, evidence snapshot,
confidence, model version, prediction timestamp, and whether the track was
already in Liked Songs. The same prediction ID is idempotent and the forecast
is not overwritten when later feedback arrives.

Call `record_feedback()` for an explicit accepted, rejected, or uncertain
decision. Reversals are appended as new events; the report uses the latest
event while retaining the full history. Ignored recommendations are not
feedback. "Uncertain" is retained for audit but excluded from calibration.

## Liked Songs and listening behavior

Liked Songs is global taste context, not proof of playlist fit. The module
stores the pre-prediction liked state and can record later liked-state
observations, but never converts a like or unlike into an accepted/rejected
playlist label. A pre-existing like must not be conflated with a save that
happens after a recommendation. Spotify/Last.fm playback exposure can later
be attached as contextual evidence, but plays alone do not prove playlist fit.

This keeps Tricky Daily's existing novelty/familiarity penalty from leaking
into playlist-fit calibration.

## Evidence strength

Default outcome weights are deliberately conservative:

- Explicit whitelist / blacklist: 1.00
- Manual removal: 0.85
- Manual addition: 0.65
- Retained after explicit review: 0.50

These weights are evidence weights, not confidence percentages. A manual
removal only applies when an exact playlist+track URI joins to a stored
prediction. Historical removal rows without a URI are skipped rather than
fuzzy-matched. Current playlist membership is not automatically treated as
approval because it may predate the prediction or be accidental.

## Calibration report and safeguards

`calibration_report()` groups labelled predictions into 20-point score bands,
reports weighted observed acceptance, and creates a stable 20% holdout split
based on prediction ID. The training MAE compares the normalized predicted
score with the binary outcome. Small bins remain provisional; the default
minimum is eight observations per bin.

The holdout is not included in training summaries. No score weights or
playlist policies are automatically changed. A future calibration transform
must be evaluated against the holdout and compared with the uncalibrated
baseline before adoption. Separate playlist IDs remain separate observations;
one playlist's blacklist must not become a global artist blacklist.

## Storage

The default append-oriented store is
`assistant_data/spotify/playlist_fit_feedback.json`. It is generated only
when prediction or feedback APIs are called. Do not commit personal feedback
records or Spotify identifiers unless the repository's data policy explicitly
allows it.


## Operating the report

Run `python compat/playlist_feedback_calibration.py report` to print the
current read-only calibration report. Use `--min-bin-samples N` to change the
minimum observations required before a score band is reviewable. The command
does not call Spotify or alter scoring weights.
