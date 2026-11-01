# SHIT Project Log

Chronological handoff record for substantial project work. New entries go at the top, newest first.

## 2026-11-01 — Project control centre proposed

- **Goal:** establish one durable place to track work completed, work in progress, next steps, blockers, and metadata that needs another provider lookup.
- **Changes proposed:** add `project/NEXT_WORK.md`, this log, and a retry-queue specification; keep the machine-maintained retry queue beside music metadata state, not inside the canonical Library records.
- **Safety:** project notes are separate from music data; retry entries must preserve the distinction between definitive negative results and transient/provider failures.
- **Verification:** documentation structure only at this stage. The retry queue still needs an implementation that builds it from canonical records and provider checkpoints.
- **Related work:** read-only Library coverage planner is proposed in PR #65: https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/65
- **Migration note:** Great Migration run #17 failed in the Git publish/rebase stage. Its output artifact and backup must be inspected before attempting recovery or another write-heavy migration. Run: https://github.com/TrickySturluson/spotify-helper-information-tracker/actions/runs/41357689889

## Entry template

### YYYY-MM-DD — Short task name
- **Goal:**
- **Work completed:**
- **Files/workflows affected:**
- **Verification:**
- **Outcome:** complete / partial / blocked
- **Next action:**
- **References:** PRs, commits, workflow runs, issues
