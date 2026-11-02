## 2026-11-02 — Switch to incremental enrichment and parallel feature work

- Decision: the Library is structurally sound enough to support feature development while metadata completeness continues to improve in the background/on demand. Do not block the sorter on filling every field for every song.
- Execution path: lookup canonical evidence first; reuse local evidence; consult provider-specific retry/cooldown state; make bounded lookups only when eligible; merge with provenance and confidence; re-audit. Keep unknowns explicit.
- Candidate intake: songs discovered through recommendations or feature use should be captured with source/context and resolved/enriched incrementally, without counting them as plays or explicit preferences.
- Boundaries: daily credential check and weekly read-only health/freshness monitoring are not automatic metadata enrichment. Retry queue/executor remain unfinished. No Spotify playlist writes authorized.
- Next: record fresh post-backfill coverage; inspect and evaluate sequencer offline using existing audio/profile/theme data; add tests for missing-data fallback and confidence visibility; implement retry queue separately.

# Canonical Library Enrichment — Actions & Evidence

Newest entries first. Record verified outcomes separately from plans, assumptions and unverified artifacts.

## 2026-11-01 — Goal workspace initialized

- **Action:** established this goal's dedicated documentation and action-history location.
- **Context:** 2026-11-01: Consolidated enrichment goals and safeguards in central handoff. No fresh coverage totals or provider-availability measurements asserted. Next: after migration verification, generate a read-only coverage report and select bounded batches.
- **Outcome:** documentation initialized; no runtime implementation or data mutation implied unless explicitly stated above.

## 2026-11-01 — Project-wide audit: enrichment backlog clarified

- **Purpose:** capture metadata/provider limitations found in prior conversations and open work.
- **Verified context:** no fresh post-publication coverage report has been confirmed. Prior conversational counts (artist 1,587; track 9,778; album 6,384; unresolved duration 2,919) are stale snapshots, not current coverage.
- **Known provider gaps:** lyrics remain unpopulated; MusicBrainz previously returned 503/rate-limit failures; Discogs and GetSongBPM require optional credentials; AcousticBrainz timeout resilience was a recent fix target. Recheck actual provider state after migration; do not infer current availability.
- **Outstanding fields:** recording IDs/MBIDs and aliases; duration; acoustic/audio features; track-level tags/mood/theme; album tracklists/descriptions/release context; artist profiles/genres; artwork references where useful.
- **Design lesson:** preserve recording/artist/album separation, field-level provenance/confidence/timestamps/evidence, and unknown values. Do not infer track mood from artist identity. Lyrics enrichment must use compact permitted features/tags, not full copyrighted lyrics.
- **Failed approach / lesson:** blind refetching unavailable providers wastes quota and can turn transient failures into misleading missing-data conclusions. Cache success, honor cooldowns and distinguish transient, ambiguous, credential-blocked and definitive negative states.
- **Outcome:** audit documentation only; no provider requests or Library mutations.
- **Next action:** after migration publication, run a read-only field coverage report and plan bounded passes.

## Entry template

### YYYY-MM-DD — Action
- **Purpose:**
- **Changes / files:**
- **Execution:** command, workflow run, PR, commit
- **Verification:** exact tests/audits, including failing steps and diagnostic evidence
- **Outcome:** complete / partial / blocked / deferred
- **Failed or abandoned approaches:** what was tried/rejected and why; never omit meaningful failures
- **Performance / provider limits:** latency, request volume, cooldowns, quotas, caching, or inefficiencies observed
- **Lessons learned / decision changes:**
- **Next action:**
- **References:**
