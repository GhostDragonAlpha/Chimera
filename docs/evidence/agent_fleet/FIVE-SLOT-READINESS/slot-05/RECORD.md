# FIVE-SLOT-READINESS-01 — slot-05 runtime probe record

Fleet task `slot05-runtime-probe` (worker-kind, slot 5/5), owner `stage05`
(scripted readiness stage), base `d7c47446`.

## Preregistration (in the task packet, before implementation)

- STATEMENT: the slot-05 worktree builds a clean engine staged into its own
  external runtime dir; the frozen-B2 numerical gate passes on its port with
  the engine launched visibly and terminated by the gate client, guarded by a
  controller-recorded GPU reservation; a real interruption of the slot-05
  worker client is recovered through the controller drill.
- PREDICTION: (1) clean build without touching the protected build path;
  (2) shader provenance blob `4f7a356e…`; (3) 21/21 gate verdicts PASS;
  (4) interruption -> task RECOVERY_HOLD generation+1 with the GPU retained;
  a zombie generation-1 write is refused; the reservation is cleared only
  after verified process drain (port free, no orphan); recovery returns the
  task READY at generation 2; the leader reclaims at the new generation.
- FALSIFIER: gate FAIL, provenance mismatch, orphan engine, a zombie write
  that is NOT refused, a reservation cleared before drain evidence, or a
  recover that runs while resources are still held.

## Execution (UTC 2026-09-10)

| step | result |
| ---- | ------ |
| build engine in `E:\ChimeraWork\slot-05\.tmp\engine_build` | PASS |
| stage runtime exe+shaders in `E:\ChimeraWork\slot-05\.tmp\engine_runtime` | PASS |
| binary identity `slot05_binary_identity.json` | exe `175f6df4…`, spv `71b5f8d3…`, comp blob `4f7a356e…`, head `d7c47446` |
| controller checkpoint (built+staged) | revision 32 |
| `resource_request rtx4090 (gpu_functionality)` as `stage05` | granted, revision 33 |
| visible-engine numerical gate on port 8105 (`20260910T020453.603679Z`) | **21/21 PASS**; engine launched visibly, terminated own pid |
| drain verification | port 8105 free (bind-free, no HTTP, no `chimera_engine` process) |

> Drill execution (interruption -> recovery) is recorded in the
> `SLOT05-DRILL` appendix below, appended after the interruption is run.

---

## SLOT05-DRILL — interruption + recovery through the live controller (UTC 2026-09-10)

The slot-05 worker client (a real `worker_step.py` process on the `stage05`
session) was parked on the slot-05 claim at generation 1 with the `rtx4090`
reservation live, then terminated with `taskkill /F` (the drill's
interruption). The trusted supervisor marked `PROCESS_EXIT`; the controller
did the rest. Every step below is the live registry's answer, not a fixture.

| step | observed | revision |
| ---- | -------- | -------- |
| owned worker client started (pid 4536, journal `waiting`) | alive | — |
| drill interruption (`taskkill /F` on the worker client) | terminated | — |
| `SUPERVISOR.fail(stage05, PROCESS_EXIT)` | leader `big-pickle`, epoch 1 | 34 |
| task state after fail | `RECOVERY_HOLD`, generation 2 | 34 |
| zombie write (gen 1, terminated session) | REFUSED: `session_revoked` | 34 |
| GPU reservation retained after fail | `rtx4090` task=slot05-runtime-probe, gen 1 | 34 |
| drain verification before clear | port 8105 bind-free, no HTTP `/state`, no `chimera_engine` process | — |
| `SUPERVISOR.resource_clear(rtx4090, verified drain)` | cleared | 35 |
| worktree reconcile | `E:\ChimeraWork\slot-05` head `3a345d15`, clean except drill evidence | — |
| `SUPERVISOR.recover(slot05-runtime-probe)` | READY, generation 3, slot cleared | 36 |
| leader `claim` (new generation) | RUNNING generation 4 | 41 |

Notes:

- Zombie writes are fenced twice: the failed agent's session is revoked and
  the obsolete generation is invalid — the controller refused with
  `session_revoked` before the check even reached the stale generation.
- The GPU reservation survived the fail (generation 1 held) because the
  controller intentionally retains ownership until the supervisor's trusted
  process-drain evidence. `recover` refused nothing here, but it enforces
  `resources_still_held` <-> drain evidence ordering internally.
- When the leader reclaimed, the registry bound the task to the FIRST free
  worker slot (slot-2, released moments before by the slot-02 publication),
  while the physical workspace holding the task branch is `E:\ChimeraWork\slot-05`
  (the slot-05 worktree checked out on `astra/tasks/slot05-runtime-probe`).
  The record is faithful: the soft binding is bookkeeping; the branch head is
  the source of truth for publication (this worktree is where that branch is
  checked out, so all remaining commits land here).

## DYAD phase (post-recovery, big-pickle owner, generation 4)

- `resource_acquire rtx4090` (rev 42) and chained `resource_acquire dyad_eye`
  (rev 43) succeeded — the chained-eye gate (`dyad_requires_gpu_reservation`)
  is satisfied by the same-task GPU reservation.
- `senses.can_see()` -> eye **DARK**: no vision model loaded in LM Studio.
- Checkpointed `BLOCKED` (rev 44); released `dyad_eye` (rev 45) then `rtx4090`
  (rev 46). Workspace drained (no engine process; port 8105 free).
- OPERATOR ACTION: load a vision-capable model in LM Studio, then rerun
  `tools/run_dyad_gpu_demo_review.py 20260910T020453.603679Z --edge` under a
  fresh reservation. No human acceptance is claimed for slot-05.

## Verified facts (gate phase)

- All 21 gate verdicts PASS; terminal energy `2.59807611 J` at iteration 126
  (`stagnated`) equals the CPU reference `2.5980761647 J`.
- `protected_build_path_used: false`; shader provenance identical across
  slots 03, 04 and 05 (spv `71b5f8d3…`, source blob `4f7a356e…`).
- Reservation granted rev 33 and held by `slot05-runtime-probe` gen 1.

## Open (DYAD + drill)

- The required interruption drill follows in the appendix (this file is
  updated in the same worktree commit after the drill completes).
- The DYAD review will run after recovery, owned by the reclaiming leader;
  the eye may be dark (see slot 03/04 records) -> BLOCKED checkpoint with
  operator action recorded, never a skip.