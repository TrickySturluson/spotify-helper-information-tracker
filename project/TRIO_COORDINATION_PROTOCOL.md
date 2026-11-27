# SHIT Trio Coordination Protocol

**Status:** Phase 1 — documented readiness checks; cross-repair is not yet enabled.  
**Workers:** Buddy (Babel documentation), Jockey (priority engineering), Boots (general engineering).  
**Handoff order:** Buddy → Jockey → Boots → Buddy.

## Purpose

The trio must remain operational during extended periods when the user is away. A scheduled task being enabled is not proof that it can start, access the repository, select safe work, or complete its next run. Each worker therefore checks the next worker's readiness before handing off.

This protocol is a coordination layer, not a fourth worker and not a replacement for the workers' existing scopes.

## Handoff cycle

| Outgoing worker | Next worker | Expected next window (Eastern) |
|---|---|---|
| Buddy | Jockey | 11:00 AM daily |
| Jockey | Boots | 4:30 PM daily |
| Boots | Buddy | 9:00 AM daily |

The automation service's current task configuration is authoritative for actual schedules. Times above are the intended order, not a substitute for checking the live schedule. Flexible schedules may run later than their nominal target.

Each outgoing worker checks the next worker's current automation record and latest result, then inspects the repository state needed by that worker. It must not infer readiness from an enabled toggle, a prior green run, or a scheduled timestamp alone.

## Readiness checklist

For the next worker, inspect:

1. **Automation:** task exists, is enabled, has a valid recurring schedule, and has a future next-run time.
2. **Execution history:** latest run status/result; identify repeated failures, stale runs, or a run that never started. Distinguish a completed task from a successful task.
3. **Instructions:** the saved task prompt still identifies the correct repository, role, scope, safety rules, and persistent branch/PR policy.
4. **Environment and access:** inherited/selected execution environment is not known to be disconnected; the connected GitHub capability can read the relevant repository state. Never test access by touching secrets or performing a write.
5. **Repository readiness:** current main, open PRs, the worker's expected branch, branch ancestry, changed files, and relevant exact-head checks are consistent with its instructions.
6. **Dependencies:** required handoff files, roadmaps, runbooks, tests, and workflows exist and are readable. Check only what is relevant to the next worker's next run.
7. **Scope separation:** the next worker's task does not collide with another active PR or current priority assignment.
8. **Recovery safety:** identify any unresolved user-only gate, secret/configuration dependency, provider restriction, or production boundary before the next worker starts.

Record one status:

- **READY:** all required checks pass and the next run has a clear safe starting point.
- **READY WITH WARNINGS:** the worker can proceed safely, but a non-blocking issue should be visible in its handoff.
- **BLOCKED:** a required prerequisite is absent, the task is disabled, access is unavailable, the branch/PR state is unsafe, or the next task cannot be selected without conflicting work or crossing an authorization boundary.

## Broken-chain fallback

A failed worker must not silently break the monitoring chain. If the immediate successor's latest run is failed, incomplete, missing, or has not produced a report after its expected window, the outgoing worker must also perform a lightweight readiness check of the following worker in the cycle. For example, if Jockey has failed, Buddy checks both Jockey and Boots; it still reports Jockey's failure and does not assume Boots has taken over Jockey's work. This is detection redundancy, not permission to reassign work or change another task.

The next worker must also perform its normal startup checks on its own branch, task scope, and dependencies. A predecessor's READY result never substitutes for the worker's own preflight.

## Phase 1 authority: inspect and prepare

Phase 1 is read-only with respect to the next worker's automation configuration and owned branch/PR.

The outgoing worker may:
- inspect the next worker's automation record, prompt, schedule, latest result and environment status;
- inspect the repository, current handoffs, branches, PRs, and relevant CI;
- repair a defect inside its own existing scope and owned branch/PR when the normal worker policy permits it;
- leave a precise, actionable readiness report for the next worker;
- identify the smallest safe repair and the exact evidence needed to verify it.

The outgoing worker must not:
- enable, disable, reschedule, or rewrite another worker's automation;
- edit another worker's prompt, environment selection, branch, or PR;
- bypass branch ancestry or force-push/rebase another worker's branch;
- merge, approve, mark ready, or close another worker's PR;
- change secrets, permissions, production configuration, external account settings, deployments, or provider data;
- take over the next worker's implementation scope.

If the next worker is blocked by something outside the outgoing worker's authority, report the blocker and the owner action. Do not disguise a blocker as READY.

## Phase 2: bounded cross-repair (not yet enabled)

Cross-repair will be considered only after Phase 1 has been exercised and reviewed. The following are candidate repairs for a future, explicitly authorized allowlist; none is enabled in Phase 1:

- **Task enablement/schedule:** restore a task to a previously user-approved enabled state and documented schedule only when there is no evidence of an intentional user pause. If intent is ambiguous, escalate.
- **Task prompt:** restore a damaged or stale prompt only from a versioned, previously approved snapshot. Do not invent or broaden another worker's scope. Save the before/after versions and verify the resulting task record.
- **Persistent branch:** if the successor has no open PR and no active run, preserve the exact old head on a separate archival branch before creating a fresh worker branch from current main. Never delete or force-push the old branch. If an open PR exists, do not cross-repair its branch; leave it to the owner or ChatGPT technical lead.
- **Repository prerequisites:** repair stale handoff links or missing non-sensitive documentation prerequisites when the fix is reversible and the repairing worker has permission to change that path.

Cross-repair must never include merging, approving, marking ready, or closing another worker's PR; changing code outside the repairing worker's remit; secrets, credentials, permissions, security controls, production deployments, external accounts, provider writes, playlist/Library data, or irreversible actions.

Any future allowlist must be explicitly documented, tested on harmless scenarios, and authorized before automation prompts are changed. Each repair must preserve a recoverable before-state, make at most one attempt per blocker, and verify the successor's resulting readiness.

## Loop and conflict prevention

- One readiness pass per outgoing run.
- At most one repair attempt for a specific blocker during a handoff cycle.
- Do not retry an unchanged failure on every cycle; require new evidence or a changed prerequisite.
- If the same blocker appears in two consecutive handoffs, escalate it rather than attempting a third automatic repair.
- Never let two workers edit the same branch, PR, or file concurrently.
- Each worker continues to own its own branch and draft PR. Buddy remains documentation-only; Jockey owns the single priority implementation; Boots owns independent general engineering.
- If the Jockey priority is unclear, Boots must not guess or overlap. It should report the conflict and choose only clearly independent work.

## Handoff report format

Every outgoing run reports:

- outgoing worker and next worker;
- next task's enabled state, schedule and next-run timestamp;
- latest run ID, recorded status and concise failure/success evidence;
- expected branch/PR and current head/base/ancestry;
- exact-head CI status where relevant;
- environment/access status (connected, offline, unknown, or unavailable);
- readiness status: READY / READY WITH WARNINGS / BLOCKED;
- blocker, safe repair attempted (if any), verification result, and owner action;
- next worker's safest first action.

Do not include secrets, token values, OAuth codes, private keys, or sensitive account data in handoffs.

## Acceptance criteria

Phase 1 is complete only when:
- all three saved task prompts contain the same handoff protocol and correct next-worker mapping;
- each worker can inspect its successor's automation record and repository readiness without changing the successor's configuration or branch;
- each run reports a truthful readiness status and exact evidence;
- a full Buddy → Jockey → Boots → Buddy cycle has been observed, with no overlapping writes or scope violations;
- a simulated disabled-task, failed-run, stale-branch, and unavailable-environment condition is classified BLOCKED rather than silently treated as ready.

Phase 2 is a separate milestone. Do not enable cross-repair merely because Phase 1 documentation exists.
