# Listening Analytics & Evidence Sources — Actions & Evidence

Newest entries first. Record verified outcomes separately from plans, assumptions and unverified artifacts.

## 2026-11-01 — Goal workspace initialized

- **Action:** established this goal's dedicated documentation and action-history location.
- **Context:** 2026-11-01: Source-of-truth and evidence separation rules consolidated in project handoff. Documentation-only; no new analytics run or fresh counts claimed. Next: preserve these invariants in enrichment, retry priority and recommendation learning.
- **Outcome:** documentation initialized; no runtime implementation or data mutation implied unless explicitly stated above.

## 2026-11-01 — Project-wide audit: duration analytics checklist captured

- **Reference:** open issue #2 https://github.com/TrickySturluson/spotify-helper-information-tracker/issues/2.
- **Outstanding validation:** keep the 3.5-minute legacy estimate as headline all-archive estimate; show verified-duration full-track-equivalent and minimum-qualifying estimates separately; publish duration coverage and unknown-duration counts; include all-scrobble legacy estimates in monthly/yearly buckets; keep measured Spotify tracker intervals separate.
- **Status:** issue checklist says updated workflows/outputs still need to be run and verified. Do not assume checked-in code or previous workflow attempts prove output correctness.
- **Evidence semantics:** Last.fm scrobbles remain historical source of truth. Spotify playback tracker is optional prospective evidence with coverage gaps; missing tracker data is unknown, not zero. Explicit likes/saves, playlist additions, recommendations and inferred preference remain separate.
- **Failed approach / lesson:** never mix estimated time with measured tracker intervals or treat absence of tracker events as zero listening.
- **Outcome:** documentation audit only; no analytics workflow run or fresh counts claimed.
- **Next action:** after migration is verified, run analytics workflows and inspect generated summaries/trend buckets.

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
