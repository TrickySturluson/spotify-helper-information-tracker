# Discovery & Recommendations — Actions & Evidence

Newest entries first. Record verified outcomes separately from plans, assumptions and unverified artifacts.

## 2026-11-01 — Goal workspace initialized

- **Action:** established this goal's dedicated documentation and action-history location.
- **Context:** 2026-11-01: User requirement to ingest suggested/recommended tracks recorded in central handoff. PR #60 identified; implementation and tests not yet verified. Next: review PR #60 and preserve strict evidence separation.
- **Outcome:** documentation initialized; no runtime implementation or data mutation implied unless explicitly stated above.

## 2026-11-01 — Project-wide audit: recommendation intake CI/security failures recorded

- **PR:** #60 https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/60 (open, not merged).
- **Observed checks:** compile, generated-data audit and maintained-file documentation steps passed; unit-test step failed; full-history secret scan failed.
- **Not yet known:** test failure root cause and whether the secret-scan finding is real, historical or a false positive. No suppression/merge decision should be made without inspecting redacted evidence.
- **Loose ends:** diagnose tests and secret scan; validate candidate dedupe against Spotify IDs, ISRCs, recording MBIDs and aliases; verify canonical writer integration and that discovery exposure/acceptance/add/save/play/reject/ignore remain distinct from listening and preferences.
- **User requirement:** every song suggested, recommended, surfaced or otherwise introduced by a discovery workflow should be eligible for Library intake even if never played or saved. Preserve source, prompt/seed/context, capture time, identity confidence and observable response.
- **Failed approach / lesson:** recommendation exposure is not a play, save, like or confirmed preference. Never feed candidate count directly into scrobble or preference analytics.
- **Outcome:** proposed implementation only; PR remains open and checks are failing.
- **Next action:** inspect sanitized unit-test output and redacted Gitleaks result; then fix and rerun both checks.

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
