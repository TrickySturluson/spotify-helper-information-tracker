# Trio Coordination — Roadmap

**Status:** Phase 1 partially implemented in [draft PR #202](https://github.com/TrickySturluson/spotify-helper-information-tracker/pull/202); all three saved prompts now contain successor-readiness instructions, but a full handoff cycle has not been verified and two workers remain disabled.  
**Last reviewed:** 2026-11-22

## User goal

The user wants to leave SHIT unattended for roughly two weeks without returning to find two of the three scheduled workers silently nonfunctional. Each worker should check the next worker's readiness before handing off, diagnose blockers, and ultimately repair safe ones.

## Requirements

- Preserve non-overlapping ownership: Buddy = Babel documentation; Jockey = current priority; Boots = other general engineering.
- Handoff order: Buddy → Jockey → Boots → Buddy.
- Check actual task enablement, schedule, next run, latest result, prompt, environment/access, repo state, branch/PR, exact-head checks, dependencies and scope conflicts.
- Use explicit READY / READY WITH WARNINGS / BLOCKED states.
- Do not infer success from enabled state, timestamps, green unrelated CI, or old reports.
- Keep handoffs actionable and auditable.
- If the immediate successor has failed or missed its run, perform a lightweight fallback check of the following worker so one failed task does not break the monitoring chain.
- Avoid repair loops, conflicting writes, and scope creep.
- Require human approval for secrets, permissions, production settings/deployments, external accounts, provider writes, irreversible changes and ambiguous repairs.

## Milestones

### Phase 1 — Readiness checks and handoffs
- [x] Define the protocol and checklist.
- [ ] Merge the canonical protocol into repository first-contact instructions and documentation navigation; PR #202 is still draft and 12 commits behind main.
- [x] Add the correct successor and read-only readiness procedure to all three saved task prompts.
- [ ] Verify all three tasks are enabled with valid schedules and accessible environments; Jockey and Boots are currently disabled.
- [ ] Exercise one full handoff cycle and record exact run IDs/results; Buddy's latest run did not include a successor-readiness report.
- [ ] Test disabled-task, failed-run, stale-branch and unavailable-environment classifications in actual worker reports.
- [ ] Reconcile overlapping documentation files between PR #201 and #202 before either PR is merged.

### Phase 2 — Bounded cross-repair
- [ ] Review Phase 1 evidence and failure patterns.
- [ ] Propose an explicit allowlist of reversible, low-risk cross-repairs: restoring a documented task enablement/schedule, restoring an approved prompt snapshot, archiving and refreshing a stale branch with no open PR, and fixing non-sensitive documentation prerequisites.
- [ ] Keep ambiguous pauses, environment changes, open-PR branch changes, credentials, permissions, deployments, provider writes and user data outside autonomous repair.
- [ ] Obtain user authorization for the specific cross-repair allowlist before enabling it.
- [ ] Test one harmless repair and prove backup, read-back, one-attempt and loop-prevention behavior.

### Phase 3 — Extended-absence reliability
- [ ] Observe at least two complete cycles without overlapping writes or scope violations.
- [ ] Verify that a blocked worker is reported clearly and does not silently count as a successful handoff.
- [ ] Confirm that a human can reconstruct all three workers' state from task records and repository artifacts alone.
- [ ] Document operational limitations: scheduled tasks are not continuous monitors, and a handoff cannot guarantee an execution environment or external service remains available.

## Current verified observations (2026-11-22)

- **Buddy** automation `6aed3a70baf88191ab1dbfaa8f7dba91` is enabled. Its latest run `e560322d-6ac8-8332-84aa-98b2b5816aeb` completed on 2026-11-22, but the report focused on PR #201 and did not contain the required successor-readiness handoff. The saved prompt does contain the Buddy → Jockey mapping and fallback to Boots. Buddy's report marked PR #201 NEEDS CHANGES and said final-head verification was outstanding.
- **Jockey** automation `6af1645551a48191900c77833073fdfd` is disabled. Its latest run `ae49786b-46e0-8321-949d-9f139020df47` disclosed two accidental commits directly to `main`: `a372f8d49817783a2ba9e9bed0f6b24f071a7cc1` (Daily recommendation-memory guide) and `649690ce545094cc0f5d19a4a57b17eac20319dd` (initial memory-ledger module). The module is explicitly incomplete and not integrated into Daily or validated. Do not revert or extend these commits without reviewing downstream dependencies.
- **Boots** automation `Automation_2e1357c87e688191829bd2380047f46d` is disabled. Its latest run `a030ee14-e434-832d-a8cc-b462d8e88ed7` correctly stopped before writing because its persistent branch was stale. It has no matching open PR.
- All three saved prompts contain the Phase 1 successor-readiness section and the correct handoff mapping. This confirms configuration text, not successful execution of the handoff behavior.
- **Buddy branch / PR #201:** branch `babel/chatgpt-buddy-v2` is 64 commits ahead and 12 behind current `main`; PR #201 remains open/draft. Exact-head `452a6d332f064b12aeecafd04ad8e87585ec54d9` checks show Mobile Auth Broker Tests failed, Daily curator tests failed, and the public repository security scan passed. The Daily test failure is `test_documentation_index_lists_every_technical_guide`: the branch's `docs/README.md` does not link the newer `TRICKY_DAILY_RECOMMENDATION_MEMORY.md` guide. The broker workflow failed in the step `Test broker access-token client and manager mode`; its underlying diagnostic still needs isolation. Do not mark PR #201 ready.
- **Jockey branch / PR #200:** branch `engineering/priority` is 67 commits ahead and 6 behind; PR #200 remains open/draft. Its branch contains substantial Daily cycle and recovery work. The direct-to-main commits above are outside the PR branch. Do not re-enable Jockey until the accidental mainline changes and branch state have been reviewed and the worker's next write is safely scoped.
- **Boots branch:** `engineering/general` is 14 commits ahead and 83 behind current `main`, with no matching open PR. Preserve its head; do not reset, force-push or rebase it as an automated repair.
- **Coordination PR #202:** branch `coordination/trio-readiness-handoffs` is 32 commits ahead and 12 behind current `main`. It overlaps PR #201 on four shared files: `docs/BABEL_CHATGPT_BUDDY.md`, `docs/README.md`, `project/ACTIVE_SESSION_BRIEF.md`, and `project/LOOSE_ENDS.md`. Keep those changes unreconciled and do not merge either PR until reviewed together.
- The live automation records report Buddy enabled, Jockey disabled, and Boots disabled. These current records supersede the 2026-11-20 historical audit below.

## Historical observations — 2026-11-20 (superseded)

The initial audit found Buddy enabled, Jockey enabled with a generic failed run, and Boots enabled with stale execution history. At that time, Buddy was 14 ahead/0 behind, Jockey 40 ahead/2 behind, and Boots 14 ahead/71 behind. Those branch counts and task states are no longer current.

## Acceptance criteria

Phase 1 requires all three task prompts to implement the protocol, at least one complete verified handoff cycle, and successful fault-classification tests. Phase 2 and extended-absence reliability remain separate gates.
