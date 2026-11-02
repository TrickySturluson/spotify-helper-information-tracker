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
