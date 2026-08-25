# THE TRIANGLE CARRIER — triangles are matter elements; the CA over them

*2026-08-23. Rule 0 shell: named before build, per the law.*
**Provenance flag:** operator data recorded verbatim below is his words (2026-08-23 session);
where a clause is synthesis from repo data it is flagged. "k with memory" is MY framing of
his timeline law — not yet his words; it stays flagged until he signs it.

## WHY TRIANGLES (the geometry, one free mode)

A triangle is the smallest element that is rigid in its own plane and still has **one**
free mode left: area. That one mode is the CA variable — strain scalar `aᵢ/A₀` plus
stiffness `k`. Three vertices, one number per element: the same one-buffer doctrine as
the splat era's 14 variables (`web/renderer/splat.wgsl`, top of file — pos3+opa / col3+
_p0 / scale3+_p1 / quat4 = 16 f32, derived never stored), with triangles as elements.
His words: *"you need a triangle in order to create this spring"*; the CA is
*"a calculus equation brought to a footstep"* — finite-difference elasticity on a
triangle lattice.

## THE SHARED-EDGE LAW

Solidity is a **shared-edge law**: springs live on edges, not vertices, and there is no
long-range part. The edge spring IS RESISTANCE at element scale (`THE_LIGHT_SEED`: M=0
the bond, M<0 the wall). Neighbors do not tear — they spring; elasticity is the bond law.

## THE SPRING GATES (before any build)

- **A₀ from import** — bit-exact chain already proven: TEST B2 readback |duv| = 0.0 exactly
  (`docs/THE_UV_METHOD.md`); `THE_TRANSLATION` Run 3 mass err 0.000%, iner ≤1.921% vs tol 2%.
- **k derived, never picked** — precedent in-repo: M3 hip bond
  `k_rot = W·0.0166 / 0.0175 = 23.5 N.m/rad` from single-support moment + deflection bound
  (`tools/kernel_walk.py` L17–20); the joint must LOOK rigid on the scale the stability
  margins were derived at. Door-material tag (THE_TRANSLATION law 4) is the other source.
- **Band clamp, derived like THETA_CLAMP 0.24 rad** — the strain update is a linearization
  valid only inside its band: `|sin t − t|/t ≤ 1% → t ≤ 0.244` (`LightEngine/kinematic/
  dynamics.py` L172–174); beyond the band it was measured wrong **in kind, not degree**
  (unclamped corrections scrambled small-link orientations into pi-flips). The triangle
  analog: k derived at A₀ stays ≤1% accurate while `|aᵢ/A₀ − 1|` is inside a named band;
  beyond it the clamp fires and the membrane says so — a static hold that trips the clamp
  is a falsifier, not a feature.
- **Energy gate** — spring PE + KE drift < 1% through his existing falsifier (THE_
  TRANSLATION's conservation contract applies to the CA field exactly as it did to packets).

## k WITH MEMORY (flagged synthesis)

Loaded triangles hold their loading in stiffness: a type is a modifier shaped by a
timeline (`THE_LIGHT_SEED`, verbatim). The timeline lives INSIDE the membrane — no second
state buffer. This is the genuine contribution beyond textbook FEM, and it stays flagged
until he signs it in his words.

## THE UE DOOR (adaptation device)

Loads + displays only; **computes no truth.** Contract: bijection ledger
(triangles_in == elements_created), vertex checksum vs an independent parse, mass/inertia
inside `THE_TRANSLATION` tolerances. Dumb pipe by design: the known local distortion is in
OUR export C++ — `/100` + Y/Z axis swap baked into `SetSplatNodeTransform` (`Chimera/
Plugins/MLSLabsRenderer/Source/MLSLabsRenderer/Private/GaussianSplatingRendererLibrary.
cpp` L530–540), with no test against a known pose — that is ours to fix/test, not the box's
fault; UE's internal rendering is exactly what we never ask for truth from.

## STATEMENT / PREDICTION / FALSIFIER

- **STATEMENT:** finite-difference elasticity on the triangle lattice reproduces the shared-
  edge bond law of `THE_LIGHT_SEED` to tolerance, with k derived (never picked) and A₀
  from import — triangles are matter elements, not a render mesh after translation.
- **PREDICTION:** first run = cad_bear at its proven import density: strain field under
  gravity matches the bond-law force read from M within named tolerance; static hold trips
  no clamp; energy gate <1%. (cad_bear because THE_TRANSLATION already proved its mass/
  inertia to the letter — the carrier is tested where the door's numbers stand.)
- **FALSIFIER:** any of — energy drift > 1%; band clamp fires on a static hold (k/A₀ wrong);
  a code path that edits mesh after translation to fix physics (`THE_TRANSLATION`'s own
  falsifier, still in force); ANY drift not produced by the sampler ⇒ **the box is a
  participant** — rebuild the membrane rather than trust the door.

## DECISION: KEEP UE (delegated judgment, flagged until he signs)

Keep UE as dumb pipe; do not build a second engine. The custom engine already exists in-repo
for everything that is truth (GPU field sim + kernel DSL + native wgpu viewer);
"make our own completely" restates what the repo owns and buys nothing new — display-side
months with zero bearing on the launch metric. UE 5.8 confirmed at source (`Chimera/
Chimera.uproject`, PCG plugin enabled). Snap points where this decision dies: (1) the
1M-element DISPLAY must hold inside OUR frame budget in our window (wgpu path already proven
for splats — triangle rasterization there becomes build work); (2) any drift not produced by
our sampler (box = participant, membrane rebuilt rather than door trusted); (3) standalone
shipping without engine dependency becomes a stated goal. Advanced-UE combination sides:
DISPLAY (Nanite shows imported meshes at any density — truth stays our elements; Lumen +
post feed the `U.light` seam already in `web/renderer/splat.wgsl`), AUTHORING (PCG generates
triangle fields that cross the door as authoring; World Partition streams import/display
regions only), OPERATOR-side (the genuine combinations: Sequencer-style tooling composing
LEVER tracks — f32 ∈ [0..1] per intent, behavior authored on inputs never state; net code
replicating levers + seed not state — `theDeterminism` ladder is ours, drift caught by this
doc's checksum falsifier; ML policies writing levers = operator device with an AI at the
wheel). PARTICIPANT LIST (falsifier fires): Chaos GPU sim / cloth / fracture truth, any
engine stepping of our state (`ChaosVehiclesPlugin` enabled in .uproject — same fence: it may
drive a displayed vehicle's wheels, never compute where matter goes). Gate for every feature:
no path from any of these into the element buffer; the lever/force law (M modifier) is the
only entry, per `THE_LEVERS.md`. Not integration-tested this session (no shell); each
gates through its own Rule-0 before build.

## KNOWN-POSE TEST SPECIFIED (algebra from source; no execution)

Full chain read end-to-end — both ends are OURS: `FGaussianSplattingSceneProxy` (`Gaussian
SplattingSceneProxy.cpp` L99–103) reads the component's Location/Rotation/Scale (UE cm) →
library call applies `/100` + axis swap (L536–538: `Translation.x = InTranslation.Y / 100.0;
y = −InTranslation.Z / 100.0; z = InTranslation.X / 100.0`; Scale remap `.x=.y, .y=.z,
.z=.x`) → native DLL. Load + update call sites: `GaussianSplattingComponent.cpp` L106–134.
Pre-derived expected table (component pose → GSR vector sent to the DLL):

| component (L cm / R deg pitch-yaw-roll / S) | GSR translation (m) | GSR rotation (rad) | GSR scale |
|---|---|---|---|
| (0,0,0) / (0,0,0) / (1,1,1) | (0, 0, 0) | (0, 0, 0) | (1, 1, 1) |
| (100,0,0) | (0, 0, +1.0) | — | — |
| (0,100,0) | (+1.0, 0, 0) | — | — |
| (0,0,100) | (0, −1.0, 0) | — | — |
| pitch = 90° | — | (π/2, 0, 0) | — |

Run spec: place a node at each pose in UE, capture the window, compare observed splat
position against this table. FALSIFIER SHARPENED: any failure lands in our proxy/library C++
(both ends of the pipe are ours per source read above) — an Ours bug to fix here; "the box is
a participant" fires only on drift NOT produced by the documented transform above. No free
numbers: every row is algebra from L536–538 + SceneProxy L99–103.

## SOURCE RE-CHECK + CONCRETE UE 5.x FEATURE MAP (continuation, no-shell)

Re-verified at source this session (not memory): the `/100` + Y/Z axis swap is in OUR export C++ — `GaussianSplatingRendererLibrary.cpp` **L529–536** (`x=InTranslation.Y/100; y=-InTranslation.Z/100; z=InTranslation.X/100`; Scale `.x=.y,.y=.z,.z=.x`), and the caller is read end-to-end — `FGaussianSplattingSceneProxy::UpdateSplatTransform()` reads component `Location/Rotation/Scale` (UE cm) → same library call → DLL. Both ends ours, so a known-pose failure = an Ours C++ bug until proven otherwise; "the box is a participant" fires only on drift NOT produced by this documented transform. Line refs corrected here: transform block L529–536 (not L536–538); `H_C` ~L88 of `tools/kernel_policy.py` (not the prior L74).
Concrete UE 5.x map, each gated "no path into the element buffer":
- **Nanite** — DISPLAY: virtualized geometry / per-pixel cluster streaming; shows imported triangles at any density without us authoring LODs. Truth stays our elements.
- **Lumen GI/Reflections** — DISPLAY: real-time light feeding the existing `U.light` seam in `web/renderer/splat.wgsl`; it lights, never owns.
- **PCG Framework** — AUTHORING: generates POINTS from spatial data (volumes/surfaces/meshes), GPU for perf; 5.7 Editor Mode + experimental Procedural Vegetation plugin. The concrete "static meshes in → triangles translated" mechanism, but per THE_TRANSLATION it authors IN only — ANY post-translation mesh edit is a violation, so our sampler is the sole field writer.
- **World Partition** — AUTHORING/streaming: streaming grid + one-file-per-actor + Data/HLOD layers streams DISPLAY/AUTHORING regions by camera position; never element state.
- **Netcode replication + ML agents** — OPERATOR: replicate levers+seed not sim state (`theDeterminism` ladder); ML policies write LEVERS ∈ [0..1] (operator device with an AI at the wheel); drift caught by this doc's checksum falsifier.
Uniqueness recheck 2026: nearest neighbors unchanged — Avalanche (GPU-resident), Houdini per-point attrs (offline), Flex/GEM (millions of points on GPU); concrete current academic neighbor = **Newton** (newton-physics, NVIDIA Warp + MuJoCo-Warp; Disney/DeepMind/NVIDIA) — GPU-resident and per-element but a differentiable robotics sim, NOT the welded one-buffer physics+picture+control with CPU levers. No shipping engine has the weld; UE5 Chaos "GPU simulation" is still the part most likely to be mistaken for this (offloads stepping, does not hand over the clock).

## T2 FIRST CA RUN — PRE-REGISTERED (continuation-4, before build)
Lattice from `models/cad_bear/cad_bear.glb` via `cad_sample.load_glb_triangles` (the bit-exact import chain): 59,712 tris / ~30.8k verts, 19 watertight per-part shells; shared-edge adjacency WITHIN a part only (parts share no vertices — cross-shell coupling is the fold walk's job, not the CA's; stated as structure, not apology). A₀ per triangle at parse: |e1×e2|/2.
Space and scale, all from `LightEngine/constants.py` (no SI this run): vertices scaled to walk space by S = R_BOND / e_med where e_med = median shared-edge length of the parsed lattice (named ratio — flagged synthesis); vertex mass m = 1 each (the seed's dimensionless convention); k_area = K_BOND/R_BOND² — the bond spring stiffness constants.py already derives in its GAMMA_W block, i.e. derived-never-picked and zero new free numbers.
Update rule: one area mode per triangle — F(v) = −k·(A/A₀−1)·∇A, ∇A finite-difference-checked against the analytic signed-area gradient at build time ("a calculus equation brought to a footstep"); symplectic Euler, dt = DT from the seed.
RUN A (bond-law match, static): per shared edge, CA stiffness slope vs the M=0 bond algebra exactly as in `LightEngine/modifier.py` (`fb = kb(r−rb)/(rb·r)`, linearized at r=R_BOND: slope K_BOND/R_BOND²). Gate: relative error ≤ 1% (flagged synthesis tolerance — same number as the energy gate).
RUN B (liveness + energy, live): from rest at import pose under the fold walk read by `compute_forces_mod` (GPU, octree rebuilt per tick — a live frame's tree moves with its points; honesty line), 1000 ticks. Gates: spring PE + KE drift < 1%; finiteness (no NaN); max |A/A₀−1| PRINTED as the honesty line that feeds the band-clamp sub-gate (the number is still derived after this run, not named here).
FALSIFIER inherits the membrane shell: energy drift > 1% / clamp on a hold / NaN / any code path that edits mesh after translation. Cad_bear because THE_TRANSLATION Run 3 stands to the letter (mass err 0.000%, iner ≤ 1.921%).

## PARALLEL OCTREE — SFC-keyed tree build (operator directive, Rule-0 shell)
The operator's algorithm, verbatim: "map your points to integer coordinates, then compute their 3D Hilbert or Z-order keys; 1) sort those keys with a parallel radix sort; 2) run a prefix sum to create leaf cells; 3) link the leaves upward into internal nodes using GPU kernels."
Contract: output = `bh_draw`'s exact tree-dict format ({sorted_pos, sorted_idx, cell_min, cell_max, cell_com, cell_mass, cell_child, cell_is_leaf, cell_leaf_start, cell_leaf_count}) so `compute_forces_mod` consumes it UNCHANGED — the folded walk is referee infrastructure (T4 measured on it; `agent_logs/envelope_million.json` stays comparable). A build that changes the walk to fit its own tree violates the door contract.
- STATEMENT: an SFC-keyed parallel octree build produces a valid nested octree in that format, at any point count the GPU holds.
- PREDICTION: on two reference scenes — cad_bear's 30,768 walk-space positions and T4's exact 1M uniform scene (same seed/scene as `envelope_million.json`) — per-point forces from the new tree vs `build_octree` at theta=DEFAULT_THETA(0.3), leaf_size 16 agree ≤ 1% relative (flagged synthesis tolerance); structural invariants: every child box ⊂ parent box, bottom-up com/mass recompute matches stored values to float32 epsilon, no leaf over 16.
- FALSIFIER: any of — non-finite or walk exception; nesting violation; com-mass mismatch beyond float32 epsilon; force rel diff > 1% on EITHER scene. Until it passes, NO build may claim per-tick tree rebuild at scale — the known CPU-visible cost in RUN B is exactly this single-threaded octree (source-verified: `LightEngine/bh_draw.py` kernels carry no prange; the walk itself is one-thread-per-point GPU and does not show in CPU usage). Do NOT touch `bh_draw.py` itself — new builder lives beside it, old one stays referee.

### MEASURED RESULT (continuation-10) — FALSIFIER FIRES; root cause named, not papered over
Built the corrected SFC builder (`LightEngine/bh_sfc.build_octree_sfc`) per the verbatim algorithm and ran `tools/gate_octree_sfc.py`. Two bugs found+fixed on the way (both real): (1) the occupancy-bump loop never terminated on coincident data — cad_bear has **3,431 exact float32 duplicates** whose max run plateaus at 43; a grid can never split identical points, so "bump B until ≤16" overflows past B>1024. Fix: refine until occupancy **plateaus** (residual = true coincidence), mirroring `build_octree`'s own `n_nonempty==1` oversized-leaf guard — no free number. (2) com/mass/min/max were written into GLOBAL `cell_*` slots using LOCAL parent ids (only correct at the root where offset=0) → root mass 281≠500, nesting broken; fixed with a local→global map.
After both fixes the tree is STRUCTURALLY VALID on both scenes (partition=n exact, root mass exact, zero nesting violations, com/mass to f32 eps). The gate still FIRES on force:
- cad_bear: **9.04%** rel vs `build_octree` (gate ≤1%).
- T4-1M uniform: **2.97%** rel vs `build_octree` (gate ≤1%); invariants all pass here.
Root cause, measured against an O(n²) ground-truth sum (`dbg`, n=2048/4096): the REFEEER is ~0.1% from truth at θ=0.3; my SFC tree is **~24× less accurate** (θ=0.3: ref 0.144% vs sfc 3.45%; both →0 as θ→0, so mine is a VALID convergent Barnes-Hut tree, just with a ~24× higher truncation constant). Cause: uniform-depth fixed-grid nodes make different (s,d) theta decisions than the adaptive referee — inherent to the operator's verbatim algorithm, not a fixable defect without making it adaptive. Build cost also WORSE, not better: T4-1M sfc 18.2 s vs ref 2.1 s (uniform grid builds deep structure in sparse regions the adaptive tree skips → 2.06M cells vs 293k); cad_bear sfc 0.79 s vs ref 0.34 s.
**Verdict:** T13-as-specified does NOT hold — the SFC build is neither a ≤1% drop-in for `build_octree` nor faster than the single-core BFS it was meant to replace. The "one core" pain is NOT solved by this construction. Per membrane: NO per-tick-rebuild-at-scale claim until it passes; it does not pass. Operator fork (his call, I do not pick): (a) keep `build_octree` as referee and make ITS build parallel/GPU instead of swapping trees; (b) run the SFC tree at a lower θ for accuracy (changes THE law's knob — not a free param); (c) accept the CPU-build cost. Gate + builder stay on disk as the honest record; `agent_logs/gate_octree_sfc.json` holds the numbers.

### MULTI-CORE REFEREEER BUILD — option (a), Rule-0 membrane (continuation-11)
**Operator pick: (a)** — keep `build_octree` as referee, make ITS build multi-core instead of swapping trees. Solves the single-core pain WITHOUT sacrificing the ≤1% adaptive accuracy, because it builds the *same* tree.
- **STATEMENT:** a level-synchronous BFS that schedules each cell's partition across all cores produces a tree BYTE-IDENTICAL to serial `LightEngine.bh_draw.build_octree` (same cells, same com/mass/min/max/child structure, same leaf memberships), so `_bh_cuda`/`compute_forces_mod` consume it UNCHANGED.
- **WHY IT IS IDENTICAL (not just ≤1%):** each cell's partition is the referee's exact njit `_partition_and_bounds` on its own disjoint `order[start:end]`; a cell's fate (leaf / coincident-guard / children) depends only on ITS points, so cells at one level are independent and can run in parallel. Children are created in parent-id × code order == serial BFS dequeue order → global cell ids match exactly; bottom-up com/mass reuses the referee's `_compute_com_mass`. Numba `@njit` releases the GIL during compiled execution, so a thread pool of workers each calling `_partition_and_bounds` on disjoint ranges runs truly in parallel (shared memory, no pickling).
- **PREDICTION:** on cad_bear (28,917) and T4-1M (1,000,000), every output array equals serial `build_octree` exactly (`np.array_equal`) → force rel err = 0.0% by construction; build wall-time drops vs serial with a measured speedup on the 24-core box.
- **FALSIFIER:** any output array differing from serial `build_octree`; OR no meaningful speedup (secretly still single-threaded — the exact pain this exists to kill); OR a crash/race. Residual named up-front: level-0 (root, 1 cell) and `_compute_com_mass` are still single-core in v1 → measured as the honest residual; within-cell parallel partition is the Phase-B membrane if that residual is significant.
- **No free parameter:** `workers = os.cpu_count()` (the box's own cores); leaf_size/θ unchanged from the referee. Reuses `_partition_and_bounds`/`_compute_com_mass`/`_pad_bounds` — no hand-rolled partition.

### MEASURED RESULT (continuation-12) — byte-identity ACHIEVED; speedup FALSIFIER FIRES; diagnosis CORRECTED
Built `LightEngine/bh_octree_mt.build_octree_mt` (level-synchronous BFS, thread-pool over cells per level, reusing the referee's exact njit `_partition_and_bounds`) and ran `tools/gate_octree_mt.py`. `agent_logs/gate_octree_mt.json` holds the numbers.
- **BYTE-IDENTITY: PASS on BOTH scenes** (cad_bear 28,917 + T4-1M 1,000,000): every output array key `np.array_equal` to serial `build_octree`; GPU force rel err = **0.0%** through the same `compute_draw_bh` kernel on both trees (bit-identical). The accuracy claim is SOLID — v1 builds the *same* tree, so `_bh_cuda`/`compute_forces_mod` consume it unchanged and the force is 0.0% by construction.
- **SPEEDUP: FALSIFIER FIRES** (membrane line "no meaningful speedup / secretly still single-threaded"): cad_bear **0.83×** (slower than serial — thread-pool overhead > work on a small scene), T4-1M **0.97×** (break-even). No net multi-core win.
- **PROFILE corrects continuation-11's "root spike caps it" assumption** (T4-1M, measured): full serial build 2405 ms; `_compute_com_mass` = **7.9 ms**; single root partition of all 1M pts = **17.9 ms (≈0.75%)**; BFS + per-cell Python overhead = total − commass ≈ **2398 ms**. The root spike and com/mass are BOTH negligible; the DOMINANT cost is Python-level BFS orchestration over ~293k cells (per-cell scratch allocs `np.empty(8)`/`np.full((8,3))`, list appends, njit call overhead).
- **Why v1 can't win:** it parallelizes only the small njit-partition fraction (~60–100 ms of 2405) across threads; the ~2398 ms Python orchestration runs serially in the main thread (child-creation + level management). Threading overhead ≥ the tiny parallelizable gain → no net speedup.
- **Verdict:** option-(a) v1 delivers BYTE-IDENTITY (the accuracy half) but NOT the multi-core speedup. The "one core" pain is still not solved by this construction — same honest bar as continuation-10's SFC verdict, now on the referee build itself.

### PHASE B' — CORRECTED membrane (continuation-12): kill the PYTHON BFS overhead, then split across cores
The original Phase-B target (within-cell parallel partition) is RETIRED as mis-scoped: it would parallelize ~60–100 ms of 2405 and still leave ~2398 ms serial. The real fix has two parts, in order:
- **B1 — de-Python the BFS (single-core first):** move the whole level-synchronous build into ONE `@njit` function (C-speed), reusing `_partition_and_bounds`'s counting-sort logic inline; preallocate scratch (reuse one `(8,)`/`(8,3)` buffer per cell instead of allocating ~4 arrays × 293k cells — the njit already resets `child_mins/maxs` to inf/-inf each call). PREDICTION: serial build drops from ~2405 ms toward the pure-compute floor (root partition alone is only 18 ms, so a C-speed BFS should land well under it); BYTE-IDENTICAL to `build_octree` by construction (same algorithm, same njit partition). FALSIFIER: any output array differing; OR no large drop in serial wall-time (means the cost was not Python overhead — re-profile).
- **B2 — split the compiled BFS across cores:** only after B1 is byte-identical AND fast-on-one-core. A single `@njit` runs one thread, so multi-core needs either (i) a sort-based build on the GPU via `LightEngine/parlib.py` (`stable_sort_by_key` + `parallel_scan` — the off-the-shelf primitives already there; byte-identity to the adaptive referee then needs its OWN proof, not assumed), or (ii) CPU multi-process over disjoint root sub-ranges with a byte-identical merge. PREDICTION: W× on the 24-core box once B1's serial floor is in place. FALSIFIER: speedup ≈1× again (still one core).
- **No free parameter:** workers = `os.cpu_count()`; leaf_size/θ unchanged. Reuse `_partition_and_bounds`/parlib — no hand-rolled partition/sort.
**Next agent, build B1 first** (cheapest falsifier: does a C-speed BFS drop the 2405 ms and stay byte-identical?). Do NOT build within-cell parallel partitioning — it is not the bottleneck.

### B1 MEASURED (continuation-13) — BYTE-IDENTITY PASS; serial build drops to ~6.6% of referee
Built `LightEngine/bh_octree_njit.py` (`build_octree_njit`: ONE `_build_core` @njit mirroring the BFS exactly, reusing the referee's njit `_partition_and_bounds` + `_compute_com_mass`, scratch preallocated once at `max_cells = 2n`) and gate `tools/gate_octree_njit.py` (reuses `_load_cad_bear`/`_load_t4_million` from `gate_octree_sfc`). Numbers in `agent_logs/gate_octree_njit.json` (+ run log `agent_logs/gate_octree_njit_run.txt`).
- **BYTE-IDENTITY: PASS on BOTH scenes** — all 12 output keys agree in value + dtype + shape (cad_bear 28,917; T4-1M 1,000,000). Force = 0.0% by construction (same tree into the same kernel).
- **SERIAL DROP: PASS** (median of 5 reps after JIT warm-up): cad_bear ref 44.5 → njit **3.5 ms**; T4-1M ref 2097.6 → njit **138.1 ms** (~15×; 6.6% of referee). The ~2398 ms Python orchestration is gone, as the profile predicted.
- **One falsifier fired and was fixed (recorded, not hidden):** first gate run MISMATCHED `cell_min`/`cell_max`. Root cause: `_pad_bounds`'s `eps_pad = 1e-6 * max(1.0, span)` is computed by numpy in f64 then cast to f32 (value-based casting); the njit mirror did a pure-f32 multiply → 1-ulp divergence on some cells. Fix: `eps = f32(f64(1e-6) * max(f64(1.0), span))` at both root and child pad sites. Re-run: byte-identical.
- **Scope honesty:** B1 is a SINGLE-CORE win — no multi-core claim yet (one @njit = one thread). The "24 cores" pain is still open; that is exactly what B2 exists for, and its gate condition (B1 byte-identical AND fast-on-one-core) is now MET. **Next: B2** — sort-based GPU build via parlib (`stable_sort_by_key` + `parallel_scan`) OR CPU multi-process over disjoint root sub-ranges with a byte-identical merge; each candidate needs its OWN byte-identity proof, not assumed.

### B2 PRE-REGISTERED (continuation-13) — serial-floor breakdown; the W× prediction is CORRECTED by measurement
Profiled T4-1M on the B1 build (medians of 5, post-JIT): `_build_core` BFS+partition = **98.2 ms** (includes ~7 ms defensive input copies in my harness); `_compute_com_mass` = **3.2 ms** (n_cells=293,478); wrapper remainder (allocs + `sorted_pos = pos[order]` fancy index + slices) = 138.1 − 98.2 − 3.2 ≈ **36.7 ms**.
- **Prediction correction (Rule-0 honesty):** B2's "W× on the 24-core box" was written BEFORE this floor was measured. Partition is ~98/138 ≈ 71% of the serial floor; even FULLY parallel across 24 cores, T4-1M speedup ceiling = 138.1 / (36.7 + 3.2 + 98.2/24) ≈ **3.1×** — derived from the measured components, not picked. The "W×" line is hereby superseded by this number.
- **Cheaper win available regardless of B2:** the CA walk rebuilds the tree EVERY tick — per-tick wrapper allocs + `pos[order]` copy (~37 ms) are pure waste; a persistent preallocated buffer pool (reused across ticks, only re-filled) removes it without any parallelism. Do this FIRST if the pain is wall-time.
- **B2 candidate A (CPU, now preferred over multi-process):** restructure `_build_core` into LEVEL-SYNCHRONOUS form with numba `prange` over the cells of one level — NO Python dispatch (v1's failure mode was per-cell *Python* njit dispatch overhead; prange stays compiled). Byte-identity mechanism: per-level prefix-sum over "non-empty children per cell" → child id = base[parent] + local code offset, which reproduces serial BFS's parent-id × code id order exactly. Per-iteration scratch (`cs/ce/cm/cx`) as loop-local arrays (per-thread stack).
- **B2 candidate B (GPU parlib sort-based):** unchanged from the membrane; still needs its OWN byte-identity proof.
- **FALSIFIER unchanged:** speedup ≈1× again → still one core. New bar: beat the 3.1× ceiling only if prange efficiency exceeds expectation — record whatever lands, honestly.

### B2 (A) MEASURED (continuation-13) — BYTE-IDENTITY PASS; speedup FALSIFIED vs its own serial
Built `LightEngine/bh_octree_prange.py` (`build_octree_prange`: level-synchronous 3-pass prange — partition+count / prefix-sum base ids / commit at cid = base[parent]+j) + gate `tools/gate_octree_prange.py`. Numbers in `agent_logs/gate_octree_prange.json` (+ run log).
- **BYTE-IDENTITY PASS both scenes** — all 12 keys agree (induction held: FIFO BFS == level order; parent-id × code-order id merge exact). The prefix-sum id-merge machinery is now a PROVEN reusable asset for any future parallel build.
- **SPEEDUP FALSIFIED vs its own purpose:** prange T4-1M = **149.3 ms** vs B1 serial njit 138.1 ms → **0.93×**. (The gate's "14.04×" is vs the Python-BFS referee — that is B1's already-landed win, NOT a multi-core win; bear: 3.8 vs 44.8 ms, same story.) Membrane line "speedup ≈1× again (still one core)" FIRES for B2-A as constructed.
- **Diagnosis (measured, not guessed):** threading layer confirmed ENGAGED — NUMBA_NUM_THREADS=24; pure prange loop over 24M elems: serial 13.44 → prange 3.92 ms. So the loss is construction overhead, not absent threads: per-level staging allocs (~20 levels × up to ~20 MB `np.empty` inside njit) + per-level thread barriers + false sharing on adjacent cell rows (a 12 B row = 5 rows/cacheline) eat the parallel gain on a floor that is already only 98 ms of partition.
- The pre-registered ~3.1× ceiling was an IDEALIZED bound (partition fully parallel, zero overhead); measured reality lands below even B1 serial. Recorded, not papered over — same honest bar as v1 mt's FALSIFIED record.
- **B2 candidate B (GPU parlib sort-based) RETIRED by continuation-10's measurement:** the SFC gate already showed a key-sorted (space-filling-curve) tree is ~24× less accurate than adaptive — "byte-identity to the adaptive referee" has no known construction; measured dead adjacent, not assumed.
- **Next cheapest win for wall-time pain (NO parallelism needed): persistent buffer pool** — the CA walk rebuilds every tick; the wrapper's ~37 ms (allocs + `pos[order]` copy) is pure per-tick waste. Floor → ~101 ms serial on T4-1M. B1's 138.1 ms stands as the landed win until then.

### CA-WALK SWAP MEASURED (continuation-14) — byte-identical drop-in LANDED in the live walk; per-tick tree build drops ~12×
The one-line swap (`tools/ca_triangle.py` L903: `build_octree` → `build_octree_njit`, import at L47) is now what RUN B actually runs. Validated by a full run to completion (RUN A + RUN B, 1000 ticks), not assumed:
- **Physics verdicts identical to the prior verified pass** (byte-identical tree ⇒ same forces): RUN A rel err 2.5e-9 PASS; RUN B finiteness HOLDS, energy gate PASS net of radiation (`E0=−832760 → E_end=−828509`, dE 4251 ≤ rad 19.9 + 1%·peak), max strain **2.19%** (same honesty line as §T2-landed), band held; curv domain 9.76e-3 / raw 0.364 excluded per the §19 domain-restriction ledger (n_curv_flat_excluded=14,458). `models/cad_bear/ca_run.json` on disk reflects this run.
- **The win measured at source:** `ms_per_tick.tree = 3.69 ms` (was ~44.5 ms Python BFS) → **~12× per-tick tree-build drop** on bear, exactly the B1 gate's prediction (44.5→3.5 ms). RSS flat 0.49 GB to tick 1000; memory guard never fired.
- **Scope honesty:** this is a SINGLE-CORE win (one @njit burst per tick) — it removes the visible pinned-core pain the operator kept killing runs for, at zero physics cost. The 24-core question stays open exactly where B2 left it: B2-A FALSIFIED (0.93×), candidate B retired; **persistent buffer pool remains NEXT** (~37 ms/tick wrapper kill inside `build_octree_njit` → T4-1M floor 138.1→~101 ms serial). The CA walk's bear per-tick build is now ~3.5 ms of that.
- **Do-not-regress note:** if a future run regresses, revert ONLY the two hunks (import L47 + call site L903); everything else in this file was untouched by the swap.
