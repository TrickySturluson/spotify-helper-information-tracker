# SHIT Great Migration and Library Operations

The Great Migration consolidates existing SHIT music evidence into **The
Library**, the canonical interconnected catalogue of artist, album, and song
records under `assistant_data/music/library/`.

## Run locally

From the repository root:

```bash
python shit.py library status
python shit.py library preview
python shit.py library migrate --yes
python shit.py library audit
python shit.py library prepare --execute
```

The command group also accepts `migration` as an alias for `library`, and
`run` / `resume` as aliases for the idempotent offline migration:

```bash
python shit.py migration status
python shit.py migration preview
python shit.py migration run --yes
python shit.py migration resume --yes
python shit.py migration audit
```

- **status** reports indexed song, artist, and album counts.
- **preview** inventories the source catalogue and predicts migration input without writes.
- **migrate/run/resume** merge all saved track profiles and accessible Spotify playlist snapshots into The Library. When an existing indexed Library is present, a timestamped sibling backup is created before writing; an initial migration with no existing Library index has no prior Library to back up.
- **audit** checks canonical record files, cross-record relationships, and resolver aliases.
- **verify** performs harmless authenticated provider checks without changing the Library or playlists.
- **prepare --execute** performs the offline migration, then bounded provider enrichment, incremental Library syncs, and a final audit. Without `--execute`, preparation is read-only preflight.

The migration preserves every playlist membership while deduplicating repeated Spotify track IDs. Inaccessible playlists are counted and skipped. An accessible snapshot whose fetched count does not match its saved item list blocks execution rather than silently migrating partial data. Existing Library records and accumulated evidence are merged, not discarded.

The offline migration makes no provider requests and never edits Spotify playlists. A local `prepare --execute` refreshes read-only Spotify reference snapshots by default, then enriches missing metadata through bounded, checkpointed provider stages. The GitHub-hosted `prepare` and `prepare-preview` issue operations explicitly pass `--skip-spotify-refresh` and therefore use the already-saved playlist snapshots; refresh those separately through the Reference Library workflow when needed. Spotify API cooldowns and each provider's own retry behavior remain authoritative; do not add blind retries or unnecessary parallel requests.

## Run from ChatGPT

After this workflow is merged into the repository's default branch, ChatGPT can start an issue-triggered operation by creating an issue with one of these exact titles:

- \`[SHIT LIBRARY] status\`
- \`[SHIT LIBRARY] preview\`
- \`[SHIT LIBRARY] migrate\`
- \`[SHIT LIBRARY] prepare\`
- \`[SHIT LIBRARY] prepare-preview\`
- \`[SHIT LIBRARY] audit\`
- \`[SHIT LIBRARY] health\`
- \`[SHIT LIBRARY] verify\`
- \`[SHIT LIBRARY] backfill-playability\`
- \`[SHIT LIBRARY] verify-catalogue\`
- \`[SHIT LIBRARY] maintain-preview\`
- \`[SHIT LIBRARY] freshness-review\`
- \`[SHIT LIBRARY] validate-freshness-branch\`
- \`[SHIT LIBRARY] duration-evidence-preview\`
- \`[SHIT LIBRARY] duration-evidence-apply\`

The dedicated **SHIT — Great Migration** workflow processes issue requests only when the issue was opened by the repository owner and its title begins with \`[SHIT LIBRARY] \`. It validates the command against the 15-operation allowlist above. Manual Actions dispatch exposes the same allowlist as a required choice. Unsupported titles or commands fail validation.

**Operation and side-effect classes:**

- Read-only Library/report operations: \`status\`, \`preview\`, \`prepare-preview\`, \`audit\`, \`health\`, \`verify-catalogue\`, \`maintain-preview\`, \`freshness-review\`, \`validate-freshness-branch\`, and \`duration-evidence-preview\`.
- Provider credential verification: \`verify\` performs Spotify refresh-token exchange plus read-only account access, Last.fm API access, and optional Discogs/GetSongBPM checks. It never prints credential values and does not mutate the Library or playlists. If Spotify returns a replacement refresh token, the cloud workflow persists it to the repository Actions secret through the narrowly scoped GitHub App token before reporting success.
- Canonical Library/data writers: \`migrate\`, \`prepare\`, \`backfill-playability\`, and \`duration-evidence-apply\`. These can update generated/canonical Library state and publish repository changes. \`prepare\` performs bounded, checkpointed provider enrichment and final audit; the workflow deliberately skips Spotify reference refresh and uses saved snapshots.

The workflow posts the execution log back to the requesting issue and uploads the pre-migration backup as a 30-day workflow artifact when one is created. Successful write operations commit generated Library/enrichment data; read-only operations do not commit Library changes. Repository maintainers can also use the manual Actions dispatch.

The \`prepare\` issue operation requires \`LASTFM_API_KEY\` for its Last.fm enrichment stages. The GitHub workflow passes \`--skip-spotify-refresh\`, so this operation uses saved Spotify snapshots and does not require \`SPOTIFY_REFRESH_TOKEN\` for a reference refresh. Discogs and GetSongBPM remain optional. The \`verify\` operation separately requires \`SPOTIFY_CLIENT_ID\`, \`SPOTIFY_REFRESH_TOKEN\`, and \`LASTFM_API_KEY\`; optional provider credentials are checked when configured. The credential verification also runs automatically every day at 09:17 UTC. Results appear in the Actions run summary; failures create or update a single \`[SHIT ALERT] Daily credential verification failed\` issue, avoiding duplicate alerts.

Never put credentials or tokens in an issue title or body.

## Recovery and continuation

When an existing indexed Library is present, the offline migration creates a sibling backup named
`assistant_data/music/library.backup-<UTC timestamp>/`. A first-time migration with no existing `library_index.json` has no existing Library to copy. The cloud workflow uploads a generated pre-migration backup as an artifact before publishing generated data; inspect the run artifacts rather than assuming a backup exists for an initial import.
Aggregate source exports remain untouched, so the previous data layout remains
available for compatibility and rollback.

A failed provider stage stops the preparation pipeline without deleting its
checkpoints. Rerun `prepare --execute` to continue from the provider caches.
The migration itself is idempotent and can be rerun safely after repairing an
incomplete source snapshot.

## FILE OVERVIEW

- **Purpose:** Operational guide for the Great Migration and ChatGPT-triggered SHIT Library workflow.
- **Commands:** `python shit.py library {status,preview,migrate,audit,prepare}`.
- **Inputs:** Existing SHIT metadata exports and complete saved Spotify playlist snapshots.
- **Outputs:** Canonical artist/album/song records, lookup indexes, and enriched metadata exports.
- **Safety:** Backup first, complete-snapshot checks, bounded provider batches, checkpointed continuation, and no playlist writes.
