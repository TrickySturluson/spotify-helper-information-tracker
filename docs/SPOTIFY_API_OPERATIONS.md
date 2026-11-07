# Spotify API Operations & Recovery

## Current operating constraints

SHIT uses the Spotify Web API through the GitHub Actions secret `SPOTIFY_REFRESH_TOKEN` and repository variable `SPOTIFY_CLIENT_ID`. The identity that matters for cloud operations is the Spotify account represented by that refresh token, not whichever Spotify account is open in a browser.

Spotify's February 2026 Web API migration changed playlist item endpoints from `/tracks` to `/items`. Full playlist item reads are available only when the authenticated user owns the playlist or is a collaborator. A public playlist being visible in Spotify does not imply that its full item list is readable through the Web API.

## Saved-item lookup batching

Spotify's current **Check User's Saved Items** endpoint is `GET /me/library/contains?uris=...`. It accepts Spotify URIs and has a hard maximum of **40 URIs per request**. Use batches of 40 or fewer; a 50-item batch returns HTTP 400. SHIT centralizes this behavior in `spotify_daily_feedback.query_liked_status()`, used by both the Daily cycle's `liked_at_add` baseline and post-add liked-song observation. Regression tests cover 81-item query splitting and 60-item observation splitting.

A missing or failed liked lookup is unknown, not unliked. Do not backfill `liked_at_add` for a past addition from a later current-state observation; retain the distinction between baseline-at-add and later liked status.

Official reference: [Check User's Saved Items](https://developer.spotify.com/documentation/web-api/reference/check-library-contains).

## Playlist snapshot evidence is not listening evidence

A playlist item returned by the Spotify Web API proves only that the track appeared in the accessible playlist snapshot at that time. Playlist membership is source/context evidence; it is **not Spotify playback, likes, saves, or Last.fm scrobbles**. Do not use a playlist snapshot as a substitute for measured playback observations, liked/saved state, or the canonical Last.fm event archive. See [Per-recording music Library](PER_RECORDING_MUSIC_LIBRARY.md) for the field-level provenance and source-of-truth rules.

## Product requirement: GitHub-hosted and PC-independent operation

SHIT's product goal is a feature-rich, conversational ChatGPT–Spotify experience. GitHub is the central source of truth for this repository's code, configuration, durable workflow state, and documentation. GitHub Actions or another managed cloud runtime must perform all supported scheduled and on-demand SHIT operations. The user's personal PC must be allowed to stay off without stopping those operations.

The current GitHub Actions playlist-control workflow already runs remotely. The repository's broader ChatGPT-to-SHIT feature surface is a product goal; document a feature as available only after its GitHub-hosted path and user-facing integration have been implemented and verified.

### Centralization rules

- Make source and documentation changes on GitHub branches and pull requests. A local clone is optional and is not the deployment source of truth.
- Run scheduled and on-demand features from GitHub Actions or another managed service. Do not require a local PowerShell window, Python process, local checkout, or local cache for normal operation.
- Keep durable state, audit trails, and recovery artifacts in their established GitHub repository or workflow-artifact locations. Cloud jobs must resume from that state after a runner is discarded.
- Keep runtime credentials in GitHub Actions secrets/variables. Never commit them.
- Treat `.spotify_playlist_token.json` as an optional local authorization cache only. It is not the cloud credential source of truth. If a local refresh changes a token, cloud operations must not silently continue with a stale GitHub secret; use one explicit, documented synchronization path and verify the next read-only cloud run.

### Feature boundaries and acceptance

Playlist control, reference-library refresh, and other supported cloud operations must complete while the user's PC is off. A feature that depends on continuous polling from a personal device, such as the optional local playback tracker, is not PC-independent: migrate it to a permitted cloud data source or label it as local-only and exclude it from the always-on guarantee.

A feature meets this requirement when its GitHub-hosted workflow has been exercised with the user's PC off, uses only repository-hosted code and authorized secrets, persists required state centrally, and reports success or actionable failure through GitHub. No feature should be described as always-on until this evidence exists.

### Secure refresh-token rotation

Spotify may return a replacement refresh token during a refresh-token exchange. A GitHub Actions runner is temporary, so saving the replacement only to `.spotify_playlist_token.json` is not durable and leaves the next run holding a stale credential. SHIT now persists a replacement immediately to the repository Actions secret before continuing the API operation.

This requires a narrowly scoped GitHub App installed on this repository:

1. Create a GitHub App for this repository (webhook not required) and grant only the repository permission **Secrets: write**.
2. Install it on `TrickySturluson/spotify-helper-information-tracker` only.
3. Add repository variable `SHIT_GITHUB_APP_CLIENT_ID` containing the App Client ID.
4. Add repository secret `SHIT_GITHUB_APP_PRIVATE_KEY` containing the generated private key.
5. After the workflow change is merged, Actions mints a short-lived installation token scoped to this repository and `Secrets: write`. The token is passed only to the Spotify-authenticated steps; the refresh token itself is sent to `gh secret set` through stdin and is never logged or committed.

If the App token is unavailable, cloud refresh fails closed **before contacting Spotify**, preventing an unpersisted token rotation. The shared Spotify client retries the secret update up to three times and stops if GitHub does not confirm persistence. Local development remains independent of this GitHub App.

### Initial reauthorization (one-time recovery)

The current repository secret has been rejected by Spotify (`invalid_grant`), so token-rotation persistence cannot repair it retroactively. Reauthorize the Spotify playlist manager once, then manually bootstrap the new token into GitHub Actions:

1. In the trusted local/Codespaces checkout, stop any other process using port `8888` and delete `.spotify_playlist_token.json`.
2. Set `SPOTIFY_CLIENT_ID`, then run `python compat/spotify_playlist_manager.py list` and approve the requested scopes.
3. For a local checkout, the default callback is `http://127.0.0.1:8888/callback`. For Codespaces, forward port `8888`, set `SPOTIFY_CALLBACK_HOST=0.0.0.0`, and set `SPOTIFY_REDIRECT_URI` to the exact HTTPS forwarded URL ending in `/callback`; register that exact URI in the Spotify Developer Dashboard before authorizing.
4. Run `python compat/spotify_playlist_manager.py export-refresh-token` and update the repository Actions secret `SPOTIFY_REFRESH_TOKEN` directly in GitHub Settings. Never paste it into an issue, chat, commit, or log.
5. Run the read-only credential verification and playlist `status` command. Confirm a second independent Actions run succeeds; this proves the secret survives runner disposal.

The manual secret update is required only for initial recovery. Once the App and workflow are installed, cloud token rotation is automatic and PC-independent.

## Safe diagnostic sequence

1. Run the repository test workflow and security scan.
2. Use a read-only `status` command before any playlist-specific action.
3. Use read-only `inspect` only after Spotify's API cooldown has expired.
4. Confirm that the playlist appears in the authenticated account's own playlist collection and that its owner ID matches `GET /me`.
5. Do not unlock, preview a write, or confirm a write until the read-only checks pass.
6. Before applying any write, require a fresh preview, exact ordered-item comparison, an explicit confirmation code, an unlocked state, managed-playlist provenance, and a recovery snapshot.

## Rate limits and quota exhaustion

Spotify may respond with HTTP 429 and a `Retry-After` header. SHIT must not automatically retry a 429. Treat `QUOTA_EXCEEDED` as an app/developer-account-level cooldown and preserve the supplied interval. The manager accepts both delta-seconds and HTTP-date values, converts them to a UTC deadline, and blocks further requests until that deadline. If the header is missing or unparseable, it persists `manual_clear_required: true` and blocks client initialization and every subsequent API request until an operator verifies that the provider restriction has elapsed and manually clears the state. Do not repeatedly edit the control issue to retry the same command: each issue event starts another workflow and can consume more API quota. Spotify calculates ordinary rate limits over a rolling 30-second window; development-mode quota is separate, shared across the developer account, and grouped by endpoint buckets.

A 429 response is not evidence of a bad refresh token, wrong playlist owner, or missing playlist. Diagnose those only after the cooldown, using the actual HTTP status and response body. SHIT persists the observed cooldown in `.github/spotify_api_cooldown.json`; cloud workflow runs commit that file so subsequent commands can stop before sending another Spotify request. Numeric and HTTP-date deadlines expire automatically. A `manual_clear_required` state has no automatic expiry: do not remove it just to resume work. First verify with authoritative provider/account evidence that the restriction has elapsed, then delete `.github/spotify_api_cooldown.json` in a reviewed commit to `main`. The next request is permitted only after that explicit clearance.

## Request minimization

- Playlist control uses one exact `GET /playlists/{id}` lookup plus the authenticated-user check. If the exact lookup fails, it stops instead of scanning every page of `/me/playlists`.
- Reference-library sync refreshes the playlist catalog but reuses saved item pages whenever Spotify's `snapshot_id` is unchanged. Item pagination is performed only for new or changed playlists.
- The reference-library schedule runs daily rather than every six hours. Manual sync remains available when a refresh is genuinely needed.
- Catalog search makes one targeted request per query. A 429 is never retried inside a command; the central client records the cooldown and stops.
- Do not add arbitrary concurrency or guessed request-per-second limits. Spotify's rate limit varies by app and quota mode; use observed 429 responses, `Retry-After`, endpoint request counts, and the Developer Dashboard request graph to tune usage.
- Local list, lookup, and health commands should use cached files and must not construct a Spotify client.

## Request accounting

Every playlist-manager command emits one `SPOTIFY_REQUEST_METRICS=` JSON record to stderr at exit. It reports:
- Total Web API HTTP attempts, including pagination pages and 401 reauthorization retries.
- Counts grouped by HTTP method and normalized endpoint, with status-code counts.
- Aggregate elapsed HTTP time and per-endpoint elapsed time.

Query strings are deliberately omitted, and 22-character Spotify object IDs are redacted as `{id}`. This prevents playlist IDs and search terms from leaking into the metrics. Repeated calls to an `/items` endpoint expose pagination cost directly. A 429 is counted as an HTTP attempt and is also recorded in the cooldown state.

The metrics are per command/run, not a rolling developer-account total. Use the GitHub Actions log record to compare command costs over time; do not infer remaining quota from these counts because Spotify's quota buckets are shared across the app and other clients.

## Live sorter evidence

A sequence preview is not proof of musical transition quality. Review its evidence tiers and transition summary. In particular, a high count of limited/unknown evidence means the sequence is provisional even if the optimizer successfully generated a complete order. Do not describe estimated energy as measured audio analysis unless the corresponding source is present and verified.

## Recovery and rollback

- Never retry a failed confirmation blindly.
- If an edit has completed, verify the exact ordered URI list before considering it successful.
- Use the saved pre-change snapshot for recovery; preserve the artifact and audit trail.
- Keep protected playlists protected. Only SHIT-created playlists and explicit approved exceptions may be modified.
- If the Spotify API denies access, stop. Do not use browser scraping, undocumented endpoints, or alternate accounts to bypass Spotify's access rules.

## Official references

- [February 2026 Web API migration guide](https://developer.spotify.com/documentation/web-api/tutorials/february-2026-migration-guide)
- [Get Playlist](https://developer.spotify.com/documentation/web-api/reference/get-playlist)
- [Get Playlist Items](https://developer.spotify.com/documentation/web-api/reference/get-playlists-items)
- [Spotify playlist concepts](https://developer.spotify.com/documentation/web-api/concepts/playlists)

---

## FILE OVERVIEW

- **Purpose:** Operational guide for Spotify API access, rate limits, safe diagnostics, and recovery.
- **Applies to:** GitHub Actions playlist control, the local playlist manager, and the sequencer's live Spotify reads.
- **Key safeguard:** A Spotify 429 cooldown must be respected; it is not a reason to retry repeatedly.
- **Related code:** `scripts/spotify/spotify_playlist_manager.py`, `scripts/spotify/spotify_playlist_cloud.py`, and `scripts/spotify/spotify_playlist_sequencer.py`.
- **Related tests:** `tests/test_spotify_playlist_manager.py` and `tests/test_spotify_playlist_cloud.py`.
