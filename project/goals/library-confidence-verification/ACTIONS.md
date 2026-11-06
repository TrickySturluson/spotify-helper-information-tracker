# Library Identity & Metadata Confidence Verification — Actions & Evidence

Newest entries first. Record verified outcomes separately from plans, assumptions and unverified artifacts.

## 2026-11-06 — Full Library confidence audit passed read-only in documentation PR CI

- Daily curator tests run #42149783445 passed the full canonical Library confidence audit on draft PR #161's then-current base data.
- This was validation only; it did not modify canonical Library records or provider state. Recheck on current main after the documentation PR is merged.
- Feature work remains paused until documentation acceptance criteria pass.

## 2026-11-02 — Create real-data identity review set and identify duplicate entity candidates

- Added `IDENTITY_REVIEW_SET.md` (commit `2b8b840`) and linked it from the goal README (commit `456fac0`).
- The review set includes a verified recording-MBID song (Messer Chups — Night Stripper), a high-confidence Spotify-ID song with market-scoped playability (Candy Claws — Into the Deep Time (One Sun)), and a low-confidence source-track-only song (S-Connection — Summerlove).
- Found a concrete duplicate-entity candidate not caught by structural health: Candy Claws has both a verified MBID artist record (`mbid:da5eaa3b-397e-4af8-9a12-5c4ec93e8b48`) and an empty name-fallback artist record (`name:df4e3388540b77ea392a`). The same album appears as enriched `album:01632cb9b68c6acda89d` and empty fallback `album:985073c24c6efb9b926d`.
- Strong cross-link evidence: Spotify song `spotify:0lw2mlzncwftftvdojdysg` has `spotify_album_id=5KkGAZrad4N4rc5FriwgzU`, matching the enriched album's Spotify album ID, but currently points to the fallback album. Artist fallback is name-only pending verification of Spotify artist ID `34Xay0uKsALHCrn5LkrYeh`.
- This is a **candidate**, not a confirmed merge instruction. No records were modified. Need a read-only duplicate-entity audit that distinguishes exact shared external IDs from name-only candidates, preserves distinct releases/versions, and emits proposed cross-links with evidence and confidence.
- Structural health can pass while duplicate entities remain internally consistent. Add duplicate artist/album/song candidate review to confidence verification before sorter integration.

## 2026-11-02 — Re-run confidence audit with missing-vs-mismatch classification (issue #92)

- Latest-main run [41372492615](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41372492615) succeeded; report scanned all 13,005 songs.
- Identity confidence: 7,525 high, 5,480 low; methods: 5,669 recording MBIDs, 5,480 source-track IDs, 1,856 Spotify IDs. Identity confidence drift=0.
- Aggregate metadata confidence drift=1,582, now classified as **1,582 missing stored duration confidence** and **0 genuine mismatches**. Missing-by-field: duration=1,582; mismatch-by-field empty.
- Existing duration coverage=10,028; track-tag coverage=179 (34 high, 1,483 low); audio-feature coverage=36; Spotify playability evidence=1,856.
- Missing duration provenance count=1,856. This is a separate gap from missing stored duration confidence: do not invent provenance for values whose source is unknown.
- Legacy source coverage remains complete: 11,130/11,130 track-index IDs and 5,358/5,358 artist names represented. No errors.
- The report is read-only. No confidence values or source metadata were rewritten.
- Next: inspect a representative sample of missing-duration-provenance records and a sample of the 1,582 duration-confidence omissions. Consider a backup-protected, missing-only confidence materialization only after confirming it uses the exact shared confidence helper and preserves all existing fields; then build the curated identity gold set.

## 2026-11-02 — Merge missing-vs-mismatch confidence classification

- PR #88 merged to main as `67ab44f17a1c94093e4a71328abded6b80d66455`.
- Confidence audit retains the aggregate drift count for compatibility and now separates missing stored field confidence from genuine stored/recomputed mismatches, including per-field counts and examples.
- This is diagnostic only: it does not write confidence values, promote evidence, or alter scoring rules.
- PR head passed full CI and the public repository security scan before merge.
- Issue #92 requests a new full-catalogue report on latest main; inspect the missing/mismatch split before planning any backfill.
- Existing baseline from issue #83: identity drift 0; aggregate metadata drift 1,582; duration coverage 10,028; track-tag coverage 179; audio-feature coverage 36; playability observations on 1,856 songs. Legacy source coverage 11,130/11,130 tracks and 5,358/5,358 artists.
- Next: build a curated gold set and manually review ambiguous/source-track-ID identities before any confidence recalibration or sorter integration.

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


## 2026-11-02 — Post-second-backfill audit/health/confidence verification (issue #118)

- Fresh latest-main `verify-catalogue` completed successfully after issue #114. Canonical audit: `ok=true`, 13,005 songs, 6,386 artists, 7,861 albums, no errors. Health: `ok=true`, indexed counts match canonical counts, alias counts include 1,856 Spotify IDs, 11,338 recording MBIDs, 1,816 ISRCs, 13,003 source-track IDs, and 11,529 name-candidate keys; zero health errors and warnings.
- Identity confidence drift remains 0 across 13,005 songs (7,525 high / 5,480 low; 5,669 recording-MBID, 5,480 source-track, 1,856 Spotify-track identity methods).
- Metadata confidence drift is 1,582 missing stored duration-confidence entries and **0 genuine mismatches**. Do not bulk-rewrite confidence; the audit classifies these as missing entries, not incorrect confidence.
- Reported evidence coverage remains duration 10,028, track tags 179, audio features 36, and Spotify playability 1,856. Legacy track coverage is 11,130/11,130; artist-name coverage is 5,358/5,358. The freshness planner's post-second-pass unknown-age count is still pending issue #117.
- Duplicate entity audit issue #102 remains open. No merges or canonical record rewrites were performed.
