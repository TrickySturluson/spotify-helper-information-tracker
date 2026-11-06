# Playlist Intelligence & Safety — Roadmap

**Last reviewed:** 2026-11-05  
**Status:** Active development; scoring preview is read-only and low-confidence. No write permission is implied by this roadmap.

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

## Next action (documentation-only priority)

Continue the documentation audit for this workstream: verify this roadmap, README, ACTIONS, linked technical guides, source overviews, tests, workflow references and evidence claims against the current repository. Record any newly discovered contradictions or stale paths here and in the central handoff. **Do not run provider checks/enrichment, alter generated data, modify playlists, or implement features while the documentation-only priority is active.**

## Next feature action after documentation pause
Audit the latest Daily code/workflows and current live playlist state, then work the P0 safety/publication items in [TRICKY_DAILY_TODO.md](../../../docs/TRICKY_DAILY_TODO.md). Separately keep fit scoring preview-only until evidence gates pass.

## Related records
[README](README.md) · [ACTIONS](ACTIONS.md) · [Daily cycle guide](../../../docs/TRICKY_DAILY_CYCLE.md) · [Daily backlog](../../../docs/TRICKY_DAILY_TODO.md)
