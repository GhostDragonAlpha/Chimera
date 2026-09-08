# GLM-RELAX-GPU-01 — the verified kernels DRIVE the declared descent: PASS (2026-09-08)

Task: continue from `c38ffe84…` on `astra/gait-capture`, isolated checkout.
Preregistration (written before the build):
`docs/THE_RELAX_GPU01_PREREGISTRATION.md`.

## What ran

`tools/membrane_gpu_probe/relax_gpu_probe.exe` (new target, same verified
`membrane.comp.spv` + the verbatim-extracted `probe_core.hpp` core): the
GPU state of record lives in the same f32 buffers the frozen fixtures
verify; the loop mirrors `run_descent` 1:1 — residual test on free DOFs,
`p = P·F` with exact-zero pins host-side, first-trial guard
`GUARD_FRAC·min_edge`, backtracking Armijo, the five named terminal
states. The ONE new kernel is the derived stage-4 trial update
(`x+ = x + alpha·p`, no physics); every evaluation re-runs the verified
stage-0/1/2 path untouched.

## Result (device: NVIDIA GeForce RTX 4090)

| Gate | Result |
|---|---|
| R1 frozen single-shot (B2+Fan12, 6 cases) | PASS (worst 1.79e-7) |
| R2 per-iteration energy vs CPU law | PASS — worst drift **3.269e-7** (frozen budget 1.1e-5) |
| R3 final centre vs CPU law | PASS — gap **1.949e-7 m** (derived f32 bound 1.502e-5) |
| R4 named terminal state | PASS — `stagnated` (same state as the CPU law) |
| R5 Armijo on every accepted step | PASS — re-checked from the trail, margin ≥ 0 |
| R6 no tolerance widened | PASS — frozen or preregistered-derived budgets only |

- GPU loop: 126 accepted steps, energy 2.625 → **2.59807611** J (f32 state)
- CPU reference (`run_descent` on the widened-f32 start): 126 accepted
  steps, energy → **2.5980761647224426** J
- Iteration counts agree exactly; no early-stop cause was needed — the f32
  loop reached true stagnation at the same step as the f64 law.
- Iterations are iterations, never time; no GPU-dynamics claim beyond this
  standalone numerical gate; no engine contact.

## Corrections preserved along the way

1. First draft of relax.cpp had a garbage assignment line, a dead
   `gpu_evaluate` scaffold and a missing residual test — rewritten clean
   before first compile.
2. `run_case` takes a `float&` energy — fixed the `double U` mismatch.
3. The verbatim-extracted header still contained the probe's `main()` —
   stripped (the certified probe keeps its own).
4. The trial-shader compile via quoted `std::system` failed on Windows —
   unquoted (paths are space-free).
5. `RELAX_FINAL_POS` initially printed the initial state —
   `result.positions` was not updated on accept; fixed and re-run.
6. The HARNESS parse bug (indices parsed as values, producing absurd
   R2/R5 failures) — fixed; the earlier FAIL run is preserved in
   `relaxgate_20260908T215828.498277Z/` with the diagnosis.

## Evidence

`docs/evidence/membrane_gpu_relax/relaxgate_20260908T220009.757271Z/`
(gate_record.json, summary.txt, raw GPU stdout + command, raw probe
output + command). Build: `.tmp/relax_build` (outside the protected path).

## Verdict classes (separate)

- CPU verification: **PASS** (the declared law on the same start state)
- GPU verification: **PASS** (single-shot frozen budgets + driven descent
  within derived budgets, preregistered)
- Runtime/window/DYAD: NOT TESTED here (unchanged from prior gates)
- Human (Alan): NOT CLAIMED
- GPU-driven engine integration: NOT CLAIMED — this gate stands alone;
  engine integration remains the next bounded task.
