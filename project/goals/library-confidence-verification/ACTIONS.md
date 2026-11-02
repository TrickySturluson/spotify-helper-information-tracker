## 2026-11-02 — Classify missing confidence separately from mismatches

- PR #88 merged to main as `67ab44f17a1c94093e4a71328abded6b80d66455`.
- The read-only confidence audit retains `metadata_confidence_drift_count` for compatibility and now reports separate missing-stored-confidence and genuine-mismatch counts, per-field counts, and examples.
- Missing means the field has recomputable evidence but no stored confidence object. Mismatch means a stored confidence object differs from recomputation.
- No confidence values are written, recalibrated, or automatically promoted.
- Fixture tests cover both categories. Full CI and secret scan passed.
- Issue #90 is running post-merge full-catalogue `audit`, `health`, and `confidence` to quantify the actual breakdown.

## 2026-11-02 — Post-playability-backfill full-catalogue confidence verification

- Read-only operation issue #83 completed successfully: https://github.com/TrickySturluson/spotify-helper-information-tracker/issues/83
- Full Library integrity audit: `ok=true`, 13,005 songs, 6,386 artists, 7,861 albums; zero errors.
- Structural health: `ok=true`, index counts match entity counts, zero errors, zero warnings. Alias counts: 1,856 Spotify IDs, 11,338 recording MBIDs, 1,816 ISRCs, 13,003 source-track IDs, 11,529 name candidates.
- Confidence report scanned 13,005 songs. Identity confidence: 7,525 high, 5,480 low; resolution methods: 5,669 recording MBIDs, 1,856 Spotify IDs, 5,480 source-track IDs. Identity confidence drift: 0.
- Metadata confidence drift: 1,582. First examples show stored duration confidence missing while recomputation finds single-source `lastfm_catalog` evidence and correctly assigns low confidence. This should be separated into missing stored confidence vs genuine conflicting/incorrect confidence before any bulk update.
- Field coverage: duration 10,028; track tags 179 (34 high, 1,483 low); audio features 36; Spotify playability 1,856. Missing duration provenance count: 1,856. Legacy source coverage remains complete: 11,130/11,130 track IDs and 5,358/5,358 artist names.
- All audits are read-only; no provider calls or Spotify playlist writes.
- Full regression suite: 327 tests passed.
- Next: classify the 1,582 confidence differences, inspect missing duration provenance, and build a curated gold set. Do not bulk-rewrite confidence until the difference taxonomy is validated.

## 2026-11-02 — Implement read-only confidence audit (draft)

- Added `scripts/music/library_confidence_audit.py` and exposed `python shit.py library confidence [--json]`.
- Reports stored identity confidence tiers, resolution methods, identity-quality labels, recomputed-vs-stored identity drift, per-field metadata confidence, metadata confidence drift, duration/tag/audio/mood/lyrics/playability coverage, missing duration provenance, ambiguous aliases, and legacy source-index coverage.
- Uses the same `identity_confidence()` and `track_metadata_confidence()` helpers as the canonical library. It does not promote or rewrite confidence.
- Added fixture tests for correct high/low tiers, legacy track/artist coverage, ambiguous aliases, confidence drift, and no-write behavior.
- Added a CI step to run the audit over the complete published catalogue, not just fixtures.
- Branch: `feature/library-confidence-audit`; not merged. Awaiting CI output.
- Next: inspect full-library report; investigate stored-vs-recomputed drift and low-confidence populations; build curated gold set before changing any confidence policy.
# Actions — Library Identity & Metadata Confidence Verification

## 2026-11-02 — Initialize confidence verification workspace

- User priority: verify confidence in the newly populated canonical Library before relying on it for the sorter.
- Inspected `scripts/music/music_evidence.py`: identity confidence is categorical (high/medium/low/unknown), not a probability. Spotify ID, recording MBID, ISRC and verified release-position matches are high; exact name matches are medium; source-track IDs and fallback identities are low; ambiguous/unsupported matches are unknown.
- Metadata confidence is field-specific and uses independent source families; conflicting values are low; single-source observations are low unless authoritative.
- Independently compared current published legacy indexes with the canonical index: 11,130/11,130 legacy track IDs resolve through source-track or recording-MBID aliases; all 5,358/5,358 legacy artist names are represented.
- This confirms catalogue coverage, not confidence quality. Full confidence distribution, provenance audit, false-match review, and gold-set testing remain outstanding.
- No confidence scoring changes or Library writes performed in this documentation pass.
- Next: build a read-only report with identity-quality counts, per-field confidence coverage, missing provenance, ambiguous candidates, and recomputed-vs-stored confidence drift; then define a curated gold set.
