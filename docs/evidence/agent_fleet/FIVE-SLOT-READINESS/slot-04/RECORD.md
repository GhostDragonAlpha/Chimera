# FIVE-SLOT-READINESS-01 — slot-04 runtime probe record

Fleet task `slot04-runtime-probe` (worker-kind, slot 4/5), owner `stage04`
(scripted readiness stage), base `d7c47446`.

## Preregistration (in the task packet, before implementation)

- STATEMENT: the slot-04 worktree builds a clean engine staged into its own
  external runtime dir; the frozen-B2 numerical gate passes on its port with
  the engine launched visibly and terminated by the gate client, guarded by a
  controller-recorded GPU reservation.
- PREDICTION: (1) build without touching the protected
  `ChimeraEngine/engine/build`; (2) shader provenance blob matches the tested
  `4f7a356e…`; (3) 21/21 gate verdicts PASS; (4) reservation granted and
  released through the controller with the port drained before release.
- FALSIFIER: build touching the protected path, any gate FAIL, shader
  provenance mismatch, orphan engine, or a reservation that is not
  controller-recorded.

## Execution (UTC 2026-09-10)

| step | result |
| ---- | ------ |
| build engine in `E:\ChimeraWork\slot-04\.tmp\engine_build` | PASS |
| stage runtime exe+shaders in `E:\ChimeraWork\slot-04\.tmp\engine_runtime` | PASS |
| binary identity `slot04_binary_identity.json` | exe `87a76649…`, spv `71b5f8d3…`, comp blob `4f7a356e…`, head `d7c47446` |
| controller checkpoint (built+staged) | revision 28 |
| `resource_request rtx4090 (gpu_functionality)` as `stage04` | granted, revision 29 |
| visible-engine numerical gate on port 8104 (`20260910T015600.626632Z`) | **21/21 PASS**; engine launched visibly, terminated own pid |
| drain verification | port 8104 free |
| DYAD eye check (`senses.can_see`) | **BLOCKED: no vision model loaded in LM Studio** |
| controller checkpoint (BLOCKED, DYAD pending) | revision 30 |
| `resource_release rtx4090` (drained) | revision 31 |

## Verified facts

- All gate verdicts PASS; terminal energy `2.59807611 J` at iteration 126
  (`stagnated`) equals the CPU reference law `2.5980761647 J`.
- `protected_build_path_used: false`; shader provenance identical across
  slots 03 and 04 (`spv 71b5f8d3…`, source blob `4f7a356e…`).
- Reservation lifecycle controller-recorded (grant rev 29 → drained release
  rev 31); port 8104 free at release, no orphan process.

## Open (DYAD)

Eye is dark (LM Studio has no vision model loaded). Task checkpointed
`BLOCKED` with operator action recorded: load a vision-capable model, then
re-run the DYAD phase (`tools/run_dyad_gpu_demo_review.py
20260910T015600.626632Z --edge`) under a fresh `rtx4090` + `dyad_eye`
reservation. No human acceptance is claimed for this slot.