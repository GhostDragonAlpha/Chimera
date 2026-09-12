# GLM-GPU-DEMO-01 — preregistration (written before implementation, 2026-09-08)

Task: the AUTONOMOUS GPU MATERIAL MILESTONE. Continue from `bf0a6216` on
`astra/gait-capture`, isolated checkout. Every claim below is made BEFORE the
code exists. Verdicts stay separate: CPU / GPU / runtime / visual(DYAD) /
human — a PASS in one never licenses a claim in another.

## STATEMENT

The certified membrane compute kernels (the exact stage-0/1/2 transcription
frozen-verified in `probe_core.hpp` and re-verified in GLM-RELAX-GPU-01) can
run INSIDE the engine process as the state of record for the B2 membrane
demonstration, such that the geometry the engine renders is the
GPU-computed accepted state — no CPU recomputation of the rendered pose, no
`/mesh_bin` animation loop, and no rejected trial ever reaches the screen.

## PREDICTIONS (each independently checkable)

1. **P1 (numerics travel):** the engine-built `membrane_demo.comp.spv`
   compiled from the same GLSL source passes the frozen single-shot fixtures
   when the standalone probe is pointed at it (`--shader`), worst deviation
   within the frozen stage budgets (B2 eval/assemble/reduce as recorded).
2. **P2 (descent inside the engine):** driving the declared overdamped
   descent through the engine's demo controller from the f32 B2 gamma=1
   state reproduces the CPU law (`projected_descent`, the window demo's
   rail-projected variant) within the GLM-RELAX-GPU-01 budgets: per-iteration
   energy drift <= 1.1e-5 J against the CPU f64 reference trajectory run on
   the same f32-widened start, final centre height within the derived f32
   bound (n*2^-23*max|coord|), same named terminal state, Armijo margin >= 0
   on every accepted step.
3. **P3 (rejection integrity):** a forced-invalid trial (non-finite /
   degenerate geometry injected into the TRIAL buffer only) is refused by
   the backtracking acceptance (invalid-surface backtrack; if exhausted,
   `no_descent_step`), leaves the accepted buffer bit-unchanged (state id
   hash equal), and the rendered geometry is bit-unchanged (render-buffer
   hash equal).
4. **P4 (gamma controls at runtime):** gamma=0 admitted at runtime yields
   STATIONARY with geometry bit-unchanged; fixed-state gamma doubling doubles
   reported energy and force magnitudes within the frozen doubling tolerance
   (the recorded bound) and implies nothing about relaxation speed.
5. **P5 (runtime controls):** reset restores the initial accepted state
   bit-exactly (state id equal to the initial id) and clears iteration
   counters; run/pause/step behave as named; iteration, energy, terminal
   state and state identity are reported in the status.
6. **P6 (compute-to-render):** the render vertex buffer is produced by a
   compute present-stage reading the ACCEPTED buffer; the frame-loop
   dispatch-to-draw chain carries a COMPUTE_SHADER ->
   VERTEX_INPUT barrier (established engine pattern); a capture's
   render-buffer hash equals the status-reported render id for the same
   accepted state id. Capture association is serial by construction in the
   harness (each ctl is cv-acknowledged before the capture request);
   residual races are reported CONDITIONAL, not assumed away.
7. **P7 (ordinary path preserved):** with the demo not initialized, the
   engine's mesh path is untouched: the patched binary is exercised for
   ordinary mesh load + capture and behaves as before; demo substitution
   code is behind `md_active_` which is false by default.

## FALSIFIERS

- P1: any frozen-budget breach with the engine-built spv.
- P2: any budget breach, unnamed terminal state, Armijo violation, or a
  rendered pose that required CPU physics to produce.
- P3: accepted-state id or render hash changes across a rejected trial.
- P4: doubling outside the recorded bound, or geometry change at gamma 0.
- P5: reset state id != initial id, or counters/status incoherent.
- P6: capture hash != reported render id for the claimed state (beyond a
  CONDITIONAL-annotated race), or a missing barrier that could tear.
- P7: any ordinary-path regression attributable to the patch.
A falsifier firing is reported as a failure with evidence kept; no tolerance
is widened to pass.

## LAWS HELD FIXED

- Certified stage-0/1/2 kernel text: TRANSPORTED VERBATIM into the engine
  shader; the only new kernels are the trial update (GLM-RELAX-GPU-01's
  derived stage-4, verbatim) and the present stage (geometry mapping only —
  the recorded rigid B2->engine rotation and presentation lift; NO physics).
- Declared constants (ARMIJO_C1, backtracking, guard, residual, stagnation):
  imported, never re-tuned.
- Material admission: scalar gamma [J/m^2] validated at admission (finite,
  > 0, and its float32 conversion re-validated: finite, > 0; positive values
  lost to zero under float32 are REJECTED, not clamped), per-run snapshot
  recorded with both bit patterns. 1 wu = 1 m (declared mapping).
- Constraints: B2 rim pinned (exact zeros host-side), centre on the vertical
  rail; all three force components computed and recorded before projection.
- Iterations are NOT physical time; no inertial, elastic, contact or fluid
  claim is made. GPU-driven means GPU-COMPUTED accepted geometry, certified
  kernels, in-engine; it does NOT mean engine-window certification of Linux,
  nor DYAD nor human acceptance — those verdicts are collected separately.
- Build outside `ChimeraEngine/engine/build/`; only the isolated demo
  process is ever launched or stopped.
