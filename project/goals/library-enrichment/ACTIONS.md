# Canonical Library Enrichment — Actions & Evidence

Newest entries first. Record verified outcomes separately from plans, assumptions and unverified artifacts.

## 2026-11-06 — Documentation-only pause recorded

- The repository-wide priority remains completion of SHIT Documentation & Continuity (internal codename: Babel).
- The roadmap now separates the current documentation-only next action from the preserved next feature action. Feature plans and acceptance criteria remain intact for later resumption.
- No feature implementation or Spotify playlist operation is part of this documentation update.

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
