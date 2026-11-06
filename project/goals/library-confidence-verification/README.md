# Library Identity & Metadata Confidence Verification
> **Roadmap:** [ROADMAP.md](ROADMAP.md) is the durable plan and next-action reference. Read it before work; update it and [ACTIONS.md](ACTIONS.md) in the same session as implementation, testing, decisions, or blockers.
> **Current repository priority:** This workstream is paused for feature implementation while SHIT's documentation audit is active. Only documentation corrections and evidence reconciliation are permitted. Preserve this roadmap; resume its feature next actions only when the [central handoff](../../NEXT_WORK.md) and Maintainability & Documentation roadmap explicitly say documentation is complete.


## Goal

Prove that canonical song records resolve to the right recordings and that confidence labels reflect the evidence actually stored. The sorter must consume confidence-aware fields, not merely the presence of a value.

## Scope

- Audit identity confidence by resolution method: Spotify track ID, recording MBID, ISRC, verified release position, source-track ID, exact artist/title/album, and ambiguous fallback.
- Verify alias completeness and uniqueness against legacy indexes, Spotify snapshots, ISRCs, MBIDs, and source IDs.
- Measure field-level confidence and source-family corroboration for duration, genres/tags, release metadata, audio features, mood/theme, and album context.
- Identify conflicts, weak single-source claims, missing provenance, stale observations, and mismatches between stored confidence and evidence.
- Build a curated regression set containing verified matches, ambiguous same-title recordings, remasters/live versions, missing IDs, conflicting sources, and false-match traps.
- Verify lookup behavior by stable ID and by name; explain match method, candidates, confidence, and source evidence.
- Test sorter readiness on a representative playlist cohort. A high confidence average must not hide a few catastrophic wrong matches.

## Confidence semantics already in code

The shared confidence helper returns categorical confidence, not a probability:
- High identity confidence for Spotify track ID, recording MBID, ISRC, and verified release-position matches.
- Medium for exact artist/title/album or unique exact artist/title matches.
- Low for source-track IDs and fallback artist/title/release-context identities.
- Unknown for ambiguous or unsupported resolution.
- Metadata confidence is field-specific: independent source families can corroborate; conflicting values lower confidence; a single source family is low unless authoritative for that field.

These rules are in `scripts/music/music_evidence.py`. Do not silently reinterpret categories as calibrated percentages.

## Verification plan

1. Run a read-only confidence coverage report across all canonical song records.
2. Cross-check legacy archive track IDs and artist identities against canonical aliases (the current published index comparison resolved 11,130/11,130 track IDs and 5,358/5,358 artist names).
3. Sample records across identity methods and confidence tiers; manually inspect a gold set.
4. Add regression tests for false positives, ambiguity, release variants, conflicts, and confidence preservation across syncs.
5. Compare stored confidence to recomputed evidence; report drift rather than rewriting labels automatically.
6. Gate sorter inputs by field-specific confidence and explain why a track is excluded or treated as uncertain.
7. Run real-playlist evaluations with confidence breakdown, unknown coverage, and transition quality before enabling writes.

## Acceptance criteria

- Every confidence value can be traced to exact evidence and match method.
- Ambiguous names never become high confidence.
- Duplicate observations from one provider family do not count as independent corroboration.
- Artist/album context never upgrades recording-level identity or acoustic confidence.
- Confidence audit is read-only and deterministic apart from report timestamp.
- A curated gold set has documented expected matches and no silent false positives.
- Sorter reports confidence per relevant field and can fall back safely when evidence is missing.

## Current status

**Read-only confidence audit is merged and remains read-only.** The historical issue #92 / run 41372492615 baseline scanned 13,005 songs and found 1,582 missing stored duration-confidence entries with zero genuine mismatches. The latest full-catalogue confidence report in Daily curator CI [#42154433350](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/42154433350), generated 2026-11-06T03:06:26Z, scanned 13,163 songs: identity confidence high 7,660 and low 5,503; methods were 5,669 recording MBIDs, 1,991 Spotify IDs and 5,503 source-track IDs. Identity confidence drift was zero. Metadata confidence had **zero missing entries and 214 mismatches, all in `track_tags`**; do not conflate these with the older missing-duration-confidence baseline or bulk-rewrite them. Duration metadata confidence was low on 8,187 records. The report is read-only; no confidence or provenance values were rewritten. The real-data review set and issue #102 still track a potential duplicate Candy Claws artist/album pair that structural health alone does not catch.

## Real-data identity review set

Read [IDENTITY_REVIEW_SET.md](IDENTITY_REVIEW_SET.md) before changing confidence or entity relationships. It records verified MBID and Spotify-ID examples, a low-confidence source-track-only example, and a concrete Candy Claws artist/album duplicate candidate. The duplicate is evidence for a read-only duplicate-entity audit; it is **not** authorized for automatic merge.

## Resume

Read `ACTIONS.md`, inspect `scripts/music/music_evidence.py`, `MusicLibrary.lookup_song()`, and the published Library. Implement a read-only confidence report before changing any confidence scoring.
