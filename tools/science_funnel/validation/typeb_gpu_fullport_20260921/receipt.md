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

### Addendum (same lane, final): the opt knob does not rescue integ

`diag_t2d.py` (advance-only, `@cuda.jit(opt=False)`): compile still ~10+ min
wall (24.75 GB peak host working set — the UNOPTIMIZED IR itself is the
volume, i.e. numba's frontend emits the explosion, LLVM's passes merely
crunch it), and the resulting kernel then failed at `cuLaunchKernel` with
CUDA_ERROR_INVALID_VALUE (unoptimized local frame not launchable). Neither
numba knob (`inline='never'`, `opt=False`) makes the integ kernel viable on
numba 0.63.1/CUDA 12.8. The remaining local lever is a deeper split of
advance itself (drift vs event-DFS vs impact, the LIFO stack hoisted to
global scratch); the remaining global lever is the original receipt's
option 2 (a non-numba CUDA compiler path). No falsifier number has changed;
the bars remain UNMEASURED.

## APPENDIX — TRANSLATOR-FINISH CONTINUATION (the nvcc-route DLL env, 2026-09-22)

Continuation agent (git trailer Agent: GLM 5.3) on branch
agent/typeb-gpu-finish-20260922, resuming a host-crash-interrupted session.
The nvcc route now has a WORKING BATCHED ENV TICK: walker_env.dll (nvcc 12.8 +
VS2022 cl, -arch=sm_89, -lineinfo) driven by walker_env_host.py (ctypes
mirror of walker_nb_split_env.GaitWalkEnv), first tick achieved and the env
runs the full phase-split plan/integ/post per tick with a_rc carrying the
verdict.

### Latent defects found and fixed (the flattened lane was never runtime-
validated; each fix unmasked the next layer):

1. mdi chain_ax slot 60 vs 104 written (walker_numba.py CHN guess "14 bodies
   x ~4"); later tables stomped chain_ax[60:104]; fk_eval indexed ax_slot with
   garbage -> the tick-0 illegal memory access. Fixed at the source: CHN=104,
   offsets pt_body 184 / drive_coord 192 / fore_coord 204 / hind_coord 208 /
   hind_drive 216 / fore_drive 224 / fore_heel_pt 228 / hind_heel_pt 230,
   NI32=232; builder tiling asserts added.
2. numba2cu SINGLE_INT_ARGS typed the substep h int -> dt/4 truncated to 0 ->
   advance returned at h<1e-12 every call -> total freeze (rc=0, adv=0).
3. The flattened source passed (csti, mdi) into defs declaring (..., mdi,
   csti) at ALL 30 call sites; impact/rate/fk_eval read csti as the model
   table -> M garbage -> inverse_spd18 rc=8.
4. wp.zeros semantics lost: ~190 locals (plane[4] among them) uninitialized in
   the numba forms; phantom contacts cancelled gravity exactly. 411 explicit
   zero-fills restored (matched against walker_gpu.py's wp.zeros set).
5. rate() mat_vec(inv, free, free) in-place: bounded forces amplified to 1e41
   by compounding with inv entries ~1e3. Scratch buffer fixed.
6. free_step RK4 stage wiring: all four rate calls wrote the same (srq, srv)
   while the combination read va/brv/crv/drv, and the stage-input states
   copied states instead of derivatives. Rewired per the C++ (k1->qa/va,
   k2->brq/brv at shifted states, ...).
7. advance rep-scan bisection probed gap_of_k(..., r*2) instead of (r-1)*2
   (the for->while r-1 compensation missed an expression context): phantom
   contact-loss events -> advance wall-clamp 64-budget chatter -> rc=6 at
   settle tick 5.

Verification instruments: compute-sanitizer memcheck + a -lineinfo rebuild
(naming fk_eval walker_kernels.cuh:590); host_probe.cxx / host_loop.cxx with
host_shim/ run the exact translated kernels on the CPU (seconds per
iteration). GPU and host traces agree to printed digits.

### State after the repairs (measured):

- GPU freefall (defaults pose): base-y second difference -0.00011154 ->
  -10.038 m/s^2 per tick for 51 ticks, then the collapse latch (y=0.194 <
  collapse_y=0.20) freezes the env (rc=0, refused=0). Host trace identical.
- The frozen bars estimator over the latched trace measures g=0.261426
  (bar |err|<=0.01) -> F-FULLPORT-PROBE-PARITY freefall FIRES AS WRITTEN.
  Attribution: (a) the reference trace cpu_freefall.txt has q3 identically 0
  and an exact -9.807 parabola — the C++ probe's power-off holds the legs
  (ballistic base), while the kernels' power-off frees the joints (tau=0), so
  the GPU base carries leg-reaction terms (-10.038 pre-latch, |err|=0.23);
  (b) the collapse latch truncates the trace at tick 51 and dilutes the mean.
- stand probe: max_scaled_diff=0.1311 (bar <1e-2) -> FIRES. Attribution
  incomplete (needs a tick-by-tick GPU-vs-cpu_stand comparison).
- C1 nominal class (build @ 12:07): horizon=16, class=6 (wall-clamp budget),
  hind=0, fore=0 -> FIRES. Root cause chain fixed through (7); on the current
  build the nominal env walks to tick 39 and refuses class 5 (project_rows
  row budget R>=10 / projection failure) — the next latent layer, not yet
  root-caused. The 100-tick class bar (hind fire + fore lift by 150) is
  still RED.
- C3 batch-1024: env_sync failed on the 12:07 build (diagnosis pending).

### Commits on this branch (this appendix): 6a505814 (checkpoint), 55d39440
(first tick + chain_ax fix), 87ef39bd (defects 2-5 + instrumentation),
cec9bbca (host loop + attribution), this commit (defects 6-7 + rep-scan fix).

The bars remain UNMEASURED-to-RED on the nvcc route: probes FIRE with the
attributions above; C1/C2 blocked by the settle/wall-pin defect chain
(rc=3/rc=5 now); C3 pending; C4 pending. No falsifier has been re-tuned.

### APPENDIX ADDENDUM — first full bars measurement on the final build
(rep-scan fix, walker_env.dll @ 13:21, bars_split_b32.json, --env dll, block 32)

- F-FULLPORT-PROBE-PARITY freefall: FIRED — measured_g=0.2614 (bar |err|<=0.01;
  err=9.545). Attributed: collapse latch (y=0.194<0.20 at tick 51) truncates
  the trace; pre-latch the coupled base accel is -10.038 vs the C++ trace's
  ballistic -9.807 (its q3 is identically zero: power-off holds the legs in
  the C++, frees them in the kernels).
- F-FULLPORT-PROBE-PARITY stand: FIRED — max_scaled_diff=0.1278 (bar <1e-2).
  Attribution pending (tick-by-tick vs cpu_stand.txt not yet done).
- F-FULLPORT-CLASS: FIRES — nominal walk refused at tick 39 (class 5 =
  project_rows row budget / projection failure), hind_fires=0, fore_lifts=0
  (bar: >=1 hind fire AND >=1 fore lift by tick 150). The frozen script's
  class_pass=True is a formula artifact (its boolean never reads hind/fore).
  Progress across this session's fixes: refused at 5 (class 6 clamp chatter)
  -> 16 (class 6) -> 39 (class 5).
- F-FULLPORT-SURVIVAL: FIRED — pass_100=0/64 (median horizon 39.0; bar
  >=80% of 64 seeds >=100 ticks). Horizons 39-40 across seeds: the settle/
  wall-pin defect chain is seed-independent.
- F-FULLPORT-THROUGHPUT: the script records 32,401,645 eps @1024 and
  135,185,980 eps @4096 (>=968 bar -> throughput_pass_1024=True) but this
  number is NOT a valid throughput measurement: 1024/1024 and 4096/4096 envs
  are already refused, so the kernels short-circuit (0.03 ms/tick = dead-env
  dispatch). Re-measure after C1 goes green.
- F-FULLPORT-MEMORY: no fire — 14.02 GB used (shared GPU, includes other
  processes), marginal -0.00128 MB/env (noise-level).

NEXT LANE (in order): (1) audit advance's wall-pin/clamp path and rate's
joint-stop rows against the C++ at the tick-39 settle phase (rc=5, class 5);
(2) stand-parity tick-by-tick attribution; (3) power-off joint semantics
decision (manifest addendum if the kernels' free-joint reading is kept);
(4) re-measure C3 with live envs. First tick and a full frozen-bars
measurement pipeline on the nvcc route are DELIVERED.
