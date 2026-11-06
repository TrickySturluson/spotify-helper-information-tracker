# Great Migration
> **Roadmap:** [ROADMAP.md](ROADMAP.md) is the durable plan and next-action reference. Read it before work; update it and [ACTIONS.md](ACTIONS.md) in the same session as implementation, testing, decisions, or blockers.
> **Current repository priority:** This workstream is paused for feature implementation while SHIT's documentation audit is active. Only documentation corrections and evidence reconciliation are permitted. Preserve this roadmap; resume its feature next actions only when the [central handoff](../../NEXT_WORK.md) and Maintainability & Documentation roadmap explicitly say documentation is complete.


## Goal

Safely migrate existing metadata into the canonical Music Library, preserve entity relationships and provenance, publish without losing concurrent changes, and verify integrity.

## Scope, decisions and constraints

Scope: prepare/dry-run; backup/checkpoint; offline import; identities, relationships, aliases, indexes and manifests; artifact recovery; publication and post-publish audit. Migration itself must not modify Spotify playlists or invent missing provider metadata.

**Status: FULL CATALOGUE PUBLISHED; STRUCTURAL HEALTH AND CONFIDENCE CI PASSED.** The canonical Library is published on `main` with 13,005 songs, 6,386 artists, and 7,861 albums. Run #18 successfully published enrichment commit `c55012f1d9707d9059be9096d0be88dbf50b1bcb`. Run #21 later completed runner-side prepare/audit but failed publication because it checked out stale issue-event SHA `b892f3b`; its generated output was not published. The workflow fix `21cc2ed` explicitly checks out latest `main` before running to avoid stale checkpoint/rebase conflicts.

**Independent verification:** read-only health run [#22](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41367899566) passed against the full catalogue: 13,005 songs, 6,386 artists, 7,861 albums; index counts matched; zero errors and zero warnings. Main-branch confidence audit and regression workflow [run](https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41368125489) passed, including 314 tests.

**Legacy source coverage:** all 11,130 unique legacy track-index IDs resolve through canonical source-track-ID or recording-MBID aliases; all 5,358 legacy artist names are represented. PR #79 merged permanent source-index coverage reporting. Raw Last.fm scrobble events remain in the separate event archive; they are not duplicated into one row per scrobble in the entity catalogue.

**Remaining work:** provider enrichment is incomplete. The published run #18 report measured duration coverage at approximately 91.1%, track profiles 1,778, artist profiles 3,998, album profiles 400, audio profiles 115, and lyric features 0. MusicBrainz encountered rate limits/503s, Last.fm track-tag requests returned HTTP 400, and Discogs/GetSongBPM credentials were absent. Treat these as the last measured run values, not fresh live counts; re-measure after the next safe enrichment pass. Continue only from durable checkpoints and avoid blind retries.

Run #17: https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41357689889  
Run #18 successful publication: https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41364145298  
Run #21 stale-checkout failure: https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41364361982

## Resume

Read [ACTIONS.md](ACTIONS.md) for dated work and evidence. Before another enrichment pass, inspect current provider checkpoints and PR #78 playability work; submit only one serialized prepare operation at a time. Run a fresh post-enrichment audit, health check, and status against published `main`. Never force-push or blindly resolve conflicts.

Commands: `python shit.py library status`, `preview`, `migrate`, `prepare`, `audit`, `health`, `confidence`. The GitHub issue workflow also exposes `[SHIT LIBRARY] prepare-preview`, which runs `python shit.py library prepare --skip-spotify-refresh` without `--execute`; it is a read-only preflight.

## Documentation and resume

After each meaningful action, update [ACTIONS.md](ACTIONS.md) with files changed, execution, exact verification and outcome. Update [the central handoff](../../NEXT_WORK.md) when priority or blockers change.
