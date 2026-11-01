# Public repository privacy guide

## Current publication model

SHIT is currently a **public** repository. The repository is more than source code: it publishes personal listening records and playlist activity. Keeping it public is a user choice, not a claim that this data is anonymous.

## Data visible to anyone

| Data family | Public details | Privacy consideration |
|---|---|---|
| Last.fm source archive (data/scrobbles.json) | Chronological scrobbles, exact timestamps, artist/track/album labels, MBIDs and URLs | Can reveal listening habits, interests, and approximate daily routines |
| Generated analytics (assistant_data/) | Rankings, first/last-seen dates, daily/monthly/UTC-hour patterns, inferred sessions and aggregates | Makes long-term habits easier to summarize and correlate |
| Spotify reference library | Playlist IDs, names, descriptions, item snapshots and dated snapshot history | Reveals playlist membership and curation activity |
| Playlist manager state/audit (.github/) | Playlist IDs/names, operation types, event timestamps, backup references and actor labels | Reveals when playlist-management actions occurred |
| Git history | Commit messages, timestamps, author/committer metadata and changed content | The current commit history includes a personal author email; future commits can use GitHub's noreply address |

The raw listening archive is intentionally retained as the canonical source for analytics. Do not describe it as anonymized or private while the repository remains public.

## Credential handling

- Keep Spotify access/refresh tokens, Last.fm API keys/secrets, GitHub tokens, .env files, private keys, and local credential caches out of commits.
- GitHub Actions should receive credentials only through repository secrets or variables, never literals in workflow YAML.
- The .gitignore includes common environment, certificate, and Spotify token filenames. Ignore rules do not untrack files that were already committed.
- Use GitHub secret scanning and push protection for this public repository where available.
- If a credential is ever committed, assume it is compromised: revoke/rotate it first. Removing it from the latest version does not remove it from Git history. History rewriting is a separate, disruptive cleanup and does not revoke the credential.

## Review findings (2026-10-31)

- Repository visibility was confirmed as public.
- The current tracked-file inventory contained no obvious .env, OAuth-token, credential, or private-key filenames.
- The inspected .gitignore, Spotify automation workflows, playlist-manager state/audit, and data manifests showed credentials passed through GitHub Actions secrets/variables rather than literal values.
- No obvious embedded credential was identified in those inspected files. GitHub code-search queries for common token/secret terms returned no matches, but this was not a complete scan of historical blob contents.
- A Gitleaks workflow has been added at `.github/workflows/public-repository-security.yml`. Its all-ref scan inspected 737 commits (218.74 MB) across the fetched branches/tags and reported **no leaks found**. This is strong evidence that the reachable history in those refs contains no detector-recognized secrets; it is not a guarantee against unsupported formats, unreferenced Git objects, or secrets that a scanner cannot recognize.
- The repository history contains hundreds of commits and exposes the personal author email in commit metadata. This review did not inspect every historical blob for leaked credentials; therefore it cannot certify that no secret was ever committed.
- The public dataset includes precise listening timestamps and identifiable playlist history. This is personal behavioral data, even though it is not an authentication secret.

## Recommendations

1. **Keep public only if the listening diary is intentionally public.** If exact timestamps and full listening history are acceptable to publish, no visibility change is needed. If not, make the repository private or redesign publication to export coarser/aggregated data while keeping the raw archive private.
2. **Use a GitHub noreply commit email going forward.** In GitHub **Settings → Emails**, enable **Keep my email addresses private** and, if desired, **Block command line pushes that expose my email**. For local Git commits, set `git config --global user.email "337022631+TrickySturluson@users.noreply.github.com"`. This protects future local commit metadata but does not erase email addresses from existing commits.
3. **Verify GitHub's built-in Secret Protection and repository push protection.** Public repositories are scanned by GitHub for free, but GitHub's March 2024 default-on rollout applied to new public repositories; existing public repositories were not automatically changed. Enable Secret Protection / secret-scanning alerts and repository push protection under **Settings → Security & quality → Advanced Security**, then review existing alerts. Personal-account push protection is a separate safeguard.
4. **Run a full history secret scan** with a dedicated scanner (for example, Gitleaks) before treating the repository as certified clean. Rotate any credential it finds; history cleanup should follow only after rotation.
5. **Keep local playback logs and OAuth caches untracked.** Publish only the derived playback aggregates that you explicitly want public.
6. **Review new data families before adding them.** Exact timestamps, stable account identifiers, private playlist contents, and raw playback segments deserve an explicit public/private decision.

## Scope and limitations

This guide records the state of the repository at the review date above. It is not a formal security audit, does not inspect GitHub account settings or repository secret values, and does not certify every historical Git object until the full-history scanner has completed and findings have been triaged. Revisit it when new data sources, workflows, or credential types are introduced.

## File overview

Purpose: Explain what personal data SHIT publishes while the repository is public, distinguish behavioral data from credentials, and record the security-review scope and recommendations.

Inputs: Current repository layout, tracked data families, workflow configuration, Git metadata, and the 2026-10-31 public-repository review.

Outputs: A public-data inventory, credential-handling rules, audit limitations, and maintenance recommendations.

Related: README.md, .gitignore, .github/README.md, data/README.md, and playback_data/README.md.
