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

---

# DIAGNOSTIC APPEND — continuation lane (2026-09-22)

Agent: GLM 5.3 · branch `agent/typeb-gpu-fullport2-20260922` @ `0763d27`+.
Prereg: `tools/science_funnel/typeb_gpu/PREREG_DIAG.md` (frozen before any
diagnostic run). The Phase-A/C falsifiers remain UNMEASURED — nothing below
changes that verdict.

## VERDICT: the tick-0 "hang" is HOST-SIDE CODEGEN, not device execution

- F-H1 FIRED. The first `tick_kernel[1,1]` launch call blocks the host in
  numba's compile pipeline: python.exe at ~94-100% of one core for the whole
  wait (CPU 627.9→660.8 s over a 35 s window), 9.3 GB working set, no device
  print flushed, no kernel completion. Attribution probe (`diag_t1.py`,
  `sample_gpu.ps1`): the box's 87-97% "GPU busy" belongs to ~34 OTHER
  compute processes (`nvidia-smi --query-compute-apps`); lane 1's GPU-busy
  reading was attribution error. The monolith codegen ran >66 CPU-min
  (harness-killed, never completed) — the Warp 45-min wall REPRODUCES on
  numba 0.63 with the same fully-inlined body. "Second launch in the same
  process" was never reached: the first never returned.
- F-H3 NOT FIRED (moot): no kernel ever executed; the while-audit was
  re-verified independently (all bounded; the `slot` grid-search advances
  Tf≈213/iteration from a bounded start).
- F-H2 (run-time local-memory stall) DEAD as the hang cause — no execution
  started. PTX census (plan kernel): .local 10,056 B/thread; block-ladder
  untested (blocked behind integ codegen below).

## WHAT THE SPLIT MEASURED (`split_kernels.py` → `walker_numba_split.py`)

plan/integ/post kernels at the receipt's seams, a_rc scratch, settle-dec
and a_ticks exactly once, bounds guard, cache=True, big-five device
functions inline='never' (VERIFIED honored: plan PTX has .func + 45 real
call ops, `diag_t2c.py`):

- plan: 14.1-16.0 s compile; 0.111 s first exec; 3.6 ms steady (E=1,
  block=1, freefall); 0.08 s cached reload in a FRESH process (cache works).
- integ: all-inlined >55 CPU-min (killed); inline='never' >62 CPU-min
  (killed); the advance-only micro-kernel alone 817.8 s (`diag_t2b.py`).
  The codegen sink is advance's own subtree (rate/free_step/impact/fk_eval
  + inlined project_rows/friction_solve/inverse_spd18), superlinear in
  module size (plan PTX 202k chars → 14 s class).
- opt=False probe: see `logs` committed alongside the branch tip.

## BAR STATUS

The six preregistered falsifiers remain UNMEASURED — the environment still
does not run, and the bar suite (`bars_fullport.py`, committed) is blocked
behind the integ kernel's one-time codegen. cache=True makes that cost
once-per-machine IF the compile is allowed to finish once; no machine has
yet finished it.

## NEXT (in order)

1. Let one integ compile run to completion uninterrupted (overnight box) —
   the cache then serves every later process; run `bars_fullport.py`.
2. If the full integ never lands: split advance itself (drift vs event-DFS
   vs impact; the LIFO stack in global scratch), or reduce NVVM input size
   per kernel further.
3. Then the block ladder (H2's surviving question) and the bars.
