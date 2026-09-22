# TypeB GPU full-body port receipt — WIP/hang state (2026-09-21)

Agent: GLM 5.3 · branch `agent/typeb-gpu-fullport-20260921` · commits
ca9f315 (prereg) → 2d31616 (WIP 1) → a336955 (WIP 2) → this receipt.

## HONEST VERDICT: NOT DONE — the batched GPU environment does not yet run

No Phase-C falsifier number is measured. The six preregistered falsifiers are
UNMEASURED, not green. Nothing here may be cited as a working training
environment.

## WHAT IS PROVEN (CPU-side anchors, all committed)

- The C++ reference rebuilt natively on this machine reproduces the banked
  walk exactly: refused at tick 302, worst ledger 30.970714 J (wave-38 ship
  numbers); refusal class gait_positional_correction_budget; 303-tick trace
  committed (cpu_walk.txt).
- The compiled scene (sha e61ad386...) parses into walker_model.WalkerSpec;
  the Python mirror matches the C++ Model's defaults-pose mass diagonal to
  1 ulp (2.2e-16 rel) and the reset state BIT-EXACTLY (worst diff 0.0).
- The Warp-form port (walker_gpu.py, 3200 lines) is COMPLETE as code: FK/
  Jacobians (GPU vs mirror frame-exact), mass-metric active-set projection,
  discrete-cone Coulomb friction, RK4 at dt/4, event DFS with 42-step
  bisections, servo stores, and the reflex deterministic core through
  wave-38 (fidelity manifest itemizes ported vs deferred).

## THE FRAMEWORK WALL (measured, not an excuse)

- Warp 1.15: the tick kernel does not finish JIT compiling. Static unrolling
  of constant-bound range loops multiplies the inlined advance/free_step/
  rate/fk_eval chain; 45+ min compile attempts stalled at 2.6-7 GB RSS
  (release AND debug modes; RTX 4090 sm89, CUDA 12.8 driver stack).
- Dynamic-loop rewrites + single-call-site collapse reduced the body; numba
  CUDA 0.63 then compiled and LAUNCHED the same kernel (grid warning fired,
  GPU execution observed) — but tick-0 has not returned (20+ min, E=2,
  device prints not flushed = kernel never completes). All while loops are
  audited bounded (mechanical scan committed in-session); the spin is in
  device execution, suspect the fully-inlined ~40 KB/thread local-memory
  working set or a codegen pathology. This is the remaining defect.

## FILES

- walker_gpu.py — the warp-form full port (reference semantics, per-func).
- walker_numba_gen.py / gen_numba.py / translate_warp_to_numba.py /
  postgen.py — the numba-CUDA pipeline (current best candidate).
- walker_nb_env.py — the batched env API (reset/set_command/step/status).
- cpu_probe.cpp + cpu_{stand,freefall,reset,walk}.txt — CPU reference traces.
- PREREG_FULLPORT.md — the frozen falsifiers (unmeasured, still binding).
- FIDELITY_MANIFEST.md — ported vs deferred reflex laws.

## NEXT (in order)

1. Device-side hang isolation: block-size/locals experiment (maxrregcount,
   splitting the tick kernel at the substep boundary), printf probes at
   kernel entry.
2. If the numba path stays hung: the C++-native CUDA extension (nvcc+MSVC
   declined cudafe++ on MSVC 14.51; needs an older MSVC or Numba remains
   the only local GPU compiler) — or a co-lane's working integration path.
3. Phase B (reflex fidelity deepening) proceeds on its dispatched lane
   against this committed interface.
