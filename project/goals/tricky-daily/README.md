# Tricky Daily
> **Current repository priority:** This workstream is paused for feature implementation while SHIT's documentation audit is active. Only documentation corrections and evidence reconciliation are permitted. Preserve this roadmap; resume its feature next actions only when the [central handoff](../../NEXT_WORK.md) and Maintainability & Documentation roadmap explicitly say documentation is complete.


Tricky Daily is the user's daily rotating 60-track discovery playlist. Its goal is to be reliably refreshed while retaining taste relevance, meaningful variety, and strict protection of explicit user feedback.

## Scope
This workspace owns Tricky Daily candidate generation, playlist publication, cycle scheduling/recovery, Daily-specific feedback and trend context, description rotation, and operational verification. The broader playlist intelligence and safety workstream owns shared playlist-fit scoring and sequencing design.

## Non-negotiable boundaries
- Exactly 60 unique valid tracks for a successful cycle.
- Blacklist and removed-track exclusions are absolute, including forced runs and every retry/fallback.
- Reconcile whitelist/blacklist and live playlist state before each run; a stale snapshot must not reverse user decisions.
- Artist diversity may be relaxed progressively only after retrying alternatives. Never relax uniqueness or exclusions.
- Forced runs bypass the schedule gate only, not safety or verification.
- Update and read back the rotating description on successful forced and scheduled cycles.
- Last.fm scrobbles, measured Spotify playback, likes/saves, playlist exposure and removals are distinct evidence.
- Missing playback coverage and an unplayed exposed track are not automatically negative preference.
- Only the explicitly authorized Tricky Daily playlist may be written under its documented controls.

## Implementation map
| Concern | Maintained implementation / evidence |
|---|---|
| Current discovery candidate generation | scripts/spotify/spotify_discovery.py (called by the cycle with target size 60) |
| 60-track assembly, validation and publication | scripts/spotify/spotify_daily_cycle.py |
| Legacy/alternate candidate builder | scripts/spotify/spotify_daily_playlist.py (30-track builder; not the live 60-track cycle) |
| Cycle orchestration and recovery state | scripts/spotify/spotify_daily_cycle.py |
| Feedback learning | scripts/spotify/spotify_daily_feedback.py and assistant_data/spotify/daily_feedback.json |
| Read-only live preflight | scripts/spotify/spotify_daily_preflight.py |
| Trend context | scripts/spotify/spotify_listening_trends.py |
| Schedule and operational semantics | [TRICKY_DAILY_CYCLE.md](../../../docs/TRICKY_DAILY_CYCLE.md) |
| Future improvements and P0/P1 backlog | [TRICKY_DAILY_TODO.md](../../../docs/TRICKY_DAILY_TODO.md) |
| Automated workflows | .github/workflows/spotify-daily-*.yml |
| Regression coverage | tests/test_spotify_daily_*.py |

## How to resume safely
1. Read the Daily roadmap, action history, and current project handoff.
2. Read the Daily TODO and cycle guide; inspect the current implementation and tests rather than assuming the docs reflect current main.
3. Inspect the latest relevant workflow runs and live preflight. Distinguish successful candidate generation, Spotify write acceptance, read-back verification, description verification and completed cycle state.
4. Inspect current live playlist contents and playlist-manager authorization/lock state before proposing a write.
5. Preview and validate the exact 60-track set, blacklist/whitelist reconciliation, deduplication, artist fallback, and description behavior.
6. Only execute a live write when explicitly authorized and all safety gates pass. Read back the live playlist and record exact evidence.
7. Update this roadmap and ACTIONS in the same session; update the cross-project handoff if priorities or blockers change.

## Evidence standard
A passing unit test does not prove a live Spotify operation. A successful API write does not prove read-back verification. A pending-verification state is not a completed cycle. Record exact commit, workflow run, test results, live snapshot/read-back and any failed step separately.

## Open proposals (not merged)

- [PR #159 — Tricky Daily DST schedule gating](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/159) is open and not merged. Current main still uses combined 04:00/05:00 UTC cron expressions and a local-hour gate; strict cron-to-Eastern-offset matching is proposed in the PR, not current behavior.
- [PR #160 — Exposure-aware Daily discovery and quality reporting](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/160) is open and not merged. Its 45/30/25 mix, exposure-decay selection changes and new read-only report are proposals until merged and verified.
- [PR #158 — Discover Weekly exposure and feedback tracking](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/158) is open and not merged; it is adjacent listening-analytics work, not a Daily playlist write feature.

## Related work
[Playlist Intelligence & Safety](../playlist-intelligence/README.md) owns shared fit-model and sequencing behavior. Daily-specific requirements and acceptance criteria remain in this workspace, even when shared modules implement them.