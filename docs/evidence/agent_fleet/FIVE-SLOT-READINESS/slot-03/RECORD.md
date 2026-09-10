# FIVE-SLOT-READINESS-01 — slot-03 runtime probe record

Fleet task `slot03-runtime-probe` (worker-kind, slot 3/5), owner `stage03`
(scripted readiness stage), base `d7c47446`.

## Preregistration (in the task packet, before implementation)

- STATEMENT: the slot-03 worktree hosts a clean engine build staged into its
  own external runtime dir, and the frozen-B2 numerical runtime gate passes
  on its port with the engine launched visibly and terminated by the gate
  client.
- PREDICTION: (1) build succeeds from the worktree head without touching the
  protected `ChimeraEngine/engine/build`; (2) binary identity is recorded
  (exe+shader hashes, shader source blob matches the tested provenance
  `4f7a356e…`); (3) the gate's 21 verdicts all PASS; (4) the GPU reservation
  is acquired and released through the controller, and the engine process is
  drained (port free) before release.
- FALSIFIER: a build writing into the protected build path, a gate FAIL, a
  shader provenance mismatch, an orphan engine process, or a reservation that
  is not controller-recorded.

## Execution (UTC 2026-09-10)

| step | result |
| ---- | ------ |
| build engine in `E:\ChimeraWork\slot-03\.tmp\engine_build` | PASS |
| stage runtime exe+24 shaders in `E:\ChimeraWork\slot-03\.tmp\engine_runtime` | PASS |
| binary identity `slot03_binary_identity.json` | exe `7fd7225d…`, spv `71b5f8d3…`, comp blob `4f7a356e…`, worktree head `d7c47446` |
| controller checkpoint (built+staged) | revision 24 |
| `resource_request rtx4090 (gpu_functionality)` as `stage03` | granted, revision 25 |
| visible-engine numerical gate on port 8103 (`20260910T015238.101816Z`) | **21/21 PASS**; engine launched pid 14240, terminated own pid |
| drain verification | port 8103 free (bind + no listener) |
| DYAD eye check (`senses.can_see`) | **BLOCKED: no vision model loaded in LM Studio** |
| controller checkpoint (BLOCKED, DYAD pending) | revision 26, state=BLOCKED |
| `resource_release rtx4090` (drained) | revision 27 |

## Verified facts

- All gate verdicts PASS: energy-vs-fixture, doubling energy and force,
  gamma-back restore, monotone descent, terminal energy `2.59807611 J` at
  iteration 126 (`stagnated`), reset restore, rejection integrity
  (`invalid_trial_REFUSED`), and gamma-zero stationary capture — numerically
  equal to the CPU law `2.5980761647 J`.
- The protected build path `ChimeraEngine/engine/build` was never used
  (`protected_build_path_used: false` in the identity record).
- Reservation lifecycle is controller-recorded end to end (grant rev 25 →
  drained release rev 27); no other holder contended (queues empty).

## Open (DYAD)

The required DYAD review could not run because the eye is dark: LM Studio has
no vision model loaded (`senses.can_see()` → `NoModelLoaded`). The task is
checkpointed `BLOCKED` with the operator action recorded. When a vision-capable
model is loaded, re-run the DYAD phase: re-reserve `rtx4090` + `dyad_eye` and
review this run's captures (`tools/run_dyad_gpu_demo_review.py
20260910T015238.101816Z --edge`). No human acceptance is claimed for this slot.