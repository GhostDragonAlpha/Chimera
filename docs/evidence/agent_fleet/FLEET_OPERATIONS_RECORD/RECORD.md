# FLEET OPERATIONS RECORD — 2026-09-11 (slot-based parallel execution)

Lead: `glm53-lead-02` (epoch 5; Alan-appointed; predecessor `glm53-fresh-01`
self-yield error recorded at rev 492 and recovered via documented vacant
election at rev 499). Controller: live service, deployed reviewed source
`d012b4b1` (deployments `slot-binding-d012b4b1`).

## Overlap evidence: three workers + lead lane concurrently

Controller events (revision-stamped, `E:\ChimeraWork\control\state.sqlite`):

```
508 claim  subagent-worker-01 gov01-evidence-reconcile-01     (slot 2)
509 claim  subagent-worker-02 fleet-catalogue-repin-01        (slot 3)
510 claim  subagent-worker-03 fleet-docs-operating-model-01   (slot 4)
511-513 provision_slot SUPERVISOR (task/generation-bound, new controller)
514-516 create/claim/provision dyad-provider-interface-01     (slot 5, lead lane)
517 submit_review glm53-lead-02      dyad-provider-interface-01
518 submit_review subagent-worker-03 fleet-docs-operating-model-01
519 submit_review subagent-worker-01 gov01-evidence-reconcile-01
520 review_requeue + 521 resubmit (dyad correction cycle)
522-524 integrate + release (dyad lane; slot 5 released)
525 submit_review subagent-worker-02 fleet-catalogue-repin-01
526-527 integrate fleet-docs-operating-model-01 (PR #45) + release slot 4
528-531 review-slot handoff gov01 (slot 2 freed while REVIEW), integrate PR #46
```

Wall-clock intervals (git commit timestamps, local -0500; claims ~22:37-22:39):

| Lane | Activity interval | Deliverable |
|---|---|---|
| subagent-worker-01 (slot 2) | 22:39 → 22:58 commit → submit 519 | GOV01 matrix + evidence (PR #46) |
| subagent-worker-02 (slot 3) | 22:39 → 23:0x commit → submit 525 | catalogue repin (PR #47) |
| subagent-worker-03 (slot 4) | 22:39 → 22:52 commit → submit 518 | operating-model docs (PR #45) |
| glm53-lead-02 (slot 5) | 22:40 → 22:49/22:59 commits → submit 517/521 | DYAD provider interface (PR #44) |

All four intervals overlap 22:39–22:52; workers 1 and 2 continued past
worker 3's submission. Each lane: distinct worktree, distinct slot, own
session/PR. Review submission did not block other lanes; gov01's slot was
freed by `release_review_slot` while its review was pending (rev 528-531),
and the freed slot 2 was immediately re-claimed by the next task
(fleet-review-followups-01) — capacity reuse demonstrated.

## Injected startup failure (drill, no worker lane touched)

- `launch_worker.py` with an executor profile naming a nonexistent executable:
  `REFUSED: ValueError`, exit 2, **no session file created** (no enrollment
  side effect).
- Preflight refusals verified: `executor_profile_required` (None),
  `invalid_executor_profile` (missing file; relative/nonexistent executable);
  a valid absolute profile passes.
- Duplicate-launch refusal (`session_path_already_exists`) and duplicate
  runner detection (`SessionLock`, same session-file path) are covered by the
  merged `test_launch_worker.py` / `test_run_queue_worker.py`.

## Controller restart/recovery (authorized, evidence retained)

- Isolated rehearsal: `test_bootstrap_fleet.py` 4/4 + `test_bootstrap.py`
  14/14 (managed stop/start/restart lifecycle on temporary roots).
- Live transition: SQLite-consistent backup
  (`control/snapshots/pre-slot-binding-transition-20260910T223857.sqlite`),
  pre-restart fingerprint (rev 491, epoch 3, tasks/slots/agents), quiescence
  verified (no RUNNING/RECOVERY_HOLD, resources empty; BLOCKED gov01
  no-writer attested), authorized stop (pid 49592, ack note), start from new
  deployment (pid 50532), post-restart comparison ALL EQUAL
  (`pre-slot-binding-transition-fingerprint.json`), command-line identity
  confirmed. Rolling back = stop + start from
  `deployments/review-handoff-2c8fb069` + same store.

## Interruption recovery (real, not injected)

- gov01 BLOCKED by slot-03 foreign-work mismatch (rev 159-era defect class)
  → fixed controller deployed → foreign work preserved (committed branch
  retained; untracked logs to control/preservations) → supervisor
  `slot_rebind` → yield/recover → READY gen 6 → worker claim gen 7 →
  completed PR #46. The historical blocked-gov01 condition is closed with
  preserved evidence at every step.

## Not claimed here

- DYAD visual acceptance (no live vision run in this record).
- External-provider worker execution (workers were host-subagent sessions
  using the documented interactive path; executor-profile external processes
  are refused-by-preflight until a real provider is configured).
- Five simultaneous GPU workloads (none requested; admission rules intact).
