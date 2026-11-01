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
- **migrate/run/resume** merge all saved track profiles and accessible Spotify playlist snapshots into The Library. A timestamped backup is created before writing.
- **audit** checks canonical record files, cross-record relationships, and resolver aliases.
- **prepare --execute** performs the offline migration, then bounded provider enrichment, incremental Library syncs, and a final audit. Without `--execute`, preparation is read-only preflight.

The migration preserves every playlist membership while deduplicating repeated Spotify track IDs. Inaccessible playlists are counted and skipped. An accessible snapshot whose fetched count does not match its saved item list blocks execution rather than silently migrating partial data. Existing Library records and accumulated evidence are merged, not discarded.

The offline migration makes no provider requests and never edits Spotify playlists. The preparation pipeline separately refreshes the read-only Spotify reference snapshots and enriches missing metadata. Its provider batches are bounded and checkpoints are retained between runs. Spotify API cooldowns and each provider's own retry behavior remain authoritative; do not add blind retries or unnecessary parallel requests.

## Run from ChatGPT

After this workflow is merged into the repository's default branch, ChatGPT can start a project operation by creating a GitHub issue with one of these exact titles:

- `[SHIT LIBRARY] status`
- `[SHIT LIBRARY] preview`
- `[SHIT LIBRARY] migrate`
- `[SHIT LIBRARY] prepare`
- `[SHIT LIBRARY] audit`

The dedicated **SHIT — Great Migration** GitHub Actions workflow accepts only
issues opened by the repository owner and only the five allow-listed operations.
It runs the native `shit.py` interface, posts the execution log back to the
issue, and uploads the pre-migration backup as a 30-day workflow artifact.
Successful `migrate` and `prepare` runs commit generated Library/enrichment
data; read-only operations do not commit anything. Repository maintainers can
also use the workflow's manual Actions dispatch.

The `prepare` operation requires the existing `LASTFM_API_KEY` secret and
Spotify refresh credentials (`SPOTIFY_CLIENT_ID` repository variable and
`SPOTIFY_REFRESH_TOKEN` secret). Discogs and GetSongBPM remain optional.
Never put credentials or tokens in an issue title or body.

## Recovery and continuation

The offline migration creates a sibling backup named
`assistant_data/music/library.backup-<UTC timestamp>/`. The cloud workflow
uploads that directory as an artifact before publishing generated data.
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
