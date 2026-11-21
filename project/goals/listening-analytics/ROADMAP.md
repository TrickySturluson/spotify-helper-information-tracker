# Listening Analytics & Evidence Sources — Roadmap

**Last reviewed:** 2026-11-21  
**Status:** Architecture and source rules established; fresh coverage and semantic verification required.

## Purpose
Provide accurate historical listening analytics and prospective playback evidence without double-counting or pretending incomplete tracker coverage is complete.

## Non-negotiable source semantics
- Last.fm scrobbles are the historical source of truth.
- Spotify playback tracking is optional prospective evidence with coverage gaps.
- Missing tracker data means unknown, not zero.
- Likes/saves, recommendations, playlist additions, and playback are separate event types.
- Never merge unlike events or double-count the same listening evidence.

## Roadmap
1. **Fresh source audit — next.** Verify canonical scrobble archive/manifests and tracker coverage separately; timestamp all totals.
2. **Historical analytics.** Validate daily/monthly/yearly, artist/track/album rankings, sessions, durations, and timezone semantics against canonical events.
3. **Playback tracker reliability.** Document capture coverage, gaps, resume behavior, and whether data is local-only or cloud-hosted; do not imply always-on tracking until verified.
4. **Cross-source reconciliation.** Link identities and detect overlap without replacing Last.fm history or inventing missing plays.
5. **Evidence-aware recommendation features.** Provide recency/momentum signals with coverage/confidence, never treating missing tracker observations as dislikes.
6. **SHIT Wrapped generator — planned.** Build a repeatable annual and all-time listening report from the canonical archive. Include top artists/tracks/albums, listening volume and time, year/month/day patterns, discovery/diversity measures, notable milestones, playful awards and evidence-backed listening-personality summaries. Support year selection and an all-time edition; regenerate from refreshed archive data rather than hard-coded snapshots. Clearly label the source, covered period, archive freshness, timezone, duration-estimation method, and missing/incomplete months or tracker coverage. Keep Last.fm scrobbles authoritative for historical rankings and show Spotify playback-tracker metrics separately only where coverage is verified. Never present estimates as measured listening time or incomplete periods as complete.
7. **Regression and reporting.** Test dedupe, event typing, unknown-vs-zero, timezone boundaries, source attribution, and Wrapped calculations against canonical fixtures.

## Acceptance criteria
Every metric names its source and period; tracker coverage is visible; no event type is silently converted into a scrobble; totals reconcile to canonical data.

## Acceptance criteria
Every metric names its source and period; tracker coverage is visible; no event type is silently converted into a scrobble; totals reconcile to canonical data.

For SHIT Wrapped specifically:
- Annual and all-time editions are reproducible from the same versioned archive inputs.
- Rankings and totals reconcile to canonical scrobbles for the selected period.
- Duration figures distinguish measured playback from estimates and disclose the calculation.
- Missing dates/months, stale inputs, and incomplete tracker coverage are surfaced rather than silently filled or hidden.
- Playful awards/personality copy is derived from actual metrics, avoids unsupported claims, and remains clearly editorial rather than a formal statistic.
- Regeneration is automated or has a documented one-command workflow; generated reports record their input snapshot/time.

## Next action (documentation-only priority)

Continue the documentation audit for this workstream: verify this roadmap, README, ACTIONS, linked technical guides, source overviews, tests, workflow references and evidence claims against the current repository. Record any newly discovered contradictions or stale paths here and in the central handoff. **Do not run provider checks/enrichment, alter generated data, modify playlists, or implement features while the documentation-only priority is active.**

## Next feature action after documentation pause
Inspect current archive manifest, analytics outputs, tracker workflow/runtime and coverage report; publish fresh separately sourced baselines. Then design the Wrapped report schema and calculation/test fixtures before implementing presentation or scheduled generation.

## Related records
[README](README.md) · [ACTIONS](ACTIONS.md) · [Discovery](../discovery-recommendations/ROADMAP.md)
