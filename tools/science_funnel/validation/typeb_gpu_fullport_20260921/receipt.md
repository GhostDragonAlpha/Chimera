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

---

# CLOSEOUT APPENDIX — the physics-repair lane (2026-09-22, agent GLM 5.3)

Branch agent/typeb-gpu-finish-20260922. Mandate: close the named bars causes
(C1/C2 refusal, stand parity, power-off semantics, C3 re-measure) without
re-tuning anything. Method: a three-way tick-by-tick diff — the C++ reference
(cpu_probe rebuilt against engine_inc/gait_controller.hpp, byte-reproducing
cpu_walk.txt today) vs the host replay of the translated kernels (host_loop)
vs the GPU DLL — plus python replicas of the frame recursion for
component-level attribution.

## HARNESS DEFECTS FOUND FIRST (the host proxy was invalid before this lane)

- host_shim/cst.txt was ~all zeros (mu=0, k_touch=0, k_slip=0, fore poses 0,
  posture gains 0) and csti_nom.txt had drive_en=0: the host replay had been
  running a phantom passive config (tau identically 0 — proven by HL_NOPOWER
  producing a bit-identical trajectory). dump_shim.py now regenerates the shim
  from walker_env_host.build_env_arrays (single source of truth with the DLL).
- The host replay tick-1 vx error vs the C++ was 2.7% BEFORE this fix; the
  prior "GPU and host traces agree" claim held only for freefall.

## THE DEEP DEFECTS (all in fk_eval's frame recursion, walker_numba_split.py)

1. THE DERIVATIVE-FRAME SEED: C++ Transform(n) (coupled_articulation.hpp:43)
   seeds t=identity but dt=ddt=ZERO; the port seeded all three at identity
   (eye16(motion_dt), eye16(motion_ddt)). A phantom "one" leaked into every
   body's frd/frdd: the kernels computed a REST BIAS of bv[y]=-88.4 N at v=0.
2. THE GROUND-BODY SEED: frd[0]/frdd[0] were identity; the reference ground
   transform has zero derivatives.
3. THE CHAIN-PRODUCT LAW: the port composed frd = pfp*motion_dt*fc and
   frdd = pfp*motion_ddt*fc, dropping the parent chain's dt/ddt entirely
   (C++ product(): ddt = a.ddt*b.t + 2*a.dt*b.dt + a.t*b.ddt), AND composed
   the per-axis recursion using POST-update motion/motion_dt where the C++
   product reads pre-update values.

MEASURED CONSEQUENCES OF THE FIX (DLL, E=1, nominal config):
- rate() at the capture pose matches the C++ solve to 2.3e-12 (was off by up
  to 11.3 rad/s^2 on Rknee).
- Powered tick-1 state divergence vs the C++ walk trace: 3.21e-2 -> 1.40e-5
  (max component). Passive: 1.39e-6.
- GPU FREEFALL IS NOW EXACT: base vy decrements by exactly -9.80665/300 per
  tick, q4 matches cpu_freefall.txt to all printed digits, joints frozen
  (q6..q13 ~1e-17), no x drift. The pre-latch second-difference estimator
  measures g = 9.80665000000 (|err| ~ 1e-12; bar <= 0.01).

## POWER-OFF SEMANTICS — DISPOSITION: THE PREMISE DISSOLVED

The prior attribution ("the C++ power-off HOLDS the legs; the kernels FREE
them; the kernels must adopt hold") was wrong on both ends. Verified today:
(a) the C++ freefall trace's frozen joints are not a hold law — tau is 0 in
both; (b) the C++ evaluate's gravity at the defaults pose is nonzero on the
hind rows (-0.0558675 N·m, byte-verified vs the kernels' gv); (c) the frozen
legs are EMERGENT physics: at the straight-chain zero pose every link CoM hangs
below its joint axis, so uniform gravity exerts zero generalized joint torque
and M^-1*gv reduces to the exact ballistic base (weightlessness). The kernels
produced -10.038 only because defect (1) above corrupted the bias. After the
fix both implementations agree bit-for-bit on the trace. NO semantic law was
adopted; none was needed. Recorded in FIDELITY_MANIFEST.md.

## FREEFALL ESTIMATOR — PREMISE NOTE (not a re-tune)

The env's collapse latch (y<0.20) freezes the trace at tick 51-52; the frozen
tail diluted the second-difference mean to 0.2614 (the old "measurement"). The
estimator now runs on the pre-latch window only (latch_tick recorded), and the
magnitude is taken (the falsifier's 9.80665 is a magnitude; the fall is in -y).
Threshold untouched. The frozen-tail value is still recorded
(g_frozen_tail_estimator) for honesty.

## C1/C2 — REMAINING RESIDUAL, PRECISELY ATTRIBUTED

Post-fix trajectory fidelity: the hind pad gaps match the C++ to 6 decimals
through tick 8; the fore MP pads graze the plane at 1e-6..1e-5 (scene design:
the fore sole sits AT the solver's knife edges — kTouch=1e-5, the poscorr
trigger -1e-6, the CoP flat-window 2e-6). Per-substep diff shows the first
discrete divergence at tick-1 substep 1: the impact projection's cone-validity
mask choice (project_rows' lam < -1e-10 test and the 42-step localization)
flips under 1e-12-scale fp-order noise between inverse_spd18 and the C++
inverse_spd, at the fore-MP contact rows. The flip selects a different active
set -> O(0.1-1) rad/s fore velocity differences from tick 4 (v15/v17), which
destabilize the settle: the GPU refuses rc=5 at tick 40-41 / rc=3 at 62-63
(the host replay jitters vs the DLL exactly as the flip jitters) while the
C++ survives to 302. The hind trajectory itself re-converges to the constraint
manifold every tick (1e-5).

VERDICT: C1/C2 remain RED but the refusal is no longer a fixed translation
defect chain — it is fp-seeded chaos through a discontinuous constraint
switch at the fore-MP knife edge. The next fix is NOT mechanical: it requires
either byte-matching the solver's fp order to the C++ (both sides' summation
order in project_rows/gram_factor, already structurally identical) or a
preregistered premise change to the scene/probe (the fore sole resting exactly
on the solver's 2e-6/1e-5/-1e-6 thresholds). Named pair: kernels lam vs C++
lambda at the -1e-10 cone boundary, fore-MP rows, tick-1 substep 1.

Refusal-tick trajectory across the lane: 39 -> 40 (DLL, rc=5), 63 (host
replay, rc=3); survival median 39.0 -> 53.0; hind/fore still 0 fires (the
settle never completes).

## C3 — STILL INVALID, SAME FLAG

1024/1024 and 4096/4096 envs refuse (median horizon 53), so the recorded
38.5M/143.8M eps are still dead-env dispatch (0.03 ms/tick short-circuit).
The valid number needs C1 alive first. Memory (C4): 14.15 GB shared GPU, no
fire.

## BARS VERDICTS AFTER THE FIX — DEFINITIVE RUN (bars_split_b32.json,
## walker_env.dll @ 15:38 2026-09-22, block 32, full fix set)

- F-FULLPORT-PROBE-PARITY freefall: GREEN — measured_g = 9.80665,
  err = 1.08e-12 <= 0.01 (pre-latch window; latch_tick=52 recorded;
  g_frozen_tail_estimator = 0.2554 kept for honesty; drop = 0.1473 m).
  FIRST FALSIFIER GREEN ON THE NVCC ROUTE.
- stand: RED — max_scaled_diff = 0.09647 (bar < 1e-2; was 0.1278); same
  fore-pad knife-edge attribution as C1/C2 (the fore limbs diverge at tick-1
  substep 1 through the impact projection's mask choice; the hind tracks the
  C++ to 1e-5 and re-converges to the constraint manifold every tick).
- C1 nominal: RED — horizon 40, class 5, hind_fires=0, fore_lifts=0 (bar:
  >=1 hind fire AND >=1 fore lift by 150). Refusal moved 39 -> 40.
- C2 survival: RED — pass_100 = 0/64, median 53.0 (was 39.0); horizons
  40-57 (modes 53x27, 41x17, 54x10), classes {5: 53, 3: 11} — the settle
  never completes, seed-independent.
- C3 throughput: 30.8M eps @1024 / 140.0M eps @4096 — STILL INVALID (all
  envs refused; 0.03 ms/tick dead-env dispatch). Re-measure after C1.
- C4 memory: no fire — 15.02 GB used (shared GPU), +0.0005 MB/env marginal.

## FILES (this lane)

walker_numba_split.py (the three fk_eval fixes + the store-bisection slot fix
scales[d-1]=mid + the 'K book' device-print removal), walker_kernels.cuh
(regenerated, numba2cu v4 — verified to contain only the intended diffs),
walker_env_host.py (build_env_arrays extracted), dump_shim.py, host_loop.cxx
(HL_NOCONTACT/HL_NOPOWER/HL_NOGAIT/HL_SETTLE knobs + HL_FULL dump),
cpu_probe.cpp (CP_FULL + CP_CFG), diag_dll_walk.py, diff_walk/diff_matrix/
py_fk/py_fk_full/py_fk_dyn/gap_track.py, grav_probe/grav_probe2/inv_probe/
rate_probe (C++-side interrogators), inject_probe.py + gait_controller_instr.hpp
(throwaway instrumented copies; the tracked reference header untouched),
build_host_loop.cmd / build_probes.cmd / build_dll.ps1 / rebuild_dll_bg.ps1,
host_shim/ regenerated.

---

# CLOSEOUT-2 APPENDIX — the byte-match lane (2026-09-22, agent GLM 5.3)

Branch agent/typeb-gpu-finish-20260922 @ b8cacfa7+. Mandate: byte-match the
solver path's fp order to the C++ reference (the lead's route; the fore-sole
premise change stays forbidden and was NOT done). Method: a per-substep drill
pair — cpp_substep_probe_instr.exe (the C++ evaluate() with SUBPRE/TAUFULL/
SUBFULL per-substep dumps via gait_controller_instr.hpp, itself instrumented
through coupled_articulation_instr.hpp) vs substep_probe.exe (the translated
kernels' host replay with the same dumps via probe_inject.py) — diffed at
token granularity by diff_census.py; full-walk traces diffed by diff_trace.py.

## THE CENSUS (knife-edge decision sites, ranked by divergence contribution)

The named wall — "tick-1 substep-1's impact projection cone-validity mask at
the fore-MP pads, flipped by 1e-12-scale fp-order noise between inverse_spd18
and inverse_spd" — was reproduced and RE-ATTRIBUTED. The two inverse_spd
implementations are source-order identical (their fp order already matches;
no reduction-order/grouping/cast difference exists). The noise that flipped
the mask was NOT fp-order noise: it was STRUCTURAL error generated upstream in
fk_eval and in the translator, and one drill-harness defect. Ranked:

1. numba2cu int_kind (THE BIGGER KILL — a REAL defect in every DLL built
   before this lane): any assignment whose RHS merely CONTAINS a comparison
   was typed int. `store = bat[d-1] if (d-1) < 12 else bat_post` became
   `int store` — the posture battery drained to zero at tick-1 substep-1, so
   tau2 (the 11.2125 N·m posture torque) was DEAD FROM TICK 1 ON in every DLL
   bars run to date. Same class: `bound` (the event-localization joint bound)
   was truncated to int. int_kind now follows both branches of a ternary.
2. fk_eval world-axis Jacobians: the axis direction was computed as COLUMN
   SUMS of pfp (not a rotation application), and the preceding same-body
   rotational composition was missing — the free-root tilt. Measured: the
   kernels' slot-2 column was exactly (0,0,1) where the reference carries
   (9.818e-7, 5.112e-8, 0.99999999999952); M[2][5] was exactly 0 where the
   reference measures 1.357248550688573e-06 at the same q.
3. rot_axis: direct sincos form vs the reference's Rodrigues
   identity()+k*sin(v)+(k*k)*(1-cos(v)) — different bits at every nonzero
   angle; invisible in freefall (zero pose), which is why it survived.
4. ptJ/contact rows and ptp/ptbias: apply_point's addition order (translation
   term LAST) vs vector()'s (FIRST) — ulp noise injected directly into the
   gap/CoP knife-edge values (2e-6/1e-5 bands).
5. frd/frdd: per-term-*fc-then-add vs product()'s sum-first-then-one-fc.
6. alpha: 3x3-only transpose dropped the col3/row3 outer terms of
   f.dt*transpose(f.dt).
7. Iw: single-pass R(i,k)*(I_k*R(j,k)) vs the reference's two-pass
   (f.t*inertia)*rt.
8. Drill harness: substep_probe's store_post hardcoded 1.0; the reference
   uses drives_[0].store_floor = 78.732.

## BYTE-MATCH VERDICT PER PATH

- inverse_spd18 vs inverse_spd: SOURCE-IDENTICAL operation order (Cholesky,
  forward/back substitution, the same reduction order). No ordering fix
  needed; the GPU side got nvcc -fmad=false (build_dll.ps1) so the device
  rounds like the cl reference. Gate met at every drilled substep once its
  INPUTS (M) were bit-matched.
- fk_eval M/gv/bv: after fixes 2-7 the host-vs-host (cl/cl) residuals are
  0.5-3.2 ulp on M entries, 1.5 ulp on gv2 — NOT yet bit-exact. The named
  remaining pair: the tables/phi interpolation path (tau 1-2 ulp: tau9/tau13)
  and the residual Jacobian-path ulps.
- Tick 1: END-OF-TICK-1 STATE BIT-EXACT (host replay vs C++, all 36
  components); GPU DLL ulp-level (max rel 7.6e-15, was 1.4e-5 — 10 orders).

## DISCRETE-DIVERGENCE COUNT, TICK 1..40 (before -> after)

- Before: first divergence tick-1 substep-1 (the named wall); O(1e-5) state
  injection; fore velocities O(1) by tick 4; host horizon 63 rc=3, GPU 40-41
  rc=5.
- After: tick 1 bit-exact (host) / ulp (GPU). The remaining residual ulp
  noise still trips ONE degenerate discrete decision: a second active-set tie
  inside tick-2 substep-2 (host) / tick 4 (GPU) — two masks are cone-valid
  within <1e-15 of each other at the settle's fore rows, i.e. the scene parks
  an EXACT tie on the solver's knife edge, and last-ulp rounding decides it.
  Count of discrete-divergence sites in ticks 1..40: was >=1 at tick-1
  substep-1 plus the flip cascade from tick 4; now exactly 1 (the tick-2/4
  tie). After the tie the trajectory is O(1) different and every later
  discrete decision differs — the refusal (rc=3 at tick 41/42) is downstream
  of that single tie.

## FROZEN BARS RE-RUN (bars_split_b32.json, walker_env.dll rebuilt with
## -fmad=false + all fixes above, block 32; thresholds untouched, nothing
## re-tuned)

- F-FULLPORT-PROBE-PARITY freefall: GREEN — measured_g = 9.806650000000689,
  err = 6.89e-13 <= 0.01 (was 1.08e-12). Still the only green.
- stand: RED — max_scaled_diff = 0.0699 (was 0.0965; bar < 1e-2). Improved
  by the posture-store repair (tau2 now alive) but the tie flip still
  diverges the fore limbs.
- C1 nominal: RED — horizon 41, class 3 (was 40, class 5), hind_fires=0,
  fore_lifts=0.
- C2 survival: RED — pass_100 = 0/64, median 41 (was 53); horizons 41-55,
  classes {3: 53, 5: 11}.
- C3 throughput: 58.5M eps @1024 / 224.5M eps @4096 — STILL INVALID (all
  envs refused; 0.018 ms/tick dead-env dispatch).
- C4 memory: no fire — 19.93 GB used (shared GPU), -0.0005 MB/env marginal.

## UPDATED ATTRIBUTION (what remains red, and why)

The refusal is no longer a translation-defect chain and no longer unexplained
fp-order noise: the port now tracks the reference bit-for-bit through tick 1
and to 1e-15 relative through tick 3. What remains red is decided by a
SCENE-DESIGN DEGENERACY: at the settle the fore-MP/heel active set is an
EXACT tie (two masks cone-valid within noise <1e-15 — the lam values sit on
the -1e-10 boundary to within a few ulps because the correction is degenerate
when the fore sole rests at 2e-6 gaps with near-parallel contact rows). Any
remaining ulp difference (tables/phi interpolation, residual Jacobian ulps,
or nvcc-vs-cl transcendental implementations on the GPU) picks a mask and the
settle diverges O(1). The route to GREEN is therefore either (a) finish the
byte-match to FULL bit-equality — the named next pair is the tables/phi
interpolation path and the residual 1-ulp M entries; the GPU additionally
needs libdevice-vs-CRT transcendental parity measured — or (b) the forbidden
preregistered premise change (move the fore sole off the knife edges), which
this lane did NOT do per mandate. Deferral honesty clause: unchanged — no
deferred law engages anywhere near ticks 1-55.

---

# CLOSEOUT-3 APPENDIX — the bit-match lane completed to the tie (2026-09-22, agent GLM 5.3)

Branch agent/typeb-gpu-finish-20260922 @ 7a845267+. Mandate: closeout-2's named
next pairs — tables/phi interpolation, residual Jacobian ulps, the
libdevice-vs-CRT question, and the host-parity bound. Method: per-body
contribution drills (CPPFK2/FKDBG2 jv·jw per body, CPPFK3/FKDBG3 Iw + per-body
M[0][0]/M[2][2] contributions, CPPFK4/FKDBG4 rate checkpoints FRHS/RHSIN/FMUL/
FPROJ), all committed.

## THE PAIRS, CLOSED

- PAIR 1 (tables/phi interpolation, tau9/tau13): the interpolation was never
  the defect — at the drill phases phi = 0/0.5 exactly, so f = 0 and every
  interp is exact. The real source was THE GAIN ANCHOR: walker_model's numpy
  mass mirror cannot reproduce Model::evaluate()'s scalar fp order, and its
  defaults-pose diagonal differs from the reference at coordinates
  0,1,2,9,13,14,16 (cpu_probe.exe diag vs spec.mass_diag) — so the
  mass-normalized gains kp=m*freq*freq / kd=2*ZETA*m*freq carried 1-ulp errors
  at drives 4/8 (the hind MPs = exactly the census's tau9/tau13), 9/11, and
  the posture drive. FIXED: GAIN_ANCHOR_DIAG pinned to the reference's own
  bits (cpu_probe diag); TAUFULL t=0 sub=0 went BIT-EXACT 20/20.
- PAIR 2 (M/gv/bv Jacobian ulps, 0.5-3.2 ulp): FIVE stacked defects, each
  isolated by the drills: (1) BODY ORDER — the C++ Model::Model insertion
  continues the alphabetical map scan from the erase point; the replica
  restarted, producing a different bodies_ order and therefore a different
  M/gv/bv ACCUMULATION order (the drill showed per-body masses misaligned
  across implementations). walker_model now replicates the exact semantics.
  (2) M/bv assembly — the C++ adds e.mass[..] += X + Y as ONE add of the
  pre-summed pair; the port rounded twice ((acc + m*jvd) + jwd). Same class in
  bias. (3) RK combine — the C++ computes h*(a+2b+2c+d)/6; the port
  pre-divided h/6 (different rounding). (4) rate rhs — the C++ adds
  rhs[i] += tau[i] - damping*v as one add of the pair; the port rounded twice.
  (5) hypot — the C++ uses std::hypot at the planar-slip and friction-accel
  sites; sqrt(x*x+y*y) differs in final bits. Plus gram_factor4 now
  symmetrizes ((g_ij+g_ji)/2) like the by-value C++ gram_factor — inner
  (r_a, inv*r_b) is bitwise asymmetric for a != b, so skipping the average
  factors a different Cholesky exactly at the cone boundary.
- RESULT: the substep census (csub_t5 vs ksub_t5, ticks 0..4) shows EVERY
  SUBPRE and TAUFULL record BIT-EXACT (398/398, 20/20) through tick 3 sub 2;
  the rate checkpoints FRHS/FMUL/FPROJ are BIT-EXACT at the armed call; the
  first three aligned walk states are BYTE-IDENTICAL (cp t=0,1,2 ==
  hl t=1,2,3; closeout-2 had ulp-level everywhere). PAIR 4's hypothesis is
  CONFIRMED at the new bound: the host parity extends until the tie.
- THE TIE, RELOCATED AND NAMED: the host replay now fires it inside tick 3's
  substep-2 -> 3 (SUBPRE t=3 sub=3 is the first diverging census record; was
  tick-2 substep-2 in closeout-2). With a BIT-EXACT entry state, the divergence
  is a discrete fore-limb event (v14..v17 injected at O(1e-2), tau14/16 at
  O(2.6e-3)) inside the advance's event interior — the joint-wall/clamp/
  projection localization on the fore shoulders/elbows, which sit exactly on
  their bounds at the fore entry pose. Named for the next lane: the wall/
  bisection interior at tick-3 substep 2->3, fore rows.
- PAIR 3 (libdevice-vs-CRT), DISPOSED BY MEASUREMENT (trig_probe.cu /
  trig_probe_host.cxx, trig_inputs.txt = the 12 live tick-1 rotation angles +
  a synthetic IK grid): 31 of 125 sampled evaluations differ in the FINAL BIT
  between libdevice and the MSVC CRT — SIN 5/25, COS 5/25, ATAN2 6/25,
  ACOS 4/25, HYPOT 11/25, always exactly 1 ulp, INCLUDING on the live tick-1
  axis angles. Route (a)/(b) therefore cannot reach GPU bit-equality without
  porting the UCRT sin/cos/atan2/acos/hypot implementations into the kernels
  (a full UCRT-math port, its own lane). Route (c) is taken for the verdict
  below: the GPU carries a measured, named, 1-ulp-class transcendental
  deviation on top of the scene's own tie.

## FROZEN BARS RE-RUN (bars_split_b32.json, walker_env.dll rebuilt 19:56 with
## all closeout-3 fixes, nvcc -fmad=false, block 32; thresholds untouched)

- F-FULLPORT-PROBE-PARITY freefall: GREEN — measured_g = 9.806650000000689,
  err = 6.89e-13 <= 0.01 (unchanged; still the only green).
- stand: RED — max_scaled_diff = 0.1082 (was 0.0699; bar < 1e-2). The tie
  fires inside the stand window either way; the metric is not monotone in the
  tie position.
- C1 nominal: RED — horizon 41, class 3, hind_fires=0, fore_lifts=0
  (unchanged vs closeout-2).
- C2 survival: RED — pass_100 = 0/64, median 41.0, classes {3: 53, 5: 11}
  (same distribution as closeout-2).
- C3 throughput: 2.3M eps @1024 / 6.2M eps @4096 — STILL INVALID (all envs
  refused -> dead-env dispatch) AND contention-polluted (the 4090 was shared
  at 100% during this phase; the clean-machine reference remains closeout-2's
  58.5M/224.5M eps).
- C4 memory: no fire — 24.90 GB used (shared GPU, near-full from co-tenants),
  marginal +0.0026 MB/env.
- GPU WALK (dll_walk_c3 vs cpu_probe 45): the GPU tracks the reference to
  ulps through ticks 1-3 (max rel 3.6e-15 at t=0, 8.9e-14 at t=1, 3.3e-15 at
  t=2 — the pair-3 transcendental ulps, visible but sub-discrete), the SAME
  discrete tie fires at the same tick as the host (aligned t=3), and the
  refusal moved 41 -> 42 (rc=3).

## FINAL ATTRIBUTION

The port is now bit-exact against the cl-compiled reference through the first
three walk states on the host replay, and ulp-level (measured libdevice 1-ulp
transcendental deviations) through the same window on the GPU. What remains
red is decided by (i) a SCENE-DESIGN degeneracy — the fore limbs' entry pose
sits exactly on the joint-wall/localization knife edges, so the discrete event
inside tick-3 substep-2->3 decides the settle — which reproduces on BOTH
implementations from bit-identical state, and (ii) on the GPU only, the
measured 1-ulp libdevice-vs-CRT transcendental deviations. The lawful routes
to GREEN remain: finish the byte-match inside the event interior (the named
next pair), or the forbidden preregistered premise change (not done). The
deferral honesty clause: unchanged — no deferred law engages near ticks 1-55.

# CLOSEOUT-4 APPENDIX — pairs 4-8 fixed; host bit-exact through 41 aligned walk states (2026-09-22, agent GLM 5.3)

## METHOD

The tick-3 interior was drilled with a line-aligned ADVTRACE pair (probe_inject.py
sections 9-15 mirrored into gait_controller_instr.hpp, the drill surface): per
advance call ent/imp/split/live/evt/clamp/cross/wallev/end, per free_step the
plane census (FST) and the RK4 end state (FSEND), per rate() call the FRHS/FMUL/
TOUCH/FFRIC/FPROJ checkpoints, per contact-scan point the gap decision (RTSC),
per friction solve the direction inputs and 2x2 internals (RTFRI/RTFS/RTFSC/
RTFRO), per impact the touching/gap census and friction catches (IMPE/IMPF/
IMPP) and the poscorr gram (IMPC). The tick window arm was moved 3 -> 41 as the
extent grew.

## THE FIVE NAMED AND FIXED PAIRS (all in walker_numba_split.py)

- PAIR 4 (crossing-time bisection): the contact-crossing localization tested
  gap_of_k on the ptp scratch left by the LAST RK STAGE inside free_step
  (stage-d at (qd,vd)) instead of evaluating the free_step's END state; the C++
  computes gap_of(evaluate(free_step(...)),k). One branch flipped at bisection
  iteration 31 (fore-pad landing, tick-3 substep-2), moving the crossing time
  5e-5 relative. FIXED.
- PAIR 5 (end-state save): C++ advance holds `end` AS A VALUE through the
  drive-stop and contact scans; the port's qe/ve/we were clobbered by each
  bisection's 42 free_steps, so the point-6 pre-test read +7.0e-7 (the mid
  state) instead of -2.9e-5 (the end state) and skipped a landed fore pad.
  FIXED: save end_q/end_v/end_w after the main free_step; the scan pre-test,
  the per-point re-test and the plain-end commit read the copy.
- PAIR 6 (friction row): rate()'s friction loop solved against the shared rn
  scratch left at the LAST point of the touching loop (point 3's row) where the
  C++ keeps per-point rown[k]; measured B=15.59 vs 0.29 on point 2's solve.
  This path is dead until the first fore-pad touch (the hind gaps ride above
  kTouch), which is why it survived the tick 0..3 census. FIXED: refresh rn
  per point.
- PAIR 7 (swallowed requires): the C++ impact friction-catch applies the
  velocity change THEN require()s loss/share_n/share_t; a throw keeps the
  change but skips caught/ledger. The port booked caught unconditionally
  (measured 0.274 vs 0, r=0 slide at the tick-41 entry). FIXED: the guards are
  computed in the reference order and gate the caught update.
- PAIR 8 (poscorr gram): the gram build wrote stride 4 while gram_factor4 reads
  stride npen (g10/g11 unwritten -> pivot failure -> the correction skipped
  while the reference applied it), and the operand order was transposed
  ((inv*row_a).row_b vs the reference's row_a.(inv*row_b)). FIXED both; the
  tick-41 poscorr now succeeds with bit-identical multipliers.

Also enlarged the LIFO interval stack 16 -> 64 slots (sq 576 -> 2304) against
the depth-58 budget; this did NOT clear the tick-42 fault (below).

## MEASURED EXTENT (the gate numbers)

- SUBSTEP CENSUS ticks 0..4: SUBPRE 20/20, TAUFULL 20/20 BIT-EXACT; SUBFULL
  20/20 BIT-EXACT at the correct sub alignment (the diff_census.py sub offset
  is a known artifact; its t-offset does not apply).
- TICK-3 INTERIOR: the full ADVTRACE pair through tick 4 is line-identical
  (was: first divergence inside tick-3 substep-2->3 with a bit-exact entry).
- TICK-41 INTERIOR: 1008/1010 drill lines identical across the whole tick.
- WALK (cp_walk45 vs hl_walk45): host replay vs cl reference BIT-EXACT at 41
  consecutive aligned states (host ticks 1..41 == cpp ticks 0..40; closeout-3:
  3 aligned states). First divergence: host tick 42 (cpp tick 41) with the
  entry state bit-exact: v9 -31.77 vs -22.20 (the collapse transient).
- THE NEXT NAMED DEFECT: at the tick-42 boundary the host replay SEGFAULTS
  (exit 139, no MSVC symbols) right after the n=112 plain-end evt print, where
  the reference continues. The interval stack was enlarged 16 -> 64 without
  clearing it; the fault is the next lane's first object.

## FROZEN BARS RE-RUN (rebuilt DLL, nvcc -fmad=false, block 32; thresholds untouched)

| bar | value | threshold | verdict | closeout-3 |
|---|---|---|---|---|
| freefall g | 9.806650000 err 6.89e-13 | <=0.01 | GREEN (still the only green) | same |
| stand scaled diff | 9.511e-01 | <=1e-2 | RED | 0.1082 |
| C1 nominal class | horizon 40 class 5 hind=0 fore=0 | fire by 150 | RED | horizon 41 class 3 |
| C2 survival | 0/64 median 40.0 | >=0.8 pass-100 | RED | 0/64 median 41.0 |
| C3 throughput | 53.36M eps b1024 / 227.6M eps b4096 | >=968M b1024 | RED (dead-env dispatch, all envs refused) | 30.8M/140.0M at c2; contended numbers not clean-comparable |
| C4 memory | no fire | ceiling | GREEN | no fire |

The stand/C1/C2 movements (0.108 -> 0.951, median 41 -> 40) are the same
scene-design knife edges firing at different ticks now that the dynamics are
bit-exact to tick 41 on the host and ulp-exact on the GPU: the GPU keeps the
31/125 measured 1-ulp libdevice-vs-CRT transcendental deviations (trig_probe),
so its discrete ties land one tick either side of the reference's. No threshold
was touched; nothing was re-tuned.

## TARGET B (transcendental class) STATUS

The 31/125 sampled libdevice-vs-CRT deviations (SIN 5, COS 5, ATAN2 6, ACOS 4,
HYPOT 11; always exactly 1 ulp) remain OPEN. The lawful port route requires the
reference's own algorithm; the UCRT math sources are NOT shipped in this
BuildTools install (Windows Kits 10 Source ucrt/ has no math implementations),
so the fdlibm fallback is only lawful IF a bit-for-bit probe proves fdlibm ==
UCRT at all 125 points before committing the port. That proof was NOT completed
this session; no kernel transcendental was replaced. The GPU walk residual
therefore remains the measured 1-ulp class, not a new defect.

# CLOSEOUT-5 APPENDIX — the tick-42 segfault root-caused as an mdi/csti swap; host bit-exact through 60 aligned walk states; Target-B routes (1) measured and (2) fully mapped (2026-09-23, agent GLM 5.3)

## TARGET A — the tick-42 segfault: CAUSE NAMED AND FIXED

- ROOT CAUSE (NOT the interval stack): walker_numba_split.py defined
  `fore_follow(mdl, cst, fr, leg, paw_t, branch, mdi, csti, result)` but BOTH
  call sites (4791, 4820) passed `(csti, mdi)`. Inside fore_follow the entire
  fore-follow chain (fore_target_headroom -> fore_ik_at) then read
  `c1 = mdi[OI_fore_coord + leg*2]` from `csti + 204` — 184 ints past the
  20-int csti array — and clamped q1/q2 against garbage bounds. cdb (committed
  co5_crash_cdb.txt): access violation c0000005 at `fore_ik_at+0x274`,
  `movsd xmm0,[rbp+rbx*8+14E0h]` = `mdl[OF_lower(668)+garbage]`,
  rbx=0xffffffffedd1b8ae; stack fore_ik_at <- fore_target_headroom+0x83 <-
  fore_follow+0x148 <- tick_plan_kernel. Same defect, two faces: the
  instrumented build read a huge garbage int and SEGFAULTED (exit 139 right
  after the n=112 plain-end evt print); the plain build read a benign garbage
  int and produced the old v9 -31.77-vs--22.20 tick-42 divergence. The C++
  reference reads member tables directly (no tables to swap); the Warp
  original carries them in typed structs — the swap was introduced by the
  numba translation's table threading. FIXED at both call sites; the
  walker_kernels.cuh + probe_kernels.cuh regenerated (numba2cu v4 +
  probe_inject).
- The prior lane's interval-stack enlargement 16->64 without clearing is
  CONFIRMED REAL (the four clear loops still clear 16 slots) but measured
  BENIGN: sq is dead scratch (written, never read), and the sh/sdep/scl pops
  only touch slots below sp, with sp <= depth <= 58 < 64. Left untouched.
- MEASURED EXTENT AFTER THE FIX: plain walk runs past tick 100 (old: refused
  rc=3 at tick 48); drill runs to tick 100 exit 0 (old: exit 139 at the
  tick-42 boundary); HOST-VS-C++ BIT-EXACT AT 60 CONSECUTIVE ALIGNED WALK
  STATES (host ticks 1..60 == cpp ticks 0..59; closeout-4: 41) against a
  fresh 120-tick cl reference walk (cpu_probe CP_FULL, committed
  cp_walk120.txt / hl_walk60.txt).

## THE NEXT NAMED DEFECT (tick 61, pair 9 class: silent plan-phase fore-left)

The drill window was moved 41 -> 60 (probe_inject.py + gait_controller_instr.hpp).
At cpp tick 60 the ENTIRE advance interior is again line-identical (604/604
drill lines through FST n=9 and the first ADV), but the FIRST rate checkpoint
already differs: `RT n=0 FRHS` components 14/15 (the fore-left shoulder/elbow
drives) — K -0.035969703327963329 vs C -0.035969703327966049 and
K 0.8387826210296021 vs C 0.83878262102960255 (~390 ulps at rhs[14]) — i.e.
tau[14]/tau[15] reach rate() already divergent: a SILENT difference in the
plan-phase fore-left follow pipeline (capture/seat/PD target), upstream of
every instrumented site. PAIR 9 (13 sqrt-vs-hypot sites fixed to the
reference's std::hypot: fore_ik_at, fore_D_at, hind_ik_at, the 6 branch-choice
err sites, the 2 seat-touch checks, the slip and chain-normalization sites —
walker_numba_split.py now uses math.hypot everywhere the reference uses
std::hypot) did NOT move this divergence (measured: same values before/after),
so the ulp source is elsewhere in the fore-left pipeline — the next drill
needs a SEAT/PD-target checkpoint section in probe_inject + instr hpp.

## TARGET B — route (1) MEASURED AND FAILED ITS GATE; route (2) FULLY MAPPED

- ROUTE (1), the preregistered fdlibm probe: ported netlib fdlibm
  (s_sin/s_cos/e_atan2/e_acos/e_hypot/e_rem_pio2/k_rem_pio2/k_sin/k_cos,
  /D__LITTLE_ENDIAN word order, __ieee754_sqrt -> the correctly-rounded CRT
  sqrt) into a host probe (trig_fdlibm.cxx; fdlibm_ref/ committed) and
  bit-compared against trig_host.txt at the trig_probe's 125 points:
  115/125 IDENTICAL, 10/125 differ ALWAYS EXACTLY 1 ULP (SIN 2, COS 1,
  ATAN2 4, ACOS 0, HYPOT 3). The 125/125 adoption gate does NOT pass: UCRT
  is not fdlibm. No kernel transcendental was replaced on this route.
- ROUTE (2), the UCRT algorithm identification — COMPLETE at the structure
  and constants level, per the standing order's "the DLL on disk is the
  ground truth": the reference links the STATIC UCRT (libucrt.lib), and its
  actual math objects were extracted from disk (extract_ucrt_math*.ps1,
  ucrt_objs/): sin.obj, cos.obj, atan2.obj, acos.obj, hypot.obj (SSE2 + FMA3
  variants), lsincos_array.obj (the polynomials), rempiby2_fma3.obj (the
  reduction). MEASURED ON THIS MACHINE: __isa_available=5 (AVX512),
  __use_fma3_lib=3 -> THE LIVE PATH IS THE FMA3 VARIANT.
- IDENTIFIED STRUCTURE (from the committed disasms + .rdata): sin entry
  dispatches on __use_fma3_lib; |x|<2^-27 returns x*(1-|x|^2/6-ish);
  2^-27<=|x|<pi/4 runs a degree-13-ish odd polynomial via a 6-step vfmadd
  Horner chain; |x|>=pi/4 calls __remainder_piby2_fma3(_bdl) (exact pi/2 as
  lead+3 parts: 0x3ff921fb50000000 / 0x3e5110b460000000 /
  0x3c91a62633145c06, plus the extended piby2_1/1tail/2/2tail/3/3tail chain
  and the round-to-nearest sigma 6755399441055744.0), then sin/cos
  polynomials selected by n parity with sign fixups.
  THE UCRT POLYNOMIALS (lsincos_array.obj, exactly):
    sin: -1.6666666666666666e-0/1 = 0xbfc5555555555555, S2 0x3f81111111110bb3,
    S3 0xbf2a01a019e83e5c, S4 0x3ec71de3796cde01, S5 0xbe5ae600b42fdfa7,
    S6 0x3de5e0b2f9a43bb8  (fdlibm-ADJACENT but different low bits — that is
    the measured 1-ulp class);
    cos: C1 0x3fa5555555555555, C2 0xbf56c16c16c16967, C3 0x3efa01a019f4ec91,
    C4 0xbe927e4fa17f667b, C5 0x3e21eeb690382eec, C6 0xbda907db47258aa7.
- WHAT REMAINS FOR THE NEXT LANE (precisely scoped): (a) write the C/fma
  reconstruction of the FMA3 sin from the committed disasms
  (ucrt_objs/*.disasm regenerable by the committed scripts), verify
  bit-exact vs the CRT at the 125 points + dense random sweeps; (b) repeat
  for cos (same machinery), then atan2/acos/hypot (own objects, same drill);
  (c) port into the kernels with EXPLICIT fma() in the vfmadd order (CUDA
  fma() stays a real fused op under -fmad=false); (d) the gate: the
  on-device trig_probe re-run matches the CRT bits at every point.
- NO ASSUMED EQUIVALENCE was used anywhere: the fdlibm adoption failed its
  probe and was not adopted; the UCRT port has not been written yet, so no
  kernel transcendental changed in this session. The GPU's measured
  31/125 1-ulp libdevice-vs-CRT class therefore still stands.

## FROZEN BARS RE-RUN (walker_env.dll rebuilt 01:34 from the pair-9-fixed
## kernels, nvcc -fmad=false, block 32; thresholds untouched)

| bar | value | threshold | verdict | closeout-4 |
|---|---|---|---|---|
| freefall g | 9.806650000000689 err 6.89e-13 | <=0.01 | GREEN | GREEN |
| stand scaled diff | 9.5112e-01 | <=1e-2 | RED | 0.9511 |
| C1 nominal class | horizon 40 class 5 hind=0 fore=0 | fire by 150 | RED | same |
| C2 survival | 0/64 median 40.0 classes {5:…,3:…} | >=0.8 pass-100 | RED | 0/64 median 40.0 |
| C3 throughput | 65.79M eps b1024 / 257.7M eps b4096 (0.016 ms/tick) — dead-env dispatch (all 1024/4096 envs refused), NOT clean-comparable | >=968M b1024 | RED | 53.4M/227.6M |
| C4 memory | no fire; 23.69 GB used (1.63 GB free), marginal -0.0005 MB/env | ceiling | GREEN | no fire |

The bars are UNCHANGED in verdict and value at three decimals where
comparable: the discrete knife edges the bars ride fire at ticks 40-41,
BEFORE the host's new bit-exact frontier (60), and the GPU still carries the
measured 31/125 transcendental class. No threshold touched; nothing re-tuned.
