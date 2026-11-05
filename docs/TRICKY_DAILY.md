# Tricky Daily

Tricky Daily is the SHIT project's discovery-first daily rotation. It is a 30-track target, refreshed once per Eastern calendar day by the scheduled workflow.

## Recommendation composition

Daily uses a soft target mix:

| Candidate tier | Target share | Meaning |
|---|---:|---|
| Discovery | 45% | No matching Last.fm scrobbles in the familiarity archive |
| Rediscovery | 30% | One or two matching Last.fm scrobbles |
| Familiar | 25% | Three or more matching Last.fm scrobbles |

These are composition targets, not hard filters. Candidates are ranked within each tier; a tier shortage or artist cap is backfilled from the global score order. A maximum of two tracks per artist is retained. The existing recommendation minimum remains in force, so a thin pool stops the rotation instead of publishing a weak or undersized set.

The tier describes Last.fm familiarity, not whether a track is new to Spotify or new to the user in every sense. Missing archive matches are treated as discovery candidates, not proof that the user has never heard a song.

## Repeat exposure

The discovery candidate ledger is read as a separate exposure signal. Only records explicitly scoped to playlist ID `4yUVHSMQySfWeEowfIMcx7` affect Daily. Recent resurfacing adds a bounded, decaying score penalty; it does not blacklist a track. Eastern cycle dates are preferred over UTC timestamps around midnight and daylight-saving boundaries.

A track's actual outcome can reduce the repeat penalty:
- A save observed after the track was added clears the exposure penalty.
- Measured Spotify playback sessions or post-add Last.fm scrobbles reduce it.
- No observed play is neutral. Missing playback-tracker coverage is unknown, not evidence of disinterest.
- Exact removals continue to follow the separate playlist feedback / whitelist policy.

Last.fm scrobbles and Spotify playback-tracker sessions are never combined into one count.

## Read-only quality report

Run:

```bash
python scripts/spotify/spotify_daily_report.py
```

Optional input/output paths:

```bash
python scripts/spotify/spotify_daily_report.py \
  --input assistant_data/spotify/daily_feedback.json \
  --candidates assistant_data/recommendations/discovery_candidates.json \
  --output reports/tricky_daily_quality.json
```

The report includes:
- Current unique track records and addition events.
- Current liked status and post-add save conversion, with denominators restricted to observed tracks with an explicit unliked baseline.
- Playback-positive rate and measured sessions among tracks with playback observations.
- Post-add Last.fm scrobbles as a separate measure.
- Historical Daily discovery mix surfaced by tier, with unique track counts and feedback coverage.
- Neutral curator rotations separated from other removals.
- Coverage state and the reason/detail for unavailable playback tracking.

A missing observation never enters a positive-rate denominator. If there is no denominator, the report emits `null`, not zero.

## Safety and deployment

- Daily is the only playlist affected by the mix quotas and Daily exposure history.
- Other generated playlists retain their existing score-only selection behavior.
- The cycle checks the exact playlist ID, owner, name, managed-playlist state, and explicit unlocked state.
- It validates minimum recommendation count and URI uniqueness before playlist replacement.
- A pre-change snapshot and per-Eastern-date idempotency guard protect the rotation.
- The quality report is read-only and does not call Spotify or alter playlist state.

Recommendation changes are exercised by unit tests and GitHub Actions before they are considered production-ready. No live playlist change is implied by generating a preview or recording discovery evidence.
