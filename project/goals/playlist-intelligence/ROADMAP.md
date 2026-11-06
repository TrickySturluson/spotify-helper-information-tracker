# Playlist Intelligence & Safety — Roadmap

**Last reviewed:** 2026-11-06  
**Status:** Feature work paused under the documentation-only priority. Existing fit scoring and sequencing remain preview-only/low-confidence; this roadmap grants no playlist-write permission.

## Repository-wide priority override — 2026-11-06

**This workstream is paused for feature implementation while SHIT's documentation audit is active.** The only permitted work here until the Maintainability & Documentation roadmap passes its acceptance criteria is documentation correction, evidence reconciliation, and recording known gaps. Do not run enrichment, modify canonical data, change playlists, or begin feature development. This workstream's feature roadmap remains queued; the active next action is the documentation-only handoff in [project/NEXT_WORK.md](../../NEXT_WORK.md). Resume feature work only when that handoff and the maintainability roadmap explicitly say documentation is complete.

## Purpose
Create enjoyable, coherent playlist discovery, sorting, feedback learning, and safe generated-playlist automation.

## User requirements and safety invariants
- Smooth transitions are the primary sorting objective; avoid jarring adjacent tracks.
- Musical arc and peak position must be controllable; peak around 80–90% is a tentative default, not a locked rule.
- Use track-level mood/theme evidence; artist identity alone is insufficient.
- Distinguish actual plays, likes/saves, removals, recommendations, and unknown playback coverage. Unplayed does not mean disliked. Liked tracks may be down-ranked, not automatically excluded.
- Generated playlists only by default. Personal playlists stay read-only unless explicitly authorized. Preserve deny-by-default locks, explicit unlocks, dedupe, blacklists, audit and rollback.
- Tricky Daily is a specifically authorized exception within its documented controls, not blanket permission.
- Booze or Boos! must be energetic, fun, and strongly Halloween-related at track level.

## Roadmap
1. **Safety and state reconciliation.** Verify playlist roles/locks, whitelist/blacklist, removed-track policy, staging, transactionality, live read-back and recovery.
2. **Tricky Daily reliability and learning.** Maintain exactly 60 valid unique tracks; hard exclusions always win; retry/fallback is bounded and audited; forced runs preserve safety and update required metadata; verify actual live playlist after publication. See [Daily backlog](../../../docs/TRICKY_DAILY_TODO.md).
3. **Candidate quality and feedback.** Separate signal types, exposure from outcome, track preference from artist affinity, and comfort discoveries from wildcards; apply saturation and confidence-aware scoring.
4. **Playlist fit model.** Improve direct recording-level Genre, Sound, Energy, Mood and Theme coverage. Keep low/context-only results preview-only; do not tune on exploratory human slider labels.
5. **Sequencing.** Validate transitions with reliable acoustic/semantic evidence; provide explainable sectioning, energy arc and peak placement; retain metadata fallback and confidence diagnostics.
6. **Booze or Boos! curation.** Refresh live snapshot before editing; validate per-track Halloween relevance and party energy; remove duplicates/blacklisted tracks; preview full sequence; use explicit confirmation-gated writes only.
7. **Operational reports.** Add quality, feedback, safety, run and recovery summaries; monitor workflow health and stale data.

## Acceptance criteria
No blocked/removed track reappears; no duplicate URIs; generated output is staged and validated before writes; live playlist is read back and matches; all writes are authorized and audited; sequencing never overstates weak evidence.

## Open proposals (not merged)

- [PR #121 — Offline sorter evaluation and listening-ingestion watchdog specification](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/121) is open/draft on `codex/sorter-evaluation-ingestion-watchdog`, diverged (10 ahead, 419 behind current main; mergeable=false). No workflow runs were found for its observed head; rebase and obtain CI before relying on it. The evaluation/watchdog remain proposed until runtime implementation and tests are verified.
- [PR #120 — Incremental Library enrichment and parallel sorter development](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/120) is open/draft on `codex/incremental-library-sorter-work`, diverged (5 ahead, 419 behind current main; mergeable=false). Old-head tests #41380622956 and security scan #41380622844 passed, but rebase and rerun before review. It does not complete sorter integration or authorize playlist writes.

## Next action (documentation-only priority)

Continue the documentation audit for this workstream: verify this roadmap, README, ACTIONS, linked technical guides, source overviews, tests, workflow references and evidence claims against the current repository. Record any newly discovered contradictions or stale paths here and in the central handoff. **Do not run provider checks/enrichment, alter generated data, modify playlists, or implement features while the documentation-only priority is active.**

## Next feature action after documentation pause

Audit the latest Daily code/workflows and current live playlist state, then work the P0 safety/publication items in [TRICKY_DAILY_TODO.md](../../../docs/TRICKY_DAILY_TODO.md). Separately keep fit scoring preview-only until evidence gates pass.
## Related records
[README](README.md) · [ACTIONS](ACTIONS.md) · [Daily cycle guide](../../../docs/TRICKY_DAILY_CYCLE.md) · [Daily backlog](../../../docs/TRICKY_DAILY_TODO.md)
