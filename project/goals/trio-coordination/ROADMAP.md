# Trio Coordination — Roadmap

**Status:** In progress — Phase 1 protocol drafted in [PR #202](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/202); not merged. Task prompts and runtime handoffs are not yet updated or verified.  
**Last reviewed:** 2026-11-20

## User goal

The user wants to be able to leave SHIT unattended for roughly two weeks without returning to find two of the three scheduled workers silently nonfunctional. Each worker should check the next worker's readiness before handing off, diagnose blockers, and ultimately repair safe ones.

## Requirements

- Preserve non-overlapping ownership: Buddy = documentation; Jockey = current priority; Boots = other general engineering.
- Handoff order: Buddy → Jockey → Boots → Buddy.
- Check actual task enablement, schedule, next run, latest result, prompt, environment/access, repo state, branch/PR, exact-head checks, dependencies and scope conflicts.
- Use explicit READY / READY WITH WARNINGS / BLOCKED states.
- Do not infer success from enabled state, timestamps, green unrelated CI, or old reports.
- Keep handoffs actionable and auditable.
- Avoid repair loops, conflicting writes, and scope creep.
- Require human approval for secrets, permissions, production settings/deployments, external accounts, provider writes, irreversible changes and ambiguous repairs.

## Milestones

### Phase 1 — Readiness checks and handoffs
- [x] Define the protocol and checklist.
- [ ] Add the canonical protocol to repository first-contact instructions and goal index.
- [ ] Update Buddy, Jockey and Boots task prompts with the correct successor and read-only readiness procedure.
- [ ] Verify that all three tasks remain enabled with valid schedules and accessible environments.
- [ ] Exercise one full handoff cycle and record exact run IDs/results.
- [ ] Test disabled-task, failed-run, stale-branch and unavailable-environment classifications.

### Phase 2 — Bounded cross-repair
- [ ] Review Phase 1 evidence and failure patterns.
- [ ] Propose an explicit allowlist of reversible, low-risk cross-repairs.
- [ ] Keep schedule, prompt, environment, branch/PR ownership, credentials, permissions, deployments, provider writes and user data outside autonomous repair.
- [ ] Obtain user authorization for the specific cross-repair allowlist before enabling it.
- [ ] Test one harmless repair and prove one-attempt/loop-prevention behavior.

### Phase 3 — Extended-absence reliability
- [ ] Observe at least two complete cycles without overlapping writes or scope violations.
- [ ] Verify that a blocked worker is reported clearly and does not silently count as a successful handoff.
- [ ] Confirm that a human can reconstruct all three workers' state from task records and repository artifacts alone.
- [ ] Document operational limitations: scheduled tasks are not continuous monitors, and a handoff cannot guarantee an execution environment or external service remains available.

## Current verified observations (2026-11-20)

- Buddy automation `6aed3a70baf88191ab1dbfaa8f7dba91` is currently enabled. Its latest recorded run `54ea442a-ca08-8326-b910-2ba2f6a15428` completed but reported a blocker on obsolete Buddy PR #163 and said it paused the task. The current automation record must be treated as authoritative for enablement; it currently reports enabled. The task prompt was updated after that run to use `babel/chatgpt-buddy-v2`; a fresh run is needed to verify that it actually follows the new instructions.
- Jockey automation `6af1645551a48191900c77833073fdfd` is enabled, but latest run `aac1531b-53d0-832f-918c-9e21a3a46772` is recorded as failed with only the generic result "There was a problem with your scheduled task." Root cause is not yet known.
- Boots automation `Automation_2e1357c87e688191829bd2380047f46d` is enabled and has a next run scheduled for 2026-11-20 4:30 PM Eastern, but its latest recorded run is 2026-11-08 4:30 PM Eastern. This is a stale execution history, not proof that today's scheduled run will fail.
- These observations show why enablement alone is insufficient. Recheck them at implementation time; do not treat this dated snapshot as current after 2026-11-20.

## Acceptance criteria

Phase 1 requires all three task prompts to implement the protocol, at least one complete verified handoff cycle, and successful fault-classification tests. Phase 2 and extended-absence reliability remain separate gates.
