# Spotify API Operations & Recovery

## Current operating constraints

SHIT uses the Spotify Web API through the GitHub Actions secret `SPOTIFY_REFRESH_TOKEN` and repository variable `SPOTIFY_CLIENT_ID`. The identity that matters for cloud operations is the Spotify account represented by that refresh token, not whichever Spotify account is open in a browser.

Spotify's February 2026 Web API migration changed playlist item endpoints from `/tracks` to `/items`. Full playlist item reads are available only when the authenticated user owns the playlist or is a collaborator. A public playlist being visible in Spotify does not imply that its full item list is readable through the Web API.

## Safe diagnostic sequence

1. Run the repository test workflow and security scan.
2. Use a read-only `status` command before any playlist-specific action.
3. Use read-only `inspect` only after Spotify's API cooldown has expired.
4. Confirm that the playlist appears in the authenticated account's own playlist collection and that its owner ID matches `GET /me`.
5. Do not unlock, preview a write, or confirm a write until the read-only checks pass.
6. Before applying any write, require a fresh preview, exact ordered-item comparison, an explicit confirmation code, an unlocked state, managed-playlist provenance, and a recovery snapshot.

## Rate limits and quota exhaustion

Spotify may respond with HTTP 429 and a `Retry-After` header. SHIT must not automatically retry a 429. Treat `QUOTA_EXCEEDED` as an app/account-level cooldown, preserve the supplied retry interval, and stop making Spotify requests until that interval has elapsed. Do not repeatedly edit the control issue to retry the same command: each issue event starts another workflow and can consume more API quota.

A 429 response is not evidence of a bad refresh token, wrong playlist owner, or missing playlist. Diagnose those only after the cooldown, using the actual HTTP status and response body. SHIT persists the observed cooldown in `.github/spotify_api_cooldown.json`; cloud workflow runs commit that file so subsequent commands can stop before sending another Spotify request. The guard expires automatically at the recorded deadline.

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
