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