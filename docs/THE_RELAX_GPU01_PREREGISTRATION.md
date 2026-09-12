# GLM-RELAX-GPU-01 — preregistration (written before the build, 2026-09-08)

Task: continue from `c38ffe84…` on `astra/gait-capture`, isolated checkout.
The next program milestone after the verified single-shot kernels and the
CPU-reference window demo: the VERIFIED KERNELS DRIVE the declared
overdamped descent, standalone — no engine, no optimizer import into the
engine, no GPU-driven claim beyond this gate.

## STATEMENT

The compiled compute kernels (the same `membrane.comp.spv` face-eval,
CSR-gather and energy-reduction stages the frozen fixtures certify, plus
one new derived stage-4 trial-update kernel with no new physics) can DRIVE
the declared overdamped descent loop on B2 at gamma=1: at every iteration
the GPU state of record is f32, and the accepted trajectory matches the
CPU float64 reference (`run_descent` from `tools/overdamped_descent.py`)
within budgets DERIVED BELOW — iteration-0 must agree at the frozen
fixture budgets, and f32-state accumulation must bound the later drift.

## PREDICTION

1. Iteration 0 (the frozen f32 fixture state): GPU forces and energy match
   the frozen references within the FROZEN budgets (assembly per-budget,
   complete-force 2.5e-5, energy 1.1e-5) — the existing probe already
   proves this; the loop inherits it.
2. The GPU loop's accepted trajectory follows the CPU reference within
   derived bounds: positions within `n_acc · 2^-23 · max|coord|` (f32
   representable state, ~1e-5 m worst-case on B2) and per-iteration energy
   within the frozen 1.1e-5 J of the reference energy at the SAME state
   (or within 8·eps·U of it when the loop terminates at machine scale).
3. The loop terminates in one of the FIVE NAMED STATES with the same
   taxonomy semantics (`stationary` / `stagnated` / `step_limit` /
   `no_descent_step` / `invalid_surface`); iterations are never time.

## FALSIFIER

Any of: a frozen-budget breach at iteration 0; per-iteration energy drift
beyond the frozen 1.1e-5; final positions beyond the derived f32 bound; a
terminal state outside the named taxonomy; Armijo violated on any accepted
step; or any attempt to widen a tolerance to make the comparison pass
(the correction history is preserved instead).

## Derived budgets (shown BEFORE the run; no fitted numbers)

- **State representation:** the GPU loop's positions live in f32 buffers
  (the verified fixture representation). Every accepted step's `x+` is
  computed in f64 on the host from the f32 force field, then quantized to
  f32 — the same validated upload boundary class the window demo uses.
  Per-step representation drift <= `2^-23 · max|coord|` (~1.2e-7 m on B2).
- **Positions vs CPU reference:** `n_accepted · 2^-23 · max|coord|`
  accumulates worst-case: for B2 (~126 accepted steps) <= ~1.5e-5 m.
- **Per-iteration energy:** the frozen 1.1e-5 J fixture budget for the
  energy at a given state, PLUS the reference's own stagnation scale
  `8·eps·max(U,1)` (~4.6e-15 J — negligible) near machine-scale decreases.
- **Forces:** the frozen complete-force budget 2.5e-5 per component at
  comparable states.
- **Stopping:** the GPU loop may reach `stagnated`/`stationary` EARLIER
  than the f64 run: once true increments fall below the f32 ULP of the
  state, no f32-representable progress exists. An earlier stop with all
  above budgets holding is a PASS with the cause recorded — not a failure
  and NOT a tolerance change.

## Scope

No engine contact, no window, no DYAD, no GPU-dynamics claim beyond this
numerical gate. The kernel change is confined to one new stage-4
trial-update (pure arithmetic on existing buffers: `x+ = x + alpha·p`,
`p` precomputed and pinned host-side; exact-zero pins enforced host-side
by the pinned-direction law). The verified stages 0–2 are untouched; the
standard probe must still PASS unchanged after the refactor.
