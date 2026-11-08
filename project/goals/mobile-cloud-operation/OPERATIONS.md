# Mobile SHIT Operations Without Codespaces

## Purpose

The GitHub issue-command workflow is SHIT's existing mobile-compatible control plane. ChatGPT can use the connected GitHub integration to prepare and submit owner-authored command issues, inspect workflow results, and verify repository state without opening a Codespaces terminal or using a personal PC.

The mobile Spotify authorization broker is a separate prerequisite for recovering the expired Spotify credential. It does not replace the playlist manager or issue-command workflow.

## Control issue contract

- Exact issue title: `SHIT — Playlist Control`
- The issue must be open.
- The issue sender must be the repository owner `TrickySturluson`.
- The issue body must be one JSON object.
- The command parser requires the exact allowed key set for each command. Extra or missing keys are rejected.
- The workflow reads the JSON from the issue body. A comment is not a substitute for editing the body; issue comments can retrigger the workflow but do not replace the command payload.
- The workflow is serialized under the `spotify-playlist-control` concurrency group.
- The workflow runs tests before execution, then persists state/audit and comments the result.
- Spotify writes remain governed by the existing manager: managed-playlist allowlist, lock state, preview, confirmation, snapshots, audit, rollback and live read-back.

## Supported command names

The authoritative schema is the `allowed` map in `scripts/spotify/spotify_playlist_cloud.py`. Current command names:

| Command | Required JSON keys | Purpose |
|---|---|---|
| `status` | `command` | Read manager status |
| `inspect` | `command`, `playlist_id` | Inspect one playlist |
| `lock_all` | `command` | Lock all playlists owned by the authenticated Spotify account |
| `lock` / `unlock` | `command`, `playlist_id` | Explicitly change one managed playlist's lock state |
| `preview` | `command`, `playlist_id`, `operations` | Stage generic playlist operations |
| `confirm` | `command`, `confirmation` | Apply the currently staged preview using its confirmation code |
| `undo` | `command` | Restore the latest eligible recovery snapshot |
| `daily_preview` | `command`, `playlist_id` | Stage a Daily cycle |
| `horror_preview` | `command`, `playlist_id` | Stage a horror expansion |
| `poker_preview` | `command`, `playlist_id` | Stage a Poker-themed addition |
| `booze5_preview`, `booze10_preview`, `booze20_preview` | `command`, `playlist_id` | Stage a themed Booze or Boos addition |
| `booze20_uri_preview` | `command`, `playlist_id`, `tracks` | Stage supplied Spotify track references |
| `sequence_preview` | `command`, `playlist_id` | Stage a sequence-based operation |
| `booze20_resolve_sources` | `command`, `sources` | Resolve approved source material |
| `cleanup_on`, `cleanup_off`, `cleanup_check`, `cleanup_run` | `command`, `playlist_id` | Manage or inspect duplicate cleanup |
| `health`, `enrich` | `command`, `playlist_id` | Run supported health/enrichment operations |

Example read-only status payload:

```json
{"command":"status"}
```

Example playlist inspection payload:

```json
{"command":"inspect","playlist_id":"4Ccwf3QRr8HfSsK48pTuBI"}
```

Example explicit unlock payload:

```json
{"command":"unlock","playlist_id":"4Ccwf3QRr8HfSsK48pTuBI"}
```

## ChatGPT mobile execution procedure

1. Read the current manager state, audit and relevant playlist data before choosing a command.
2. Preserve the user's exact scope. Do not infer unlock, removal, replacement, reorder or confirmation permission from a request to preview or stage.
3. Use the GitHub connector to create a new control issue or update the active control issue body with the exact JSON payload. Then verify the Actions event sender is `TrickySturluson`; if the connector's event identity is not the owner, stop and have the owner create/edit the issue in GitHub. Never weaken the owner check or put tokens/credentials in the issue.
4. Inspect the resulting Actions run and job logs. Do not treat a green trigger or queued run as successful execution.
5. Read the issue result comment and persisted manager state/audit. For a preview, report the exact staged changes and confirmation code.
6. Obtain explicit user approval for the exact consequential write. Only then submit the `confirm` command with the issued confirmation code.
7. After execution, verify the live Spotify playlist through SHIT and confirm post-snapshot, audit and state persistence. If the outcome is ambiguous, stop and inspect; never blindly retry a playlist write.

## What ChatGPT can do through the connected GitHub integration

- Read repository files, manager state, audit, workflow definitions and issue history.
- Create or update control issues using the exact JSON schema when the connected GitHub identity is authorized to act as the repository owner. The event sender identity must be verified before relying on the workflow.
- Read workflow runs, jobs and supported logs; inspect issue comments and persisted results.
- Update documentation and code on feature branches and prepare pull requests.
- Verify repository-side evidence after a workflow completes.

## What still requires a user action or is not exposed

- ChatGPT does not have an interactive Codespaces terminal through the current GitHub connector.
- The connected GitHub identity's ability to satisfy the workflow's `sender.login == TrickySturluson` gate has not yet been end-to-end verified; test with a read-only `status` command after Spotify reauthorization. If it fails, the owner must submit the issue manually from GitHub rather than weakening the gate.
- ChatGPT cannot read the Spotify refresh token or GitHub Actions secret values.
- Initial broker deployment requires the user to configure the Cloudflare Worker, dedicated GitHub App, exact Spotify/GitHub callback URLs and runtime secrets in their provider dashboards.
- The user must complete GitHub and Spotify OAuth consent in the phone browser. ChatGPT can then monitor and verify the read-only cloud health workflow.
- The user must explicitly approve every consequential playlist write; the mobile interface does not bypass the manager's confirmation gate.

## Current blocker

Issue [#175](https://github.com/TrickySturluson/spotify-helper-information-tracker/issues/175) currently contains an explicit unlock request for Poker Test. Its previous workflow failed because Spotify rejected the repository refresh token with `invalid_grant`. Do not retrigger that command until the mobile broker is deployed and a fresh read-only auth-health run succeeds.

## Acceptance test

Complete one end-to-end control operation from an Android phone while the user's PC is off:

1. Complete broker OAuth from the phone.
2. Verify the repository secret was updated without retrieving its value.
3. Verify two independent read-only auth-health runs.
4. Submit a read-only `status` command through the control issue.
5. Stage a harmless preview and inspect its exact contents.
6. Confirm that no playlist mutation occurs without the explicit confirmation code.
7. Execute one explicitly authorized test operation only after the user approves it, then verify live Spotify read-back and all state/audit/snapshot records.
